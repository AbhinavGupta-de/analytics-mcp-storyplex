"""Tests for the LLM service."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest


class TestLLMServiceImports:
    """Test that LLM service imports correctly."""

    def test_import_llm_service(self):
        """Test that LLMService can be imported."""
        from src.llm import LLMService

        assert LLMService is not None

    def test_import_config(self):
        """Test that config includes LLM settings."""
        from src.config import settings

        assert hasattr(settings, "anthropic_api_key")
        assert hasattr(settings, "llm_model")
        assert hasattr(settings, "llm_max_tokens")


class TestLLMServiceInitialization:
    """Test LLM service initialization."""

    def test_init_without_api_key_raises(self):
        """Test that initialization without API key raises ValueError."""
        from src.llm import LLMService

        # Clear any existing API key
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}, clear=False):
            with patch("src.config.settings.anthropic_api_key", None):
                with pytest.raises(ValueError) as exc_info:
                    LLMService()
                assert "ANTHROPIC_API_KEY" in str(exc_info.value)

    def test_init_with_api_key_succeeds(self):
        """Test that initialization with API key succeeds."""
        from src.llm import LLMService

        # Provide a test API key
        with patch("anthropic.Anthropic"):
            service = LLMService(api_key="test-api-key")
            assert service.api_key == "test-api-key"


class TestLLMServiceMethods:
    """Test LLM service methods with mocked API."""

    @pytest.fixture
    def mock_llm_service(self):
        """Create a mocked LLM service."""
        with patch("anthropic.Anthropic") as mock_anthropic:
            from src.llm import LLMService

            service = LLMService(api_key="test-key")
            yield service, mock_anthropic

    def test_estimate_fandom_time_returns_dict(self, mock_llm_service):
        """Test that estimate_fandom_time returns a dictionary."""
        service, mock_anthropic = mock_llm_service

        # Mock the API response
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = json.dumps(
            {
                "fandom": "Final Fantasy",
                "source_type": "Video Games",
                "total_hours": 500,
                "minimum_hours": 40,
                "recommendation": "Start with FFX or FFVII",
                "components": [],
                "entry_points": ["Final Fantasy VII", "Final Fantasy X"],
            }
        )
        service.client.messages.create = MagicMock(return_value=mock_response)

        result = service.estimate_fandom_time("Final Fantasy")

        assert isinstance(result, dict)
        assert result["fandom"] == "Final Fantasy"
        assert "total_hours" in result
        assert "recommendation" in result

    def test_estimate_fandom_time_handles_json_error(self, mock_llm_service):
        """Test that estimate_fandom_time handles JSON parse errors."""
        service, mock_anthropic = mock_llm_service

        # Mock invalid JSON response
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "This is not valid JSON"
        service.client.messages.create = MagicMock(return_value=mock_response)

        result = service.estimate_fandom_time("Test Fandom")

        assert isinstance(result, dict)
        assert "error" in result

    def test_analyze_fandom_genres(self, mock_llm_service):
        """Test analyze_fandom_genres method."""
        service, mock_anthropic = mock_llm_service

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = json.dumps(
            {
                "fandom": "Harry Potter",
                "summary": "Romance-heavy fandom with strong shipping culture",
                "dominant_themes": ["Romance", "Angst", "AU"],
                "popular_tropes": ["Enemies to Lovers", "Time Travel"],
                "shipping_culture": "Very active",
                "content_warnings": "Mostly teen-rated",
                "audience_profile": "Young adult readers",
                "writing_opportunities": ["Underserved side characters"],
                "market_insights": "High engagement potential",
            }
        )
        service.client.messages.create = MagicMock(return_value=mock_response)

        genre_data = {
            "total_works": 500000,
            "genres": [{"name": "Fluff", "count": 60000}],
            "relationships": [{"name": "Draco/Harry", "count": 70000}],
            "characters": [],
            "ratings": [],
            "categories": [],
        }

        result = service.analyze_fandom_genres("Harry Potter", genre_data)

        assert isinstance(result, dict)
        assert "summary" in result
        assert "dominant_themes" in result

    def test_analyze_market_trends(self, mock_llm_service):
        """Test analyze_market_trends method."""
        service, mock_anthropic = mock_llm_service

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = json.dumps(
            {
                "market_summary": "K-pop and anime dominate",
                "top_categories": [{"category": "K-pop", "analysis": "Growing fast"}],
                "growth_opportunities": ["Western TV shows"],
                "saturation_warnings": ["Harry Potter"],
                "recommendations": ["Focus on K-pop"],
                "answer": "Anime fandoms are growing fastest",
            }
        )
        service.client.messages.create = MagicMock(return_value=mock_response)

        fandoms = [
            {"name": "BTS", "work_count": 500000, "category": "K-pop"},
            {"name": "Marvel", "work_count": 600000, "category": "Movies"},
        ]

        result = service.analyze_market_trends(fandoms, "Which fandoms are growing?")

        assert isinstance(result, dict)
        assert "market_summary" in result
        assert "recommendations" in result

    def test_find_ao3_fandom_name(self, mock_llm_service):
        """Test finding correct AO3 fandom name."""
        service, mock_anthropic = mock_llm_service

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "原神 | Genshin Impact (Video Game)"
        service.client.messages.create = MagicMock(return_value=mock_response)

        result = service.find_ao3_fandom_name("Genshin Impact")

        assert "Genshin Impact" in result

    def test_generate_fandom_analysis(self, mock_llm_service):
        """Test generating fandom analysis."""
        service, mock_anthropic = mock_llm_service

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = json.dumps(
            {
                "fandom": "Final Fantasy",
                "category": "Video Games",
                "estimated_works": "100000+",
                "popularity_tier": "A",
                "summary": "Long-running JRPG franchise with diverse fanfic",
                "dominant_genres": ["Romance", "Adventure"],
                "popular_ships": ["Cloud/Tifa", "Noctis/Prompto"],
                "top_characters": ["Cloud", "Sephiroth"],
                "common_tropes": ["Fix-it fics", "Canon divergence"],
                "audience_profile": "Mixed gender, 18-30",
                "content_rating_breakdown": "Mostly Teen/Mature",
                "unique_aspects": "Multi-game crossovers common",
                "writing_opportunities": ["FFXVI content"],
                "crossover_potential": ["Kingdom Hearts"],
            }
        )
        service.client.messages.create = MagicMock(return_value=mock_response)

        result = service.generate_fandom_analysis("Final Fantasy")

        assert isinstance(result, dict)
        assert result["fandom"] == "Final Fantasy"
        assert "dominant_genres" in result
        assert "popular_ships" in result

    def test_answer_any_question(self, mock_llm_service):
        """Test answering any analytics question."""
        service, mock_anthropic = mock_llm_service

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = json.dumps(
            {
                "answer": "The top anime fandoms by work count are: 1. My Hero Academia (500K+), 2. Haikyuu!! (400K+), 3. Attack on Titan (350K+)",
                "data": [
                    {"fandom": "My Hero Academia", "works": 500000},
                    {"fandom": "Haikyuu!!", "works": 400000},
                ],
                "insights": ["Anime fandoms dominate AO3", "Sports anime surprisingly popular"],
                "recommendations": ["Target BnHA for maximum reach"],
                "confidence": "high",
                "data_sources": "AO3 fandom statistics",
            }
        )
        service.client.messages.create = MagicMock(return_value=mock_response)

        result = service.answer_any_question("What are the top anime fandoms?")

        assert isinstance(result, dict)
        assert "answer" in result
        assert "insights" in result
