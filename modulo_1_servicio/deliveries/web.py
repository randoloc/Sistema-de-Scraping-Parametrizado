"""Entrega de resultados vía web: genera página HTML elegante."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from modulo_1_servicio.scraping.models import ScrapeResult

HERE = Path(__file__).parent.parent
TEMPLATE_DIR = str(HERE / "templates")

_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))


def generate_results_page(result: ScrapeResult, result_id: str) -> str:
    """Genera una página HTML con los resultados del scraping.

    Returns:
        HTML string completo, listo para servir.
    """
    template = _env.get_template("web_result.html")

    items_data = []
    for i, item in enumerate(result.items, 1):
        items_data.append(
            {
                "rank": i,
                "data": item.data,
                "source_url": item.source_url,
                "extracted_at": item.extracted_at.isoformat(),
            }
        )

    return template.render(
        title=f"Resultados: {result.config.source}",
        source=result.config.source,
        source_type=result.config.source_type.value,
        total=result.success_count,
        errors=result.errors,
        elapsed=result.elapsed,
        items=items_data,
        result_id=result_id,
        generated_at=result.completed_at.isoformat() if result.completed_at else "",
    )
