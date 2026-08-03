from __future__ import annotations

import importlib
import logging
from typing import Any
from urllib.parse import quote

from modulo_1_servicio.scraping.adapters.loader import AdapterLoader
from modulo_1_servicio.scraping.engine import Orchestrator
from modulo_1_servicio.scraping.extractors.beautifulsoup_extractor import (
    BeautifulSoupExtractor,
)
from modulo_1_servicio.scraping.models import (
    FieldDefinition,
    FieldType,
    ScrapeConfig,
    SourceType,
)
from modulo_1_servicio.scraping.normalizer import ResultNormalizer

logger = logging.getLogger(__name__)

_orchestrator = Orchestrator()
_orchestrator.register_engine("web_page", BeautifulSoupExtractor())

_adapter_loader = AdapterLoader()
_adapter_loader.load_all()

_normalizer = ResultNormalizer()

# Cache de clases de adaptadores Python custom (ej: revolico_adapter.RevolicoAdapter)
_python_adapter_classes: dict[str, type] = {}


def _get_python_adapter_class(python_adapter_path: str) -> type:
    """Importa dinámicamente y cachea una clase de adaptador Python custom."""
    if python_adapter_path in _python_adapter_classes:
        return _python_adapter_classes[python_adapter_path]

    parts = python_adapter_path.rsplit(".", 1)
    if len(parts) != 2:
        raise ValueError(
            f"Formato inválido: '{python_adapter_path}'. Esperado: 'module.ClassName'"
        )
    module_name, class_name = parts
    full_module = f"modulo_1_servicio.scraping.adapters.{module_name}"
    module = importlib.import_module(full_module)
    cls = getattr(module, class_name)
    _python_adapter_classes[python_adapter_path] = cls
    logger.info("Adaptador Python cargado: %s → %s.%s", python_adapter_path, full_module, class_name)
    return cls


async def search(
    query: str,
    vertical: str = "test",
    site: str | None = None,
    max_pages: int = 1,
) -> dict[str, Any]:
    if site:
        adapter = _adapter_loader.get(site)
        if adapter is None:
            return {"error": f"Adaptador '{site}' no encontrado"}
        if adapter.vertical != vertical:
            return {"error": f"Adaptador '{site}' no pertenece a vertical '{vertical}'"}
        matching = [adapter]
    else:
        matching = _adapter_loader.get_by_vertical(vertical)
        if not matching:
            return {
                "query": query,
                "vertical": vertical,
                "total_found": 0,
                "adapters_used": 0,
                "items": [],
            }

    all_items: list[dict[str, Any]] = []
    total_rank = 0

    for adapter in matching:
        try:
            # ── RUTA: Adaptador Python custom (ej: Revolico Next.js) ──
            if adapter.python_adapter:
                cls = _get_python_adapter_class(adapter.python_adapter)
                instance = cls()
                try:
                    canonical_items = await instance.search(query, page=1)
                finally:
                    await instance.close()

                normalized_dicts = [item.model_dump() for item in canonical_items]
                for item in normalized_dicts:
                    item["rank"] = total_rank
                    total_rank += 1
                all_items.extend(normalized_dicts)
                continue

            encoded = quote(query)
            search_url = adapter.search_url.replace("{query}", encoded).replace("{page}", str(1))
            if "{query}" not in adapter.search_url and "{page}" not in adapter.search_url:
                search_url = adapter.search_url

            fields = tuple(
                FieldDefinition(
                    name=f.name,
                    selector=f.selector,
                    field_type=(
                        FieldType(f.type)
                        if f.type in ("text", "price", "url", "number", "date", "image")
                        else FieldType.TEXT
                    ),
                    required=f.required,
                )
                for f in adapter.fields
            )

            scrape_config = ScrapeConfig(
                source_type=SourceType.WEB_PAGE,
                source=search_url,
                fields=fields,
                container_selector=adapter.container_selector,
                rate_limit=1.0,
            )

            result = await _orchestrator.run(scrape_config)

            if not result.items:
                continue

            raw_items = [item.data for item in result.items]

            if adapter.canonical_map:
                canonical_items = _normalizer.normalize(
                    canonical_map=adapter.canonical_map,
                    raw_items=raw_items,
                    source_site=adapter.name,
                    source_url=search_url,
                    start_rank=total_rank,
                )
                normalized_dicts = [item.model_dump() for item in canonical_items]
                all_items.extend(normalized_dicts)
                total_rank += len(canonical_items)
            else:
                for i, raw in enumerate(raw_items):
                    all_items.append({
                        "title": None,
                        "description": None,
                        "price": None,
                        "currency": None,
                        "url": None,
                        "image_url": None,
                        "date": None,
                        "location": None,
                        "source_site": adapter.name,
                        "source_url": search_url,
                        "rank": total_rank + i,
                        "raw_data": raw,
                    })
                total_rank += len(raw_items)

        except Exception as e:
            logger.error("Error en adaptador %s: %s", adapter.name, e)

    return {
        "query": query,
        "vertical": vertical,
        "total_found": len(all_items),
        "adapters_used": len(matching),
        "items": all_items,
    }
