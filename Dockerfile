# Dockerfile para HuggingFace Spaces — Docker SDK
# Motor de scraping genérico con API FastAPI + Gradio

FROM python:3.11-slim

WORKDIR /app

# ── Dependencias del sistema ───────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Dependencias Python (cache layer) ──────────────────────────────────
COPY modulo_1_servicio/requirements-hf.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ── Código de la aplicación ────────────────────────────────────────────
COPY app.py .
COPY modulo_1_servicio ./modulo_1_servicio
COPY adapters ./adapters
COPY requirements.txt ./requirements-root.txt

# ── Puerto que HF espera ───────────────────────────────────────────────
EXPOSE 7860

# ── Healthcheck ────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/api/health')" || exit 1

# ── Entrypoint: FastAPI + Gradio montado ───────────────────────────────
CMD ["uvicorn", "modulo_1_servicio.main:app", "--host", "0.0.0.0", "--port", "7860"]
