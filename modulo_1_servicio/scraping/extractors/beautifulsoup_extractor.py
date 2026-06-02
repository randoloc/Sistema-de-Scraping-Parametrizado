"""Extractor concreto usando BeautifulSoup + httpx para scraping web real.

Este es el extractor que realmente hace el trabajo:
1. Fetch con httpx (async) con anti-scraping (UA rotativo, retry, delays)
2. Parseo con BeautifulSoup
3. Extracción de campos por selectores CSS
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from bs4 import BeautifulSoup, Tag

from modulo_1_servicio.scraping.anti_scraping import DomainDelay, RetryPolicy, UARotator
from modulo_1_servicio.scraping.extractors.base import BaseExtractor
from modulo_1_servicio.scraping.models import ScrapeConfig, ScraperConnectionError, ScraperParseError
from modulo_1_servicio.scraping.url_utils import normalize_url

logger = logging.getLogger(__name__)

# Singleton global de mecanismos anti-scraping
_ua_rotator = UARotator()
_retry_policy = RetryPolicy(max_retries=3, base_delay=1.0)
_domain_delay = DomainDelay(default_delay=1.0)


class BeautifulSoupExtractor(BaseExtractor):
    """Extractor que usa httpx + BeautifulSoup para scraping web.

    Soporta:
    - Selectores CSS para localizar contenedores y campos
    - Paginación por URL template
    - Headers personalizados y User-Agent
    - Timeout configurable
    - Anti-scraping: UA rotativo, retry con backoff, delay entre requests
    - Normalización automática de URLs
    """

    async def fetch_content(self, config: ScrapeConfig) -> BeautifulSoup:
        """Obtiene el HTML de la fuente y lo parsea con BeautifulSoup.

        Incluye:
        - Normalización de URL (agrega ``https://`` si falta)
        - Rotación de User-Agent
        - Reintentos con backoff exponencial en errores transitorios
        - Delay mínimo entre requests al mismo dominio
        """
        # 1. Normalizar URL
        source = normalize_url(config.source)

        # 2. Preparar headers con UA rotativo
        headers = dict(config.headers)
        if config.user_agent:
            headers.setdefault("User-Agent", config.user_agent)
        else:
            headers.setdefault("User-Agent", _ua_rotator.get_ua())

        # 3. Extraer dominio para delay
        from urllib.parse import urlparse
        domain = urlparse(source).netloc

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(config.timeout),
                follow_redirects=True,
            ) as client:
                # 4. Delay anti-bloqueo
                await _domain_delay.wait_if_needed(domain, config.rate_limit)

                # 5. Request con retry
                async def _do_request() -> httpx.Response:
                    return await client.get(source, headers=headers)

                response = await _retry_policy.execute(_do_request)
                response.raise_for_status()

        except httpx.TimeoutException as e:
            raise ScraperConnectionError(
                f"Timeout después de {config.timeout}s",
                source=source,
            ) from e
        except httpx.HTTPStatusError as e:
            raise ScraperConnectionError(
                f"HTTP {e.response.status_code}",
                source=source,
            ) from e
        except httpx.RequestError as e:
            raise ScraperConnectionError(
                str(e),
                source=source,
            ) from e

        try:
            return BeautifulSoup(response.text, "lxml")
        except Exception as e:
            raise ScraperParseError(
                f"Error parseando HTML: {e}",
                source=source,
            ) from e

    def _select_one(self, container: Any, selector: str) -> Any | None:
        """Selecciona un elemento CSS del contenedor BeautifulSoup."""
        if not isinstance(container, Tag):
            return None
        element = container.select_one(selector)
        if element is None:
            return None
        return element.get_text(strip=True) or element.get("href") or str(element)

    def _select_all(self, container: Any, selector: str) -> list[Any]:
        """Selecciona todos los elementos CSS del contenedor."""
        if not isinstance(container, Tag):
            return []
        return container.select(selector)

    async def fetch_content_paginated(
        self, config: ScrapeConfig, page: int
    ) -> BeautifulSoup:
        """Obtiene una página específica cuando hay paginación."""
        if config.pagination.url_template:
            url = config.pagination.url_template.format(
                **{config.pagination.page_param: page}
            )
        else:
            url = config.source

        page_config = ScrapeConfig(
            source_type=config.source_type,
            source=url,
            fields=config.fields,
            container_selector=config.container_selector,
            filters=config.filters,
            pagination=config.pagination,
            timeout=config.timeout,
            user_agent=config.user_agent or self.DEFAULT_USER_AGENT,
            headers=config.headers,
            rate_limit=config.rate_limit,
        )
        return await self.fetch_content(page_config)
