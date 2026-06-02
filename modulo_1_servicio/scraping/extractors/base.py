"""Extractor base para implementar extractores concretos."""

from __future__ import annotations

import logging
from abc import abstractmethod
from datetime import datetime, timezone
from typing import Any

from modulo_1_servicio.scraping.engine import ScraperEngine
from modulo_1_servicio.scraping.models import (
    ExtractedItem,
    FieldDefinition,
    FieldType,
    ScrapeConfig,
    ScrapeResult,
)

logger = logging.getLogger(__name__)


class BaseExtractor(ScraperEngine):
    """Base para extractores concretos. Solo implementar fetch_content."""

    async def execute(self, config: ScrapeConfig) -> ScrapeResult:
        started_at = datetime.now(timezone.utc)
        errors: list[str] = []
        all_items: list[ExtractedItem] = []

        try:
            content = await self.fetch_content(config)
            items = await self.parse_items(content, config)
            all_items.extend(items)
        except Exception as e:
            logger.exception("Error executing extractor")
            errors.append(str(e))

        return ScrapeResult(
            config=config,
            items=tuple(all_items),
            total_found=len(all_items),
            errors=tuple(errors),
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            pages_scraped=1,
        )

    @abstractmethod
    async def fetch_content(self, config: ScrapeConfig) -> Any:
        ...

    async def parse_items(
        self, content: Any, config: ScrapeConfig
    ) -> list[ExtractedItem]:
        raw_items = self._locate_items(content, config)
        return [self._extract_fields(item, config) for item in raw_items]

    def _locate_items(self, content: Any, config: ScrapeConfig) -> list[Any]:
        if config.container_selector:
            return self._select_all(content, config.container_selector)
        return [content]

    def _extract_fields(self, container: Any, config: ScrapeConfig) -> ExtractedItem:
        data: dict[str, Any] = {}
        for field in config.fields:
            try:
                value = self._extract_field(container, field)
                data[field.name] = value
            except Exception as e:
                logger.warning("Error extrayendo campo '%s': %s", field.name, e)
                data[field.name] = field.default if not field.required else None
        return ExtractedItem(data=data, source_url=config.source, rank=0)

    def _extract_field(self, container: Any, field: FieldDefinition) -> Any:
        raw = self._select_one(container, field.selector)
        if raw is None:
            if field.required:
                raise ValueError(f"Campo requerido '{field.name}' no encontrado")
            return field.default
        return self._convert_type(raw, field.field_type)

    def _convert_type(self, value: Any, field_type: FieldType) -> Any:
        text = str(value).strip()
        converters = {
            FieldType.TEXT: lambda t: t,
            FieldType.URL: lambda t: t,
            FieldType.HTML: lambda t: t,
            FieldType.IMAGE: lambda t: t,
            FieldType.NUMBER: lambda t: self._safe_float(t),
            FieldType.PRICE: lambda t: self._parse_price(t),
            FieldType.DATE: lambda t: t,
            FieldType.BOOLEAN: lambda t: t.lower() in ("true", "1", "yes", "sí"),
        }
        return converters.get(field_type, converters[FieldType.TEXT])(text)

    @staticmethod
    def _safe_float(value: str) -> float | None:
        try:
            return float(value.replace(",", "").replace(" ", ""))
        except ValueError:
            return None

    @staticmethod
    def _parse_price(value: str) -> float | None:
        """Parsea un precio desde string, manejando formatos US y europeos.

        $39.99          → 39.99
        €1.234,56       → 1234.56
        1,234.56 USD    → 1234.56
        39.99           → 39.99
        """
        import re

        cleaned = re.sub(r"[^\d,.]", "", value)
        if not cleaned:
            return None

        dots = cleaned.count(".")
        commas = cleaned.count(",")

        try:
            # Sin separadores
            if dots == 0 and commas == 0:
                return float(cleaned)

            # US: 1,234.56 → quita comas
            if commas > 0 and dots > 0 and cleaned.rfind(".") > cleaned.rfind(","):
                return float(cleaned.replace(",", ""))

            # EU: 1.234,56 → quita puntos, coma a punto
            if commas > 0 and dots > 0 and cleaned.rfind(",") > cleaned.rfind("."):
                return float(cleaned.replace(".", "").replace(",", "."))

            # Solo comas
            if commas > 0 and dots == 0:
                parts = cleaned.split(",")
                if len(parts[-1]) == 2:
                    return float(cleaned.replace(",", "."))
                return float(cleaned.replace(",", ""))

            # Solo puntos
            if dots > 0 and commas == 0:
                parts = cleaned.split(".")
                if len(parts[-1]) == 2 and len(parts) == 2:
                    return float(cleaned)
                return float(cleaned.replace(".", ""))

            return float(cleaned)
        except (ValueError, TypeError):
            return None

    @abstractmethod
    def _select_one(self, container: Any, selector: str) -> Any | None:
        ...

    @abstractmethod
    def _select_all(self, container: Any, selector: str) -> list[Any]:
        ...
