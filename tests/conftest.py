"""Pytest configuration and fixtures."""

import os
import sys

import pytest

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")


@pytest.fixture(autouse=True)
def reset_llm_service():
    """Reset LLM service between tests."""
    import src.mcp_server

    src.mcp_server._llm_service = None
    yield
    src.mcp_server._llm_service = None
