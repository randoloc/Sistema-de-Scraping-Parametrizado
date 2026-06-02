"""Tests para el motor de scraping."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from modulo_1_servicio.scraping.engine import FilterEngine, Orchestrator, ScraperEngine
from modulo_1_servicio.scraping.models import (
    ExtractedItem,
    FilterConfig,
    ScrapeConfig,
    ScraperError,
)


class TestFilterEngine:
    def test_no_filters_returns_all(self) -> None:
        items = [
            ExtractedItem(data={"t": "A"}, source_url="https://x.com"),
            ExtractedItem(data={"t": "B"}, source_url="https://x.com"),
        ]
        result = FilterEngine(FilterConfig()).apply(items)
        assert len(result) == 2

    def test_max_results(self) -> None:
        items = [
            ExtractedItem(data={"t": str(i)}, source_url="https://x.com")
            for i in range(10)
        ]
        result = FilterEngine(FilterConfig(max_results=3)).apply(items)
        assert len(result) == 3

    def test_deduplicate(self) -> None:
        items = [
            ExtractedItem(data={"t": "X"}, source_url="https://x.com"),
            ExtractedItem(data={"t": "X"}, source_url="https://x.com"),
        ]
        result = FilterEngine(FilterConfig(deduplicate=True)).apply(items)
        assert len(result) == 1

    def test_include_pattern(self) -> None:
        items = [
            ExtractedItem(data={"t": "Python"}, source_url="https://x.com"),
            ExtractedItem(data={"t": "Java"}, source_url="https://x.com"),
        ]
        result = FilterEngine(
            FilterConfig(include_patterns=(r"Python",))
        ).apply(items)
        assert len(result) == 1

    def test_exclude_pattern(self) -> None:
        items = [
            ExtractedItem(data={"t": "Python"}, source_url="https://x.com"),
            ExtractedItem(data={"t": "Tutorial"}, source_url="https://x.com"),
        ]
        result = FilterEngine(
            FilterConfig(exclude_patterns=(r"Tutorial",))
        ).apply(items)
        assert len(result) == 1


class TestOrchestrator:
    @pytest.fixture
    def orchestrator(self) -> Orchestrator:
        return Orchestrator()

    async def test_get_engine_not_found(self, orchestrator: Orchestrator) -> None:
        with pytest.raises(ScraperError):
            orchestrator.get_engine("unknown")

    async def test_register_and_get(
        self, orchestrator: Orchestrator
    ) -> None:
        engine = AsyncMock(spec=ScraperEngine)
        orchestrator.register_engine("web_page", engine)
        assert orchestrator.get_engine("web_page") is engine

    async def test_run_no_engine(
        self, orchestrator: Orchestrator
    ) -> None:
        config = ScrapeConfig(
            source_type="web_page",  # type: ignore[arg-type]
            source="https://example.com",
            fields=(),
        )
        result = await orchestrator.run(config)
        assert len(result.errors) > 0
