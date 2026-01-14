"""Tests for the AO3 scraper."""

from unittest.mock import MagicMock, patch


class TestAO3ScraperImports:
    """Test that scraper imports correctly."""

    def test_import_scraper(self):
        """Test that AO3Scraper can be imported."""
        from src.scrapers.ao3 import AO3Scraper

        assert AO3Scraper is not None

    def test_import_base_classes(self):
        """Test that base classes can be imported."""
        from src.scrapers.base import BaseScraper, ScrapedAuthor, ScrapedWork

        assert BaseScraper is not None
        assert ScrapedWork is not None
        assert ScrapedAuthor is not None


class TestAO3ScraperProperties:
    """Test scraper properties."""

    def test_platform_type(self):
        """Test platform type is correct."""
        from src.db.models import PlatformType
        from src.scrapers.ao3 import AO3Scraper

        # Mock playwright to avoid browser initialization
        with patch("src.scrapers.ao3.scraper.sync_playwright"):
            scraper = AO3Scraper.__new__(AO3Scraper)
            scraper._client = MagicMock()
            assert scraper.platform_type == PlatformType.AO3

    def test_base_url(self):
        """Test base URL is correct."""
        from src.scrapers.ao3 import AO3Scraper

        with patch("src.scrapers.ao3.scraper.sync_playwright"):
            scraper = AO3Scraper.__new__(AO3Scraper)
            scraper._client = MagicMock()
            assert scraper.base_url == "https://archiveofourown.org"


class TestAO3ScraperParsing:
    """Test parsing methods."""

    def test_parse_number(self):
        """Test number parsing."""
        from src.scrapers.ao3 import AO3Scraper

        with patch("src.scrapers.ao3.scraper.sync_playwright"):
            scraper = AO3Scraper.__new__(AO3Scraper)
            scraper._client = MagicMock()

            assert scraper._parse_number("1,234") == 1234
            assert scraper._parse_number("5678") == 5678
            assert scraper._parse_number("") == 0
            assert scraper._parse_number(None) == 0
            assert scraper._parse_number("1,234,567") == 1234567

    def test_parse_date(self):
        """Test date parsing."""
        from datetime import datetime

        from src.scrapers.ao3 import AO3Scraper

        with patch("src.scrapers.ao3.scraper.sync_playwright"):
            scraper = AO3Scraper.__new__(AO3Scraper)
            scraper._client = MagicMock()

            result = scraper._parse_date("2024-01-15")
            assert result == datetime(2024, 1, 15)

            assert scraper._parse_date("") is None
            assert scraper._parse_date(None) is None
            assert scraper._parse_date("invalid") is None

    def test_map_rating(self):
        """Test rating mapping."""
        from src.db.models import ContentRating
        from src.scrapers.ao3 import AO3Scraper

        with patch("src.scrapers.ao3.scraper.sync_playwright"):
            scraper = AO3Scraper.__new__(AO3Scraper)
            scraper._client = MagicMock()

            assert scraper._map_rating("General Audiences") == ContentRating.GENERAL
            assert scraper._map_rating("Teen And Up") == ContentRating.TEEN
            assert scraper._map_rating("Mature") == ContentRating.MATURE
            assert scraper._map_rating("Explicit") == ContentRating.EXPLICIT
            assert scraper._map_rating("Not Rated") == ContentRating.NOT_RATED

    def test_map_status(self):
        """Test status mapping."""
        from src.db.models import WorkStatus
        from src.scrapers.ao3 import AO3Scraper

        with patch("src.scrapers.ao3.scraper.sync_playwright"):
            scraper = AO3Scraper.__new__(AO3Scraper)
            scraper._client = MagicMock()

            assert scraper._map_status("Complete") == WorkStatus.COMPLETED
            assert scraper._map_status("Work in Progress") == WorkStatus.ONGOING
            assert scraper._map_status("Unknown") == WorkStatus.UNKNOWN


class TestScrapedWorkDataclass:
    """Test ScrapedWork dataclass."""

    def test_scraped_work_defaults(self):
        """Test ScrapedWork default values."""
        from src.db.models import ContentRating, WorkStatus
        from src.scrapers.base import ScrapedWork

        work = ScrapedWork(
            platform_work_id="123", title="Test Work", url="https://example.com/work/123"
        )

        assert work.platform_work_id == "123"
        assert work.title == "Test Work"
        assert work.author is None
        assert work.rating == ContentRating.NOT_RATED
        assert work.status == WorkStatus.UNKNOWN
        assert work.views == 0
        assert work.likes == 0
        assert work.tags == []
        assert work.fandoms == []


class TestScrapedAuthorDataclass:
    """Test ScrapedAuthor dataclass."""

    def test_scraped_author_creation(self):
        """Test ScrapedAuthor creation."""
        from src.scrapers.base import ScrapedAuthor

        author = ScrapedAuthor(
            platform_author_id="user123", username="testuser", display_name="Test User"
        )

        assert author.platform_author_id == "user123"
        assert author.username == "testuser"
        assert author.display_name == "Test User"
        assert author.bio is None
        assert author.work_count == 0
