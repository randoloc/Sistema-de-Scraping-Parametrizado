"""Modelos de la aplicación de administración.

Replican (y a veces simplifican) los modelos del Módulo 1 para
no depender directamente de ellos. La API layer los usa para
construir los payloads que se envían al servicio.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FieldConfig:
    """Configuración de un campo a extraer."""

    name: str
    selector: str
    field_type: str = "text"
    transform: str | None = None
    required: bool = True
    default: Any = None


@dataclass
class FilterConfig:
    """Filtros para refinar resultados."""

    include_patterns: list[str] = field(default_factory=list)
    exclude_patterns: list[str] = field(default_factory=list)
    min_length: int | None = None
    max_length: int | None = None
    deduplicate: bool = True
    max_results: int | None = None


@dataclass
class PaginationConfig:
    """Configuración de paginación."""

    strategy: str = "url"
    url_template: str | None = None
    max_pages: int = 1


@dataclass
class DeliveryConfig:
    """Configuración de entrega de resultados."""

    emails: list[str] = field(default_factory=list)
    whatsapp_numbers: list[str] = field(default_factory=list)
    generate_web: bool = True


@dataclass
class ScrapeJobConfig:
    """Configuración completa para un trabajo de scraping."""

    source: str
    source_type: str = "web_page"
    fields: list[FieldConfig] = field(default_factory=list)
    container_selector: str | None = None
    filters: FilterConfig = field(default_factory=FilterConfig)
    pagination: PaginationConfig = field(default_factory=PaginationConfig)
    delivery: DeliveryConfig = field(default_factory=DeliveryConfig)
    timeout: int = 30
    rate_limit: float = 1.0

    def to_api_dict(self) -> dict[str, Any]:
        """Convierte a diccionario para enviar al Módulo 1."""
        return {
            "source_type": self.source_type,
            "source": self.source,
            "container_selector": self.container_selector,
            "fields": [
                {
                    "name": f.name,
                    "selector": f.selector,
                    "type": f.field_type,
                    "transform": f.transform,
                    "required": f.required,
                    "default": f.default,
                }
                for f in self.fields
            ],
            "filters": {
                "include": self.filters.include_patterns,
                "exclude": self.filters.exclude_patterns,
                "min_length": self.filters.min_length,
                "max_length": self.filters.max_length,
                "deduplicate": self.filters.deduplicate,
                "max_results": self.filters.max_results,
            },
            "pagination": {
                "strategy": self.pagination.strategy,
                "url_template": self.pagination.url_template,
                "max_pages": self.pagination.max_pages,
            },
            "delivery": {
                "emails": self.delivery.emails,
                "whatsapp_numbers": self.delivery.whatsapp_numbers,
                "generate_web": self.delivery.generate_web,
            },
            "timeout": self.timeout,
            "rate_limit": self.rate_limit,
        }


@dataclass
class HistoryEntry:
    """Entrada en el historial de operaciones."""

    operation_id: str
    source: str
    total_found: int
    errors: int
    timestamp: str
    status: str
