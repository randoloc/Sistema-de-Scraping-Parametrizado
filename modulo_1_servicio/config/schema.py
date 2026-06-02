"""Carga de configuraciones desde YAML/JSON a los modelos de dominio."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from modulo_1_servicio.scraping.models import (
    DeliveryConfig,
    FieldDefinition,
    FieldType,
    FilterConfig,
    OutputFormat,
    PaginationConfig,
    ScrapeConfig,
    SourceType,
)


def load_config(path: str | Path) -> ScrapeConfig:
    return _dict_to_config(_read_file(Path(path)))


def load_config_from_dict(data: dict[str, Any]) -> ScrapeConfig:
    return _dict_to_config(data)


def _read_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config no encontrado: {path}")
    content = path.read_text(encoding="utf-8")
    if path.suffix in (".yaml", ".yml"):
        return dict(yaml.safe_load(content))
    return dict(json.loads(content))


def _dict_to_config(data: dict[str, Any]) -> ScrapeConfig:
    source_type = SourceType(data.get("source_type", "web_page"))

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
    )

    f = data.get("filters", {})
    filters = FilterConfig(
        include_patterns=tuple(f.get("include", [])),
        exclude_patterns=tuple(f.get("exclude", [])),
        min_length=f.get("min_length"),
        max_length=f.get("max_length"),
        deduplicate=f.get("deduplicate", True),
        max_results=f.get("max_results"),
    )

    p = data.get("pagination", {})
    pagination = PaginationConfig(
        strategy=p.get("strategy", "url"),
        url_template=p.get("url_template"),
        next_selector=p.get("next_selector"),
        max_pages=p.get("max_pages", 1),
        page_param=p.get("page_param", "page"),
        start_page=p.get("start_page", 1),
        step=p.get("step", 1),
    )

    d = data.get("delivery", {})
    delivery = DeliveryConfig(
        emails=tuple(d.get("emails", [])),
        whatsapp_numbers=tuple(d.get("whatsapp_numbers", [])),
        generate_web=d.get("generate_web", True),
    )

    return ScrapeConfig(
        source_type=source_type,
        source=data["source"],
        fields=fields,
        container_selector=data.get("container_selector"),
        filters=filters,
        pagination=pagination,
        delivery=delivery,
        output_format=OutputFormat(data.get("output_format", "json")),
        output_path=data.get("output_path"),
        headers=data.get("headers", {}),
        timeout=data.get("timeout", 30),
        user_agent=data.get("user_agent"),
        respect_robots_txt=data.get("respect_robots_txt", True),
        rate_limit=data.get("rate_limit", 1.0),
    )
