"""Tests para utilidades de normalización de URLs."""

from __future__ import annotations

import pytest

from modulo_1_servicio.scraping.url_utils import normalize_url


class TestNormalizeURL:
    def test_already_with_https(self) -> None:
        """URL con https:// se mantiene igual."""
        url = normalize_url("https://example.com")
        assert url == "https://example.com"

    def test_already_with_http(self) -> None:
        """URL con http:// se mantiene igual."""
        url = normalize_url("http://example.com")
        assert url == "http://example.com"

    def test_missing_protocol_adds_https(self) -> None:
        """URL sin protocolo recibe https://."""
        url = normalize_url("example.com")
        assert url == "https://example.com"

    def test_missing_protocol_with_path(self) -> None:
        """URL con path pero sin protocolo."""
        url = normalize_url("example.com/products?id=1")
        assert url == "https://example.com/products?id=1"

    def test_strips_whitespace(self) -> None:
        """Espacios alrededor se eliminan."""
        url = normalize_url("  https://example.com  ")
        assert url == "https://example.com"

    def test_empty_raises_valueerror(self) -> None:
        """URL vacía levanta ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            normalize_url("")

    def test_blank_raises_valueerror(self) -> None:
        """URL con solo espacios levanta ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            normalize_url("   ")

    def test_invalid_no_domain_raises_valueerror(self) -> None:
        """URL sin dominio válido levanta ValueError."""
        with pytest.raises(ValueError, match="Invalid URL"):
            normalize_url("not-a-domain")

    def test_invalid_scheme_only_raises_valueerror(self) -> None:
        """Solo esquema sin dominio levanta ValueError."""
        with pytest.raises(ValueError, match="Invalid URL"):
            normalize_url("https://")
