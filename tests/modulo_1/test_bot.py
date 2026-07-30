from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from modulo_1_servicio.bot.formatters import (
    format_help,
    format_item,
    format_search_results,
    format_welcome,
)
from modulo_1_servicio.bot.search_service import search
from modulo_1_servicio.scraping.normalizer import CanonicalItem


class TestFormatters:
    def test_format_welcome_contains_commands(self):
        text = format_welcome()
        assert "/buscar" in text
        assert "/ayuda" in text
        assert "ScrapperGenérico Bot" in text

    def test_format_help_contains_commands(self):
        text = format_help()
        assert "/start" in text
        assert "/buscar" in text
        assert "/ayuda" in text

    def test_format_item_with_price_and_url(self):
        item = {
            "title": "iPhone 15",
            "price": 999.99,
            "currency": "USD",
            "location": "La Habana",
            "url": "https://example.com/iphone",
            "source_site": "test",
            "source_url": "https://example.com",
            "rank": 0,
        }
        result = format_item(item, index=1)
        assert "iPhone 15" in result
        assert "La Habana" in result
        assert "Ver anuncio" in result

    def test_format_item_without_optional_fields(self):
        item = {
            "title": "MacBook Air",
            "price": None,
            "location": None,
            "url": None,
            "source_site": "test",
            "source_url": "https://example.com",
            "rank": 0,
        }
        result = format_item(item, index=1)
        assert "MacBook Air" in result
        assert "💰" not in result
        assert "📍" not in result

    def test_format_search_results_empty(self):
        result = format_search_results(query="test", items=[], vertical="test")
        assert "No encontré resultados" in result
        assert "test" in result

    def test_format_search_results_with_items(self):
        items = [
            {
                "title": "Item 1",
                "price": 100.0,
                "currency": "USD",
                "location": "Habana",
                "url": "https://example.com/1",
                "source_site": "site_a",
                "source_url": "https://example.com",
                "rank": 0,
            },
            {
                "title": "Item 2",
                "price": 200.0,
                "currency": "USD",
                "location": "Santiago",
                "url": "https://example.com/2",
                "source_site": "site_a",
                "source_url": "https://example.com",
                "rank": 1,
            },
        ]
        result = format_search_results(query="test", items=items, vertical="test")
        assert "Resultados para: test" in result
        assert "site_a" in result
        assert "Item 1" in result
        assert "Item 2" in result
        assert "2 resultados" in result

    def test_format_item_from_canonical_item(self):
        canonical = CanonicalItem(
            title="Test Item",
            price=50.0,
            currency="USD",
            location="Matanzas",
            url="https://example.com/test",
            source_site="test",
            source_url="https://example.com",
            rank=0,
        )
        result = format_item(canonical, index=1)
        assert "Test Item" in result
        assert "USD" in result

    def test_format_item_no_title(self):
        item = {
            "title": None,
            "price": None,
            "source_site": "test",
            "source_url": "https://example.com",
            "rank": 0,
        }
        result = format_item(item, index=1)
        assert "Sin título" in result

    def test_format_item_price_as_string(self):
        item = {
            "title": "Test",
            "price": "1500",
            "currency": "CUP",
            "source_site": "test",
            "source_url": "https://example.com",
            "rank": 0,
        }
        result = format_item(item, index=1)
        assert "CUP" in result

    def test_format_results_grouped_by_site(self):
        items = [
            {
                "title": "A",
                "price": 10.0,
                "source_site": "site_x",
                "source_url": "https://example.com",
                "rank": 0,
            },
            {
                "title": "B",
                "price": 20.0,
                "source_site": "site_y",
                "source_url": "https://example.com",
                "rank": 1,
            },
        ]
        result = format_search_results(query="test", items=items, vertical="test")
        assert "site_x" in result
        assert "site_y" in result


class TestSearchService:
    @patch("modulo_1_servicio.bot.search_service._adapter_loader")
    async def test_search_no_adapters(self, mock_loader: MagicMock) -> None:
        mock_loader.get_by_vertical.return_value = []
        result = await search(query="test", vertical="nonexistent")
        assert result["total_found"] == 0
        assert result["items"] == []

    @patch("modulo_1_servicio.bot.search_service._adapter_loader")
    async def test_search_site_not_found(self, mock_loader: MagicMock) -> None:
        mock_loader.get.return_value = None
        result = await search(query="test", site="unknown")
        assert "error" in result
        assert "no encontrado" in result["error"]

    @patch("modulo_1_servicio.bot.search_service._adapter_loader")
    async def test_search_site_wrong_vertical(self, mock_loader: MagicMock) -> None:
        mock_adapter = MagicMock()
        mock_adapter.vertical = "cars"
        mock_loader.get.return_value = mock_adapter
        result = await search(query="test", vertical="real_estate", site="some_adapter")
        assert "error" in result
        assert "no pertenece" in result["error"]
