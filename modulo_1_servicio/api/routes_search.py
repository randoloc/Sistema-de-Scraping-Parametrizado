"""Rutas de búsqueda multi-adaptador con normalización de resultados.

Fase 2: endpoint ``POST /api/search`` que recibe una consulta y vertical,
encuentra adaptadores YAML, ejecuta scraping en cada uno y normaliza
los resultados a un schema canónico.

Soporta dos tipos de adaptadores:
- **YAML estándar**: usa selectores CSS + BS4 extractor (flujo normal)
- **Python custom**: usa una clase Python para sitios dinámicos (ej: Revolico)
"""

from __future__ import annotations

import importlib
import logging
from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

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
from modulo_1_servicio.scraping.normalizer import CanonicalItem, ResultNormalizer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["search"])

# Singleton compartido con routes_scrape
_orchestrator = Orchestrator()
_orchestrator.register_engine("web_page", BeautifulSoupExtractor())

_adapter_loader = AdapterLoader()
_adapter_loader.load_all()

_normalizer = ResultNormalizer()

# Cache de clases de adaptadores Python importados
_python_adapter_classes: dict[str, type] = {}


def _get_python_adapter_class(python_adapter_path: str) -> type:
    """Importa dinámicamente y cachea una clase de adaptador Python.

    El formato es ``module.ClassName`` relativo al paquete de adaptadores.
    Ej: ``revolico_adapter.RevolicoAdapter``.
    """
    if python_adapter_path in _python_adapter_classes:
        return _python_adapter_classes[python_adapter_path]

    try:
        parts = python_adapter_path.rsplit(".", 1)
        if len(parts) != 2:
            raise ValueError(
                f"Formato inválido: '{python_adapter_path}'. "
                "Esperado: 'module.ClassName'"
            )
        module_name, class_name = parts

        full_module = f"modulo_1_servicio.scraping.adapters.{module_name}"
        module = importlib.import_module(full_module)
        cls = getattr(module, class_name)
        _python_adapter_classes[python_adapter_path] = cls
        logger.info("Adaptador Python cargado: %s → %s.%s", python_adapter_path, full_module, class_name)
        return cls
    except (ImportError, AttributeError, ValueError) as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error cargando adaptador Python '{python_adapter_path}': {exc}",
        )


class SearchRequest(BaseModel):
    """Payload para búsqueda por adaptadores."""

    query: str = Field(
        min_length=1,
        description="Término de búsqueda (ej: 'autos usados', 'iphone 15')",
    )
    vertical: str = Field(
        min_length=1,
        description="Vertical a buscar (ej: cars, real_estate, jobs, test)",
    )
    site: str | None = Field(
        default=None,
        description="Opcional: filtrar a un sitio específico por nombre de adaptador",
    )
    max_pages: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Páginas de resultados por adaptador",
    )


class SearchAdapterResult(BaseModel):
    """Resultados de un adaptador individual en la búsqueda."""

    adapter_name: str
    site: str
    vertical: str
    items_count: int
    error: str | None = None


class SearchResponse(BaseModel):
    """Respuesta completa de búsqueda multi-adaptador."""

    query: str
    vertical: str
    total_found: int
    adapters_used: int
    adapters: list[SearchAdapterResult]
    items: list[dict[str, Any]]


def _expand_search_url(template: str, query: str, page: int = 1) -> str:
    """Expande un template de URL de búsqueda con query y página.

    Soporta:
    - ``{query}`` → reemplazado con el query URL-encoded
    - ``{page}`` → reemplazado con el número de página
    """
    encoded = quote(query)
    url = template.replace("{query}", encoded).replace("{page}", str(page))
    return url


@router.post("/search")
async def search_adapters(payload: SearchRequest) -> dict[str, Any]:
    """Busca en múltiples adaptadores y normaliza resultados.

    Flujo:
    1. Encuentra adaptadores que coinciden con la vertical
    2. Para cada adaptador, construye la URL de búsqueda
    3. Ejecuta scraping con los selectores del adaptador
    4. Normaliza resultados usando el canonical_map
    5. Retorna items combinados con schema canónico
    """
    # 1. Encontrar adaptadores
    if payload.site:
        adapter = _adapter_loader.get(payload.site)
        if adapter is None:
            raise HTTPException(
                status_code=404,
                detail=f"Adaptador '{payload.site}' no encontrado",
            )
        if adapter.vertical != payload.vertical:
            raise HTTPException(
                status_code=400,
                detail=f"Adaptador '{payload.site}' no pertenece a vertical '{payload.vertical}'",
            )
        matching = [adapter]
    else:
        matching = _adapter_loader.get_by_category(payload.vertical)
        if not matching:
            raise HTTPException(
                status_code=404,
                detail=f"No hay adaptadores para la vertical '{payload.vertical}'",
            )

    all_items: list[dict[str, Any]] = []
    adapter_results: list[SearchAdapterResult] = []
    total_rank = 0

    # 2-4. Ejecutar scraping en cada adaptador
    for adapter in matching:
        adapter_result = SearchAdapterResult(
            adapter_name=adapter.name,
            site=adapter.site,
            vertical=adapter.vertical,
            items_count=0,
        )

        try:
            # ── RUTA: Adaptador Python custom ──
            if adapter.python_adapter:
                cls = _get_python_adapter_class(adapter.python_adapter)
                instance = cls()
                try:
                    canonical_items = await instance.search(payload.query, page=1)
                finally:
                    await instance.close()

                normalized_dicts = [item.model_dump() for item in canonical_items]
                for item in normalized_dicts:
                    item["rank"] = total_rank
                    total_rank += 1

                all_items.extend(normalized_dicts)
                adapter_result.items_count = len(normalized_dicts)

                logger.info(
                    "Adaptador Python %s: %d items para '%s'",
                    adapter.name,
                    adapter_result.items_count,
                    payload.query,
                )
                adapter_results.append(adapter_result)
                continue

            # ── RUTA: YAML estándar (BS4 + selectores) ──
            # Construir URL de búsqueda
            search_url = _expand_search_url(adapter.search_url, payload.query)

            # Si el adapter no usa {query}, usar search_url directamente
            # (como en el caso de httpbin que es una URL fija)
            if "{query}" not in adapter.search_url and "{page}" not in adapter.search_url:
                search_url = adapter.search_url

            # Construir config de scraping desde el adaptador
            fields = tuple(
                FieldDefinition(
                    name=f.name,
                    selector=f.selector,
                    field_type=FieldType(f.type) if f.type in ("text", "price", "url", "number", "date", "image") else FieldType.TEXT,
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

            # Ejecutar scraping
            result = await _orchestrator.run(scrape_config)

            if not result.items:
                logger.info("Adaptador %s: 0 resultados para '%s'", adapter.name, payload.query)
                adapter_results.append(adapter_result)
                continue

            # Extraer datos crudos
            raw_items = [item.data for item in result.items]

            # 5. Normalizar usando canonical_map
            if adapter.canonical_map:
                canonical_items = _normalizer.normalize(
                    canonical_map=adapter.canonical_map,
                    raw_items=raw_items,
                    source_site=adapter.name,
                    source_url=search_url,
                    start_rank=total_rank,
                )
                # Convertir a dicts para serialización
                normalized_dicts = [item.model_dump() for item in canonical_items]
                all_items.extend(normalized_dicts)
                total_rank += len(canonical_items)
                adapter_result.items_count = len(canonical_items)
            else:
                # Sin canonical_map, devolver raw_data envuelto
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
                adapter_result.items_count = len(raw_items)

            logger.info(
                "Adaptador %s: %d items para '%s'",
                adapter.name,
                adapter_result.items_count,
                payload.query,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error en adaptador %s: %s", adapter.name, e)
            adapter_result.error = str(e)

        adapter_results.append(adapter_result)

    # Si ningún adaptador produjo resultados, igual retornamos respuesta
    response = {
        "query": payload.query,
        "vertical": payload.vertical,
        "total_found": len(all_items),
        "adapters_used": len(matching),
        "adapters": [a.model_dump() for a in adapter_results],
        "items": all_items,
    }

    return response


@router.get("/demo", include_in_schema=False, response_class=HTMLResponse)
async def demo_page() -> str:
    """Página HTML de demostración para probar adaptadores sin internet."""
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Demo ScrapperGenérico</title>
<style>
  .item { border:1px solid #ddd; padding:12px; margin:8px 0; border-radius:6px; }
  .title { font-size:18px; font-weight:bold; color:#333; }
  .desc { color:#666; margin:4px 0; }
  .price { color:#059669; font-weight:bold; font-size:16px; }
</style>
</head><body>
<h1>Resultados de Demo</h1>
<p>Esta página simula resultados de búsqueda para probar adaptadores.</p>

<div class="item">
  <div class="title">iPhone 15 Pro Max 256GB</div>
  <div class="desc">Teléfono inteligente Apple, color titanio natural, pantalla 6.7"</div>
  <div class="price">$1,299.00</div>
</div>

<div class="item">
  <div class="title">Samsung Galaxy S24 Ultra</div>
  <div class="desc">Teléfono Android, 512GB, S-Pen integrado, pantalla 6.8"</div>
  <div class="price">$1,199.00</div>
</div>

<div class="item">
  <div class="title">MacBook Air M3 15"</div>
  <div class="desc">Laptop Apple, chip M3, 16GB RAM, 512GB SSD</div>
  <div class="price">$1,499.00</div>
</div>

<div class="item">
  <div class="title">PlayStation 5 Slim</div>
  <div class="desc">Consola Sony, 1TB SSD, incluye control DualSense</div>
  <div class="price">$499.99</div>
</div>

<div class="item">
  <div class="title">Audífonos Sony WH-1000XM5</div>
  <div class="desc">Cancelación de ruido activa, 30h batería, Bluetooth 5.2</div>
  <div class="price">$349.00</div>
</div>
</body></html>"""
