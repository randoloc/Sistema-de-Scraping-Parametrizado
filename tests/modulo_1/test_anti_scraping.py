"""Tests para mecanismos anti-scraping."""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from modulo_1_servicio.scraping.anti_scraping import DomainDelay, RetryPolicy, UARotator


class TestUARotator:
    def test_get_ua_returns_string(self) -> None:
        """get_ua retorna un string no vacío."""
        rotator = UARotator(pool=("UA-1", "UA-2", "UA-3"))
        ua = rotator.get_ua()
        assert isinstance(ua, str)
        assert len(ua) > 0

    def test_rotates_through_all_uas(self) -> None:
        """La rotación circular pasa por todos los UAs del pool."""
        pool = ("A", "B", "C")
        rotator = UARotator(pool=pool)
        seen = {rotator.get_ua() for _ in range(len(pool))}
        assert seen == set(pool)

    def test_circular_rotation(self) -> None:
        """Después de N llamadas, vuelve al primer UA."""
        pool = ("A", "B")
        rotator = UARotator(pool=pool)
        # Consumir los 2
        rotator.get_ua()
        rotator.get_ua()
        # La tercera debe volver a A
        assert rotator.get_ua() == "A"

    def test_default_pool_not_empty(self) -> None:
        """El pool por defecto tiene al menos un UA."""
        rotator = UARotator()
        ua = rotator.get_ua()
        assert "Mozilla" in ua

    def test_random_initial_index(self) -> None:
        """Dos instancias pueden tener distinto índice inicial."""
        pool = tuple(f"UA-{i}" for i in range(100))
        indices = {UARotator(pool=pool)._index for _ in range(5)}
        # Es muy probable que al menos 2 tengan índices distintos
        assert len(indices) > 1, "El índice inicial debería ser aleatorio"


class TestRetryPolicy:
    @pytest.mark.asyncio
    async def test_success_on_first_try(self) -> None:
        """Si la función tiene éxito al primer intento, no reintenta."""
        mock_func = AsyncMock(return_value=MagicMock(spec=httpx.Response))
        policy = RetryPolicy(max_retries=3)
        result = await policy.execute(mock_func)
        assert result is not None
        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_timeout(self) -> None:
        """Reintenta cuando hay TimeoutException, eventualmente falla."""
        mock_func = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
        policy = RetryPolicy(max_retries=2, base_delay=0.01)

        with pytest.raises(httpx.TimeoutException):
            await policy.execute(mock_func)

        # 1 intento inicial + 2 reintentos = 3 llamadas
        assert mock_func.call_count == 3

    @pytest.mark.asyncio
    async def test_succeeds_after_retry(self) -> None:
        """Falla N veces luego éxito en el reintento N+1."""
        mock_func = AsyncMock(side_effect=[
            httpx.TimeoutException("timeout 1"),
            httpx.TimeoutException("timeout 2"),
            MagicMock(spec=httpx.Response),
        ])
        policy = RetryPolicy(max_retries=3, base_delay=0.01)

        result = await policy.execute(mock_func)
        assert result is not None
        assert mock_func.call_count == 3

    @pytest.mark.asyncio
    async def test_does_not_retry_http_errors(self) -> None:
        """HTTPStatusError (4xx/5xx) NO se reintenta."""
        response = MagicMock(spec=httpx.Response)
        response.status_code = 404
        mock_func = AsyncMock(side_effect=httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=response,
        ))
        policy = RetryPolicy(max_retries=3, base_delay=0.01)

        with pytest.raises(httpx.HTTPStatusError):
            await policy.execute(mock_func)

        assert mock_func.call_count == 1


class TestDomainDelay:
    @pytest.mark.asyncio
    async def test_no_wait_on_first_request(self) -> None:
        """Primera request a un dominio no espera."""
        delay = DomainDelay(default_delay=10.0)
        start = time.monotonic()
        await delay.wait_if_needed("example.com")
        elapsed = time.monotonic() - start
        assert elapsed < 1.0  # No debió esperar 10s

    @pytest.mark.asyncio
    async def test_waits_when_needed(self) -> None:
        """Dos requests rápidas al mismo dominio esperan el delay."""
        delay = DomainDelay(default_delay=0.5)
        await delay.wait_if_needed("example.com")
        start = time.monotonic()
        await delay.wait_if_needed("example.com")
        elapsed = time.monotonic() - start
        assert elapsed >= 0.5

    @pytest.mark.asyncio
    async def test_no_wait_after_sufficient_time(self) -> None:
        """Si pasó suficiente tiempo, no espera."""
        delay = DomainDelay(default_delay=0.1)
        await delay.wait_if_needed("example.com")
        await asyncio.sleep(0.2)
        start = time.monotonic()
        await delay.wait_if_needed("example.com")
        elapsed = time.monotonic() - start
        assert elapsed < 0.1  # No debió esperar

    @pytest.mark.asyncio
    async def test_custom_delay_per_domain(self) -> None:
        """Usa delay custom por dominio cuando se provee."""
        delay = DomainDelay(default_delay=0.01)
        await delay.wait_if_needed("fast.com")
        start = time.monotonic()
        await delay.wait_if_needed("fast.com", delay=0.3)
        elapsed = time.monotonic() - start
        # Tolerancia por precisión de asyncio.sleep en Windows
        assert elapsed >= 0.25, f"Esperaba >=0.3s, obtuve {elapsed:.4f}s"

    @pytest.mark.asyncio
    async def test_different_domains_independent(self) -> None:
        """Dominios distintos no interfieren entre sí."""
        delay = DomainDelay(default_delay=5.0)
        await delay.wait_if_needed("domain-a.com")
        start = time.monotonic()
        await delay.wait_if_needed("domain-b.com")
        elapsed = time.monotonic() - start
        assert elapsed < 1.0  # Dominio distinto, no debe esperar
