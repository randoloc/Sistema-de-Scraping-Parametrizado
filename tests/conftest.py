"""Fixtures compartidos para todos los tests."""

from __future__ import annotations

from typing import Any

import pytest

from scrapper_generico.core.models import (
    FieldDefinition,
    FieldType,
    FilterConfig,
    OutputFormat,
    PaginationConfig,
    ScrapeConfig,
    SourceType,
)


@pytest.fixture
def sample_field() -> FieldDefinition:
    return FieldDefinition(
        name="title",
        selector="h1.title",
        field_type=FieldType.TEXT,
    )


@pytest.fixture
def sample_fields() -> tuple[FieldDefinition, ...]:
    return (
        FieldDefinition(name="title", selector="h1.title"),
        FieldDefinition(name="price", selector=".price", field_type=FieldType.PRICE),
        FieldDefinition(name="url", selector="a.link", field_type=FieldType.URL),
    )


@pytest.fixture
def minimal_config() -> ScrapeConfig:
    return ScrapeConfig(
        source_type=SourceType.WEB_PAGE,
        source="https://example.com/products",
        fields=(
            FieldDefinition(name="title", selector="h2.product-title"),
        ),
    )


@pytest.fixture
def config_with_filters() -> ScrapeConfig:
    return ScrapeConfig(
        source_type=SourceType.WEB_PAGE,
        source="https://example.com/products",
        fields=(
            FieldDefinition(name="title", selector="h2.product-title"),
        ),
        filters=FilterConfig(
            include_patterns=(r"python", r"react"),
            exclude_patterns=(r"tutorial",),
            min_length=10,
            max_results=5,
        ),
        pagination=PaginationConfig(
            strategy="url",
            url_template="https://example.com/products?page={page}",
            max_pages=3,
        ),
    )


@pytest.fixture
def sample_html() -> str:
    return """<!DOCTYPE html>
<html>
<body>
    <div class="product">
        <h2 class="product-title">Python Scraping Guide</h2>
        <span class="price">$39.99</span>
        <a class="link" href="/python-guide">Details</a>
    </div>
    <div class="product">
        <h2 class="product-title">React Testing</h2>
        <span class="price">$29.99</span>
        <a class="link" href="/react-testing">Details</a>
    </div>
</body>
</html>"""


@pytest.fixture
def sample_config_dict() -> dict[str, Any]:
    return {
        "source_type": "web_page",
        "source": "https://example.com/products",
        "container_selector": ".product",
        "fields": [
            {"name": "title", "selector": ".product-title", "type": "text"},
            {"name": "price", "selector": ".price", "type": "price"},
            {"name": "link", "selector": ".link", "type": "url"},
        ],
        "filters": {
            "max_results": 10,
            "deduplicate": True,
        },
        "output_format": "json",
        "timeout": 30,
    }
