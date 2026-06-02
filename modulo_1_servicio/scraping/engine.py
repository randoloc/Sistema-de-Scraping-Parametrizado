"""Motor principal de scraping.

Coordina el flujo completo: recibe una configuración,
orquesta los extractores, aplica filtros y devuelve resultados.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from modulo_1_servicio.scraping.models import (
    ExtractedItem,
    FilterConfig,
    ScrapeConfig,
    ScrapeResult,
    ScraperError,
)

logger = logging.getLogger(__name__)


class ScraperEngine(ABC):
    """Motor abstracto de scraping."""

    @abstractmethod
    async def execute(self, config: ScrapeConfig) -> ScrapeResult:
        ...


class FilterEngine:
    """Aplica filtros a los items extraídos."""

    def __init__(self, config: FilterConfig) -> None:
        self._config = config

    def apply(self, items: list[ExtractedItem]) -> list[ExtractedItem]:
        result = items
        if self._config.include_patterns:
            result = self._filter_include(result)
        if self._config.exclude_patterns:
            result = self._filter_exclude(result)
        if self._config.min_length is not None:
            result = self._filter_min_length(result)
        if self._config.max_length is not None:
            result = self._filter_max_length(result)
        if self._config.deduplicate:
            result = self._deduplicate(result)
        if self._config.max_results is not None:
            result = result[: self._config.max_results]
        return result

    def _filter_include(self, items: list[ExtractedItem]) -> list[ExtractedItem]:
        import re
        return [
            it for it in items
            if any(re.search(p, str(it.data)) for p in self._config.include_patterns)
        ]

    def _filter_exclude(self, items: list[ExtractedItem]) -> list[ExtractedItem]:
        import re
        return [
            it for it in items
            if not any(re.search(p, str(it.data)) for p in self._config.exclude_patterns)
        ]

    def _filter_min_length(self, items: list[ExtractedItem]) -> list[ExtractedItem]:
        min_len = self._config.min_length or 0
        return [it for it in items if len(str(it.data)) >= min_len]

    def _filter_max_length(self, items: list[ExtractedItem]) -> list[ExtractedItem]:
        max_len = self._config.max_length or 0
        return [it for it in items if len(str(it.data)) <= max_len]

    def _deduplicate(self, items: list[ExtractedItem]) -> list[ExtractedItem]:
        seen: set[int] = set()
        result = []
        for item in items:
            key = hash(frozenset(item.data.items()))
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result


class Orchestrator:
    """Orquestador principal del scraping."""

    def __init__(self) -> None:
        self._engines: dict[str, ScraperEngine] = {}

    def register_engine(self, source_type: str, engine: ScraperEngine) -> None:
        self._engines[source_type] = engine

    def get_engine(self, source_type: str) -> ScraperEngine:
        engine = self._engines.get(source_type)
        if engine is None:
            raise ScraperError(
                f"No hay engine registrado para source_type: {source_type}"
            )
        return engine

    async def run(self, config: ScrapeConfig) -> ScrapeResult:
        logger.info("Iniciando scraping | source=%s | type=%s", config.source, config.source_type)
        started_at = datetime.now(timezone.utc)
        errors: list[str] = []
        all_items: list[ExtractedItem] = []

        try:
            engine = self.get_engine(config.source_type.value)
            result = await engine.execute(config)
            all_items = list(result.items)
            errors.extend(result.errors)
            if config.filters:
                filter_engine = FilterEngine(config.filters)
                all_items = filter_engine.apply(all_items)
        except ScraperError as e:
            logger.error("Error durante scraping: %s", e)
            errors.append(str(e))
        except Exception as e:
            logger.exception("Error inesperado durante scraping")
            errors.append(f"Unexpected error: {e}")

        return ScrapeResult(
            config=config,
            items=tuple(all_items),
            total_found=len(all_items),
            errors=tuple(errors),
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )
