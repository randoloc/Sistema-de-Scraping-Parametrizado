"""Tests para el normalizador de resultados a schema canónico."""

from __future__ import annotations

import pytest

from modulo_1_servicio.scraping.normalizer import CanonicalItem, ResultNormalizer


class TestCanonicalItem:
    def test_minimal_item(self) -> None:
        """Item con solo campos requeridos."""
        item = CanonicalItem(source_site="test", source_url="https://example.com")
        assert item.source_site == "test"
        assert item.title is None
        assert item.price is None

    def test_full_item(self) -> None:
        """Item con todos los campos."""
        item = CanonicalItem(
            title="iPhone 15",
            description="El nuevo iPhone",
            price=999.99,
            currency="USD",
            url="https://example.com/iphone",
            image_url="https://example.com/iphone.jpg",
            date="2024-01-15",
            location="CDMX",
            source_site="mercadolibre",
            source_url="https://mercadolibre.com.mx/search",
            rank=1,
            raw_data={"nombre": "iPhone 15", "precio": "$999.99"},
        )
        assert item.title == "iPhone 15"
        assert item.price == 999.99
        assert item.rank == 1

    def test_optional_fields_default_none(self) -> None:
        """Campos opcionales son None por defecto."""
        item = CanonicalItem(source_site="test", source_url="https://example.com")
        assert item.image_url is None
        assert item.location is None
        assert item.raw_data == {}


class TestNormalizePrice:
    """Tests para _to_float (transformación de precios)."""

    def test_none_returns_none(self) -> None:
        assert ResultNormalizer._to_float(None) is None

    def test_int_converted(self) -> None:
        assert ResultNormalizer._to_float(100) == 100.0

    def test_float_passthrough(self) -> None:
        assert ResultNormalizer._to_float(99.99) == 99.99

    def test_string_with_dollar(self) -> None:
        assert ResultNormalizer._to_float("$1,234.56") == 1234.56

    def test_string_with_euro(self) -> None:
        assert ResultNormalizer._to_float("€ 50,00") == 50.00

    def test_string_with_peso(self) -> None:
        assert ResultNormalizer._to_float("$ 25,000 MXN") == 25000.0

    def test_invalid_string_returns_none(self) -> None:
        assert ResultNormalizer._to_float("gratis") is None


class TestNormalizeURL:
    """Tests para _extract_url."""

    def test_https_url(self) -> None:
        assert ResultNormalizer._extract_url("https://example.com") == "https://example.com"

    def test_http_url(self) -> None:
        assert ResultNormalizer._extract_url("http://example.com") == "http://example.com"

    def test_relative_path(self) -> None:
        assert ResultNormalizer._extract_url("/producto/123") == "/producto/123"

    def test_none_returns_none(self) -> None:
        assert ResultNormalizer._extract_url(None) is None

    def test_random_text_returns_none(self) -> None:
        assert ResultNormalizer._extract_url("not a url") is None


class TestResultNormalizer:
    """Tests completos para ResultNormalizer.normalize()."""

    def test_empty_raw_items(self) -> None:
        """Lista vacía retorna lista vacía."""
        normalizer = ResultNormalizer()
        result = normalizer.normalize(
            canonical_map={"title": "nombre"},
            raw_items=[],
            source_site="test",
            source_url="https://example.com",
        )
        assert result == []

    def test_basic_normalization(self) -> None:
        """Mapeo básico de campos funciona."""
        normalizer = ResultNormalizer()
        raw = [
            {"nombre": "iPhone 15", "precio": "$999.99"},
            {"nombre": "Samsung S24", "precio": "$899.00"},
        ]
        result = normalizer.normalize(
            canonical_map={"title": "nombre", "price": "precio"},
            raw_items=raw,
            source_site="test_site",
            source_url="https://example.com/search",
            start_rank=0,
        )

        assert len(result) == 2
        assert result[0].title == "iPhone 15"
        assert result[0].price == 999.99
        assert result[0].source_site == "test_site"
        assert result[0].rank == 0
        assert result[1].title == "Samsung S24"
        assert result[1].price == 899.00
        assert result[1].rank == 1

    def test_partial_fields(self) -> None:
        """Campos faltantes quedan como None."""
        normalizer = ResultNormalizer()
        raw = [
            {"nombre": "Producto A"},  # Sin precio
        ]
        result = normalizer.normalize(
            canonical_map={"title": "nombre", "price": "precio"},
            raw_items=raw,
            source_site="test",
            source_url="https://example.com",
        )
        assert result[0].title == "Producto A"
        assert result[0].price is None

    def test_url_extraction(self) -> None:
        """Urls se extraen correctamente."""
        normalizer = ResultNormalizer()
        raw = [{"link": "https://example.com/item/1", "img": "/images/photo.jpg"}]
        result = normalizer.normalize(
            canonical_map={"url": "link", "image_url": "img"},
            raw_items=raw,
            source_site="test",
            source_url="https://example.com",
        )
        assert result[0].url == "https://example.com/item/1"
        assert result[0].image_url == "/images/photo.jpg"

    def test_raw_data_preserved(self) -> None:
        """Los datos originales se preservan en raw_data."""
        normalizer = ResultNormalizer()
        raw = [{"nombre": "Test", "precio": "$10", "extra": "info"}]
        result = normalizer.normalize(
            canonical_map={"title": "nombre", "price": "precio"},
            raw_items=raw,
            source_site="test",
            source_url="https://example.com",
        )
        assert result[0].raw_data == {"nombre": "Test", "precio": "$10", "extra": "info"}
        assert result[0].raw_data["extra"] == "info"

    def test_rank_increment(self) -> None:
        """El ranking se incrementa correctamente con start_rank."""
        normalizer = ResultNormalizer()
        raw = [{"n": "A"}, {"n": "B"}, {"n": "C"}]
        result = normalizer.normalize(
            canonical_map={"title": "n"},
            raw_items=raw,
            source_site="test",
            source_url="https://example.com",
            start_rank=10,
        )
        assert result[0].rank == 10
        assert result[1].rank == 11
        assert result[2].rank == 12

    def test_description_field(self) -> None:
        """Campo description se mapea como texto."""
        normalizer = ResultNormalizer()
        raw = [{"desc": "Un producto excelente con muchas características"}]
        result = normalizer.normalize(
            canonical_map={"description": "desc"},
            raw_items=raw,
            source_site="test",
            source_url="https://example.com",
        )
        assert result[0].description == "Un producto excelente con muchas características"
