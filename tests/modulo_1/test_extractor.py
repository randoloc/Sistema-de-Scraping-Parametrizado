"""Tests para el extractor BeautifulSoup."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from modulo_1_servicio.scraping.extractors.beautifulsoup_extractor import (
    BeautifulSoupExtractor,
)
from modulo_1_servicio.scraping.models import (
    FieldDefinition,
    FieldType,
    ScrapeConfig,
    SourceType,
)


@pytest.fixture
def extractor() -> BeautifulSoupExtractor:
    return BeautifulSoupExtractor()


@pytest.fixture
def sample_html() -> str:
    return """<!DOCTYPE html>
<html><body>
<div class="product">
    <h2 class="title">Python Guide</h2>
    <span class="price">$39.99</span>
    <a class="link" href="/python">Details</a>
</div>
<div class="product">
    <h2 class="title">React Book</h2>
    <span class="price">$29.99</span>
    <a class="link" href="/react">Details</a>
</div>
</body></html>"""


class TestBeautifulSoupExtractor:
    def test_select_one(self, extractor: BeautifulSoupExtractor) -> None:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup("<div><p class='x'>Hello</p></div>", "lxml")
        result = extractor._select_one(soup, "p.x")
        assert result == "Hello"

    def test_select_one_none(self, extractor: BeautifulSoupExtractor) -> None:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup("<div></div>", "lxml")
        result = extractor._select_one(soup, ".nonexistent")
        assert result is None

    def test_select_all(self, extractor: BeautifulSoupExtractor) -> None:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(
            "<ul><li>A</li><li>B</li><li>C</li></ul>", "lxml"
        )
        result = extractor._select_all(soup, "li")
        assert len(result) == 3

    def test_select_all_empty(self, extractor: BeautifulSoupExtractor) -> None:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup("<div></div>", "lxml")
        result = extractor._select_all(soup, "span")
        assert result == []

    def test_convert_type_text(self, extractor: BeautifulSoupExtractor) -> None:
        result = extractor._convert_type("Hello", FieldType.TEXT)
        assert result == "Hello"

    def test_convert_type_price(self, extractor: BeautifulSoupExtractor) -> None:
        result = extractor._convert_type("$39.99", FieldType.PRICE)
        assert result == 39.99

    def test_convert_type_price_eu(self, extractor: BeautifulSoupExtractor) -> None:
        result = extractor._convert_type("€1.234,56", FieldType.PRICE)
        assert result == 1234.56

    def test_convert_type_price_no_symbol(
        self, extractor: BeautifulSoupExtractor
    ) -> None:
        result = extractor._convert_type("39.99", FieldType.PRICE)
        assert result == 39.99

    def test_convert_type_price_commas(
        self, extractor: BeautifulSoupExtractor
    ) -> None:
        result = extractor._convert_type("1,234.56 USD", FieldType.PRICE)
        assert result == 1234.56

    def test_convert_type_number(self, extractor: BeautifulSoupExtractor) -> None:
        result = extractor._convert_type("1,234", FieldType.NUMBER)
        assert result == 1234.0

    def test_convert_type_boolean_true(self, extractor: BeautifulSoupExtractor) -> None:
        assert extractor._convert_type("true", FieldType.BOOLEAN) is True
        assert extractor._convert_type("1", FieldType.BOOLEAN) is True

    def test_convert_type_boolean_false(self, extractor: BeautifulSoupExtractor) -> None:
        assert extractor._convert_type("false", FieldType.BOOLEAN) is False
        assert extractor._convert_type("0", FieldType.BOOLEAN) is False

    @patch("httpx.AsyncClient.get")
    async def test_fetch_content(
        self, mock_get: MagicMock, extractor: BeautifulSoupExtractor
    ) -> None:
        mock_response = MagicMock()
        mock_response.text = "<html><body><p>Hello</p></body></html>"
        mock_get.return_value = mock_response

        config = ScrapeConfig(
            source_type=SourceType.WEB_PAGE,
            source="https://example.com",
            fields=(FieldDefinition(name="title", selector="p"),),
        )
        soup = await extractor.fetch_content(config)
        assert soup is not None
        assert soup.select_one("p").text == "Hello"

    @patch("httpx.AsyncClient.get")
    async def test_execute_full(
        self, mock_get: MagicMock, extractor: BeautifulSoupExtractor, sample_html: str
    ) -> None:
        mock_response = MagicMock()
        mock_response.text = sample_html
        mock_get.return_value = mock_response

        config = ScrapeConfig(
            source_type=SourceType.WEB_PAGE,
            source="https://example.com/products",
            container_selector=".product",
            fields=(
                FieldDefinition(name="title", selector=".title"),
                FieldDefinition(name="price", selector=".price", field_type=FieldType.PRICE),
            ),
        )

        result = await extractor.execute(config)
        assert result.success_count == 2
        assert result.items[0].data["title"] == "Python Guide"
        assert result.items[0].data["price"] == 39.99
        assert result.items[1].data["title"] == "React Book"
