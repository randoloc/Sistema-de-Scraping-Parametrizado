from __future__ import annotations

import logging
import os

from telegram.ext import Application, CommandHandler

from modulo_1_servicio.bot.handlers import ayuda_command, buscar_command, start_command

logger = logging.getLogger(__name__)

_bot_app: Application | None = None


def create_app(token: str | None = None) -> Application:
    global _bot_app
    token = token or os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN no configurado")

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("buscar", buscar_command))
    app.add_handler(CommandHandler("ayuda", ayuda_command))

    _bot_app = app
    return app


async def run_bot(token: str | None = None) -> None:
    app = create_app(token)
    logger.info("Bot iniciado en polling mode")
    await app.run_polling()


async def stop_bot() -> None:
    global _bot_app
    if _bot_app:
        logger.info("Deteniendo bot...")
        await _bot_app.shutdown()
        _bot_app = None
