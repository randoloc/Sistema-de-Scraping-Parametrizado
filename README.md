---
title: NovaSearch
emoji: 🔍
colorFrom: #1e3a5f
colorTo: #2c5282
sdk: gradio
sdk_version: 6.20.0
app_file: app.py
pinned: true
short_description: Buscador multi-sitio de clasificados cubanos
---

# 🔍 NovaSearch

**Busca en múltiples clasificados cubanos, en un solo lugar.**

NovaSearch es un motor de búsqueda unificado que consulta simultáneamente varios sitios de clasificados cubanos (Revolico, Porlalivre, etc.) y te muestra los resultados en tarjetas visuales con precio, contacto, ubicación y más.

---

## 🚀 Cómo usar

1. **Escribe** lo que quieres buscar (ej: "casa", "laptop", "zapatos")
2. **Selecciona** una categoría
3. **Presiona** Buscar y obtén resultados de todos los sitios

## 🛠 Stack

| Capa | Tecnología |
|------|-----------|
| **Frontend** | Gradio 6 |
| **API** | FastAPI + Uvicorn |
| **Scraping** | httpx + BeautifulSoup + lxml |
| **Config** | Pydantic + PyYAML |
| **Hosting** | Hugging Face Spaces |

## 🧪 Modo desarrollo

```bash
# Activar entorno
source .venv/bin/activate

# Ejecutar con modo demo (datos simulados)
DEMO_MODE=1 python app.py

# Modo producción (intenta sitios reales)
python app.py
```

## 📁 Estructura

```
app.py                         ← Entry point HF Spaces
modulo_1_servicio/
├── main.py                    ← FastAPI app
├── ui/gradio_app.py           ← Frontend Gradio (NovaSearch)
├── scraping/                  ← Motor de scraping multi-site
├── bot/telegram_bot.py        ← Bot de Telegram
adapters/                      ← Config YAML por sitio
├── revolico.yaml
├── porlalivre.yaml
└── demo_local.yaml
```

---

<p align="center">
  <sub>Hecho con ❤️ para Cuba</sub>
</p>
