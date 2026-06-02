"""Tests para los modelos de dominio del scraper."""

from __future__ import annotations

from datetime import datetime

import pytest

from scrapper_generico.core.models import (
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
        assert field.name == "title"
        assert field.selector == "h1"
        assert field.field_type == FieldType.TEXT
        assert field.required is True
        assert field.default is None

    def test_create_price_field(self) -> None:
        field = FieldDefinition(
            name="price",
            selector=".price",
            field_type=FieldType.PRICE,
        )
        assert field.field_type == FieldType.PRICE

    def test_frozen_immutable(self) -> None:
        field = FieldDefinition(name="title", selector="h1")
        with pytest.raises(AttributeError):
            field.name = "new-name"  # type: ignore[misc]


class TestFilterConfig:
    def test_defaults(self) -> None:
        f = FilterConfig()
        assert f.include_patterns == ()
        assert f.exclude_patterns == ()
        assert f.deduplicate is True
        assert f.max_results is None

    def test_with_patterns(self) -> None:
        f = FilterConfig(
            include_patterns=(r"python",),
            exclude_patterns=(r"spam",),
            max_results=10,
        )
        assert "python" in f.include_patterns
        assert "spam" in f.exclude_patterns
        assert f.max_results == 10


class TestScrapeConfig:
    def test_minimal_config(self, minimal_config: ScrapeConfig) -> None:
        assert minimal_config.source_type == SourceType.WEB_PAGE
        assert minimal_config.source == "https://example.com/products"
        assert len(minimal_config.fields) == 1
        assert minimal_config.fields[0].name == "title"

    def test_default_output_format(self, minimal_config: ScrapeConfig) -> None:
        assert minimal_config.output_format == OutputFormat.JSON

    def test_default_rate_limit(self, minimal_config: ScrapeConfig) -> None:
        assert minimal_config.rate_limit == 1.0

    def test_config_with_filters(self, config_with_filters: ScrapeConfig) -> None:
        assert len(config_with_filters.filters.include_patterns) == 2
        assert config_with_filters.pagination.max_pages == 3


class TestScrapeResult:
    def test_empty_result(self, minimal_config: ScrapeConfig) -> None:
        result = ScrapeResult(config=minimal_config)
        assert result.items == ()
        assert result.errors == ()
        assert result.success_count == 0
        assert result.error_count == 0
        assert result.elapsed is None

    def test_result_with_items(self, minimal_config: ScrapeConfig) -> None:
        items = (
            ExtractedItem(data={"title": "Guide"}, source_url="https://example.com"),
        )
        result = ScrapeResult(
            config=minimal_config,
            items=items,
            total_found=1,
            started_at=datetime(2024, 1, 1, 0, 0, 0),
            completed_at=datetime(2024, 1, 1, 0, 0, 5),
        )
        assert result.success_count == 1
        assert result.elapsed == 5.0

    def test_result_with_errors(self, minimal_config: ScrapeConfig) -> None:
        result = ScrapeResult(
            config=minimal_config,
            errors=("Connection refused",),
        )
        assert result.error_count == 1


class TestExtractedItem:
    def test_default_extracted_at(self) -> None:
        item = ExtractedItem(data={"key": "val"}, source_url="https://example.com")
        assert item.extracted_at is not None
        assert isinstance(item.extracted_at, datetime)

    def test_default_rank(self) -> None:
        item = ExtractedItem(data={}, source_url="https://example.com")
        assert item.rank == 0


class TestScraperErrors:
    def test_base_error_with_source(self) -> None:
        error = ScraperError("Not found", source="https://example.com")
        assert "[https://example.com] Not found" in str(error)

    def test_base_error_without_source(self) -> None:
        error = ScraperError("Something broke")
        assert "Something broke" in str(error)

    def test_connection_error(self) -> None:
        error = ScraperConnectionError("Timeout")
        assert isinstance(error, ScraperError)
        assert "Timeout" in str(error)

    def test_parse_error(self) -> None:
        error = ScraperParseError("Malformed HTML", source="https://example.com")
        assert isinstance(error, ScraperError)

    def test_validation_error(self) -> None:
        error = ScraperValidationError("Invalid field config")
        assert isinstance(error, ScraperError)


class TestEnums:
    def test_field_type_values(self) -> None:
        assert FieldType.TEXT.value == "text"
        assert FieldType.PRICE.value == "price"
        assert FieldType.URL.value == "url"

    def test_source_type_values(self) -> None:
        assert SourceType.WEB_PAGE.value == "web_page"
        assert SourceType.API.value == "api"

    def test_output_format_values(self) -> None:
        assert OutputFormat.JSON.value == "json"
        assert OutputFormat.CSV.value == "csv"
