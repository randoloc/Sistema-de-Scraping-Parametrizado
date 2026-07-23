"""Entry point del servicio de scraping (FastAPI).

Uso:
    uvicorn modulo_1_servicio.main:app --reload

Despliegue en HuggingFace Spaces:
    - Copiar modulo_1_servicio/ al Space
    - Crear requirements.txt con las dependencias
    - Configurar app.py que importe desde modulo_1_servicio.main
    - Añadir cron-job.org apuntando a /api/health cada 30 min
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

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

app = FastAPI(
    title="ScrapperGenérico — Servicio de Scraping",
    version="0.1.0",
    description="API para scraping genérico y entrega multi-canal",
)

app.include_router(scrape_router)
app.include_router(deliver_router)
app.include_router(search_router)
app.include_router(whatsapp_router)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


@app.get("/", response_class=HTMLResponse)
async def root() -> str:
    return """<!DOCTYPE html>
<html><body style="font-family: sans-serif; max-width: 600px; margin: 40px auto;">
<h1>ScrapperGenérico 🚀</h1>
<p>Servicio de scraping activo.</p>
<p><a href="/docs">Swagger API</a></p>
<p><a href="/api/health">Health Check</a></p>
</body></html>"""
