"""Tests para modelos del dominio del scraper."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from modulo_1_servicio.scraping.models import (
    ExtractedItem,
    FieldDefinition,
    FieldType,
    FilterConfig,
    OutputFormat,
    PaginationConfig,
    ScrapeConfig,
    ScrapeResult,
    ScraperConnectionError,
    ScraperError,
    ScraperParseError,
    ScraperValidationError,
    SourceType,
)


class TestFieldDefinition:
    def test_create_text_field_default(self) -> None:
        field = FieldDefinition(name="title", selector="h1")
        assert field.field_type == FieldType.TEXT
        assert field.required is True

    def test_frozen_immutable(self) -> None:
        field = FieldDefinition(name="title", selector="h1")
        with pytest.raises(AttributeError):
            field.name = "new-name"  # type: ignore[misc]


class TestFilterConfig:
    def test_defaults(self) -> None:
        f = FilterConfig()
        assert f.include_patterns == ()
        assert f.deduplicate is True

    def test_with_patterns(self) -> None:
        f = FilterConfig(include_patterns=(r"python",), max_results=10)
        assert f.max_results == 10


class TestScrapeConfig:
    def test_minimal_config(self) -> None:
        config = ScrapeConfig(
            source_type=SourceType.WEB_PAGE,
            source="https://example.com",
            fields=(FieldDefinition(name="title", selector="h1"),),
        )
        assert config.source == "https://example.com"
        assert config.output_format == OutputFormat.JSON


class TestScrapeResult:
    def test_empty_result(self) -> None:
        config = ScrapeConfig(
            source_type=SourceType.WEB_PAGE,
            source="https://example.com",
            fields=(),
        )
        result = ScrapeResult(config=config)
        assert result.success_count == 0
        assert result.elapsed is None

    def test_with_items(self) -> None:
        config = ScrapeConfig(
            source_type=SourceType.WEB_PAGE,
            source="https://example.com",
            fields=(),
        )
        items = (
            ExtractedItem(data={"title": "A"}, source_url="https://example.com"),
        )
        result = ScrapeResult(
            config=config,
            items=items,
            total_found=1,
            started_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            completed_at=datetime(2024, 1, 1, 0, 0, 5, tzinfo=timezone.utc),
        )
        assert result.elapsed == 5.0


class TestScraperErrors:
    def test_base_error_with_source(self) -> None:
        error = ScraperError("Not found", source="https://example.com")
        assert "[https://example.com]" in str(error)

    def test_inheritance(self) -> None:
        assert issubclass(ScraperConnectionError, ScraperError)
        assert issubclass(ScraperParseError, ScraperError)
        assert issubclass(ScraperValidationError, ScraperError)
