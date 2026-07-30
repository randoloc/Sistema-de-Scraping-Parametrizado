"""Entry point para HuggingFace Spaces — NovaSearch.

HF Spaces ejecuta este archivo con sdk:gradio.
El servidor se inicia explícitamente con demo.launch().

La API REST (/api/*) NO está disponible en HF Spaces por simplicidad.
Para API completa, correr localmente con: uvicorn modulo_1_servicio.main:app
"""

from __future__ import annotations

import os

# Modo demostración por defecto en HF Spaces (sin acceso a sitios reales)
os.environ.setdefault("DEMO_MODE", "1")

from modulo_1_servicio.ui.gradio_app import build_app  # noqa: E402

# Construir y lanzar la interfaz NovaSearch
demo = build_app()
demo.queue()
demo.launch(server_name="0.0.0.0", server_port=7860)
