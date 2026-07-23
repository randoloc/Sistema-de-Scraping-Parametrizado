"""Frontend Gradio para ScrapperGenérico.

Se monta sobre la app FastAPI existente para servir en HuggingFace Spaces.
Incluye búsqueda multi-adaptador, visualización de resultados y estado.
"""

from __future__ import annotations

import json
import logging
from urllib.parse import quote

import gradio as gr

from modulo_1_servicio.scraping.adapters.loader import AdapterLoader
from modulo_1_servicio.scraping.engine import Orchestrator
from modulo_1_servicio.scraping.extractors.beautifulsoup_extractor import (
    BeautifulSoupExtractor,
)
from modulo_1_servicio.scraping.models import FieldDefinition, FieldType, ScrapeConfig
from modulo_1_servicio.scraping.normalizer import ResultNormalizer

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singletons compartidos (mismos patron que routes_search.py)
# ---------------------------------------------------------------------------
_adapter_loader = AdapterLoader()
_adapter_loader.load_all()
_orchestrator = Orchestrator()
_orchestrator.register_engine("web_page", BeautifulSoupExtractor())
_normalizer = ResultNormalizer()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_verticals() -> list[str]:
    return sorted({a.vertical for a in _adapter_loader.get_all()})


def _get_adapter_names() -> list[str]:
    return sorted(a.name for a in _adapter_loader.get_all())


# ---------------------------------------------------------------------------
# Lógica de búsqueda (async para integrar con Orchestrator.run)
# ---------------------------------------------------------------------------
async def search_action(
    query: str,
    vertical: str,
    site: str,
    progress: gr.Progress = gr.Progress(),
) -> tuple[str, list[list], str]:
    """Ejecuta búsqueda multi-adaptador.

    Returns:
        (summary_markdown, table_data, raw_json)
    """
    if not query or not query.strip():
        return "⚠️ Ingresa un término de búsqueda.", [], "{}"
    if not vertical:
        return "⚠️ Selecciona una vertical.", [], "{}"

    query = query.strip()

    # --- Determinar adaptadores a usar ---
    if site and site != "all":
        adapter = _adapter_loader.get(site)
        matching = [adapter] if adapter else []
    else:
        matching = _adapter_loader.get_by_vertical(vertical)

    if not matching:
        msg = f"⚠️ No hay adaptadores para la vertical **'{vertical}'**."
        return msg, [], "{}"

    progress(0.0, desc="Iniciando búsqueda…")
    all_items: list[dict] = []
    total_rank = 0

    for idx, adapter in enumerate(matching):
        progress(
            (idx + 0.5) / len(matching),
            desc=f"Consultando {adapter.name}…",
        )
        try:
            # Construir URL de búsqueda
            search_url = adapter.search_url
            if "{query}" in search_url:
                search_url = search_url.replace("{query}", quote(query))
            if "{page}" in search_url:
                search_url = search_url.replace("{page}", "1")

            fields = tuple(
                FieldDefinition(
                    name=f.name,
                    selector=f.selector,
                    field_type=(
                        FieldType(f.type)
                        if f.type
                        in ("text", "price", "url", "number", "date", "image")
                        else FieldType.TEXT
                    ),
                )
                for f in adapter.fields
            )

            config = ScrapeConfig(
                source_type="web_page",
                source=search_url,
                fields=fields,
                container_selector=adapter.container_selector,
                rate_limit=1.0,
            )

            result = await _orchestrator.run(config)

            if not result.items:
                continue

            raw_items = [item.data for item in result.items]

            if adapter.canonical_map:
                canonical = _normalizer.normalize(
                    canonical_map=adapter.canonical_map,
                    raw_items=raw_items,
                    source_site=adapter.name,
                    source_url=search_url,
                    start_rank=total_rank,
                )
                for item in canonical:
                    all_items.append(
                        {
                            "rank": item.rank + 1,
                            "title": item.title or "(Sin título)",
                            "description": (item.description or "")[:150],
                            "price": (
                                f"${item.price:,.2f}"
                                if item.price is not None
                                else ""
                            ),
                            "site": item.source_site,
                            "url": item.url or "",
                        }
                    )
                total_rank += len(canonical)
            else:
                first_field = adapter.fields[0].name if adapter.fields else ""
                for j, raw in enumerate(raw_items):
                    all_items.append(
                        {
                            "rank": total_rank + j + 1,
                            "title": raw.get(first_field, "(Sin título)"),
                            "description": "",
                            "price": "",
                            "site": adapter.name,
                            "url": "",
                        }
                    )
                total_rank += len(raw_items)

        except Exception as exc:
            logger.error("Error en adaptador %s: %s", adapter.name, exc)

    progress(1.0, desc="Completado")

    if not all_items:
        return "😕 No se encontraron resultados.", [], "[]"

    table = [
        [it["rank"], it["title"], it["description"], it["price"], it["site"]]
        for it in all_items
    ]

    summary = (
        f"✅ **{len(all_items)} resultados** en "
        f"{len(matching)} adaptador(es) para **'{query}'**"
    )

    return summary, table, json.dumps(all_items, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Construcción de la UI Gradio
# ---------------------------------------------------------------------------
def build_app() -> gr.Blocks:
    """Construye y retorna la aplicación Gradio lista para montar."""
    verticals = _get_verticals()
    adapter_names = _get_adapter_names()

    css = """
    footer {display:none !important}
    .gradio-container {max-width: 1200px !important; margin: 0 auto !important}
    """

    with gr.Blocks(
        title="ScrapperGenérico",
    ) as demo:
        # Gradio 6.x: theme y css se setean después de crear el bloque
        demo.theme = gr.themes.Soft()
        demo.css = css
        # Header
        gr.HTML(
            """
            <div style="text-align:center;padding:24px 0 8px">
                <h1 style="margin:0;font-size:2rem">🕸️ ScrapperGenérico</h1>
                <p style="color:#64748b;margin:4px 0 0;font-size:1.1rem">
                    Buscador universal — productos, servicios y ofertas
                    en múltiples sitios simultáneamente
                </p>
            </div>
            """
        )

        with gr.Tabs():
            # =================================================================
            # TAB 1 — BÚSQUEDA
            # =================================================================
            with gr.Tab("🔍 Buscar"):
                with gr.Row(equal_height=True):
                    query_input = gr.Textbox(
                        label="¿Qué buscas?",
                        placeholder=(
                            "Ej: casa 3 habitaciones La Habana, "
                            "iPhone 15, zapatos talla 42…"
                        ),
                        scale=3,
                        container=True,
                    )
                    vertical_dropdown = gr.Dropdown(
                        label="Vertical",
                        choices=verticals,
                        value=verticals[0] if verticals else None,
                        scale=1,
                        interactive=True,
                    )

                with gr.Row(equal_height=True):
                    site_dropdown = gr.Dropdown(
                        label="Sitio (opcional — vacío = todos)",
                        choices=["all"] + adapter_names,
                        value="all",
                        scale=2,
                        interactive=True,
                    )
                    search_btn = gr.Button(
                        "🔍 Buscar", variant="primary", size="lg", scale=1
                    )

                summary_md = gr.Markdown(
                    value="",
                    label="Resumen",
                )

                results_table = gr.Dataframe(
                    headers=["#", "Título", "Descripción", "Precio", "Sitio"],
                    datatype=["number", "str", "str", "str", "str"],
                    column_count=(5, "fixed"),
                    label="Adaptadores Cargados",
                    wrap=True,
                )

                # Ajustar ancho de columnas para adaptadores
                gr.Markdown(
                    f"**Total:** {_adapter_loader.count} adaptadores  ·  "
                    f"**Verticales:** {', '.join(verticals)}"
                )

                # Recargar adaptadores (por si se agregaron nuevos YAML)
                if verticals:
                    gr.Markdown("---")
                    gr.Markdown(
                        "💡 *Agrega archivos ``.yaml`` en el directorio "
                        "``adapters/`` y reinicia el servidor.*"
                    )

            # =================================================================
            # TAB 3 — ESTADO / AYUDA
            # =================================================================
            with gr.Tab("⚙️ Estado"):
                gr.Markdown("## 🚦 Estado del Servicio")
                gr.Markdown(f"- **Adaptadores cargados:** {_adapter_loader.count}")
                gr.Markdown(
                    f"- **Verticales disponibles:** {', '.join(verticals)}"
                )
                gr.Markdown(
                    "- **API REST:** Visita "
                    "[`/api/docs`](/api/docs) para Swagger"
                )
                gr.Markdown(
                    "- **Health Check:** [`/api/health`](/api/health)"
                )
                gr.Markdown(
                    "- **Stack:** FastAPI + BeautifulSoup + Gradio "
                    "en HuggingFace Spaces"
                )

                gr.Markdown("---")
                gr.Markdown("## 📖 Cómo usar")
                gr.Markdown(
                    """
                    1. Escribe lo que buscas en el campo **¿Qué buscas?**
                    2. Selecciona la **Vertical** (categoría)
                    3. Opcional: elige un **Sitio** específico
                    4. Presiona **Buscar** o la tecla **Enter**
                    5. Los resultados aparecen en la tabla inferior

                    Los adaptadores definen qué sitios se buscan y cómo
                    se extraen los datos. Puedes crear nuevos adaptadores
                    agregando archivos YAML en ``adapters/``.
                    """
                )

    return demo
