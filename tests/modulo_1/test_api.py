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
        response = client.get("/")
        assert response.status_code == 200
        assert "ScrapperGenérico" in response.text

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
