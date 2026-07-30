---
title: NovaSearch
emoji: 🕸️
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# 🕸️ ScrapperGenérico

**Sistema parametrizado de scraping, extracción y entrega multi-canal.**

> Un motor de scraping genérico, configurable por YAML/JSON, con API REST, app de escritorio y entregas automatizadas por email, WhatsApp y web. Diseñado para ser **independiente del dominio**: scrapeas lo que quieras, de donde quieras, y lo recibes donde lo necesites.

---

## 📦 Arquitectura

El proyecto se divide en **tres módulos independientes** que pueden desplegarse por separado:

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

### Módulo 1 — Servicio de Scraping (`modulo_1_servicio/`)

API REST construida con **FastAPI** que orquesta todo el pipeline:

1. **Configuración** — Recibe YAML/JSON con qué extraer, dónde y cómo
2. **Extracción** — Motores plugables (BeautifulSoup, Playwright, HTTP API)
3. **Filtrado** — Inclusión/exclusión por patrón, longitud, deduplicación
4. **Paginación** — Template de URLs, páginas múltiples
5. **Entrega** — Email, WhatsApp, generación de página web

**Endpoints principales:**

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/scrape` | Ejecutar scraping |
| `GET` | `/api/results/{id}` | Resultados JSON |
| `GET` | `/api/results/{id}/web` | Página HTML de resultados |
| `POST` | `/api/deliver/{id}` | Entregar resultados |
| `POST` | `/api/whatsapp/send-activation` | Activar WhatsApp |
| `POST` | `/api/whatsapp/webhook` | Webhook WhatsApp |

**Despliegue inmediato en HuggingFace Spaces** — incluye `Dockerfile.hf`.

### Módulo 2 — App de Administración (`modulo_2_admin/`)

Aplicación desktop con **PySide6 + QML** que expone:

- **Dashboard** — Estadísticas en vivo, estado del servicio
- **Nuevo Scraper** — Configuración visual de fuentes, campos y selectores CSS
- **Resultados** — Exploración de items extraídos por operación
- **Entregas** — Gestión de destinatarios email/WhatsApp
- **Historial** — Registro local en SQLite con detalle completo

La lógica de negocio vive en `PythonBridge`, un puente Python ↔ QML que **puede reutilizarse desde Flutter/Dart** en una futura versión mobile.

### Módulo 3 — Resultados y Plantillas (`modulo_3_resultados/`)

Templates Jinja2 para renderizar resultados en múltiples formatos:
- Email HTML responsivo
- Página web embebida
- Mensajes de WhatsApp

---

## ⚙️ Configuración

El scraper se configura con un diccionario JSON/YAML. Ejemplo mínimo:

```json
{
  "source": "https://ejemplo.com/productos",
  "source_type": "web_page",
  "fields": [
    { "name": "titulo", "selector": "h2.product-title", "type": "text" },
    { "name": "precio", "selector": "span.price", "type": "price" },
    { "name": "imagen", "selector": "img.product-img", "type": "image" }
  ],
  "container_selector": "div.product-card",
  "filters": {
    "min_length": 10,
    "deduplicate": true,
    "max_results": 50
  },
  "pagination": {
    "strategy": "url",
    "url_template": "https://ejemplo.com/productos?page={page}",
    "max_pages": 5
  },
  "delivery": {
    "emails": ["user@ejemplo.com"],
    "generate_web": true
  }
}
```

### Tipos de campo soportados

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| `text` | Texto plano | `"Zapatos deportivos"` |
| `price` | Precio (US/EU) | `"$39.99"` → `39.99` |
| `url` | Enlace | `"/producto/123"` |
| `number` | Número | `"1,234"` → `1234.0` |
| `date` | Fecha | `"2024-01-15"` |
| `image` | URL de imagen | `"/img/photo.jpg"` |
| `boolean` | Verdadero/falso | `"true"` → `True` |

---

## 🚀 Primeros pasos

```bash
# Clonar
git clone https://github.com/randoloc/Sistema-de-Scraping-Parametrizado.git
cd Sistema-de-Scraping-Parametrizado

# Instalar dependencias base
pip install -e .

# Con todas las dependencias
pip install -e ".[all]"

# Solo módulo 1 (servicio API)
pip install -e ".[modulo1]"

# Solo módulo 2 (app desktop)
pip install -e ".[modulo2]"
```

### Iniciar el servicio

```bash
uvicorn modulo_1_servicio.main:app --reload
# → http://localhost:8000/docs (Swagger UI)
# → http://localhost:8000/api/health
```

### Iniciar la app de administración

```bash
python -m modulo_2_admin.main
```

---

## 🧪 Tests

```bash
# Todo el suite
pytest -v --tb=short

# Solo módulo 1 (servicio)
pytest tests/modulo_1/ -v

# Solo módulo 2 (admin + integración)
pytest tests/modulo_2/ -v

# Tests de integración (admin client ↔ FastAPI)
pytest tests/modulo_2/test_integration.py -v

# Con cobertura
pytest --cov=modulo_1_servicio --cov=modulo_2_admin --cov-report=term-missing
```

**60+ tests** — unitarios, de integración y mocks — **100% pasando**.

---

## 🏗️ Stack

| Capa | Tecnología |
|------|-----------|
| **Lenguaje** | Python 3.11+ |
| **API** | FastAPI + Uvicorn |
| **Scraping** | httpx + BeautifulSoup + lxml |
| **Configuración** | Pydantic + PyYAML |
| **GUI Desktop** | PySide6 + QML |
| **Cliente HTTP** | httpx (preparado para migrar a Dart/Flutter) |
| **Persistencia** | SQLite (historial local) |
| **Templates** | Jinja2 |
| **Tests** | pytest + pytest-asyncio + cobertura |
| **Calidad** | Ruff + MyPy strict |

---

## 🧠 Filosofía

> **CONCEPTOS > CÓDIGO**

Este proyecto no es solo un scraper. Es un **ejercicio de arquitectura limpia**: separación de responsabilidades, inyección de dependencias, modelos de dominio ricos y una API layer que trasciende el framework.

El `PythonBridge` del Módulo 2 está diseñado para que, cuando migres a Flutter, **solo reemplaces QML por Dart** — la lógica de negocio permanece intacta.

---

## 📄 Licencia

MIT — Randy Mustelier Rivero

---

<p align="center">
  <sub>Hecho con ❤️ y cero frameworks mágicos.</sub>
</p>
