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

    def test_extract_url_from_anchor(self, extractor: BeautifulSoupExtractor) -> None:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(
            '<div class="item"><a class="link" href="/detalles/123">Titulo del anuncio</a></div>',
            "lxml",
        )
        container = soup.select_one(".item")
        field = FieldDefinition(name="url", selector="a.link", field_type=FieldType.URL)
        assert extractor._extract_field(container, field) == "/detalles/123"

    def test_extract_url_full(self, extractor: BeautifulSoupExtractor) -> None:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(
            '<div class="item"><a href="https://www.timbirichi.com/x/y-z">Titulo</a></div>',
            "lxml",
        )
        field = FieldDefinition(name="url", selector="a", field_type=FieldType.URL)
        assert extractor._extract_field(soup.select_one(".item"), field) == (
            "https://www.timbirichi.com/x/y-z"
        )

    def test_extract_image_data_src(self, extractor: BeautifulSoupExtractor) -> None:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(
            '<img class="thumb lazy" data-src="https://x/img.jpg" src="blank.gif">',
            "lxml",
        )
        field = FieldDefinition(name="imagen", selector="img.thumb", field_type=FieldType.IMAGE)
        assert extractor._extract_field(soup, field) == "https://x/img.jpg"

    def test_extract_image_style_background(self, extractor: BeautifulSoupExtractor) -> None:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(
            '<div class="cover" style="background-image: url(https://x/cover.jpg);"></div>',
            "lxml",
        )
        field = FieldDefinition(name="imagen", selector=".cover", field_type=FieldType.IMAGE)
        assert extractor._extract_field(soup, field) == "https://x/cover.jpg"

    def test_extract_image_missing(self, extractor: BeautifulSoupExtractor) -> None:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup('<div class="item"></div>', "lxml")
        field = FieldDefinition(
            name="imagen", selector="img", field_type=FieldType.IMAGE, required=False
        )
        assert extractor._extract_field(soup.select_one(".item"), field) is None

    def test_extract_url_from_self_container(
        self, extractor: BeautifulSoupExtractor
    ) -> None:
        """El contenedor es el propio <a> → selector 'self' lee su href.

        Patrón real de Timbirichi: container_selector='a.anuncio-list'
        y el campo url usa selector 'self'.
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(
            '<a class="anuncio-list" href="https://www.timbirichi.com/moviles/-cable-iphone--kOBsAJhu">'
            '<h5 class="anuncio-titulo">Cable iPhone</h5></a>',
            "lxml",
        )
        container = soup.select_one("a.anuncio-list")
        field = FieldDefinition(
            name="url", selector="self", field_type=FieldType.URL
        )
        assert extractor._extract_field(container, field) == (
            "https://www.timbirichi.com/moviles/-cable-iphone--kOBsAJhu"
        )

    def test_extract_url_from_at_self_alias(
        self, extractor: BeautifulSoupExtractor
    ) -> None:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(
            '<a class="item" href="/ruta/1">Titulo</a>', "lxml"
        )
        field = FieldDefinition(name="url", selector="@self", field_type=FieldType.URL)
        assert extractor._extract_field(soup.select_one(".item"), field) == "/ruta/1"

    def test_extract_required_field_missing_raises(
        self, extractor: BeautifulSoupExtractor
    ) -> None:
        """Campo requerido ausente → error (default required=True)."""
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(
            '<div class="item"><h5 class="titulo">X</h5></div>', "lxml"
        )
        field = FieldDefinition(name="precio", selector="precio", field_type=FieldType.PRICE)
        with pytest.raises(ValueError):
            extractor._extract_field(soup.select_one(".item"), field)

    def test_extract_optional_field_missing_returns_default(
        self, extractor: BeautifulSoupExtractor
    ) -> None:
        """Campo no-requerido ausente → None (sin error).

        Patrón real de Timbirichi: tiendas que no publican <precio>.
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(
            '<div class="item"><h5 class="titulo">X</h5></div>', "lxml"
        )
        field = FieldDefinition(
            name="precio", selector="precio", field_type=FieldType.PRICE, required=False
        )
        assert extractor._extract_field(soup.select_one(".item"), field) is None

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
