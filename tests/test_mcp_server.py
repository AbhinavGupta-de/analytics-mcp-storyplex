"""Tests for the MCP server."""

import json
from unittest.mock import patch

import pytest


class TestMCPServerImports:
    """Test MCP server imports."""

    def test_import_server(self):
        """Test that MCP server module can be imported."""
        import src.mcp_server

        assert src.mcp_server.server is not None

    def test_import_json_encoder(self):
        """Test custom JSON encoder import."""
        from src.mcp_server import CustomJSONEncoder, json_dumps

        assert CustomJSONEncoder is not None
        assert json_dumps is not None


class TestCustomJSONEncoder:
    """Test custom JSON encoder."""

    def test_encode_decimal(self):
        """Test encoding Decimal values."""
        from decimal import Decimal

        from src.mcp_server import json_dumps

        result = json_dumps({"value": Decimal("123.45")})
        data = json.loads(result)
        assert data["value"] == 123.45

    def test_encode_decimal_integer(self):
        """Test encoding integer Decimal values."""
        from decimal import Decimal

        from src.mcp_server import json_dumps

        result = json_dumps({"value": Decimal("100")})
        data = json.loads(result)
        assert data["value"] == 100

    def test_encode_datetime(self):
        """Test encoding datetime values."""
        from datetime import datetime

        from src.mcp_server import json_dumps

        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = json_dumps({"timestamp": dt})
        data = json.loads(result)
        assert data["timestamp"] == "2024-01-15T10:30:00"


class TestHelperFunctions:
    """Test helper functions."""

    def test_log_error(self, capsys):
        """Test error logging goes to stderr."""
        from src.mcp_server import log_error

        log_error("Test error message")
        captured = capsys.readouterr()
        assert "[ERROR] Test error message" in captured.err

    def test_log_info(self, capsys):
        """Test info logging goes to stderr."""
        from src.mcp_server import log_info

        log_info("Test info message")
        captured = capsys.readouterr()
        assert "[INFO] Test info message" in captured.err


class TestLLMServiceGetter:
    """Test LLM service getter."""

    def test_get_llm_service_with_api_key(self):
        """Test getting LLM service when API key is configured."""
        import src.mcp_server
        from src.mcp_server import get_llm_service

        # Reset the cached service
        src.mcp_server._llm_service = None

        with patch("src.config.settings.anthropic_api_key", "test-key"):
            with patch("anthropic.Anthropic"):
                service = get_llm_service()
                assert service is not None

        # Reset again for other tests
        src.mcp_server._llm_service = None

    def test_get_llm_service_without_api_key(self):
        """Test getting LLM service when API key is not configured."""
        import src.mcp_server
        from src.mcp_server import get_llm_service

        # Reset the cached service
        src.mcp_server._llm_service = None

        with patch("src.config.settings.anthropic_api_key", None):
            with pytest.raises(ValueError):
                get_llm_service()

        # Reset again for other tests
        src.mcp_server._llm_service = None


class TestToolDefinitions:
    """Test tool definitions."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_tools(self):
        """Test that list_tools returns a list of tools."""
        from src.mcp_server import list_tools

        tools = await list_tools()

        assert isinstance(tools, list)
        assert len(tools) > 0

        # Check that expected tools exist
        tool_names = [t.name for t in tools]
        assert "get_analytics_summary" in tool_names
        assert "search_works" in tool_names
        assert "get_top_fandoms" in tool_names
        assert "scrape_ao3_works" in tool_names
        assert "scrape_ao3_fandoms" in tool_names
        assert "estimate_fandom_time" in tool_names
        assert "analyze_fandom_insights" in tool_names
        assert "analyze_market_trends" in tool_names

    @pytest.mark.asyncio
    async def test_llm_powered_tools_have_description(self):
        """Test that LLM-powered tools are marked in description."""
        from src.mcp_server import list_tools

        tools = await list_tools()

        llm_tools = ["estimate_fandom_time", "analyze_fandom_insights", "analyze_market_trends"]
        for tool in tools:
            if tool.name in llm_tools:
                assert "[LLM-POWERED]" in tool.description


class TestRunWithRetry:
    """Test retry logic."""

    @pytest.mark.asyncio
    async def test_run_with_retry_success_first_try(self):
        """Test successful execution on first try."""
        from src.mcp_server import run_with_retry

        call_count = 0

        def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await run_with_retry(success_func, max_retries=3, retry_delay=0.1)
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_run_with_retry_success_after_failures(self):
        """Test successful execution after retries."""
        from src.mcp_server import run_with_retry

        call_count = 0

        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary error")
            return "success"

        result = await run_with_retry(flaky_func, max_retries=3, retry_delay=0.1)
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_run_with_retry_all_failures(self):
        """Test that exception is raised after all retries fail."""
        from src.mcp_server import run_with_retry

        def always_fails():
            raise Exception("Permanent error")

        with pytest.raises(Exception) as exc_info:
            await run_with_retry(always_fails, max_retries=2, retry_delay=0.1)
        assert "Permanent error" in str(exc_info.value)
