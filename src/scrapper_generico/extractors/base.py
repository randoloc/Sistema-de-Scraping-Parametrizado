"""Extractor base y helpers para implementar extractores concretos.

Un extractor sabe cómo navegar una fuente específica
(web, API, archivo local) y extraer los campos definidos.
"""

from __future__ import annotations

import logging
from abc import abstractmethod
from datetime import datetime
from typing import Any

from scrapper_generico.core.engine import ScraperEngine
from scrapper_generico.core.models import (
    ExtractedItem,
    FieldDefinition,
    FieldType,
    ScrapeConfig,
    ScrapeResult,
)

logger = logging.getLogger(__name__)


class BaseExtractor(ScraperEngine):
    """Base para todos los extractores concretos.

    Implementa la lógica común de extracción de campos.
    Cada extractor concreto solo necesita implementar ``fetch_content``.
    """

    async def execute(self, config: ScrapeConfig) -> ScrapeResult:
        """Ejecuta la extracción: fetch -> parse -> extract."""
        started_at = datetime.utcnow()
        errors: list[str] = []
        all_items: list[ExtractedItem] = []

        try:
            content = await self.fetch_content(config)
            items = await self.parse_items(content, config)
            all_items.extend(items)
        except Exception as e:
            logger.exception("Error executing extractor")
            errors.append(str(e))

        completed_at = datetime.utcnow()

        return ScrapeResult(
            config=config,
            items=tuple(all_items),
            total_found=len(all_items),
            errors=tuple(errors),
            started_at=started_at,
            completed_at=completed_at,
            pages_scraped=1,
        )

    @abstractmethod
    async def fetch_content(self, config: ScrapeConfig) -> Any:
        """Obtiene el contenido crudo de la fuente."""

    async def parse_items(
        self, content: Any, config: ScrapeConfig
    ) -> list[ExtractedItem]:
        """Parsea el contenido y extrae los items según la config.

        Este método puede ser sobreescrito para lógica de parseo
        más compleja (paginación, navegación, etc).
        """
        raw_items = self._locate_items(content, config)
        return [self._extract_fields(item, config) for item in raw_items]

    def _locate_items(self, content: Any, config: ScrapeConfig) -> list[Any]:
        """Localiza los contenedores de items dentro del contenido.

        Si container_selector está definido, busca dentro de esos contenedores.
        Si no, trata el contenido completo como un solo item.
        """
        if config.container_selector:
            return self._select_all(content, config.container_selector)
        return [content]

    def _extract_fields(
        self, container: Any, config: ScrapeConfig
    ) -> ExtractedItem:
        """Extrae todos los campos definidos de un contenedor."""
        data: dict[str, Any] = {}
        for field in config.fields:
            try:
                value = self._extract_field(container, field)
                data[field.name] = value
            except Exception as e:
                logger.warning("Error extrayendo campo '%s': %s", field.name, e)
                if field.required:
                    data[field.name] = None
                else:
                    data[field.name] = field.default

        return ExtractedItem(
            data=data,
            source_url=config.source,
            rank=0,
        )

    def _extract_field(self, container: Any, field: FieldDefinition) -> Any:
        """Extrae un campo específico usando el selector y tipo."""
        raw = self._select_one(container, field.selector)

        if raw is None:
            if field.required:
                raise ValueError(
                    f"Campo requerido '{field.name}' no encontrado "
                    f"con selector '{field.selector}'"
                )
            return field.default

        return self._convert_type(raw, field.field_type)

    def _convert_type(self, value: Any, field_type: FieldType) -> Any:
        """Convierte el valor extraído al tipo de campo deseado."""
        text = str(value).strip()

        converters = {
            FieldType.TEXT: lambda t: t,
            FieldType.URL: lambda t: t,
            FieldType.HTML: lambda t: t,
            FieldType.IMAGE: lambda t: t,
            FieldType.NUMBER: lambda t: self._safe_float(t),
            FieldType.PRICE: lambda t: self._parse_price(t),
            FieldType.DATE: lambda t: t,  # Se define el formato en transform
            FieldType.BOOLEAN: lambda t: t.lower() in ("true", "1", "yes", "sí"),
        }

        converter = converters.get(field_type, converters[FieldType.TEXT])
        return converter(text)

    @staticmethod
    def _safe_float(value: str) -> float | None:
        try:
            return float(value.replace(",", "").replace(" ", ""))
        except ValueError:
            return None

    @staticmethod
    def _parse_price(value: str) -> float | None:
        import re

        match = re.search(r"[\d,.]+", value.replace(".", "").replace(",", "."))
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None
        return None

    @abstractmethod
    def _select_one(self, container: Any, selector: str) -> Any | None:
        """Selecciona UN elemento del contenedor usando el selector."""

    @abstractmethod
    def _select_all(self, container: Any, selector: str) -> list[Any]:
        """Selecciona TODOS los elementos del contenedor usando el selector."""
