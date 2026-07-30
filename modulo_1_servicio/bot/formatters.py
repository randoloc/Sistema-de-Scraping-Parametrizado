from __future__ import annotations

from collections import defaultdict
from typing import Any

from modulo_1_servicio.scraping.normalizer import CanonicalItem


def format_item(item: dict[str, Any] | CanonicalItem, index: int = 1) -> str:
    if isinstance(item, CanonicalItem):
        item = item.model_dump()

    title = item.get("title") or "Sin título"
    price = item.get("price")
    currency = item.get("currency") or ""
    location = item.get("location")
    url = item.get("url")

    lines = [f"{index}. *{title}*"]

    if price is not None:
        try:
            price_f = float(price)
            price_str = f"{currency} {price_f:,.2f}" if currency else f"${price_f:,.2f}"
            lines.append(f"   💰 {price_str}")
        except (ValueError, TypeError):
            lines.append(f"   💰 {price}")

    if location:
        lines.append(f"   📍 {location}")

    if url:
        lines.append(f"   🔗 [Ver anuncio]({url})")

    return "\n".join(lines)


def format_search_results(
    query: str,
    items: list[dict[str, Any]],
    vertical: str,
) -> str:
    if not items:
        return f"😕 No encontré resultados para *{query}* en la vertical _{vertical}_."

    parts: list[str] = []

    by_site: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        by_site[item.get("source_site", "desconocido")].append(item)

    parts.append(f"*🏠 Resultados para: {query}*")
    parts.append("")

    total = 0
    for site, site_items in by_site.items():
        parts.append(f"📌 *{site}* — {len(site_items)} resultados")
        for item in site_items:
            total += 1
            parts.append(format_item(item, total))
        parts.append("")

    parts.append("🔍 Más resultados en /buscar \"otra consulta\"")

    return "\n".join(parts)


def format_welcome() -> str:
    return (
        "🤖 *ScrapperGenérico Bot*\n\n"
        "Sistema de búsqueda multi-sitio para clasificados en Cuba.\n\n"
        "*Comandos disponibles:*\n"
        "/buscar <consulta> — Busca en todas las verticales\n"
        "/buscar <consulta> vertical:<nombre> — Busca en una vertical específica\n"
        "/ayuda — Muestra esta ayuda\n\n"
        "*Ejemplos:*\n"
        "/buscar iphone\n"
        "/buscar casa vertical:real_estate\n"
        "/buscar toyota"
    )


def format_help() -> str:
    return (
        "*Comandos disponibles:*\n\n"
        "/start — Mensaje de bienvenida\n"
        "/buscar <consulta> — Busca clasificados\n"
        "/buscar <consulta> vertical:<nombre> — Busca en una vertical específica\n"
        "/ayuda — Muestra esta ayuda\n\n"
        "*Verticales disponibles:*\n"
        "• test — Adaptadores de prueba\n"
        "• cars — Autos\n"
        "• real_estate — Casas y propiedades\n"
        "• jobs — Empleos\n\n"
        "*Ejemplos:*\n"
        "/buscar iphone\n"
        "/buscar casa vertical:real_estate\n"
        "/buscar playstation"
    )
