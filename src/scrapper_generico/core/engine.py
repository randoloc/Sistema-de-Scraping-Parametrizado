"""Motor principal de scraping.

Coordina el flujo completo: recibe una configuración,
orquesta los extractores, aplica filtros y devuelve resultados.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from scrapper_generico.core.models import (
    ExtractedItem,
    FilterConfig,
    ScrapeConfig,
    ScrapeResult,
    ScraperError,
)

logger = logging.getLogger(__name__)


class ScraperEngine(ABC):
    """Motor abstracto de scraping.

    La idea es simple: le pasas un ScrapeConfig y te devuelve un ScrapeResult.
    Cada implementación concreta sabe cómo lidiar con un SourceType específico.
    """

    @abstractmethod
    async def execute(self, config: ScrapeConfig) -> ScrapeResult:
        """Ejecuta una operación de scraping.

        Args:
            config: Configuración completa de la operación.

        Returns:
            Resultado con los items extraídos y metadatos.

        Raises:
            ScraperConnectionError: Si no se puede conectar a la fuente.
            ScraperParseError: Si el contenido no se puede parsear.
        """


class FilterEngine:
    """Aplica filtros a los items extraídos."""

    def __init__(self, config: FilterConfig) -> None:
        self._config = config

    def apply(self, items: list[ExtractedItem]) -> list[ExtractedItem]:
        """Aplica todos los filtros configurados."""
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
        """Mantiene solo items que coinciden con al menos un patrón de inclusión."""
        import re

        filtered: list[ExtractedItem] = []
        for item in items:
            text = str(item.data)
            if any(re.search(p, text) for p in self._config.include_patterns):
                filtered.append(item)
        return filtered

    def _filter_exclude(self, items: list[ExtractedItem]) -> list[ExtractedItem]:
        """Elimina items que coinciden con algún patrón de exclusión."""
        import re

        return [
            item
            for item in items
            if not any(
                re.search(p, str(item.data))
                for p in self._config.exclude_patterns
            )
        ]

    def _filter_min_length(self, items: list[ExtractedItem]) -> list[ExtractedItem]:
        min_len = self._config.min_length or 0
        return [item for item in items if len(str(item.data)) >= min_len]

    def _filter_max_length(self, items: list[ExtractedItem]) -> list[ExtractedItem]:
        max_len = self._config.max_length or 0
        return [item for item in items if len(str(item.data)) <= max_len]

    def _deduplicate(self, items: list[ExtractedItem]) -> list[ExtractedItem]:
        seen: set[int] = set()
        result: list[ExtractedItem] = []
        for item in items:
            key = hash(frozenset(item.data.items()))
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result


class Orchestrator:
    """Orquestador principal del scraping.

    Coordina el pipeline completo:
    1. Selecciona el engine adecuado según el source_type.
    2. Ejecuta el scraping.
    3. Aplica filtros.
    4. Devuelve el resultado estructurado.
    """

    def __init__(self) -> None:
        self._engines: dict[str, ScraperEngine] = {}

    def register_engine(self, source_type: str, engine: ScraperEngine) -> None:
        """Registra un engine para un tipo de fuente."""
        self._engines[source_type] = engine

    def get_engine(self, source_type: str) -> ScraperEngine:
        """Obtiene el engine para un tipo de fuente."""
        engine = self._engines.get(source_type)
        if engine is None:
            raise ScraperError(
                f"No hay engine registrado para source_type: {source_type}"
            )
        return engine

    async def run(self, config: ScrapeConfig) -> ScrapeResult:
        """Ejecuta el pipeline completo de scraping."""
        logger.info(
            "Iniciando scraping | source=%s | type=%s",
            config.source,
            config.source_type,
        )

        started_at = datetime.utcnow()
        errors: list[str] = []
        all_items: list[ExtractedItem] = []

        try:
            engine = self.get_engine(config.source_type.value)
            result = await engine.execute(config)

            all_items = list(result.items)
            errors.extend(result.errors)

            # Aplicar filtros
            if config.filters:
                filter_engine = FilterEngine(config.filters)
                all_items = filter_engine.apply(all_items)

        except ScraperError as e:
            logger.error("Error durante scraping: %s", e)
            errors.append(str(e))
        except Exception as e:
            logger.exception("Error inesperado durante scraping")
            errors.append(f"Unexpected error: {e}")

        completed_at = datetime.utcnow()

        return ScrapeResult(
            config=config,
            items=tuple(all_items),
            total_found=len(all_items),
            errors=tuple(errors),
            started_at=started_at,
            completed_at=completed_at,
        )
