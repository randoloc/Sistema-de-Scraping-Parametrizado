"""Tests de integración para la API REST."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from modulo_1_servicio.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestHealth:
    def test_health_endpoint(self, client: TestClient) -> None:
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_root_endpoint(self, client: TestClient) -> None:
        """La raíz sirve la UI de NovaSearch (Gradio montado sobre FastAPI)."""
        response = client.get("/")
        assert response.status_code == 200
        assert "NovaSearch" in response.text

    def test_swagger_docs(self, client: TestClient) -> None:
        response = client.get("/docs")
        assert response.status_code == 200


class TestScrapeAPI:
    def test_scrape_invalid_config(self, client: TestClient) -> None:
        response = client.post("/api/scrape", json={"invalid": True})
        assert response.status_code == 400

    def test_scrape_missing_source(self, client: TestClient) -> None:
        response = client.post(
            "/api/scrape",
            json={"source_type": "web_page", "fields": []},
        )
        assert response.status_code == 400

    def test_results_not_found(self, client: TestClient) -> None:
        response = client.get("/api/results/nonexistent")
        assert response.status_code == 404

    def test_results_web_not_found(self, client: TestClient) -> None:
        response = client.get("/api/results/nonexistent/web")
        assert response.status_code == 404

    def test_deliver_not_found(self, client: TestClient) -> None:
        response = client.post(
            "/api/deliver/nonexistent",
            json={"emails": []},
        )
        assert response.status_code == 404


class TestAdaptersAPI:
    def test_list_adapters(self, client: TestClient) -> None:
        """GET /api/adapters retorna lista de adaptadores."""
        response = client.get("/api/adapters")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "adapters" in data
        assert isinstance(data["adapters"], list)

    def test_list_adapters_with_vertical(self, client: TestClient) -> None:
        """Filtrar por vertical retorna solo los de esa vertical."""
        response = client.get("/api/adapters?vertical=test")
        assert response.status_code == 200
        data = response.json()
        assert data["vertical"] == "test"
        assert isinstance(data["adapters"], list)

    def test_list_adapters_unknown_vertical(self, client: TestClient) -> None:
        """Vertical sin adaptadores retorna lista vacía."""
        response = client.get("/api/adapters?vertical=nonexistent")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["adapters"] == []

    def test_adapter_has_expected_structure(self, client: TestClient) -> None:
        """Cada adaptador en la respuesta tiene los campos esperados."""
        response = client.get("/api/adapters")
        assert response.status_code == 200
        data = response.json()
        if data["total"] > 0:
            adapter = data["adapters"][0]
            assert "name" in adapter
            assert "site" in adapter
            assert "vertical" in adapter
            assert "search_url" in adapter
            assert "fields" in adapter
