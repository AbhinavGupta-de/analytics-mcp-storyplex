"""Base scraper abstraction for all platform scrapers."""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterator, Optional

import httpx
from rich.console import Console

from src.config import settings
from src.db.models import ContentRating, PlatformType, WorkStatus

console = Console(stderr=True)


@dataclass
class ScrapedAuthor:
    """Scraped author data."""

    platform_author_id: str
    username: str
    display_name: Optional[str] = None
    profile_url: Optional[str] = None
    bio: Optional[str] = None
    joined_date: Optional[datetime] = None
    work_count: int = 0
    patreon_url: Optional[str] = None
    kofi_url: Optional[str] = None


@dataclass
class ScrapedWork:
    """Scraped work data ready for database insertion."""

    platform_work_id: str
    title: str
    url: str

    # Author
    author: Optional[ScrapedAuthor] = None

    # Metadata
    summary: Optional[str] = None
    rating: ContentRating = ContentRating.NOT_RATED
    language: str = "English"
    is_translated: bool = False
    original_language: Optional[str] = None

    # Structure
    status: WorkStatus = WorkStatus.UNKNOWN
    chapter_count: int = 0
    word_count: int = 0

    # Timestamps
    published_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Engagement
    views: int = 0
    likes: int = 0  # kudos, votes, etc.
    comments: int = 0
    bookmarks: int = 0
    subscribers: int = 0  # followers

    # Tags and categories
    tags: list[str] = field(default_factory=list)
    fandoms: list[str] = field(default_factory=list)
    relationships: list[str] = field(default_factory=list)
    characters: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class BaseScraper(ABC):
    """Abstract base class for all platform scrapers.

    All scrapers must implement:
    - platform_type: The platform identifier
    - base_url: The base URL for the platform
    - scrape_work: Scrape a single work by ID
    - search_works: Search/list works with filters

    The base class provides:
    - Rate limiting
    - HTTP client with retries
    - Logging
    """

    def __init__(self, rate_limit: Optional[float] = None):
        """Initialize the scraper.

        Args:
            rate_limit: Requests per second (None uses platform default)
        """
        self.rate_limit = rate_limit or self._default_rate_limit()
        self._last_request_time: float = 0
        self._client = httpx.Client(
            headers={
                "User-Agent": settings.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0",
            },
            timeout=settings.request_timeout,
            follow_redirects=True,
            http2=True,
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._client.close()

    @property
    @abstractmethod
    def platform_type(self) -> PlatformType:
        """Return the platform type identifier."""
        pass

    @property
    @abstractmethod
    def base_url(self) -> str:
        """Return the base URL for this platform."""
        pass

    def _default_rate_limit(self) -> float:
        """Return default rate limit for this platform."""
        return settings.default_rate_limit

    def _wait_for_rate_limit(self) -> None:
        """Wait to respect rate limiting."""
        if self.rate_limit <= 0:
            return

        min_interval = 1.0 / self.rate_limit
        elapsed = time.time() - self._last_request_time
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_request_time = time.time()

    def _get(self, url: str, **kwargs) -> httpx.Response:
        """Make a rate-limited GET request."""
        self._wait_for_rate_limit()
        response = self._client.get(url, **kwargs)
        response.raise_for_status()
        return response

    @abstractmethod
    def scrape_work(self, work_id: str) -> Optional[ScrapedWork]:
        """Scrape a single work by its platform-specific ID.

        Args:
            work_id: The platform-specific work identifier

        Returns:
            ScrapedWork if found, None otherwise
        """
        pass

    @abstractmethod
    def search_works(
        self,
        query: Optional[str] = None,
        fandom: Optional[str] = None,
        tag: Optional[str] = None,
        sort_by: str = "popular",
        limit: int = 100,
    ) -> Iterator[ScrapedWork]:
        """Search for works matching criteria.

        Args:
            query: Text search query
            fandom: Filter by fandom
            tag: Filter by tag
            sort_by: Sort order (platform-specific)
            limit: Maximum number of results

        Yields:
            ScrapedWork for each matching work
        """
        pass

    def log_info(self, message: str) -> None:
        """Log an info message."""
        console.print(f"[blue][{self.platform_type.value}][/blue] {message}")

    def log_error(self, message: str) -> None:
        """Log an error message."""
        console.print(f"[red][{self.platform_type.value}][/red] {message}")

    def log_success(self, message: str) -> None:
        """Log a success message."""
        console.print(f"[green][{self.platform_type.value}][/green] {message}")
