from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from modulo_1_servicio.bot.formatters import format_help, format_search_results, format_welcome
from modulo_1_servicio.bot.search_service import search

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(format_welcome(), parse_mode="Markdown")


async def ayuda_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(format_help(), parse_mode="Markdown")


async def buscar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "❌ Usá: /buscar <consulta>\n\n"
            "Ejemplo: /buscar iphone\n"
            "Ejemplo: /buscar casa vertical:real_estate",
            parse_mode="Markdown",
        )
        return

    query_parts = " ".join(context.args)

    vertical = "general"
    query = query_parts
    if "vertical:" in query_parts:
        parts = query_parts.split("vertical:")
        query = parts[0].strip()
        vertical = parts[1].strip() if len(parts) > 1 else "general"

    if not query:
        await update.message.reply_text(
            "❌ La consulta no puede estar vacía.\n"
            "Ejemplo: /buscar iphone",
            parse_mode="Markdown",
        )
        return

    await update.message.reply_text(
        f"🔍 Buscando *{query}* en vertical _{vertical}_...",
        parse_mode="Markdown",
    )

    try:
        result = await search(query=query, vertical=vertical)

        if "error" in result:
            await update.message.reply_text(f"❌ {result['error']}", parse_mode="Markdown")
            return

        formatted = format_search_results(
            query=result["query"],
            items=result["items"],
            vertical=result["vertical"],
        )

        if len(formatted) > 4000:
            formatted = formatted[:3997] + "..."

        await update.message.reply_text(formatted, parse_mode="Markdown")
    except Exception as e:
        logger.exception("Error en búsqueda")
        await update.message.reply_text(f"❌ Error al buscar: {e}", parse_mode="Markdown")
