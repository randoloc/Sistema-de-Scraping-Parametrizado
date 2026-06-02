"""Tests para el motor de scraping y el orquestador."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from scrapper_generico.core.engine import FilterEngine, Orchestrator, ScraperEngine
from scrapper_generico.core.models import (
    ExtractedItem,
    FilterConfig,
    ScrapeConfig,
    ScraperError,
)


class TestFilterEngine:
    def test_no_filters_returns_all(self) -> None:
        items = [
            ExtractedItem(data={"title": "A"}, source_url="https://x.com"),
            ExtractedItem(data={"title": "B"}, source_url="https://x.com"),
        ]
        engine = FilterEngine(FilterConfig())
        result = engine.apply(items)
        assert len(result) == 2

    def test_max_results(self) -> None:
        items = [
            ExtractedItem(data={"title": str(i)}, source_url="https://x.com")
            for i in range(10)
        ]
        engine = FilterEngine(FilterConfig(max_results=3))
        result = engine.apply(items)
        assert len(result) == 3

    def test_deduplicate(self) -> None:
        items = [
            ExtractedItem(data={"title": "Same"}, source_url="https://x.com"),
            ExtractedItem(data={"title": "Same"}, source_url="https://x.com"),
        ]
        engine = FilterEngine(FilterConfig(deduplicate=True))
        result = engine.apply(items)
        assert len(result) == 1

    def test_include_pattern(self) -> None:
        items = [
            ExtractedItem(data={"title": "Python guide"}, source_url="https://x.com"),
            ExtractedItem(data={"title": "Java guide"}, source_url="https://x.com"),
        ]
        engine = FilterEngine(FilterConfig(include_patterns=(r"Python",)))
        result = engine.apply(items)
        assert len(result) == 1
        assert result[0].data["title"] == "Python guide"

    def test_exclude_pattern(self) -> None:
        items = [
            ExtractedItem(data={"title": "Python guide"}, source_url="https://x.com"),
            ExtractedItem(data={"title": "Python tutorial"}, source_url="https://x.com"),
        ]
        engine = FilterEngine(FilterConfig(exclude_patterns=(r"tutorial",)))
        result = engine.apply(items)
        assert len(result) == 1
        assert result[0].data["title"] == "Python guide"

    def test_min_length(self) -> None:
        items = [
            ExtractedItem(
                data={"t": "x"}, source_url="https://x.com"
            ),
            ExtractedItem(
                data={"t": "long enough content"}, source_url="https://x.com"
            ),
        ]
        engine = FilterEngine(FilterConfig(min_length=20))
        result = engine.apply(items)
        assert len(result) == 1
        assert result[0].data["t"] == "long enough content"

    def test_empty_items(self) -> None:
        engine = FilterEngine(FilterConfig(max_results=5))
        result = engine.apply([])
        assert result == []


class TestOrchestrator:
    @pytest.fixture
    def orchestrator(self) -> Orchestrator:
        return Orchestrator()

    @pytest.fixture
    def mock_engine(self) -> AsyncMock:
        engine = AsyncMock(spec=ScraperEngine)
        return engine

    async def test_register_and_get_engine(
        self, orchestrator: Orchestrator, mock_engine: AsyncMock
    ) -> None:
        orchestrator.register_engine("web_page", mock_engine)
        retrieved = orchestrator.get_engine("web_page")
        assert retrieved is mock_engine

    async def test_get_engine_not_found(
        self, orchestrator: Orchestrator
    ) -> None:
        with pytest.raises(ScraperError, match="No hay engine registrado"):
            orchestrator.get_engine("unknown")

    async def test_run_with_no_engine(
        self, orchestrator: Orchestrator, minimal_config: ScrapeConfig
    ) -> None:
        result = await orchestrator.run(minimal_config)
        assert len(result.errors) > 0
        assert "No hay engine registrado" in result.errors[0]
        assert result.completed_at is not None
