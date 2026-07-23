"""Rutas de búsqueda multi-adaptador con normalización de resultados.

Fase 2: endpoint ``POST /api/search`` que recibe una consulta y vertical,
encuentra adaptadores YAML, ejecuta scraping en cada uno y normaliza
los resultados a un schema canónico.
"""

from __future__ import annotations

import logging
from typing import Annotated, Any
from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from modulo_1_servicio.scraping.adapters.loader import AdapterLoader
from modulo_1_servicio.scraping.engine import Orchestrator
from modulo_1_servicio.scraping.extractors.beautifulsoup_extractor import (
    BeautifulSoupExtractor,
)
from modulo_1_servicio.scraping.models import FieldDefinition, FieldType, ScrapeConfig
from modulo_1_servicio.scraping.normalizer import ResultNormalizer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["search"])

# Singleton compartido con routes_scrape
_orchestrator = Orchestrator()
_orchestrator.register_engine("web_page", BeautifulSoupExtractor())

_adapter_loader = AdapterLoader()
_adapter_loader.load_all()

_normalizer = ResultNormalizer()


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
        matching = _adapter_loader.get_by_vertical(payload.vertical)
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
                )
                for f in adapter.fields
            )

            scrape_config = ScrapeConfig(
                source_type="web_page",
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
