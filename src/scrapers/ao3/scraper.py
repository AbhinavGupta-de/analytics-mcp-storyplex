"""AO3 (Archive of Our Own) scraper implementation.

AO3 has no official API but allows non-commercial scraping under CC BY-NC-SA.
This scraper uses Playwright to bypass bot detection.

Important: AO3's November 2024 ToS update prohibits commercial scraping for AI training.
This tool is for personal research and analytics only.
"""

import re
from datetime import datetime
from typing import Iterator, Optional
from urllib.parse import urlencode, urljoin

from bs4 import BeautifulSoup, Tag
from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext

from src.config import settings
from src.db.models import ContentRating, PlatformType, WorkStatus
from src.scrapers.base import BaseScraper, ScrapedAuthor, ScrapedWork


class AO3Scraper(BaseScraper):
    """Scraper for Archive of Our Own (AO3) using Playwright browser."""

    def __init__(self, rate_limit: Optional[float] = None, headless: bool = True):
        """Initialize the AO3 scraper with Playwright browser.

        Args:
            rate_limit: Requests per second (None uses platform default)
            headless: Run browser in headless mode
        """
        super().__init__(rate_limit)
        self.headless = headless
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    def __enter__(self):
        # Close the httpx client from parent, we'll use Playwright instead
        self._client.close()

        # Start Playwright
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(headless=self.headless)
        self._context = self._browser.new_context(
            user_agent=settings.user_agent,
            viewport={"width": 1920, "height": 1080},
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def _browser_get(self, url: str, timeout: int = 60000) -> str:
        """Fetch a URL using Playwright browser.

        Args:
            url: The URL to fetch
            timeout: Timeout in milliseconds (default 60s)

        Returns:
            The page HTML content
        """
        self._wait_for_rate_limit()

        page = self._context.new_page()
        page.set_default_timeout(timeout)

        try:
            self.log_info(f"Navigating to: {url}")
            response = page.goto(url, wait_until="networkidle", timeout=timeout)

            # Check for HTTP errors
            if response and response.status >= 400:
                self.log_error(f"HTTP {response.status} for {url}")
                if response.status == 403:
                    raise Exception("AO3 blocked request (403 Forbidden) - may need to retry")
                elif response.status == 429:
                    raise Exception("Rate limited by AO3 (429) - please wait and retry")
                elif response.status == 404:
                    raise Exception(f"Page not found (404): {url}")
                else:
                    raise Exception(f"HTTP error {response.status}")

            page.wait_for_timeout(1000)  # Additional wait for dynamic content
            return page.content()
        except Exception as e:
            self.log_error(f"Browser fetch failed: {e}")
            raise
        finally:
            page.close()

    @property
    def platform_type(self) -> PlatformType:
        return PlatformType.AO3

    @property
    def base_url(self) -> str:
        return "https://archiveofourown.org"

    def _default_rate_limit(self) -> float:
        return settings.ao3_rate_limit  # 0.2 rps = 1 request per 5 seconds

    def _parse_number(self, text: Optional[str]) -> int:
        """Parse a number from text, handling commas."""
        if not text:
            return 0
        # Remove commas and non-digit characters
        cleaned = re.sub(r"[^\d]", "", text)
        return int(cleaned) if cleaned else 0

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse AO3 date format (YYYY-MM-DD)."""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str.strip(), "%Y-%m-%d")
        except ValueError:
            return None

    def _map_rating(self, rating_text: str) -> ContentRating:
        """Map AO3 rating to normalized ContentRating."""
        rating_lower = rating_text.lower()
        if "general" in rating_lower:
            return ContentRating.GENERAL
        elif "teen" in rating_lower:
            return ContentRating.TEEN
        elif "mature" in rating_lower:
            return ContentRating.MATURE
        elif "explicit" in rating_lower:
            return ContentRating.EXPLICIT
        return ContentRating.NOT_RATED

    def _map_status(self, status_text: str) -> WorkStatus:
        """Map AO3 work status to normalized WorkStatus."""
        status_lower = status_text.lower()
        if "complete" in status_lower:
            return WorkStatus.COMPLETED
        elif "in progress" in status_lower or "work in progress" in status_lower:
            return WorkStatus.ONGOING
        return WorkStatus.UNKNOWN

    def _extract_tags_from_list(self, ul_element: Optional[Tag]) -> list[str]:
        """Extract tag names from a UL element."""
        if not ul_element:
            return []
        tags = []
        for li in ul_element.find_all("li"):
            a_tag = li.find("a")
            if a_tag:
                tags.append(a_tag.get_text(strip=True))
        return tags

    def _parse_work_blurb(self, blurb: Tag) -> Optional[ScrapedWork]:
        """Parse a work blurb from search/listing pages."""
        try:
            # Get work ID from the blurb
            work_id_match = blurb.get("id", "")
            if not work_id_match:
                return None
            work_id = work_id_match.replace("work_", "")

            # Title and URL
            title_link = blurb.select_one("h4.heading a")
            if not title_link:
                return None
            title = title_link.get_text(strip=True)
            url = urljoin(self.base_url, title_link.get("href", ""))

            # Author
            author = None
            author_link = blurb.select_one("h4.heading a[rel='author']")
            if author_link:
                author_href = author_link.get("href", "")
                author_id = author_href.split("/users/")[-1].split("/")[0] if "/users/" in author_href else ""
                author = ScrapedAuthor(
                    platform_author_id=author_id,
                    username=author_link.get_text(strip=True),
                    profile_url=urljoin(self.base_url, author_href) if author_href else None,
                )

            # Fandoms
            fandom_tags = blurb.select("h5.fandoms a.tag")
            fandoms = [f.get_text(strip=True) for f in fandom_tags]

            # Required tags (rating, warnings, category, status)
            rating = ContentRating.NOT_RATED
            status = WorkStatus.UNKNOWN
            warnings = []

            required_tags = blurb.select("ul.required-tags li")
            for req_tag in required_tags:
                span = req_tag.find("span")
                if span:
                    class_list = span.get("class", [])
                    text = span.get_text(strip=True)
                    if "rating" in class_list:
                        rating = self._map_rating(text)
                    elif "warning" in class_list:
                        warnings.append(text)
                    elif "iswip" in class_list:
                        status = self._map_status(text)

            # Additional tags
            tags_ul = blurb.select_one("ul.tags")
            relationships = []
            characters = []
            freeform_tags = []

            if tags_ul:
                for li in tags_ul.find_all("li"):
                    classes = li.get("class", [])
                    a_tag = li.find("a")
                    if a_tag:
                        tag_text = a_tag.get_text(strip=True)
                        if "relationships" in classes:
                            relationships.append(tag_text)
                        elif "characters" in classes:
                            characters.append(tag_text)
                        elif "freeforms" in classes:
                            freeform_tags.append(tag_text)

            # Summary
            summary_block = blurb.select_one("blockquote.userstuff.summary")
            summary = summary_block.get_text(strip=True) if summary_block else None

            # Stats
            stats = blurb.select_one("dl.stats")
            language = "English"
            word_count = 0
            chapter_count = 0
            views = 0
            likes = 0  # kudos
            comments = 0
            bookmarks = 0
            published_at = None
            updated_at = None

            if stats:
                # Language
                lang_dd = stats.select_one("dd.language")
                if lang_dd:
                    language = lang_dd.get_text(strip=True)

                # Word count
                words_dd = stats.select_one("dd.words")
                if words_dd:
                    word_count = self._parse_number(words_dd.get_text())

                # Chapters
                chapters_dd = stats.select_one("dd.chapters")
                if chapters_dd:
                    chapters_text = chapters_dd.get_text(strip=True)
                    # Format is "X/Y" where Y might be "?"
                    match = re.match(r"(\d+)", chapters_text)
                    if match:
                        chapter_count = int(match.group(1))

                # Hits (views)
                hits_dd = stats.select_one("dd.hits")
                if hits_dd:
                    views = self._parse_number(hits_dd.get_text())

                # Kudos (likes)
                kudos_dd = stats.select_one("dd.kudos")
                if kudos_dd:
                    likes = self._parse_number(kudos_dd.get_text())

                # Comments
                comments_dd = stats.select_one("dd.comments")
                if comments_dd:
                    comments = self._parse_number(comments_dd.get_text())

                # Bookmarks
                bookmarks_dd = stats.select_one("dd.bookmarks")
                if bookmarks_dd:
                    bookmarks = self._parse_number(bookmarks_dd.get_text())

            # Dates
            date_p = blurb.select_one("p.datetime")
            if date_p:
                date_text = date_p.get_text(strip=True)
                published_at = self._parse_date(date_text)
                updated_at = published_at  # Listing shows last update date

            return ScrapedWork(
                platform_work_id=work_id,
                title=title,
                url=url,
                author=author,
                summary=summary,
                rating=rating,
                language=language,
                status=status,
                chapter_count=chapter_count,
                word_count=word_count,
                published_at=published_at,
                updated_at=updated_at,
                views=views,
                likes=likes,
                comments=comments,
                bookmarks=bookmarks,
                tags=freeform_tags,
                fandoms=fandoms,
                relationships=relationships,
                characters=characters,
                warnings=warnings,
            )

        except Exception as e:
            self.log_error(f"Error parsing work blurb: {e}")
            return None

    def _parse_work_page(self, html: str, work_id: str) -> Optional[ScrapedWork]:
        """Parse a full work page for detailed information."""
        try:
            soup = BeautifulSoup(html, "lxml")

            # Check for error page
            if soup.select_one("div.error") or "Error 404" in html:
                return None

            # Title
            title_elem = soup.select_one("h2.title")
            if not title_elem:
                return None
            title = title_elem.get_text(strip=True)

            url = f"{self.base_url}/works/{work_id}"

            # Author
            author = None
            author_link = soup.select_one("h3.byline a[rel='author']")
            if author_link:
                author_href = author_link.get("href", "")
                author_id = author_href.split("/users/")[-1].split("/")[0] if "/users/" in author_href else ""
                author = ScrapedAuthor(
                    platform_author_id=author_id,
                    username=author_link.get_text(strip=True),
                    profile_url=urljoin(self.base_url, author_href) if author_href else None,
                )

            # Work meta (tags, rating, etc.)
            meta = soup.select_one("dl.work.meta")

            # Rating
            rating = ContentRating.NOT_RATED
            rating_dd = meta.select_one("dd.rating") if meta else None
            if rating_dd:
                rating = self._map_rating(rating_dd.get_text())

            # Warnings
            warnings = []
            warnings_dd = meta.select_one("dd.warning") if meta else None
            if warnings_dd:
                warnings = self._extract_tags_from_list(warnings_dd.find("ul"))

            # Fandoms
            fandoms = []
            fandom_dd = meta.select_one("dd.fandom") if meta else None
            if fandom_dd:
                fandoms = self._extract_tags_from_list(fandom_dd.find("ul"))

            # Relationships
            relationships = []
            rel_dd = meta.select_one("dd.relationship") if meta else None
            if rel_dd:
                relationships = self._extract_tags_from_list(rel_dd.find("ul"))

            # Characters
            characters = []
            char_dd = meta.select_one("dd.character") if meta else None
            if char_dd:
                characters = self._extract_tags_from_list(char_dd.find("ul"))

            # Additional tags
            tags = []
            tags_dd = meta.select_one("dd.freeform") if meta else None
            if tags_dd:
                tags = self._extract_tags_from_list(tags_dd.find("ul"))

            # Language
            language = "English"
            lang_dd = meta.select_one("dd.language") if meta else None
            if lang_dd:
                language = lang_dd.get_text(strip=True)

            # Summary
            summary = None
            summary_block = soup.select_one("div.summary blockquote.userstuff")
            if summary_block:
                summary = summary_block.get_text(strip=True)

            # Stats
            stats_dl = soup.select_one("dl.stats")
            published_at = None
            updated_at = None
            word_count = 0
            chapter_count = 0
            views = 0
            likes = 0
            comments = 0
            bookmarks = 0
            status = WorkStatus.UNKNOWN

            if stats_dl:
                # Published date
                pub_dd = stats_dl.select_one("dd.published")
                if pub_dd:
                    published_at = self._parse_date(pub_dd.get_text())

                # Updated/completed date
                status_dd = stats_dl.select_one("dd.status")
                if status_dd:
                    updated_at = self._parse_date(status_dd.get_text())
                else:
                    updated_at = published_at

                # Word count
                words_dd = stats_dl.select_one("dd.words")
                if words_dd:
                    word_count = self._parse_number(words_dd.get_text())

                # Chapters
                chapters_dd = stats_dl.select_one("dd.chapters")
                if chapters_dd:
                    chapters_text = chapters_dd.get_text(strip=True)
                    match = re.match(r"(\d+)/(\d+|\?)", chapters_text)
                    if match:
                        chapter_count = int(match.group(1))
                        expected = match.group(2)
                        if expected != "?" and int(expected) == chapter_count:
                            status = WorkStatus.COMPLETED
                        else:
                            status = WorkStatus.ONGOING

                # Hits
                hits_dd = stats_dl.select_one("dd.hits")
                if hits_dd:
                    views = self._parse_number(hits_dd.get_text())

                # Kudos
                kudos_dd = stats_dl.select_one("dd.kudos")
                if kudos_dd:
                    likes = self._parse_number(kudos_dd.get_text())

                # Comments
                comments_dd = stats_dl.select_one("dd.comments")
                if comments_dd:
                    comments = self._parse_number(comments_dd.get_text())

                # Bookmarks
                bookmarks_dd = stats_dl.select_one("dd.bookmarks")
                if bookmarks_dd:
                    bookmarks = self._parse_number(bookmarks_dd.get_text())

            return ScrapedWork(
                platform_work_id=work_id,
                title=title,
                url=url,
                author=author,
                summary=summary,
                rating=rating,
                language=language,
                status=status,
                chapter_count=chapter_count,
                word_count=word_count,
                published_at=published_at,
                updated_at=updated_at,
                views=views,
                likes=likes,
                comments=comments,
                bookmarks=bookmarks,
                tags=tags,
                fandoms=fandoms,
                relationships=relationships,
                characters=characters,
                warnings=warnings,
            )

        except Exception as e:
            self.log_error(f"Error parsing work page {work_id}: {e}")
            return None

    def scrape_work(self, work_id: str) -> Optional[ScrapedWork]:
        """Scrape a single work by its AO3 work ID."""
        url = f"{self.base_url}/works/{work_id}?view_adult=true"
        self.log_info(f"Scraping work {work_id}")

        try:
            html = self._browser_get(url)
            work = self._parse_work_page(html, work_id)
            if work:
                self.log_success(f"Scraped: {work.title}")
            return work
        except Exception as e:
            self.log_error(f"Failed to scrape work {work_id}: {e}")
            return None

    def search_works(
        self,
        query: Optional[str] = None,
        fandom: Optional[str] = None,
        tag: Optional[str] = None,
        sort_by: str = "kudos",
        limit: int = 100,
    ) -> Iterator[ScrapedWork]:
        """Search for works on AO3.

        Args:
            query: Text search in title/summary
            fandom: Filter by fandom name
            tag: Filter by tag name
            sort_by: Sort order (kudos, hits, bookmarks, date)
            limit: Maximum number of results

        Yields:
            ScrapedWork for each result
        """
        # Build search URL
        params = {
            "commit": "Sort and Filter",
            "work_search[sort_column]": self._map_sort(sort_by),
            "work_search[sort_direction]": "desc",
        }

        if query:
            params["work_search[query]"] = query

        # Determine base URL based on filters
        # AO3 uses special encoding for tags: periods become *d*, slashes become *s*
        def encode_tag(tag_name: str) -> str:
            return tag_name.replace(".", "*d*").replace("/", "*s*")

        if fandom:
            # Use fandom-specific tag page
            from urllib.parse import quote
            fandom_encoded = quote(encode_tag(fandom), safe="")
            base_search_url = f"{self.base_url}/tags/{fandom_encoded}/works"
        elif tag:
            from urllib.parse import quote
            tag_encoded = quote(encode_tag(tag), safe="")
            base_search_url = f"{self.base_url}/tags/{tag_encoded}/works"
        else:
            base_search_url = f"{self.base_url}/works"

        page = 1
        scraped_count = 0

        while scraped_count < limit:
            params["page"] = page
            url = f"{base_search_url}?{urlencode(params)}"

            self.log_info(f"Fetching page {page} ({scraped_count}/{limit} works)")

            try:
                html = self._browser_get(url)
                soup = BeautifulSoup(html, "lxml")

                # Find work blurbs
                blurbs = soup.select("li.work.blurb")
                if not blurbs:
                    self.log_info("No more works found")
                    break

                for blurb in blurbs:
                    if scraped_count >= limit:
                        break

                    work = self._parse_work_blurb(blurb)
                    if work:
                        scraped_count += 1
                        yield work

                # Check for next page
                next_link = soup.select_one("li.next a")
                if not next_link:
                    break

                page += 1

            except Exception as e:
                self.log_error(f"Error fetching page {page}: {e}")
                break

        self.log_success(f"Scraped {scraped_count} works total")

    def _map_sort(self, sort_by: str) -> str:
        """Map sort option to AO3 sort column."""
        sort_map = {
            "kudos": "kudos_count",
            "hits": "hits",
            "bookmarks": "bookmarks_count",
            "comments": "comments_count",
            "date": "revised_at",
            "words": "word_count",
        }
        return sort_map.get(sort_by.lower(), "kudos_count")

    def get_top_fandoms(self, limit: int = 100) -> list[dict]:
        """Get list of top fandoms by work count.

        Returns list of dicts with 'name', 'work_count', and 'category' keys.
        """
        url = f"{self.base_url}/media"
        self.log_info("Fetching top fandoms")

        try:
            html = self._browser_get(url)
            soup = BeautifulSoup(html, "lxml")

            fandoms = []

            # Find all category sections (li.medium.listbox.group)
            for category_section in soup.select("li.medium.listbox.group"):
                # Get category name from h3.heading
                h3 = category_section.select_one("h3.heading")
                category = h3.get_text(strip=True) if h3 else None

                # Get fandom items from ol.index.group > li
                for li in category_section.select("ol.index.group > li"):
                    a_tag = li.select_one("a.tag")
                    if a_tag:
                        name = a_tag.get_text(strip=True)
                        # Work count is in parentheses after the link
                        full_text = li.get_text(strip=True)
                        count_match = re.search(r"\((\d[\d,]*)\)", full_text)
                        work_count = self._parse_number(count_match.group(1)) if count_match else 0

                        fandoms.append({
                            "name": name,
                            "work_count": work_count,
                            "category": category,
                        })

            # Deduplicate by name (keep first occurrence with highest work count)
            seen = {}
            for fandom in fandoms:
                name = fandom["name"]
                if name not in seen or fandom["work_count"] > seen[name]["work_count"]:
                    seen[name] = fandom

            unique_fandoms = list(seen.values())

            # Sort by work count and limit
            unique_fandoms.sort(key=lambda x: x["work_count"], reverse=True)
            unique_fandoms = unique_fandoms[:limit]

            self.log_success(f"Found {len(unique_fandoms)} fandoms")
            return unique_fandoms

        except Exception as e:
            self.log_error(f"Error fetching fandoms: {e}")
            return []

    def get_fandom_tag_stats(self, fandom_tag: str) -> dict:
        """Get tag statistics for a specific fandom.

        Args:
            fandom_tag: The fandom tag as it appears in AO3 URLs
                       (e.g., "Harry Potter - J. K. Rowling" or URL-encoded version)

        Returns:
            Dict with tag categories and their counts
        """
        from urllib.parse import quote

        # Encode the fandom tag for URL (AO3 uses *d* for dots, *s* for slashes)
        def encode_tag(tag: str) -> str:
            return tag.replace(".", "*d*").replace("/", "*s*")

        encoded = quote(encode_tag(fandom_tag), safe="")
        url = f"{self.base_url}/tags/{encoded}/works"
        self.log_info(f"Fetching tag stats for {fandom_tag}")

        try:
            html = self._browser_get(url)
            soup = BeautifulSoup(html, "lxml")

            result = {
                "fandom": fandom_tag,
                "total_works": 0,
                "ratings": [],
                "warnings": [],
                "categories": [],
                "genres": [],  # freeform tags
                "relationships": [],
                "characters": [],
            }

            # Get total works count from heading - try multiple patterns
            # AO3 format: "1 - 20 of 556,855 Works in Fandom Name"
            for heading in soup.select("h2.heading"):
                heading_text = heading.get_text()
                # Match "of X Works" pattern (handles "1 - 20 of 556,855 Works in...")
                count_match = re.search(r"of\s+([\d,]+)\s+Works", heading_text)
                if count_match:
                    result["total_works"] = self._parse_number(count_match.group(1))
                    break

            # Parse filter sections
            def parse_tag_section(dd_class: str) -> list[dict]:
                section = soup.select_one(f"dd.{dd_class}.tags")
                tags = []
                if section:
                    for li in section.select("li"):
                        label = li.select_one("label")
                        if label:
                            text = label.get_text(strip=True)
                            # Extract name and count from "Tag Name (12345)"
                            match = re.match(r"(.+?)\s*\((\d[\d,]*)\)$", text)
                            if match:
                                tags.append({
                                    "name": match.group(1).strip(),
                                    "count": self._parse_number(match.group(2)),
                                })
                return tags

            result["ratings"] = parse_tag_section("rating")
            result["warnings"] = parse_tag_section("warning")
            result["categories"] = parse_tag_section("category")
            result["genres"] = parse_tag_section("freeform")
            result["relationships"] = parse_tag_section("relationship")
            result["characters"] = parse_tag_section("character")

            self.log_success(f"Found {len(result['genres'])} genre tags")
            return result

        except Exception as e:
            self.log_error(f"Error fetching tag stats: {e}")
            return {"fandom": fandom_tag, "error": str(e)}
