"""Entry point para HuggingFace Spaces.

Monta el frontend Gradio sobre la API FastAPI existente.
HF Spaces busca este archivo automáticamente en la raíz.

Gradio maneja la ruta raíz (/) como home page.
La API REST sigue disponible en /api/*.
"""

from __future__ import annotations

import gradio as gr

from modulo_1_servicio.main import app as fastapi_app
from modulo_1_servicio.ui.gradio_app import build_app

# Eliminar la ruta raíz de FastAPI para que Gradio pueda manejarla
fastapi_app.router.routes = [
    r
    for r in fastapi_app.router.routes
    if not (getattr(r, "path", None) == "/" and getattr(r, "methods", None) == {"GET"})
]

# Construir y montar Gradio sobre FastAPI
gradio_ui = build_app()
app = gr.mount_gradio_app(fastapi_app, gradio_ui, path="/")
