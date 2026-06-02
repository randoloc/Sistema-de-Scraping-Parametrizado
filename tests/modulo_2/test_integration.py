"""Test de integración: Admin Client ←→ Scraper Service.

Levanta el servicio FastAPI con TestClient y usa ScrapperClient
para enviar configuraciones de scraping y verificar resultados.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from modulo_1_servicio.main import app
from modulo_2_admin.core.client import ScrapperClient
from modulo_2_admin.core.models import FieldConfig, ScrapeJobConfig


@pytest.fixture
def test_client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def admin_client(test_client: TestClient) -> ScrapperClient:
    """Admin client apuntando al TestClient de FastAPI.

    Parcheamos httpx.Client para que use el TestClient internamente.
    """
    client = ScrapperClient(base_url="http://testserver")

    original_post = client._client.post
    original_get = client._client.get

    def _patched_post(url, *args, **kwargs):
        relative = url.replace("http://testserver", "")
        response = test_client.post(relative, *args, **kwargs)
        return _FakeResponse(response.status_code, response.json())

    def _patched_get(url, *args, **kwargs):
        relative = url.replace("http://testserver", "")
        response = test_client.get(relative, *args, **kwargs)
        content_type = response.headers.get("content-type", "")
        if "json" in content_type:
            return _FakeResponse(response.status_code, response.json())
        return _FakeResponse(response.status_code, response.text)

    client._client.post = _patched_post
    client._client.get = _patched_get
    return client


class _FakeResponse:
    def __init__(self, status_code: int, data: Any) -> None:
        self.status_code = status_code
        self._data = data

    def json(self) -> Any:
        if isinstance(self._data, str):
            return json.loads(self._data)
        return self._data

    @property
    def text(self) -> str:
        if isinstance(self._data, str):
            return self._data
        return json.dumps(self._data)

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


class TestIntegrationAdminWithScraper:
    """Test de integración: Admin Client → Scraper API."""

    def test_health_check(self, admin_client: ScrapperClient) -> None:
        """El admin client puede verificar que el servicio está vivo."""
        assert admin_client.health() is True

    def test_run_scrape_basic(self, admin_client: ScrapperClient) -> None:
        """Admin envía config básica de web_page y recibe operation_id."""
        config = ScrapeJobConfig(
            source="https://example.com",
            source_type="web_page",
            fields=[
                FieldConfig(name="title", selector="h1"),
            ],
        ).to_api_dict()

        response = admin_client.run_scrape(config)
        assert response.operation_id
        assert len(response.operation_id) == 8
        assert response.status in ("completed", "completed_with_errors")
        assert response.total_found >= 0

    def test_run_scrape_and_get_results(
        self, admin_client: ScrapperClient
    ) -> None:
        """Admin ejecuta scraping y luego consulta resultados."""
        config = ScrapeJobConfig(
            source="https://example.com",
            source_type="web_page",
            fields=[
                FieldConfig(name="title", selector="h1"),
                FieldConfig(name="description", selector="p"),
            ],
        ).to_api_dict()

        scrape_resp = admin_client.run_scrape(config)
        assert scrape_resp.operation_id

        results = admin_client.get_results(scrape_resp.operation_id)
        assert results.operation_id == scrape_resp.operation_id
        assert results.total_found >= 0
        assert isinstance(results.items, list)

    def test_run_scrape_and_get_web_results(
        self, admin_client: ScrapperClient
    ) -> None:
        """Admin ejecuta scraping y obtiene página HTML de resultados."""
        config = ScrapeJobConfig(
            source="https://example.com",
            source_type="web_page",
            fields=[FieldConfig(name="title", selector="h1")],
        ).to_api_dict()

        scrape_resp = admin_client.run_scrape(config)
        html = admin_client.get_results_web(scrape_resp.operation_id)
        assert isinstance(html, str)
        assert "doctype" in html.lower() or "<html" in html.lower()

    def test_run_scrape_with_pagination(
        self, admin_client: ScrapperClient
    ) -> None:
        """Admin puede configurar paginación."""
        config = ScrapeJobConfig(
            source="https://example.com",
            source_type="web_page",
            fields=[FieldConfig(name="title", selector="h1")],
            pagination=type(
                "PaginationConfig",
                (),
                {"strategy": "url", "url_template": None, "max_pages": 1},
            )(),
        ).to_api_dict()

        response = admin_client.run_scrape(config)
        assert response.operation_id

    def test_run_scrape_invalid_source(self, admin_client: ScrapperClient) -> None:
        """Admin recibe error con fuente inválida (URL sin protocolo)."""
        config = ScrapeJobConfig(
            source="not-a-valid-url",
            source_type="web_page",
            fields=[FieldConfig(name="title", selector="h1")],
        ).to_api_dict()

        response = admin_client.run_scrape(config)
        # La API captura el error y devuelve un operation_id igual
        assert response.operation_id
        assert response.status == "completed_with_errors"
        assert response.total_found == 0

    def test_get_results_not_found(self, admin_client: ScrapperClient) -> None:
        """Admin recibe 404 al consultar operation_id inexistente."""
        with pytest.raises(Exception):
            admin_client.get_results("nonexistent")

    def test_full_admin_workflow(self, admin_client: ScrapperClient) -> None:
        """Workflow completo: config → scrape → results → web."""
        config = ScrapeJobConfig(
            source="https://httpbin.org/html",
            source_type="web_page",
            fields=[
                FieldConfig(name="title", selector="h1"),
                FieldConfig(name="body", selector="p"),
            ],
            filters=type(
                "FilterConfig",
                (),
                {
                    "include_patterns": [],
                    "exclude_patterns": [],
                    "min_length": None,
                    "max_length": None,
                    "deduplicate": True,
                    "max_results": 10,
                },
            )(),
        ).to_api_dict()

        # 1. Ejecutar scraping
        scrape_resp = admin_client.run_scrape(config)
        assert scrape_resp.operation_id

        # 2. Obtener resultados JSON
        results = admin_client.get_results(scrape_resp.operation_id)
        assert results.source == "https://httpbin.org/html"
        assert isinstance(results.items, list)

        # 3. Obtener página web de resultados
        html = admin_client.get_results_web(scrape_resp.operation_id)
        assert isinstance(html, str) and len(html) > 50
