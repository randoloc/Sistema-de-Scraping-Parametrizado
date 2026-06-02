"""Rutas de la API para gestionar operaciones de scraping."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from modulo_1_servicio.config.schema import load_config_from_dict
from modulo_1_servicio.deliveries.web import generate_results_page
from modulo_1_servicio.scraping.adapters.loader import AdapterLoader
from modulo_1_servicio.scraping.engine import Orchestrator
from modulo_1_servicio.scraping.extractors.beautifulsoup_extractor import (
    BeautifulSoupExtractor,
)
from modulo_1_servicio.scraping.models import ScrapeResult

router = APIRouter(prefix="/api", tags=["scraping"])

# Almacenamiento en memoria para resultados (V1)
# En producción: SQLite
_results_store: dict[str, ScrapeResult] = {}

_orchestrator = Orchestrator()
_orchestrator.register_engine("web_page", BeautifulSoupExtractor())
_orchestrator.register_engine("api", BeautifulSoupExtractor())
_orchestrator.register_engine("html_file", BeautifulSoupExtractor())
_orchestrator.register_engine("sitemap", BeautifulSoupExtractor())

# Cargador de adaptadores
_adapter_loader = AdapterLoader()
_adapter_loader.load_all()


@router.post("/scrape")
async def run_scrape(config: dict[str, Any]) -> dict[str, Any]:
    """Recibe una configuración de scraping y la ejecuta.

    Returns:
        ID de la operación para consultar resultados.
    """
    try:
        scrape_config = load_config_from_dict(config)
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    op_id = str(uuid.uuid4())[:8]

    result = await _orchestrator.run(scrape_config)
    _results_store[op_id] = result

    return {
        "operation_id": op_id,
        "status": "completed" if not result.errors else "completed_with_errors",
        "total_found": result.success_count,
        "total_errors": result.error_count,
        "endpoint": f"/api/results/{op_id}",
    }


@router.get("/results/{operation_id}")
async def get_results(operation_id: str) -> dict[str, Any]:
    """Obtiene los resultados de una operación de scraping."""
    result = _results_store.get(operation_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Operación no encontrada")

    return {
        "operation_id": operation_id,
        "source": result.config.source,
        "total_found": result.success_count,
        "errors": list(result.errors),
        "elapsed_seconds": result.elapsed,
        "items": [
            {"data": item.data, "source_url": item.source_url, "rank": item.rank}
            for item in result.items
        ],
    }


@router.get("/results/{operation_id}/web")
async def get_results_web(operation_id: str) -> str:
    """Obtiene una página HTML elegante con los resultados."""
    result = _results_store.get(operation_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Operación no encontrada")
    return generate_results_page(result, operation_id)


@router.get("/adapters")
async def list_adapters(
    vertical: str | None = Query(default=None, description="Filtrar por vertical"),
) -> dict[str, Any]:
    """Lista todos los adaptadores cargados, opcionalmente filtrados por vertical.

    Returns:
        Dict con lista de adaptadores y metadatos.
    """
    if vertical:
        adapters = _adapter_loader.get_by_vertical(vertical)
    else:
        adapters = _adapter_loader.get_all()

    return {
        "total": len(adapters),
        "vertical": vertical,
        "adapters": [a.model_dump() for a in adapters],
    }
