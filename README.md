---
title: NovaSearch
emoji: 🕸️
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# 🕸️ ScrapperGenérico / NovaSearch

**Sistema parametrizado de scraping, extracción y entrega multi-canal — desplegado como NovaSearch en HF Spaces.**

> Busca en múltiples clasificados cubanos, en un solo lugar. Motor genérico configurable por YAML/JSON, con API REST y entregas automatizadas por email, WhatsApp y web.

---

## 🚀 Acceso rápido

| Recurso | URL |
|---------|-----|
| 🌐 **Web UI (Gradio)** | [https://randolo-novasearch.hf.space](https://randolo-novasearch.hf.space) |
| 📚 **API Docs (Swagger)** | [https://randolo-novasearch.hf.space/api/docs](https://randolo-novasearch.hf.space/api/docs) |
| ❤️ **Health Check** | [https://randolo-novasearch.hf.space/api/health](https://randolo-novasearch.hf.space/api/health) |

## 🚀 Cómo usar

1. **Escribe** lo que quieres buscar (ej: "casa", "laptop", "zapatos")
2. **Selecciona** una vertical (categoría)
3. **Presiona** Buscar y obtén resultados de todos los sitios

## 🛠 Stack

| Capa | Tecnología |
|------|-----------|
| **Frontend** | Gradio 6 (montado sobre FastAPI) |
| **API** | FastAPI + Uvicorn |
| **Scraping** | httpx + BeautifulSoup + lxml |
| **Config** | Pydantic + PyYAML |
| **Bot** | Python Telegram Bot |
| **Hosting** | Hugging Face Spaces (Docker SDK) |

## 📦 Arquitectura

```
┌─────────────────────────────────────────────────────┐
│                  ScrapperGenérico                     │
├─────────────────┬─────────────────┬─────────────────┤
│                 │                 │                 │
│   Módulo 1      │   Módulo 2      │   Módulo 3      │
│   Servicio      │   Admin         │   Resultados     │
│   (FastAPI)     │   (PySide6+QML) │   (Templates)    │
│                 │                 │                 │
│  ◦ API REST     │  ◦ GUI desktop  │  ◦ Email HTML    │
│  ◦ Scraping     │  ◦ Cliente HTTP  │  ◦ Web embebida  │
│  ◦ Entregas     │  ◦ Historial    │  ◦ WhatsApp      │
│  ◦ Webhooks     │  ◦ SQLite local  │  ◦ Templates     │
└─────────────────┴─────────────────┴─────────────────┘
```

## ⚙️ Configuración

### Adaptadores YAML

Los adaptadores definen cómo extraer datos de cada sitio. Se cargan desde `adapters/*.yaml`:

```yaml
name: revolico
vertical: clasificados
container_selector: "div.advice"
fields:
  - name: title
    selector: "h2 a"
    type: text
  - name: price
    selector: "span.price"
    type: price
```

### Variables de entorno

| Variable | Descripción | Requerida |
|----------|-------------|-----------|
| `SENDGRID_API_KEY` | API key de SendGrid | Para email |
| `TELEGRAM_TOKEN` | Token del bot de Telegram | Para Telegram |
| `WHATSAPP_ACCOUNT_SID` | Account SID de Twilio | Para WhatsApp |
| `WHATSAPP_AUTH_TOKEN` | Auth token de Twilio | Para WhatsApp |

## 🧪 Tests

```bash
pytest -v                          # todos los tests
pytest -v -m "not slow"            # solo tests rápidos
pytest -v --cov=modulo_1_servicio  # con cobertura
```

## 📁 Estructura del proyecto

```
app.py                         ← Entry point HF Spaces
Dockerfile                     ← Docker SDK para HF
requirements.txt               ← Dependencias HF Spaces
adapters/                      ← Config YAML por sitio
├── revolico.yaml
├── porlalivre.yaml
└── demo_local.yaml
modulo_1_servicio/             ← API REST + scraping
├── main.py                    ← FastAPI app
├── api/                       ← Rutas FastAPI
├── bot/                       ← Bot de Telegram
├── scraping/                  ← Motor de scraping
│   ├── adapters/              ← Carga de adaptadores YAML
│   ├── extractors/            ← Estrategias de extracción
│   ├── engine.py              ← Orquestador
│   ├── normalizer.py          ← Normalización de resultados
│   └── anti_scraping.py
├── config/                    ← Esquemas de configuración
├── deliveries/                ← Canales de entrega
├── templates/                 ← Templates HTML
└── ui/gradio_app.py           ← Frontend Gradio (NovaSearch)
modulo_2_admin/                ← App de escritorio (PySide6)
modulo_3_resultados/           ← Templates multi-canal
tests/                         ← Tests con pytest
pyproject.toml                 ← Configuración del proyecto
```

## 🧪 Modo desarrollo

```bash
# Activar entorno
source .venv/bin/activate

# Ejecutar con modo demo (datos simulados)
DEMO_MODE=1 python app.py

# Modo producción
python app.py
```

---

<p align="center">
  <sub>Hecho con ❤️ para Cuba</sub>
</p>
