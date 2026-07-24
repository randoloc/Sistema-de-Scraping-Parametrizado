"""Frontend Gradio para BuscadorGenérico — versión usuario final.

Interfaz limpia: escribe qué buscas, selecciona categoría,
y obtén resultados en tarjetas visuales con precio, fotos, contacto y más.
"""

from __future__ import annotations

import json
import logging
import os
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
# CSS moderno para las tarjetas
# ---------------------------------------------------------------------------
CARDS_CSS = """
<style>
/* ─── Grid de tarjetas ─── */
.cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 20px;
    padding: 8px 0;
}

/* ─── Tarjeta individual ─── */
.result-card {
    background: #ffffff;
    border-radius: 16px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    border: 1px solid #eef2f6;
    display: flex;
    flex-direction: column;
}
.result-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.12);
}

/* ─── Imagen ─── */
.card-image {
    width: 100%;
    height: 200px;
    object-fit: cover;
    background: #f1f5f9;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #94a3b8;
    font-size: 3rem;
}
.card-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

/* ─── Contenido ─── */
.card-body {
    padding: 18px 20px 20px;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.card-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #0f172a;
    line-height: 1.3;
    margin: 0;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.card-price {
    font-size: 1.5rem;
    font-weight: 800;
    color: #059669;
    margin: 2px 0;
}
.card-price.free {
    color: #6366f1;
}

.card-description {
    font-size: 0.9rem;
    color: #475569;
    line-height: 1.5;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    margin: 0;
}

/* ─── Detalles ─── */
.card-details {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-top: 4px;
}
.card-detail {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.85rem;
    color: #64748b;
}
.card-detail .label {
    font-weight: 600;
    color: #475569;
    min-width: 70px;
}
.card-detail .value {
    color: #334155;
}

/* Badges */
.card-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}
.badge-site {
    background: #ede9fe;
    color: #6d28d9;
}
.badge-warranty {
    background: #dcfce7;
    color: #15803d;
}
.badge-urgent {
    background: #fee2e2;
    color: #dc2626;
}

/* ─── Footer de la tarjeta ─── */
.card-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 20px;
    background: #f8fafc;
    border-top: 1px solid #eef2f6;
    gap: 8px;
    flex-wrap: wrap;
}

.card-site {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 0.8rem;
    color: #94a3b8;
}
.card-site strong {
    color: #475569;
}

.card-link {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 18px;
    background: #2563eb;
    color: white;
    text-decoration: none;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 600;
    transition: background 0.2s;
}
.card-link:hover {
    background: #1d4ed8;
}

/* ─── Estados ─── */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #94a3b8;
}
.empty-state .icon {
    font-size: 4rem;
    margin-bottom: 16px;
}
.empty-state h3 {
    font-size: 1.3rem;
    color: #64748b;
    margin: 0 0 8px;
}
.empty-state p {
    font-size: 0.95rem;
    margin: 0;
}
</style>
"""


# ---------------------------------------------------------------------------
# Lógica de búsqueda
# ---------------------------------------------------------------------------
async def search_action(
    query: str,
    category: str,
    progress: gr.Progress = gr.Progress(),
) -> tuple[str, str, str]:
    """Busca en todos los sitios de una categoría.

    Returns:
        (summary_markdown, cards_html, raw_json)
    """
    if not query or not query.strip():
        return "⚠️ Escribe algo para buscar.", "", "{}"
    if not category or category == "Todas":
        return "⚠️ Selecciona una categoría.", "", "{}"

    query = query.strip()

    # ─── Modo demo ───
    if os.environ.get("DEMO_MODE") == "1":
        return _generate_demo_results(query, category)

    # Buscar adaptadores por categoría
    matching = _adapter_loader.get_by_vertical(category)

    if not matching:
        msg = f"⚠️ No hay sitios disponibles en la categoría **'{category}'**."
        return msg, "", "{}"

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
                        _build_item(
                            rank=item.rank + 1,
                            title=item.title or "(Sin título)",
                            description=(item.description or "")[:300],
                            price=item.price,
                            site=item.source_site,
                            url=item.url or "",
                        )
                    )
                total_rank += len(canonical)
            else:
                first_field = adapter.fields[0].name if adapter.fields else ""
                for j, raw in enumerate(raw_items):
                    all_items.append(
                        _build_item(
                            rank=total_rank + j + 1,
                            title=raw.get(first_field, "(Sin título)"),
                            description="",
                            price=None,
                            site=adapter.name,
                            url="",
                        )
                    )
                total_rank += len(raw_items)

        except Exception as exc:
            logger.error("Error en %s: %s", adapter.name, exc)

    progress(1.0, desc="Listo")

    # ─── Fallback a demo ───
    if not all_items:
        demo = _generate_demo_results(query, category)
        if demo:
            return demo
        return (
            f"😕 No se encontraron resultados para **'{query}'** en **{category}**.",
            _empty_state_html("Sin resultados", "Intenta con otros términos o categoría."),
            "[]",
        )

    summary = (
        f"✅ **{len(all_items)} resultados** "
        f"en {len(matching)} sitio(s) para **'{query}'**"
    )

    cards = _render_cards(all_items)
    return summary, cards, json.dumps(all_items, indent=2, ensure_ascii=False)


def _build_item(
    rank: int,
    title: str,
    description: str,
    price: float | None,
    site: str,
    url: str,
    **kwargs,
) -> dict:
    """Construye un item con campos enriquecidos."""
    return {
        "rank": rank,
        "title": title,
        "description": description,
        "price": f"${price:,.2f}" if price is not None else "",
        "price_raw": price,
        "site": site,
        "url": url,
        # Campos enriquecidos (desde adaptadores o demo)
        "image": kwargs.get("image", ""),
        "contact": kwargs.get("contact", ""),
        "address": kwargs.get("address", ""),
        "warranty": kwargs.get("warranty", ""),
        "phone": kwargs.get("phone", ""),
        "email": kwargs.get("email", ""),
        "condition": kwargs.get("condition", ""),  # nuevo/usado
        "badges": kwargs.get("badges", []),
    }


# ---------------------------------------------------------------------------
# Renderizador de tarjetas HTML
# ---------------------------------------------------------------------------
def _render_cards(items: list[dict]) -> str:
    """Convierte una lista de items en HTML de tarjetas."""
    if not items:
        return _empty_state_html("Sin resultados", "No hay resultados para mostrar.")

    cards_html = "\n".join(_render_single_card(it) for it in items)

    return f"""{CARDS_CSS}
<div class="cards-grid">
{cards_html}
</div>"""


def _render_single_card(item: dict) -> str:
    """Renderiza una tarjeta HTML para un item."""
    # ── Imagen ──
    img_html = ""
    if item.get("image"):
        img_html = f'<img src="{item["image"]}" alt="{item["title"]}" />'
    else:
        img_html = '<div class="card-image">📷</div>'

    # ── Precio ──
    price_html = ""
    if item.get("price"):
        price_html = f'<div class="card-price">{item["price"]}</div>'
    else:
        price_html = '<div class="card-price free">💰 Consultar</div>'

    # ── Badges ──
    badges_html = ""
    badges = item.get("badges", [])
    if badges:
        badge_items = "".join(
            f'<span class="card-badge badge-{b.get("type","site")}">{b.get("icon","")} {b.get("label","")}</span>'
            for b in badges
        )
        badges_html = f'<div style="display:flex;gap:6px;flex-wrap:wrap">{badge_items}</div>'

    # ── Detalles dinámicos ──
    details = []
    detail_fields = [
        ("📍 Ubicación", "address"),
        ("📞 Contacto", "contact"),
        ("📱 Teléfono", "phone"),
        ("✉️ Email", "email"),
        ("🏷️ Estado", "condition"),
        ("🛡️ Garantía", "warranty"),
    ]
    for label, field in detail_fields:
        val = item.get(field, "").strip()
        if val:
            details.append(
                f'<div class="card-detail">'
                f'<span class="label">{label}:</span>'
                f'<span class="value">{val}</span>'
                f'</div>'
            )

    details_html = ""
    if details:
        details_html = f'<div class="card-details">{"".join(details)}</div>'

    # ── Descripción ──
    desc_html = ""
    if item.get("description"):
        desc_html = f'<p class="card-description">{item["description"]}</p>'

    # ── Enlace ──
    link_html = ""
    if item.get("url"):
        link_html = (
            f'<a class="card-link" href="{item["url"]}" '
            f'target="_blank" rel="noopener">🔗 Ver oferta</a>'
        )
    else:
        link_html = (
            f'<span class="card-link" style="background:#94a3b8;cursor:default">'
            f'🔗 No disponible</span>'
        )

    # ── Sitio ──
    site = item.get("site", "?")
    site_icons = {"revolico": "🏪", "porlalivre": "📦", "demo_local": "🧪"}

    return f"""
<div class="result-card">
    <div class="card-image">{img_html}</div>
    <div class="card-body">
        {badges_html}
        <h3 class="card-title">{item["title"]}</h3>
        {price_html}
        {desc_html}
        {details_html}
    </div>
    <div class="card-footer">
        <span class="card-site">
            {site_icons.get(site, "🌐")} <strong>{site}</strong>
        </span>
        {link_html}
    </div>
</div>"""


def _empty_state_html(title: str, message: str) -> str:
    """HTML para estado vacío."""
    return f"""{CARDS_CSS}
<div class="empty-state">
    <div class="icon">🔍</div>
    <h3>{title}</h3>
    <p>{message}</p>
</div>"""


# ---------------------------------------------------------------------------
# Datos de demostración
# ---------------------------------------------------------------------------
def _generate_demo_results(query: str, category: str) -> tuple:
    """Genera resultados simulados con datos enriquecidos."""
    q = query.title()
    items = [
        _build_item(
            rank=1,
            title=f"{q} — 3 hab., recién remodelado",
            description=f"Se vende {query} en excelente estado. Consta de sala-comedor, cocina, 3 habitaciones, baño, patio y terraza. Piso baldosa, techos altos, carpintería de aluminio. Acepto financiamiento.",
            price=25000.00,
            site="revolico",
            url="https://www.revolico.cu/search/all/" + quote(query),
            contact="Carlos Pérez",
            phone="+53 5 1234567",
            email="carlos@email.com",
            address="Calle 23 #456, Vedado, La Habana",
            warranty="Escritura pública garantizada",
            condition="Excelente",
            badges=[
                {"type": "urgent", "icon": "🔥", "label": "Oferta"},
                {"type": "site", "icon": "✅", "label": "Verificado"},
            ],
        ),
        _build_item(
            rank=2,
            title=f"{q} — Oportunidad única",
            description=f"{q} completamente amueblado. Listo para entrar a vivir. Cocina equipada, closet empotrados, rejas y aires acondicionados. Precio negociable.",
            price=18000.00,
            site="revolico",
            url="https://www.revolico.cu/search/all/" + quote(query),
            contact="María García",
            phone="+53 7 7654321",
            address="Miramar, La Habana",
            condition="Seminuevo",
            badges=[
                {"type": "warranty", "icon": "🛡️", "label": "Con garantía"},
            ],
        ),
        _build_item(
            rank=3,
            title=f"{q} en Vedado — Venta directa",
            description=f"Venta directa de {query} en Vedado. 2 plantas, 4 cuartos, 2 baños, garage, patio interior. Agua 24h, electricidad estable. Ideal para inversión.",
            price=32000.00,
            site="porlalivre",
            url="https://www.porlalivre.com/search/" + quote(query),
            contact="Antonio Rodríguez",
            phone="+53 5 9988776",
            email="antonio.r@email.com",
            address="Calle Línea esq. A, Vedado, La Habana",
            warranty="Libre de gravamen",
            condition="Impecable",
            badges=[
                {"type": "site", "icon": "⭐", "label": "Destacado"},
            ],
        ),
        _build_item(
            rank=4,
            title=f"{q} económico — Urgente",
            description=f"Vendo {query} por cambio de ciudad. Precio rebajado. Acepto pesos CUP y USD. Trato directo sin intermediarios. Llama ahora!",
            price=9500.00,
            site="porlalivre",
            url="https://www.porlalivre.com/search/" + quote(query),
            contact="Laura Martínez",
            phone="+53 5 5544332",
            address="Centro Habana",
            condition="Bueno",
            badges=[
                {"type": "urgent", "icon": "🔥", "label": "Precio rebajado"},
                {"type": "warranty", "icon": "🤝", "label": "Trato directo"},
            ],
        ),
        _build_item(
            rank=5,
            title=f"{q} de lujo — Casa moderna",
            description=f"Moderna {query} en reparto residencial. 3 habitaciones con baño en suite, cocina integral, piscina, jardín, cisterna, planta eléctrica. La mejor oportunidad!",
            price=55000.00,
            site="revolico",
            url="https://www.revolico.cu/search/all/" + quote(query),
            contact="Inmobiliaria Díaz",
            phone="+53 7 2045678",
            email="ventas@inmobiliariadiaz.cu",
            address="Siboney, Playa, La Habana",
            warranty="1 año de garantía estructural",
            condition="Nuevo",
            badges=[
                {"type": "warranty", "icon": "🛡️", "label": "Garantía 1 año"},
                {"type": "site", "icon": "💎", "label": "Premium"},
            ],
        ),
    ]

    cards = _render_cards(items)
    summary = (
        f"✅ **{len(items)} resultados** para "
        f"**'{query}'** en **{category}** "
        f"<span style='color:#94a3b8;font-size:0.85rem'>"
        f"— modo demostración</span>"
    )

    return summary, cards, json.dumps(items, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
def build_app() -> gr.Blocks:
    """Construye la interfaz de usuario con tarjetas modernas."""
    verticals = _get_verticals()

    css = """
    footer {display:none !important}
    .gradio-container {max-width: 1100px !important; margin: 0 auto !important}
    .gr-box {border: none !important; box-shadow: none !important}
    """

    with gr.Blocks(
        title="BuscadorGenérico",
        theme=gr.themes.Soft(),
        css=css,
    ) as demo:
        # ─── Encabezado ──────────────────────────────────────
        gr.HTML(
            f"""
            <div style="text-align:center;padding:24px 0 12px">
                <h1 style="margin:0;font-size:2rem;font-weight:800;
                           background:linear-gradient(135deg,#2563eb,#7c3aed);
                           -webkit-background-clip:text;-webkit-text-fill-color:transparent">
                    🔍 BuscadorGenérico
                </h1>
                <p style="color:#64748b;margin:6px 0 0;font-size:1.05rem">
                    Encuentra lo que buscas en múltiples sitios a la vez
                </p>
                <div style="margin-top:8px;display:flex;justify-content:center;gap:16px;
                            font-size:0.85rem;color:#94a3b8">
                    <span>🏪 {_adapter_loader.count} sitios</span>
                    <span>📂 {len(verticals)} categorías</span>
                </div>
            </div>
            """
        )

        # ─── Pestañas ────────────────────────────────────────
        with gr.Tabs():
            # ═══════════════════════════════════════════════════
            # PESTAÑA 1: BUSCAR
            # ═══════════════════════════════════════════════════
            with gr.Tab("🔍 Buscar"):
                # --- Barra de búsqueda ---
                with gr.Row(equal_height=True):
                    query_input = gr.Textbox(
                        label="",
                        placeholder="¿Qué quieres buscar?  Ej: casa, laptop, zapatos...",
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

                cards_output = gr.HTML(
                    value="",
                    label="Resultados",
                )

                raw_json = gr.JSON(
                    label="Datos completos",
                    visible=False,
                )

                # --- Conexión del botón ---
                search_btn.click(
                    fn=search_action,
                    inputs=[query_input, category_dropdown],
                    outputs=[summary_md, cards_output, raw_json],
                )

                query_input.submit(
                    fn=search_action,
                    inputs=[query_input, category_dropdown],
                    outputs=[summary_md, cards_output, raw_json],
                )

                # --- Sitios disponibles (plegable) ---
                with gr.Accordion("📡 Sitios disponibles", open=False):
                    adapter_rows = []
                    for a in _adapter_loader.get_all():
                        adapter_rows.append([a.name, a.vertical, len(a.fields)])
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
                gr.HTML(
                    """
                    <div style="max-width:700px;margin:0 auto;padding:20px 0">
                        <h2>📖 ¿Cómo usar este buscador?</h2>

                        <div style="display:flex;gap:20px;margin:24px 0;flex-wrap:wrap">
                            <div style="flex:1;min-width:160px;padding:20px;
                                        background:#f8fafc;border-radius:12px;text-align:center">
                                <div style="font-size:2rem">✏️</div>
                                <h3 style="margin:8px 0 4px;font-size:1rem">1. Escribe</h3>
                                <p style="margin:0;font-size:0.85rem;color:#64748b">
                                    Lo que quieres buscar. Sé específico.</p>
                            </div>
                            <div style="flex:1;min-width:160px;padding:20px;
                                        background:#f8fafc;border-radius:12px;text-align:center">
                                <div style="font-size:2rem">📂</div>
                                <h3 style="margin:8px 0 4px;font-size:1rem">2. Categoría</h3>
                                <p style="margin:0;font-size:0.85rem;color:#64748b">
                                    Selecciona dónde buscar.</p>
                            </div>
                            <div style="flex:1;min-width:160px;padding:20px;
                                        background:#f8fafc;border-radius:12px;text-align:center">
                                <div style="font-size:2rem">🔍</div>
                                <h3 style="margin:8px 0 4px;font-size:1rem">3. Buscar</h3>
                                <p style="margin:0;font-size:0.85rem;color:#64748b">
                                    Presiona y obtén resultados.</p>
                            </div>
                        </div>

                        <h3>❓ Preguntas frecuentes</h3>

                        <div style="background:#f8fafc;border-radius:12px;padding:16px 20px;margin:12px 0">
                            <p><strong>🔹 ¿Qué sitios busca?</strong><br>
                            Todos los sitios disponibles en la categoría que elijas.</p>
                        </div>
                        <div style="background:#f8fafc;border-radius:12px;padding:16px 20px;margin:12px 0">
                            <p><strong>🔹 ¿Por qué no aparecen resultados?</strong><br>
                            El sitio puede no estar accesible en este momento, o no hay
                            resultados para tu búsqueda. Intenta con otros términos.</p>
                        </div>
                        <div style="background:#f8fafc;border-radius:12px;padding:16px 20px;margin:12px 0">
                            <p><strong>🔹 ¿Los precios son actualizados?</strong><br>
                            Los resultados se obtienen en tiempo real desde los sitios
                            de clasificados.</p>
                        </div>
                        <div style="background:#f8fafc;border-radius:12px;padding:16px 20px;margin:12px 0">
                            <p><strong>🔹 ¿Cómo agrego más sitios?</strong><br>
                            Contacta al administrador del sistema.</p>
                        </div>
                    </div>
                    """
                )

    return demo


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_verticals() -> list[str]:
    return sorted({a.vertical for a in _adapter_loader.get_all()})
