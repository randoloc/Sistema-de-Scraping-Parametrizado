"""Utilidades para normalización y validación de URLs."""

from __future__ import annotations

from urllib.parse import urlparse


def normalize_url(url: str) -> str:
    """Normaliza una URL: agrega ``https://`` si falta protocolo.

    Args:
        url: URL cruda ingresada por el usuario.

    Returns:
        URL normalizada con protocolo.

    Raises:
        ValueError: Si la URL está vacía o es inválida.
    """
    url = url.strip()
    if not url:
        raise ValueError("URL cannot be empty")

    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url

    # Re-parse para validar
    parsed = urlparse(url)
    if not parsed.netloc or "." not in parsed.netloc:
        raise ValueError(f"Invalid URL: {url}")

    return url
