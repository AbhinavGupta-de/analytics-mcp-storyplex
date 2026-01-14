"""Browser-based scraper using Playwright for tricky sites.

Use this for sites that:
- Have Cloudflare protection
- Require JavaScript rendering
- Have aggressive anti-bot measures
"""

import asyncio
from typing import Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright


class BrowserScraper:
    """Browser-based scraper using Playwright."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._playwright = None

    async def __aenter__(self):
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self.headless)
        self._context = await self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def get_page(self) -> Page:
        """Get a new page."""
        if not self._context:
            raise RuntimeError("Browser not initialized. Use async with.")
        return await self._context.new_page()

    async def fetch_with_js(
        self,
        url: str,
        wait_for: Optional[str] = None,
        wait_time: int = 2000,
    ) -> str:
        """Fetch a URL and wait for JavaScript to render.

        Args:
            url: The URL to fetch
            wait_for: CSS selector to wait for (optional)
            wait_time: Time to wait after load (ms)

        Returns:
            The page HTML content
        """
        page = await self.get_page()
        try:
            await page.goto(url, wait_until="networkidle")

            if wait_for:
                await page.wait_for_selector(wait_for, timeout=10000)

            await page.wait_for_timeout(wait_time)

            return await page.content()
        finally:
            await page.close()

    async def bypass_cloudflare(self, url: str, max_retries: int = 3) -> str:
        """Attempt to bypass Cloudflare protection.

        Args:
            url: The URL to access
            max_retries: Maximum number of retry attempts

        Returns:
            The page HTML content after Cloudflare check
        """
        page = await self.get_page()
        try:
            for attempt in range(max_retries):
                await page.goto(url)

                # Wait for Cloudflare challenge to complete
                # Look for common Cloudflare challenge indicators
                cloudflare_selectors = [
                    "#challenge-running",
                    "#cf-challenge-running",
                    ".cf-browser-verification",
                ]

                for selector in cloudflare_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            # Wait for challenge to complete
                            await page.wait_for_selector(
                                selector,
                                state="hidden",
                                timeout=30000,
                            )
                            break
                    except Exception:
                        continue

                # Check if we passed the challenge
                content = await page.content()
                if "Just a moment" not in content and "Checking your browser" not in content:
                    return content

                # Wait before retry
                await page.wait_for_timeout(5000)

            # Final attempt
            return await page.content()

        finally:
            await page.close()

    async def screenshot(self, url: str, path: str) -> None:
        """Take a screenshot of a page.

        Args:
            url: The URL to screenshot
            path: Path to save the screenshot
        """
        page = await self.get_page()
        try:
            await page.goto(url, wait_until="networkidle")
            await page.screenshot(path=path, full_page=True)
        finally:
            await page.close()


async def test_browser():
    """Test the browser scraper."""
    async with BrowserScraper(headless=True) as browser:
        # Test fetching AO3
        html = await browser.fetch_with_js(
            "https://archiveofourown.org/works/12345678",
            wait_for="h2.title",
        )
        print(f"Got {len(html)} bytes of HTML")


if __name__ == "__main__":
    asyncio.run(test_browser())
