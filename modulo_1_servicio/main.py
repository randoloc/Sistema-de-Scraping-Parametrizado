"""Entry point del servicio de scraping (FastAPI).

Uso:
    uvicorn modulo_1_servicio.main:app --reload

Despliegue en HuggingFace Spaces:
    - Copiar modulo_1_servicio/ al Space
    - Crear requirements.txt con las dependencias
    - Configurar app.py que importe desde modulo_1_servicio.main
    - Añadir cron-job.org apuntando a /api/health cada 30 min

Bot de Telegram:
    La app inicia automáticamente el bot en background si
    TELEGRAM_BOT_TOKEN está configurado en el entorno.
    También se puede ejecutar standalone con:
        python -m modulo_1_servicio.run_bot
"""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

import gradio as gr

from modulo_1_servicio.api.routes_deliver import router as deliver_router
from modulo_1_servicio.api.routes_scrape import router as scrape_router
from modulo_1_servicio.api.routes_search import router as search_router
from modulo_1_servicio.api.routes_whatsapp_webhook import (
    router as whatsapp_router,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

_bot_task: asyncio.Task[None] | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _bot_task
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if token:
        from modulo_1_servicio.bot.bot_app import run_bot
        _bot_task = asyncio.create_task(run_bot(token))
        logger.info("Telegram bot iniciado en background")
    yield
    if _bot_task:
        _bot_task.cancel()
        try:
            await _bot_task
        except asyncio.CancelledError:
            pass
        logger.info("Telegram bot detenido")


app = FastAPI(
    title="ScrapperGenérico — Servicio de Scraping",
    version="0.1.0",
    description="API para scraping genérico y entrega multi-canal",
    lifespan=lifespan,
)

app.include_router(scrape_router)
app.include_router(deliver_router)
app.include_router(search_router)
app.include_router(whatsapp_router)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


# ─────────────────────────────────────────────────────────────────────
# UI NovaSearch (Gradio) montada sobre la misma app FastAPI
# ─────────────────────────────────────────────────────────────────────
# La raíz "/" sirve la interfaz web de búsqueda; la API REST sigue
# disponible en /api/* y /docs. Esto es lo que HF Spaces sirve.
from modulo_1_servicio.ui.gradio_app import build_app  # noqa: E402

_demo = build_app()
_demo.queue()
# PWA nativo de Gradio: genera manifest.json (display standalone) para
# instalar NovaSearch en el teléfono (Android/iOS) sin App Store.
# Los meta tags Apple hacen que iOS lo trate como app instalable.
_PWA_HEAD = """
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="NovaSearch">
<meta name="theme-color" content="#1e3a5f">
"""
app = gr.mount_gradio_app(
    app, _demo, path="/", pwa=True, head=_PWA_HEAD
)
