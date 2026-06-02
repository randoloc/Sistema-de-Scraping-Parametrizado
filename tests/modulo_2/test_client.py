"""Tests para el cliente HTTP del Módulo 2."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from modulo_2_admin.core.client import ScrapperClient
from modulo_2_admin.core.models import ScrapeJobConfig


class TestScrapeJobConfig:
    def test_to_api_dict_basic(self) -> None:
        config = ScrapeJobConfig(
            source="https://example.com",
            source_type="web_page",
        )
        result = config.to_api_dict()
        assert result["source"] == "https://example.com"
        assert result["source_type"] == "web_page"
        assert result["fields"] == []

    def test_to_api_dict_with_fields(self) -> None:
        from modulo_2_admin.core.models import FieldConfig

        config = ScrapeJobConfig(
            source="https://example.com",
            fields=[
                FieldConfig(name="title", selector="h1"),
                FieldConfig(name="price", selector=".price", field_type="price"),
            ],
        )
        result = config.to_api_dict()
        assert len(result["fields"]) == 2
        assert result["fields"][0]["name"] == "title"
        assert result["fields"][1]["type"] == "price"


class TestScrapperClient:
    @pytest.fixture
    def client(self) -> ScrapperClient:
        return ScrapperClient(base_url="http://test:8000")

    @patch("httpx.Client.get")
    def test_health_success(self, mock_get: MagicMock, client: ScrapperClient) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        assert client.health() is True

    @patch("httpx.Client.get")
    def test_health_fail(self, mock_get: MagicMock, client: ScrapperClient) -> None:
        mock_get.side_effect = Exception("Connection error")
        assert client.health() is False

    @patch("httpx.Client.post")
    def test_run_scrape(
        self, mock_post: MagicMock, client: ScrapperClient
    ) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "operation_id": "abc123",
            "status": "completed",
            "total_found": 5,
            "total_errors": 0,
            "endpoint": "/api/results/abc123",
        }
        mock_post.return_value = mock_response

        result = client.run_scrape(
            {"source": "https://example.com", "fields": []}
        )
        assert result.operation_id == "abc123"
        assert result.total_found == 5
