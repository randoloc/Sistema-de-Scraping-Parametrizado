"""Modelos de la aplicación de administración.

Replican (y a veces simplifican) los modelos del Módulo 1 para
no depender directamente de ellos. La API layer los usa para
construir los payloads que se envían al servicio.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ─── Tipos de filtros de usuario ─────────────────────────────

FILTER_TYPES = [
    ("text", "Texto libre"),
    ("range", "Rango (min/max)"),
    ("dropdown", "Lista desplegable"),
    ("checkbox", "Checkbox"),
    ("date_range", "Rango de fechas"),
]

FIELD_TYPES = [
    "text",
    "price",
    "url",
    "number",
    "date",
    "image",
    "phone",
    "email",
    "boolean",
]


# ─── Modelos existentes ──────────────────────────────────────


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


# ═══════════════════════════════════════════════════════════════
# NUEVOS: Servicio de scraping + Filtros de usuario
# ═══════════════════════════════════════════════════════════════


@dataclass
class SourceConfig:
    """Una fuente/dirección web donde buscar.

    Attributes:
        name: Nombre descriptivo (ej. "Revolico", "Facebook Marketplace")
        url: Dirección web completa
        source_type: Tipo ("web_page" por defecto)
    """

    name: str
    url: str
    source_type: str = "web_page"


@dataclass
class FieldFilterDef:
    """Define un filtro que el usuario podrá ajustar al ejecutar el servicio.

    Attributes:
        field_name: Nombre del campo al que aplica (debe coincidir con un FieldConfig.name)
        label: Etiqueta visible en la UI (ej. "Precio mínimo", "Ubicación")
        filter_type: Tipo de control UI — "text", "range", "dropdown", "checkbox", "date_range"
        options: Opciones para dropdown/checkbox
        placeholder: Texto de ayuda en el input
        required: Si el usuario debe completarlo antes de ejecutar
        order: Orden de aparición en la UI
    """

    field_name: str
    label: str
    filter_type: str = "text"
    options: list[str] | None = None
    placeholder: str | None = None
    required: bool = False
    order: int = 0


@dataclass
class ServiceDefinition:
    """Un servicio de scraping guardado, con nombre y filtros configurables.

    Representa un scraper para un dominio específico (autos, casas, medicamentos...)
    que el usuario crea una vez y ejecuta múltiples veces con distintos filtros.
    Soporta múltiples fuentes (varios sitios web) para un mismo servicio.
    """

    service_id: str = ""
    name: str = ""
    description: str = ""
    created_at: str = ""
    updated_at: str = ""
    # Múltiples fuentes
    sources: list[SourceConfig] = field(default_factory=list)
    # Campos a extraer (compartidos entre todas las fuentes)
    fields: list[FieldConfig] = field(default_factory=list)
    field_filters: list[FieldFilterDef] = field(default_factory=list)
    # Config de scraping (se aplica a todas las fuentes)
    delivery: DeliveryConfig = field(default_factory=DeliveryConfig)
    timeout: int = 30

    def generate_id(self) -> str:
        return uuid.uuid4().hex[:12]

    def to_dict(self) -> dict[str, Any]:
        return {
            "service_id": self.service_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "sources": [
                {"name": s.name, "url": s.url, "source_type": s.source_type}
                for s in self.sources
            ],
            "fields": [
                {"name": f.name, "selector": f.selector, "field_type": f.field_type}
                for f in self.fields
            ],
            "field_filters": [
                {
                    "field_name": ff.field_name,
                    "label": ff.label,
                    "filter_type": ff.filter_type,
                    "options": ff.options,
                    "placeholder": ff.placeholder,
                    "required": ff.required,
                    "order": ff.order,
                }
                for ff in self.field_filters
            ],
            "delivery": {
                "emails": self.delivery.emails,
                "whatsapp_numbers": self.delivery.whatsapp_numbers,
                "generate_web": self.delivery.generate_web,
            },
            "timeout": self.timeout,
            "source": self.sources[0].url if self.sources else "",
            "source_type": self.sources[0].source_type if self.sources else "web_page",
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ServiceDefinition:
        fields = [
            FieldConfig(name=f["name"], selector=f["selector"], field_type=f.get("field_type", "text"))
            for f in data.get("fields", [])
        ]
        field_filters = [
            FieldFilterDef(
                field_name=ff["field_name"],
                label=ff["label"],
                filter_type=ff.get("filter_type", "text"),
                options=ff.get("options"),
                placeholder=ff.get("placeholder"),
                required=ff.get("required", False),
                order=ff.get("order", 0),
            )
            for ff in data.get("field_filters", [])
        ]
        # Soporta tanto el nuevo formato (sources) como el viejo (source único)
        sources_raw = data.get("sources", [])
        if not sources_raw and data.get("source"):
            sources_raw = [
                {"name": "Fuente 1", "url": data["source"], "source_type": data.get("source_type", "web_page")}
            ]
        sources = [
            SourceConfig(name=s["name"], url=s["url"], source_type=s.get("source_type", "web_page"))
            for s in sources_raw
        ]
        deliv = data.get("delivery", {})
        return cls(
            service_id=data.get("service_id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            sources=sources,
            fields=fields,
            field_filters=field_filters,
            delivery=DeliveryConfig(
                emails=deliv.get("emails", []),
                whatsapp_numbers=deliv.get("whatsapp_numbers", []),
                generate_web=deliv.get("generate_web", True),
            ),
            timeout=data.get("timeout", 30),
        )
