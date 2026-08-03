"""Tests para el verificador de accesibilidad de sitios (site_verifier)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from modulo_1_servicio.scraping.site_verifier import (
    SPA_EMPTY_THRESHOLD_BYTES,
    build_adapter_yaml,
    check_accessibility,
)


class TestCheckAccessibilityDNS:
    @patch("modulo_1_servicio.scraping.site_verifier._resolve_dns")
    async def test_dns_failure(self, mock_dns) -> None:
        """DNS no resuelve → no accesible con mensaje claro."""
        mock_dns.return_value = (False, [])
        result = await check_accessibility("sitio-caido.cu")
        assert result["accessible"] is False
        assert result["dns_ok"] is False
        assert result["http_ok"] is False
        assert "DNS no resuelve" in result["message"]

    async def test_invalid_url(self) -> None:
        """URL inválida → mensaje de error sin llamar red."""
        result = await check_accessibility("")
        assert result["accessible"] is False
        assert "URL inválida" in result["message"]


class TestCheckAccessibilityHTTP:
    @patch("modulo_1_servicio.scraping.site_verifier._resolve_dns")
    @patch("httpx.AsyncClient.get")
    async def test_accessible_ok(self, mock_get, mock_dns) -> None:
        """HTTP 200 con contenido real → accesible."""
        mock_dns.return_value = (True, ["1.2.3.4"])
        resp = MagicMock()
        resp.status_code = 200
        resp.text = "<html>" + "x" * (SPA_EMPTY_THRESHOLD_BYTES + 1000) + "</html>"
        resp.url = "https://sitio.com/"
        mock_get.return_value = resp

        result = await check_accessibility("sitio.com")
        assert result["accessible"] is True
        assert result["http_status"] == 200
        assert result["dns_ok"] is True
        assert result["likely_spa"] is False

    @patch("modulo_1_servicio.scraping.site_verifier._resolve_dns")
    @patch("httpx.AsyncClient.get")
    async def test_forbidden_403(self, mock_get, mock_dns) -> None:
        """HTTP 403 → bloqueado (anti-bot), no accesible."""
        mock_dns.return_value = (True, ["1.2.3.4"])
        resp = MagicMock()
        resp.status_code = 403
        resp.text = "<html>Forbidden</html>"
        resp.url = "https://sitio.com/"
        mock_get.return_value = resp

        result = await check_accessibility("sitio.com")
        assert result["accessible"] is False
        assert result["blocked"] is True
        assert "anti-bot" in result["message"]

    @patch("modulo_1_servicio.scraping.site_verifier._resolve_dns")
    @patch("httpx.AsyncClient.get")
    async def test_spa_empty_html(self, mock_get, mock_dns) -> None:
        """HTTP 200 pero HTML diminuto → SPA, requiere adaptador Python."""
        mock_dns.return_value = (True, ["1.2.3.4"])
        resp = MagicMock()
        resp.status_code = 200
        resp.text = "<html><div id='root'></div></html>"  # ~30 bytes
        resp.url = "https://sitio.com/"
        mock_get.return_value = resp

        result = await check_accessibility("sitio.com")
        assert result["accessible"] is False
        assert result["likely_spa"] is True
        assert "SPA" in result["message"]

    @patch("modulo_1_servicio.scraping.site_verifier._resolve_dns")
    @patch("httpx.AsyncClient.get")
    async def test_http_error_500(self, mock_get, mock_dns) -> None:
        """HTTP 500 → no accesible con mensaje de error."""
        mock_dns.return_value = (True, ["1.2.3.4"])
        resp = MagicMock()
        resp.status_code = 500
        resp.text = "<html>error</html>"
        resp.url = "https://sitio.com/"
        mock_get.return_value = resp

        result = await check_accessibility("sitio.com")
        assert result["accessible"] is False
        assert result["http_status"] == 500
        assert "error" in result["message"]

    @patch("modulo_1_servicio.scraping.site_verifier._resolve_dns")
    @patch("httpx.AsyncClient.get")
    async def test_timeout(self, mock_get, mock_dns) -> None:
        """Timeout → no accesible con mensaje de timeout."""
        mock_dns.return_value = (True, ["1.2.3.4"])
        mock_get.side_effect = httpx.TimeoutException("slow")

        result = await check_accessibility("lento.com")
        assert result["accessible"] is False
        assert "Timeout" in result["message"]

    @patch("modulo_1_servicio.scraping.site_verifier._resolve_dns")
    @patch("httpx.AsyncClient.get")
    async def test_network_error(self, mock_get, mock_dns) -> None:
        """Error de red → no accesible."""
        mock_dns.return_value = (True, ["1.2.3.4"])
        mock_get.side_effect = httpx.ConnectError("connection refused")

        result = await check_accessibility("sitio.com")
        assert result["accessible"] is False
        assert "Error de red" in result["message"]


class TestBuildAdapterYaml:
    def test_minimal_default_fields(self) -> None:
        """Sin fields → genera un campo titulo por defecto."""
        yaml_text = build_adapter_yaml(
            name="misitio",
            site="misitio.com",
            vertical="general",
            search_url="https://misitio.com/?q={query}",
        )
        assert "name: misitio" in yaml_text
        assert "site: misitio.com" in yaml_text
        assert "vertical: general" in yaml_text
        assert "search_url:" in yaml_text
        assert "name: titulo" in yaml_text
        # Sin container_selector → TODO como guía
        assert "TODO" in yaml_text

    def test_with_fields_and_container(self) -> None:
        """Con fields y container_selector definidos."""
        yaml_text = build_adapter_yaml(
            name="itencel",
            site="itencel.com",
            vertical="general",
            search_url="https://itencel.com/buscar?q={query}",
            container_selector="div.resultado",
            fields=[
                {"name": "titulo", "selector": "h3", "type": "text"},
                {"name": "precio", "selector": ".price", "type": "price", "required": False},
                {"name": "url", "selector": "a", "type": "url"},
            ],
        )
        assert 'container_selector: "div.resultado"' in yaml_text
        assert "name: precio" in yaml_text
        assert "required: false" in yaml_text
        assert "name: url" in yaml_text

    def test_yaml_roundtrip_loads(self, tmp_path) -> None:
        """El YAML generado es válido y carga con el loader."""
        import yaml

        from modulo_1_servicio.scraping.adapters.loader import AdapterLoader

        yaml_text = build_adapter_yaml(
            name="nuevositio",
            site="nuevositio.com",
            vertical="general",
            search_url="https://nuevositio.com/?q={query}",
            container_selector="div.card",
            fields=[{"name": "titulo", "selector": "h3", "type": "text"}],
        )
        (tmp_path / "nuevositio.yaml").write_text(yaml_text, encoding="utf-8")

        loader = AdapterLoader(adapters_dir=tmp_path)
        adapters = loader.load_all()
        assert len(adapters) == 1
        assert adapters[0].name == "nuevositio"
        assert adapters[0].fields[0].name == "titulo"
