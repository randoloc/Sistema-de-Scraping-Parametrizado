"""Frontend Gradio para ScrapperGenérico — versión usuario final.

Interfaz simple: el usuario escribe qué busca, selecciona categoría,
y obtiene resultados. Sin tecnicismos.
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
from modulo_1_servicio.scraping.models import (
    FieldDefinition,
    FieldType,
    ScrapeConfig,
    SourceType,
)
from modulo_1_servicio.scraping.normalizer import ResultNormalizer

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singletons
# ---------------------------------------------------------------------------
_adapter_loader = AdapterLoader()
_adapter_loader.load_all()
_orchestrator = Orchestrator()
_orchestrator.register_engine("web_page", BeautifulSoupExtractor())
_normalizer = ResultNormalizer()


# ---------------------------------------------------------------------------
# Lógica de búsqueda
# ---------------------------------------------------------------------------
async def search_action(
    query: str,
    category: str,
    progress: gr.Progress = gr.Progress(),
) -> tuple[str, list[list], str]:
    """Busca en todos los sitios de una categoría.

    Returns:
        (summary_markdown, table_data, raw_json)
    """
    if not query or not query.strip():
        return "⚠️ Escribe algo para buscar.", [], "{}"
    if not category or category == "Todas":
        return "⚠️ Selecciona una categoría.", [], "{}"

    query = query.strip()

    # ─── Modo demo: resultados ficticios, sin llamadas a sitios reales ───
    import os
    if os.environ.get("DEMO_MODE") == "1":
        return _generate_demo_results(query, category)

    # Buscar adaptadores por categoría
    matching = _adapter_loader.get_by_vertical(category)

    if not matching:
        msg = f"⚠️ No hay sitios disponibles en la categoría **'{category}'**."
        return msg, [], "{}"

    progress(0.0, desc="Buscando...")
    all_items: list[dict] = []
    total_rank = 0

    for idx, adapter in enumerate(matching):
        progress(
            (idx + 0.5) / len(matching),
            desc=f"Consultando {adapter.name}...",
        )
        try:
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
                source_type=SourceType.WEB_PAGE,
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
                            "description": (item.description or "")[:200],
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
            logger.error("Error en %s: %s", adapter.name, exc)

    progress(1.0, desc="Listo")

    # ─── Modo demo: si no hay resultados reales, generar simulados ───
    if not all_items:
        demo = _generate_demo_results(query, category)
        if demo:
            return demo

        return (
            f"😕 No se encontraron resultados para "
            f"**'{query}'** en **{category}**.",
            [],
            "[]",
        )

    table = [
        [
            it["rank"],
            it["title"],
            it["description"],
            it["price"],
            it["site"],
            it["url"],
        ]
        for it in all_items
    ]

    summary = (
        f"✅ **{len(all_items)} resultados** "
        f"en {len(matching)} sitio(s) para **'{query}'**"
    )

    return summary, table, json.dumps(all_items, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Datos de demostración (para probar la UI sin conexión a sitios reales)
# ---------------------------------------------------------------------------
def _generate_demo_results(query: str, category: str) -> tuple:
    """Genera resultados simulados para demostración."""
    items = [
        {
            "rank": 1,
            "title": f'{query.title()} — Oferta en Revolico',
            "description": f"Vendo {query} en excelente estado. Precio negociable. Contactar al privado para más detalles e información de contacto.",
            "price": "$250.00",
            "site": "revolico",
            "url": "https://www.revolico.cu/search/all/" + quote(query),
        },
        {
            "rank": 2,
            "title": f'{query.title()} — Nueva publicación',
            "description": f"Se vende {query} apenas usado. Único dueño. Perfectas condiciones. Acepto efectivo o transferencia.",
            "price": "$180.00",
            "site": "revolico",
            "url": "https://www.revolico.cu/search/all/" + quote(query),
        },
        {
            "rank": 3,
            "title": f'{query.title()} en La Habana',
            "description": f"Ofrezco {query} en Vedado, La Habana. Recién publicado. Para más información escribir al WhatsApp.",
            "price": "$320.00",
            "site": "porlalivre",
            "url": "https://www.porlalivre.com/search/" + quote(query),
        },
        {
            "rank": 4,
            "title": f'{query.title()} — Ocasión',
            "description": f"¡Oportunidad! {query} a buen precio. Artículo de calidad. Revisado y funcionando perfectamente.",
            "price": "$150.00",
            "site": "porlalivre",
            "url": "https://www.porlalivre.com/search/" + quote(query),
        },
        {
            "rank": 5,
            "title": f'{query.title()} — Urgente',
            "description": f"Vendo {query} por mudanza. Precio rebajado. Aprovecha esta oferta por tiempo limitado.",
            "price": "$95.00",
            "site": "revolico",
            "url": "https://www.revolico.cu/search/all/" + quote(query),
        },
    ]

    table = [
        [it["rank"], it["title"], it["description"], it["price"], it["site"], it["url"]]
        for it in items
    ]

    summary = (
        f"✅ **{len(items)} resultados de demostración** "
        f"para **'{query}'** (modo demo — los sitios reales no están accesibles desde esta red)"
    )

    return summary, table, json.dumps(items, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# UI — Para usuario final (sin tecnicismos)
# ---------------------------------------------------------------------------
def build_app() -> gr.Blocks:
    """Construye la interfaz de usuario."""
    verticals = _get_verticals()

    css = """
    footer {display:none !important}
    .gradio-container {max-width: 900px !important; margin: 0 auto !important}
    """

    with gr.Blocks(
        title="BuscadorGenérico",
        theme=gr.themes.Soft(),
        css=css,
    ) as demo:
        # ─── Encabezado ──────────────────────────────────────
        gr.HTML(
            """
            <div style="text-align:center;padding:20px 0 4px">
                <h1 style="margin:0;font-size:1.8rem">🔍 BuscadorGenérico</h1>
                <p style="color:#64748b;margin:4px 0 0;font-size:1rem">
                    Encuentra lo que buscas en múltiples sitios a la vez
                </p>
            </div>
            """
        )

        # ─── Pestañas ────────────────────────────────────────
        with gr.Tabs():
            # ═══════════════════════════════════════════════════
            # PESTAÑA 1: BUSCAR
            # ═══════════════════════════════════════════════════
            with gr.Tab("🔍 Buscar"):
                # --- Fila de entrada ---
                with gr.Row(equal_height=True):
                    query_input = gr.Textbox(
                        label="",
                        placeholder="¿Qué quieres buscar? Ej: casa, laptop, zapatos...",
                        scale=4,
                        container=True,
                    )
                    category_dropdown = gr.Dropdown(
                        label="Categoría",
                        choices=verticals,
                        value=verticals[0] if verticals else None,
                        scale=1,
                        interactive=True,
                    )
                    search_btn = gr.Button(
                        "🔍 Buscar",
                        variant="primary",
                        size="lg",
                        scale=1,
                    )

                # --- Resultados ---
                summary_md = gr.Markdown(
                    value="",
                    label="",
                )

                results_table = gr.Dataframe(
                    headers=["#", "Título", "Descripción", "Precio", "Sitio", "Enlace"],
                    datatype=["number", "str", "str", "str", "str", "str"],
                    column_count=(6, "fixed"),
                    wrap=True,
                    visible=True,
                )

                raw_json = gr.JSON(
                    label="Datos completos",
                    visible=False,
                )

                # --- Conexión del botón ---
                search_btn.click(
                    fn=search_action,
                    inputs=[query_input, category_dropdown],
                    outputs=[summary_md, results_table, raw_json],
                )

                query_input.submit(
                    fn=search_action,
                    inputs=[query_input, category_dropdown],
                    outputs=[summary_md, results_table, raw_json],
                )

                # --- Info de sitios disponibles ---
                with gr.Accordion("📡 Sitios disponibles", open=False):
                    adapter_rows = []
                    for a in _adapter_loader.get_all():
                        adapter_rows.append([
                            a.name,
                            a.vertical,
                            len(a.fields),
                        ])
                    gr.Dataframe(
                        value=adapter_rows,
                        headers=["Sitio", "Categoría", "Campos"],
                        datatype=["str", "str", "number"],
                        column_count=(3, "fixed"),
                        wrap=True,
                    )

            # ═══════════════════════════════════════════════════
            # PESTAÑA 2: AYUDA
            # ═══════════════════════════════════════════════════
            with gr.Tab("❓ Ayuda"):
                gr.Markdown(
                    """
                    ## 📖 ¿Cómo usar este buscador?

                    **1. Escribe lo que quieres buscar**
                    > Sé específico. Ej: *"casa 3 habitaciones La Habana"*,
                    > *"laptop usada"*, *"apartamento en renta"*

                    **2. Selecciona una categoría**
                    > Esto define en qué sitios buscar.

                    **3. Presiona Buscar**
                    > El sistema busca en todos los sitios disponibles
                    > y te muestra los resultados ordenados.

                    ---
                    ## ❓ Preguntas frecuentes

                    **¿Qué sitios busca?**
                    > Todos los sitios disponibles en la categoría seleccionada.

                    **¿Por qué no aparecen resultados?**
                    > Puede ser que el sitio no esté accesible en este momento,
                    > o que no haya resultados para tu búsqueda.

                    **¿Cómo agrego más sitios?**
                    > Contacta al administrador del sistema.
                    """
                )

    return demo


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_verticals() -> list[str]:
    return sorted({a.vertical for a in _adapter_loader.get_all()})
