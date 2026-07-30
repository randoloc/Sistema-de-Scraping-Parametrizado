"""Entry point standalone para el bot de Telegram.

Uso:
    python -m modulo_1_servicio.run_bot

Requiere TELEGRAM_BOT_TOKEN en el entorno.
"""

from __future__ import annotations

import asyncio
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from modulo_1_servicio.bot.bot_app import run_bot

if __name__ == "__main__":
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN no configurado")
        print("Configurá la variable de entorno y volvé a intentar.")
        raise SystemExit(1)
    asyncio.run(run_bot(token))
