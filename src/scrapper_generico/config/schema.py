"""Esquemas de configuración serializable (YAML/JSON).

Permite definir configuraciones de scraping en archivos YAML/JSON
y convertirlas a los modelos de dominio.

Separa la representación serializable (dict/YAML/JSON)
de los modelos de dominio tipados (core.models).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from scrapper_generico.core.models import (
    FieldDefinition,
    FieldType,
    FilterConfig,
    OutputFormat,
    PaginationConfig,
    ScrapeConfig,
    SourceType,
)


def load_config(path: str | Path) -> ScrapeConfig:
    """Carga una configuración desde un archivo YAML/JSON."""
    path = Path(path)
    raw = _read_file(path)
    return _dict_to_config(raw)


def load_config_from_dict(data: dict[str, Any]) -> ScrapeConfig:
    """Convierte un diccionario en ScrapeConfig."""
    return _dict_to_config(data)


def _read_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Archivo de config no encontrado: {path}")

    content = path.read_text(encoding="utf-8")

    if path.suffix in (".yaml", ".yml"):
        return dict(yaml.safe_load(content))

    import json

    return dict(json.loads(content))


def _dict_to_config(data: dict[str, Any]) -> ScrapeConfig:
    """Transforma un dict genérico en ScrapeConfig."""

    source_type_str = data.get("source_type", "web_page")
    source_type = SourceType(source_type_str)

    fields = tuple(
        FieldDefinition(
            name=f["name"],
            selector=f["selector"],
            field_type=FieldType(f.get("type", "text")),
            transform=f.get("transform"),
            required=f.get("required", True),
            default=f.get("default"),
        )
        for f in data.get("fields", [])
    ]

    filter_raw = data.get("filters", {})
    filters = FilterConfig(
        include_patterns=tuple(filter_raw.get("include", [])),
        exclude_patterns=tuple(filter_raw.get("exclude", [])),
        min_length=filter_raw.get("min_length"),
        max_length=filter_raw.get("max_length"),
        deduplicate=filter_raw.get("deduplicate", True),
        max_results=filter_raw.get("max_results"),
    )

    pag_raw = data.get("pagination", {})
    pagination = PaginationConfig(
        strategy=pag_raw.get("strategy", "url"),
        url_template=pag_raw.get("url_template"),
        next_selector=pag_raw.get("next_selector"),
        max_pages=pag_raw.get("max_pages", 1),
        page_param=pag_raw.get("page_param", "page"),
        start_page=pag_raw.get("start_page", 1),
        step=pag_raw.get("step", 1),
    )

    return ScrapeConfig(
        source_type=source_type,
        source=data["source"],
        fields=fields,
        container_selector=data.get("container_selector"),
        filters=filters,
        pagination=pagination,
        output_format=OutputFormat(data.get("output_format", "json")),
        output_path=data.get("output_path"),
        headers=data.get("headers", {}),
        timeout=data.get("timeout", 30),
        user_agent=data.get("user_agent"),
        respect_robots_txt=data.get("respect_robots_txt", True),
        rate_limit=data.get("rate_limit", 1.0),
    )
