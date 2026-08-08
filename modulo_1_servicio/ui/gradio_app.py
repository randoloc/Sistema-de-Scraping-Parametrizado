"""Frontend Gradio para NovaSearch — buscador multi-site de clasificados cubanos.

Interfaz elegante: escribe qué buscas, selecciona categoría,
y obtén resultados en tarjetas visuales con precio, fotos, contacto y más.
"""

from __future__ import annotations

import importlib
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

# ---------------------------------------------------------------------------
# CSS moderno para las tarjetas
# ---------------------------------------------------------------------------
CARDS_CSS = """
<style>
/* ─── Paleta NovaSearch ───
 *  Fondo:     #f5f3ef (cáscara de huevo)
 *  Primary:   #1e3a5f (navy)
 *  Accent:    #b45309 (ámbar)
 *  Teal:      #0f766e (teal oscuro para precios — AA 4.5:1)
 *  Cards:     #ffffff
 *  Text:      #1e293b
 *  Muted:     #334155
 *  Hairstyle: #e2ddd4 (bordes)
 *  Todos los textos sobre blanco ≥ 4.5:1 (WCAG AA).
 * ────────────────────────────────── */

/* ─── Grid de tarjetas ─── */
.cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
    gap: 24px;
    padding: 8px 0;
}

/* ─── Tarjeta individual ─── */
.result-card {
    position: relative;
    background: #ffffff;
    border-radius: 16px;
    box-shadow: 0 1px 3px rgba(30,58,95,0.08), 0 2px 6px rgba(30,58,95,0.05);
    overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    border: 1px solid #e2ddd4;
    display: flex;
    flex-direction: column;
}
/* Barra de acento superior (navy → ámbar → teal) */
.result-card::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #1e3a5f 0%, #b45309 55%, #0f766e 100%);
    z-index: 1;
}
.result-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 35px rgba(30,58,95,0.12), 0 4px 8px rgba(30,58,95,0.05);
}

/* ─── Imagen ─── */
.card-image {
    width: 100%;
    height: 200px;
    object-fit: cover;
    background: #f0ede8;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #78716c;
    font-size: 3rem;
    border-bottom: 1px solid #ebe6de;
}
.card-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

/* ─── Contenido ─── */
.card-body {
    padding: 18px 20px 16px;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 10px;
}

/* Título — punto focal de la tarjeta (navy de marca) */
.card-title {
    font-size: 1.2rem;
    font-weight: 700;
    color: #1e3a5f;
    line-height: 1.4;
    margin: 0;
    letter-spacing: -0.01em;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

/* Precio — acento secundario distinguible */
.card-price {
    font-size: 1.6rem;
    font-weight: 800;
    color: #0f766e;
    margin: 4px 0 2px;
    letter-spacing: -0.02em;
}
.card-price.free {
    color: #52525b;
    font-weight: 600;
}

.card-description {
    font-size: 0.9rem;
    color: #334155;
    line-height: 1.6;
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
    margin-top: 8px;
    padding-top: 12px;
    border-top: 1px solid #e2ddd4;
}
.card-detail {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.85rem;
    color: #44403c;
    line-height: 1.5;
}
.card-detail .label {
    font-weight: 600;
    color: #292524;
    min-width: 72px;
    flex-shrink: 0;
}
.card-detail .value {
    color: #1c1917;
}
.card-detail a {
    color: #1e3a5f;
    text-decoration: none;
    font-weight: 600;
}
.card-detail a:hover {
    text-decoration: underline;
}

/* Badges */
.card-badges {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    margin-bottom: 2px;
}
.card-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    line-height: 1.3;
    border: 1px solid;
}
.badge-site {
    background: #f0e9d8;
    border-color: #d8c9a3;
    color: #6b4f1d;
}
.badge-warranty {
    background: #e0f2f1;
    border-color: #9cd8d4;
    color: #0f766e;
}
.badge-urgent {
    background: #fde8e8;
    border-color: #f5b8b8;
    color: #a01b1b;
}

/* ─── Footer de la tarjeta ─── */
.card-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    background: #fbfaf8;
    border-top: 1px solid #e2ddd4;
    gap: 8px;
    flex-wrap: wrap;
}

.card-site {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 0.8rem;
    color: #57534e;
    font-weight: 500;
}
.card-site strong {
    color: #292524;
    font-weight: 600;
}

.card-footer-actions {
    display: flex;
    gap: 8px;
    align-items: center;
}

.card-link {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 18px;
    background: #1e3a5f;
    color: #ffffff;
    text-decoration: none;
    border-radius: 8px;
    font-size: 0.85rem;
    font-weight: 600;
    transition: background 0.2s;
}
.card-link:hover {
    background: #2c5282;
}

/* Botón Contactar (estilo secundario) */
.contact-btn {
    background: #ffffff;
    color: #1e3a5f;
    border: 1.5px solid #d4cfc7;
}
.contact-btn:hover {
    background: #f5f3ef;
    color: #1e3a5f;
    border-color: #1e3a5f;
}

/* ─── Estados ─── */
.empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #57534e;
}
.empty-state .icon {
    font-size: 4rem;
    margin-bottom: 16px;
}
.empty-state h3 {
    font-size: 1.3rem;
    color: #1e3a5f;
    margin: 0 0 8px;
}
.empty-state p {
    font-size: 0.95rem;
    color: #57534e;
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

    # ─── Modo demo EXPLÍCITO (solo si DEMO_MODE está activo en el entorno) ───
    # Por defecto NO está activo. Se usa únicamente para desarrollo sin internet.
    if os.environ.get("DEMO_MODE") == "1":
        return _generate_demo_results(query, category)

    # Buscar adaptadores por categoría
    matching = _adapter_loader.get_by_vertical(category)

    if not matching:
        msg = f"⚠️ No hay sitios disponibles en la categoría **'{category}'**."
        return msg, "", "{}"

    progress(0.0, desc="Buscando...")
    all_items: list[dict] = []
    site_errors: list[str] = []
    total_rank = 0

    for idx, adapter in enumerate(matching):
        progress(
            (idx + 0.5) / len(matching),
            desc=f"Consultando {adapter.name}...",
        )
        try:
            # ── RUTA: Adaptador Python custom (ej: Revolico Next.js) ──
            if adapter.python_adapter:
                cls = _get_python_adapter_class(adapter.python_adapter)
                instance = cls()
                try:
                    canonical_items = await instance.search(query, page=1)
                finally:
                    await instance.close()

                for item in canonical_items:
                    all_items.append(
                        _build_item(
                            rank=total_rank + 1,
                            title=item.title or "(Sin título)",
                            description=(item.description or "")[:300],
                            price=item.price,
                            site=item.source_site,
                            url=item.url or "",
                            image=item.image_url or "",
                            address=item.location or "",
                        )
                    )
                total_rank += len(canonical_items)
                continue

            # ── RUTA: YAML estándar (BS4 + selectores) ──
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
                    required=f.required,
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
            site_errors.append(f"❌ **{adapter.name}**: {exc}")

    progress(1.0, desc="Listo")

    # ─── Sin fallback a demo: se reporta el resultado REAL y los errores ───
    if not all_items:
        errors_section = ""
        if site_errors:
            errors_section = "\n\n### Detalles por sitio\n" + "\n".join(site_errors)
        msg = (
            f"😕 No se obtuvieron resultados para **'{query}'** en **{category}**. "
            f"Los sitios no respondieron o están bloqueando el acceso."
            f"{errors_section}"
        )
        return (
            msg,
            _empty_state_html(
                "Sin resultados",
                "Los sitios no devolvoun datos en este momento. "
                "Puede ser bloqueo anti-bot o falta de resultados reales.",
            ),
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
        badges_html = f'<div class="card-badges">{badge_items}</div>'

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

    # ── Enlace "Ver oferta" ──
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

    # ── Botón "Contactar" ──
    contact_html = ""
    phone = item.get("phone", "").strip()
    email = item.get("email", "").strip()
    if phone:
        # Limpiar el teléfono para el enlace tel:
        clean_phone = phone.replace(" ", "").replace("-", "")
        contact_html = (
            f'<a class="card-link contact-btn" href="tel:{clean_phone}" '
            f'title="Llamar al {phone}">📞 Contactar</a>'
        )
    elif email:
        contact_html = (
            f'<a class="card-link contact-btn" href="mailto:{email}" '
            f'title="Enviar email a {email}">✉️ Contactar</a>'
        )
    else:
        contact_html = (
            f'<span class="card-link contact-btn" style="background:#cbd5e1;cursor:default;opacity:0.6">'
            f'📞 Contactar</span>'
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
        <div class="card-footer-actions">
            {contact_html}
            {link_html}
        </div>
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
    body {background: #f5f3ef !important}
    .gradio-container {background: #f5f3ef !important}
    /* Primary button → navy */
    button.gr-button-primary {background: #1e3a5f !important; border-color: #1e3a5f !important}
    button.gr-button-primary:hover {background: #2c5282 !important; border-color: #2c5282 !important}
    /* Tabs accent */
    .gr-tabs .tab-nav button.selected {border-bottom-color: #1e3a5f !important; color: #1e3a5f !important}
    /* Inputs subtle border */
    input, textarea, select {border-color: #d4cfc7 !important}
    input:focus, textarea:focus {border-color: #1e3a5f !important; box-shadow: 0 0 0 2px rgba(30,58,95,0.15) !important}
    .gr-dropdown {border-color: #d4cfc7 !important}
    .gr-dropdown:focus {border-color: #1e3a5f !important}
    """

    demo = gr.Blocks(title="NovaSearch")
    demo.css = css
    demo.theme = gr.themes.Soft()
    with demo:
        # ─── Encabezado ──────────────────────────────────────
        gr.HTML(
            f"""
            <div style="text-align:center;padding:28px 0 16px;
                        background:linear-gradient(180deg,#1e3a5f 0%,#152d4a 100%);
                        border-radius:20px;margin-bottom:24px;
                        box-shadow:0 4px 20px rgba(30,58,95,0.15)">
                <div style="display:flex;align-items:center;justify-content:center;gap:12px">
                    <span style="font-size:2.2rem">🔍</span>
                    <h1 style="margin:0;font-size:2rem;font-weight:800;
                               color:#ffffff;letter-spacing:-0.02em">
                        NovaSearch
                    </h1>
                </div>
                <p style="color:#cbd5e1;margin:8px 0 0;font-size:1.05rem;font-weight:400;
                           letter-spacing:0.01em">
                    Busca en múltiples clasificados cubanos, en un solo lugar
                </p>
                <div style="margin-top:12px;display:flex;justify-content:center;gap:24px;
                            font-size:0.85rem;color:#94a3b8">
                    <span style="background:rgba(255,255,255,0.1);padding:4px 14px;
                                 border-radius:20px">🏪 {_adapter_loader.count} sitios</span>
                    <span style="background:rgba(255,255,255,0.1);padding:4px 14px;
                                 border-radius:20px">📂 {len(verticals)} categorías</span>
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
            # PESTAÑA 2: AGREGAR SITIO
            # ═══════════════════════════════════════════════════
            with gr.Tab("➕ Agregar sitio"):
                gr.HTML(
                    """
                    <div style="max-width:760px;margin:0 auto;padding:12px 0">
                        <h2 style="color:#1e3a5f;font-weight:700">➕ Agregar un nuevo sitio</h2>
                        <p style="color:#57534e">
                            Registra un clasificado cubano nuevo: el sistema verifica
                            automáticamente si es accesible (DNS + HTTP) antes de integrarlo.
                        </p>
                    </div>
                    """
                )
                with gr.Row(equal_height=True):
                    new_site_name = gr.Textbox(
                        label="Nombre (identificador)",
                        placeholder="ej: itencel",
                        scale=1,
                    )
                    new_site_domain = gr.Textbox(
                        label="Dominio",
                        placeholder="ej: itencel.com",
                        scale=1,
                    )
                    new_site_vertical = gr.Textbox(
                        label="Categoría",
                        placeholder="ej: general, cars, jobs",
                        value="general",
                        scale=1,
                    )

                new_site_url = gr.Textbox(
                    label="URL de búsqueda (usa {query} para el término)",
                    placeholder="ej: https://itencel.com/?q={query}",
                )

                verify_btn = gr.Button(
                    "🔍 Verificar acceso",
                    variant="secondary",
                )
                verify_output = gr.Markdown(value="")

                gr.HTML(
                    """
                    <div style="max-width:760px;margin:16px auto 0">
                        <h3 style="color:#1e3a5f;font-weight:600;font-size:1.05rem">
                            Selectores de resultados
                        </h3>
                        <p style="color:#78716c;font-size:0.9rem">
                            Opcionales — completa los que conozcas. Si dejas vacíos,
                            se genera un YAML base para afinar luego.
                        </p>
                    </div>
                    """
                )
                with gr.Row(equal_height=True):
                    new_site_container = gr.Textbox(
                        label="Contenedor de resultados (CSS)",
                        placeholder='ej: a.anuncio-list, li.card',
                        scale=2,
                    )
                    new_site_title = gr.Textbox(
                        label="Selector título",
                        placeholder="ej: h5.anuncio-titulo",
                        scale=1,
                    )
                    new_site_price = gr.Textbox(
                        label="Selector precio",
                        placeholder="ej: .price (opcional)",
                        scale=1,
                    )
                    new_site_url_sel = gr.Textbox(
                        label="Selector enlace",
                        placeholder="ej: a (o 'self' si es el contenedor)",
                        scale=1,
                    )

                save_btn = gr.Button(
                    "💾 Guardar adaptador",
                    variant="primary",
                )
                save_output = gr.Markdown(value="")

                verify_btn.click(
                    fn=verify_site_action,
                    inputs=[new_site_domain],
                    outputs=[verify_output],
                )

                save_btn.click(
                    fn=save_adapter_action,
                    inputs=[
                        new_site_name,
                        new_site_domain,
                        new_site_vertical,
                        new_site_url,
                        new_site_container,
                        new_site_title,
                        new_site_price,
                        new_site_url_sel,
                    ],
                    outputs=[save_output],
                )

            # ═══════════════════════════════════════════════════
            # PESTAÑA 3: AYUDA
            # ═══════════════════════════════════════════════════
            with gr.Tab("❓ Ayuda"):
                        gr.HTML(
                            """
                            <div style="max-width:700px;margin:0 auto;padding:20px 0">
                                <h2 style="color:#1e3a5f;font-weight:700">📖 ¿Cómo usar NovaSearch?</h2>

                                <div style="display:flex;gap:20px;margin:24px 0;flex-wrap:wrap">
                                    <div style="flex:1;min-width:160px;padding:20px;
                                                background:#f0ede8;border-radius:12px;text-align:center;
                                                border:1px solid #e8e4de">
                                        <div style="font-size:2rem">✏️</div>
                                        <h3 style="margin:8px 0 4px;font-size:1rem;color:#1e3a5f">1. Escribe</h3>
                                        <p style="margin:0;font-size:0.85rem;color:#57534e">
                                            Lo que quieres buscar. Sé específico.</p>
                                    </div>
                                    <div style="flex:1;min-width:160px;padding:20px;
                                                background:#f0ede8;border-radius:12px;text-align:center;
                                                border:1px solid #e8e4de">
                                        <div style="font-size:2rem">📂</div>
                                        <h3 style="margin:8px 0 4px;font-size:1rem;color:#1e3a5f">2. Categoría</h3>
                                        <p style="margin:0;font-size:0.85rem;color:#57534e">
                                            Selecciona dónde buscar.</p>
                                    </div>
                                    <div style="flex:1;min-width:160px;padding:20px;
                                                background:#f0ede8;border-radius:12px;text-align:center;
                                                border:1px solid #e8e4de">
                                        <div style="font-size:2rem">🔍</div>
                                        <h3 style="margin:8px 0 4px;font-size:1rem;color:#1e3a5f">3. Buscar</h3>
                                        <p style="margin:0;font-size:0.85rem;color:#57534e">
                                            Presiona y obtén resultados.</p>
                                    </div>
                                </div>

                                <h3 style="color:#1e3a5f;font-weight:600">❓ Preguntas frecuentes</h3>

                                <div style="background:#f0ede8;border-radius:12px;padding:16px 20px;margin:12px 0;border:1px solid #e8e4de">
                                    <p style="margin:0"><strong style="color:#1e3a5f">🔹 ¿Qué sitios busca?</strong><br>
                                    <span style="color:#57534e">Todos los sitios disponibles en la categoría que elijas.</span></p>
                                </div>
                                <div style="background:#f0ede8;border-radius:12px;padding:16px 20px;margin:12px 0;border:1px solid #e8e4de">
                                    <p style="margin:0"><strong style="color:#1e3a5f">🔹 ¿Por qué no aparecen resultados?</strong><br>
                                    <span style="color:#57534e">El sitio puede no estar accesible en este momento, o no hay resultados para tu búsqueda. Intenta con otros términos.</span></p>
                                </div>
                                <div style="background:#f0ede8;border-radius:12px;padding:16px 20px;margin:12px 0;border:1px solid #e8e4de">
                                    <p style="margin:0"><strong style="color:#1e3a5f">🔹 ¿Los precios son actualizados?</strong><br>
                                    <span style="color:#57534e">Los resultados se obtienen en tiempo real desde los sitios de clasificados.</span></p>
                                </div>
                                <div style="background:#f0ede8;border-radius:12px;padding:16px 20px;margin:12px 0;border:1px solid #e8e4de">
                                    <p style="margin:0"><strong style="color:#1e3a5f">🔹 ¿Cómo agrego más sitios?</strong><br>
                                    <span style="color:#57534e">Usa la pestaña <strong>➕ Agregar sitio</strong>: escribe el dominio, verifica si es accesible y guarda el adaptador. El sistema comprueba DNS + HTTP automáticamente.</span></p>
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


# ---------------------------------------------------------------------------
# Gestión de sitios: verificación de accesibilidad + guardado de adaptadores
# ---------------------------------------------------------------------------
from modulo_1_servicio.scraping.site_verifier import (  # noqa: E402
    build_adapter_yaml,
    check_accessibility,
)

# Último resultado de verificación (para habilitar el botón Guardar)
_verification_state: dict[str, Any] = {}


async def verify_site_action(domain: str) -> str:
    """Verifica la accesibilidad de un dominio desde la UI."""
    if not domain or not domain.strip():
        return "⚠️ Escribe un dominio para verificar. Ej: `itencel.com`"

    result = await check_accessibility(domain.strip())
    _verification_state["last"] = result

    ips = ", ".join(result.get("ips", [])) or "—"
    status = result.get("http_status") or "—"
    time_ms = result.get("response_time_ms") or "—"
    size = result.get("content_length") or "—"
    spa = "🧩 Sí (SPA — requiere adaptador Python)" if result.get("likely_spa") else "No"

    header_emoji = "✅" if result["accessible"] else "❌"
    return f"""
{header_emoji} **{result['domain']}** — {result['message']}

| Chequeo | Resultado |
|---|---|
| 🌐 DNS | {'✅ resuelve' if result['dns_ok'] else '❌ falla'} `{ips}` |
| 🔌 HTTP | {'✅ responde' if result['http_ok'] else '❌ no responde'} (status {status}) |
| ⏱️ Tiempo | {time_ms} ms |
| 📦 Contenido | {size} bytes |
| 🧩 SPA | {spa} |
"""


def save_adapter_action(
    name: str,
    site: str,
    vertical: str,
    search_url: str,
    container_selector: str,
    title_selector: str,
    price_selector: str,
    url_selector: str,
) -> str:
    """Genera, valida y guarda el YAML de un adaptador nuevo.

    Flujo: el usuario primero verifica accesibilidad y luego completa
    los selectores básicos (puede afinarlos luego editando el YAML).
    """
    name = (name or "").strip().lower()
    site = (site or "").strip()
    vertical = (vertical or "").strip() or "general"
    search_url = (search_url or "").strip()
    container_selector = (container_selector or "").strip()
    title_selector = (title_selector or "").strip() or "h2"
    price_selector = (price_selector or "").strip()
    url_selector = (url_selector or "").strip()

    # ── Validaciones ──
    if not name or not site or not search_url:
        return "⚠️ **Nombre**, **dominio** y **URL de búsqueda** son obligatorios."

    if not name.replace("-", "").replace("_", "").isalnum():
        return "⚠️ El **nombre** solo puede contener letras, números, `-` y `_`."

    if "{query}" not in search_url:
        return "⚠️ La **URL de búsqueda** debe contener `{query}` (se reemplaza con el término buscado)."

    if _verification_state.get("last", {}).get("domain") != _normalize_domain(site):
        return (
            "⚠️ Verifica primero la **accesibilidad** del dominio "
            "(botón '🔍 Verificar acceso') antes de guardar."
        )

    fields = [{"name": "titulo", "selector": title_selector, "type": "text"}]
    if price_selector:
        fields.append({"name": "precio", "selector": price_selector, "type": "price", "required": False})
    if url_selector:
        fields.append({"name": "url", "selector": url_selector, "type": "url"})

    yaml_text = build_adapter_yaml(
        name=name,
        site=site,
        vertical=vertical,
        search_url=search_url,
        container_selector=container_selector,
        fields=fields,
    )

    # ── Guardar en adapters/ ──
    adapter_path = _ADAPTERS_DIR / f"{name}.yaml"
    try:
        adapter_path.write_text(yaml_text, encoding="utf-8")
    except OSError as exc:
        return f"❌ Error escribiendo `{adapter_path}`: {exc}"

    # ── Recargar el loader para que el nuevo sitio se use en búsquedas ──
    _adapter_loader.load_all()

    return (
        f"✅ **Adaptador `{name}` guardado** en `adapters/{name}.yaml`\n\n"
        f"Ya está disponible en la pestaña **Buscar** (categoría `{vertical}`).\n\n"
        f"💡 Puedes afinar los selectores editando el archivo YAML si los "
        f"resultados no son exactos."
    )


def _normalize_domain(value: str) -> str:
    """Extrae el host de un dominio o URL (ej: 'https://x.com/y' → 'x.com')."""
    from urllib.parse import urlparse

    v = value.strip()
    if "://" not in v:
        v = "https://" + v
    return urlparse(v).netloc.split(":")[0]


from pathlib import Path  # noqa: E402

# Directorio donde se guardan los adaptadores YAML (raíz del proyecto / adapters)
_ADAPTERS_DIR = Path(__file__).parent.parent.parent / "adapters"
