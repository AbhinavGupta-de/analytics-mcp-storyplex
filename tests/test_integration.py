"""Integration tests for Storyplex Analytics.

These tests require:
- PostgreSQL database running
- Playwright browsers installed
- ANTHROPIC_API_KEY environment variable (for LLM tests)
"""

import os

import pytest

# Skip all integration tests if not explicitly enabled
pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_INTEGRATION_TESTS") != "1",
    reason="Integration tests disabled. Set RUN_INTEGRATION_TESTS=1 to run.",
)


class TestScraperIntegration:
    """Integration tests for the AO3 scraper."""

    @pytest.mark.slow
    def test_get_top_fandoms(self):
        """Test fetching top fandoms from AO3."""
        from src.scrapers.ao3 import AO3Scraper

        with AO3Scraper(headless=True) as scraper:
            fandoms = scraper.get_top_fandoms(limit=5)

        assert len(fandoms) == 5
        assert all("name" in f for f in fandoms)
        assert all("work_count" in f for f in fandoms)
        assert all(f["work_count"] > 0 for f in fandoms)

        # Check that we're getting real top fandoms
        names = [f["name"] for f in fandoms]
        # At least one of these should be in top 5
        top_fandoms = ["Real Person Fiction", "K-pop", "Marvel", "Harry Potter"]
        assert any(any(tf in name for tf in top_fandoms) for name in names)

    @pytest.mark.slow
    def test_get_fandom_tag_stats(self):
        """Test fetching tag stats for a fandom."""
        from src.scrapers.ao3 import AO3Scraper

        with AO3Scraper(headless=True) as scraper:
            stats = scraper.get_fandom_tag_stats("Harry Potter - J. K. Rowling")

        assert "error" not in stats
        assert stats["total_works"] > 500000  # HP should have 500k+ works
        assert len(stats["genres"]) > 0
        assert len(stats["relationships"]) > 0

        # Check for expected popular tags
        genre_names = [g["name"] for g in stats["genres"]]
        assert any("Fluff" in g or "Angst" in g for g in genre_names)


class TestLLMIntegration:
    """Integration tests for LLM-powered features."""

    @pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
    @pytest.mark.slow
    def test_estimate_fandom_time(self):
        """Test LLM-powered fandom time estimation."""
        from src.llm import LLMService

        llm = LLMService()
        result = llm.estimate_fandom_time("Final Fantasy")

        assert "error" not in result
        assert "fandom" in result
        assert "total_hours" in result
        assert "recommendation" in result
        assert isinstance(result["total_hours"], (int, float))

    @pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set")
    @pytest.mark.slow
    def test_analyze_fandom_genres(self):
        """Test LLM-powered genre analysis."""
        from src.llm import LLMService

        llm = LLMService()

        # Sample genre data
        genre_data = {
            "total_works": 500000,
            "genres": [
                {"name": "Fluff", "count": 60000},
                {"name": "Angst", "count": 55000},
                {"name": "Romance", "count": 40000},
            ],
            "relationships": [
                {"name": "Draco Malfoy/Harry Potter", "count": 70000},
                {"name": "Hermione/Ron", "count": 20000},
            ],
            "characters": [],
            "ratings": [
                {"name": "Teen And Up Audiences", "count": 200000},
                {"name": "Explicit", "count": 100000},
            ],
            "categories": [],
        }

        result = llm.analyze_fandom_genres("Harry Potter", genre_data)

        assert "error" not in result
        assert "summary" in result
        assert "dominant_themes" in result


class TestDatabaseIntegration:
    """Integration tests for database operations."""

    @pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
    def test_database_connection(self):
        """Test database connection works."""
        from src.db.connection import get_session

        with get_session() as session:
            # Just check we can connect
            result = session.execute("SELECT 1").scalar()
            assert result == 1

    @pytest.mark.skipif(not os.environ.get("DATABASE_URL"), reason="DATABASE_URL not set")
    def test_repository_operations(self):
        """Test repository get_or_create operations."""
        from src.db.connection import get_session
        from src.db.models import PlatformType
        from src.db.repository import WorkRepository

        with get_session() as session:
            repo = WorkRepository(session)

            # Test platform creation
            platform = repo.get_or_create_platform(PlatformType.AO3, "https://archiveofourown.org")
            assert platform.id is not None
            assert platform.platform_type == PlatformType.AO3

            # Test fandom creation
            fandom = repo.get_or_create_fandom(
                "Test Fandom", category="Test", estimated_work_count=1000
            )
            assert fandom.id is not None
            assert fandom.name == "Test Fandom"

            # Rollback to not pollute the database
            session.rollback()
