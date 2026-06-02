"""Mecanismos anti-bloqueo: rotación de User-Agent, retry, delays."""

from __future__ import annotations

import asyncio
import logging
import math
import random
import time
from typing import Any, Awaitable, Callable

import httpx

logger = logging.getLogger(__name__)

# Pool de User-Agents realistas (Chrome, Firefox, Edge, Safari variantes)
_USER_AGENTS: tuple[str, ...] = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) "
    "Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) "
    "Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36",
)


class UARotator:
    """Rota User-Agents secuencialmente para evitar detección."""

    def __init__(self, pool: tuple[str, ...] = _USER_AGENTS) -> None:
        self._pool = pool
        self._index = random.randint(0, len(pool) - 1) if pool else 0

    def get_ua(self) -> str:
        """Retorna el siguiente User-Agent del pool (rotación circular)."""
        ua = self._pool[self._index]
        self._index = (self._index + 1) % len(self._pool)
        return ua


class RetryPolicy:
    """Política de reintentos con backoff exponencial.

    Attributes:
        max_retries: Número máximo de reintentos (excluye el intento inicial).
        base_delay: Delay base en segundos para el backoff.
    """

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0) -> None:
        self.max_retries = max_retries
        self.base_delay = base_delay

    async def execute(
        self,
        func: Callable[..., Awaitable[httpx.Response]],
        *args: Any,
        **kwargs: Any,
    ) -> httpx.Response:
        """Ejecuta *func* con reintentos.

        Los reintentos solo aplican para excepciones transitorias
        (timeout, network error). Errores HTTP 4xx/5xx NO se reintentan.

        Returns:
            Respuesta HTTP exitosa.

        Raises:
            httpx.TimeoutException: Si se agotan los reintentos por timeout.
            httpx.RequestError: Si se agotan los reintentos por error de red.
        """
        last_exc: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except httpx.TimeoutException as e:
                last_exc = e
                logger.warning(
                    "Timeout (intento %d/%d): %s",
                    attempt + 1,
                    self.max_retries + 1,
                    e,
                )
            except httpx.RequestError as e:
                # No reintentamos HTTPStatusError (4xx/5xx deliberados)
                if isinstance(e, httpx.HTTPStatusError):
                    raise
                last_exc = e
                logger.warning(
                    "Network error (intento %d/%d): %s",
                    attempt + 1,
                    self.max_retries + 1,
                    e,
                )

            if attempt < self.max_retries:
                delay = self.base_delay * math.pow(2, attempt)
                logger.info("Reintentando en %.1fs...", delay)
                await asyncio.sleep(delay)

        # Si llegamos aquí, todos los intentos fallaron
        if last_exc:
            raise last_exc  # type: ignore[misc]


class DomainDelay:
    """Controla el delay mínimo entre requests al mismo dominio."""

    def __init__(self, default_delay: float = 1.0) -> None:
        self._default_delay = default_delay
        self._last_request: dict[str, float] = {}

    async def wait_if_needed(self, domain: str, delay: float | None = None) -> None:
        """Espera si es necesario para respetar el delay mínimo.

        Args:
            domain: Dominio al que se va a hacer la request.
            delay: Delay mínimo en segundos (usar default si None).
        """
        min_delay = delay if delay is not None else self._default_delay
        last = self._last_request.get(domain, 0.0)
        elapsed = time.monotonic() - last
        if elapsed < min_delay:
            wait = min_delay - elapsed
            logger.debug("Esperando %.2fs antes de request a %s", wait, domain)
            await asyncio.sleep(wait)
        self._last_request[domain] = time.monotonic()
