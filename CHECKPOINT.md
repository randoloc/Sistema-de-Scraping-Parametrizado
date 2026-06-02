# 🕸️ Checkpoint: ScrapperGenérico

**Última actualización:** 2026-06-02
**Repo remoto:** `https://github.com/randoloc/Sistema-de-Scraping-Parametrizado`

---

## ✅ Estado actual

| Componente | Estado | Notas |
|-----------|--------|-------|
| **Servicio FastAPI** (Módulo 1) | ✅ Funcionando | `http://127.0.0.1:8000` — health, scraping, resultados, entregas |
| **Email Delivery** (SMTP Gmail) | ✅ Configurado | `.env` con credenciales, carga vía `python-dotenv` |
| **Admin core** (client, models, repo) | ✅ Funcionando | Cliente HTTP, modelos de datos, SQLite local |
| **GUI PySide6+QML** (Módulo 2) | ✅ Corregida | Padding bugs en Rectangles → Pane. UI completa visible |
| **PythonBridge** (slots Python↔QML) | ✅ Completo | Dashboard, scraping, resultados, entregas, historial |
| **QML UI** | ✅ Wireado | Todos los botones conectados al scraper real |
| **Historial SQLite** | ✅ Persistente | `~/.scrapper_generico/admin.db` |
| **Tests** | ✅ **96/96 pasando** | 75 unitarios + 13 integración + 8 nuevos archivos test |
| **Fase 1 — Base Genérica** | ✅ **Completada** | URL normalizer, adapters YAML, anti-scraping, endpoint, tests |
| **Adapters API** | ✅ `/api/adapters` | Listado con filtro por vertical, estructuras Pydantic |
| **README** | ✅ Creado | En raíz del repo |
| **Repo GitHub** | ✅ Creado | `randoloC/Sistema-de-Scraping-Parametrizado` |

---

## 📋 Últimas sesiones

### Sesión 4 (2026-06-02) — Fase 1 Completa: Endpoint adapters + 36 tests nuevos
- ✅ Agregado `GET /api/adapters` con filtro opcional `?vertical=`
- ✅ Escritos 36 tests nuevos:
  - 9 tests para `normalize_url()` (con/sin protocolo, vacía, inválida)
  - 5 tests para `UARotator` (rotación, circular, pool default)
  - 4 tests para `RetryPolicy` (éxito, timeout, retry con éxito, HTTP errors)
  - 5 tests para `DomainDelay` (primera request, espera, suficiente tiempo, custom delay, dominios distintos)
  - 9 tests para `AdapterLoader` (YAML válido/inválido, filtros, count)
  - 4 tests para endpoint `/api/adapters` (listado, filtro vertical, estructura)
- ✅ Suite completa: **96 tests, 0 fallas** (antes 60)
- ✅ Todos los tasks de Fase 1 marcados como completados en `openspec/`

### Sesión 3 (2026-06-02) — Email delivery + Fix QML + Sistema funcionando
- ✅ Corregido bug de `padding` en QML (Rectangle no tiene `padding` en QtQuick 2.15)
  - `RowLayout` → `anchors.margins`
  - `Rectangle` → `Pane` (que sí soporta `padding`)
  - ToolBar tiene `padding` nativamente
  - QML carga sin errores: 1 root object, 0 syntax errors
- ✅ Configurado email delivery vía `.env`:
  - Creado `.env` con credenciales SMTP Gmail
  - Modificado `EmailDelivery` para leer de `os.getenv()` con defaults
  - Agregado `load_dotenv()` en módulo de email
- ✅ Prueba completa exitosa:
  - Scraping `http://httpbin.org/html` → 1 item extraído ✅
  - Página web generada → 8,139 caracteres ✅
  - Email enviado a `randolo92cromix@gmail.com` → `email_sent: true` ✅
- ✅ Comunicación M1↔GUI probada y funcionando

### Sesión 2 — App funcional + Tests en vivo
- ✅ Instalado `PySide6-Essentials` (77.5 MB)
- ✅ Prueba en vivo del admin client contra FastAPI
- ✅ Creado README.md y pusheado a GitHub

### Sesión 1 — App de Admin + Tests de Integración
- ✅ PythonBridge + QML + 8 tests de integración
- ✅ Arquitectura documentada

---

## 🧪 Cómo probar

```bash
# 1. Configurar credenciales (copiar .env.example a .env y completar)
cp .env.example .env

# 2. Iniciar servicio FastAPI
uvicorn modulo_1_servicio.main:app --reload --port 8000

# 3. En otra terminal, abrir la app desktop
python -m modulo_2_admin.main

# 4. O ejecutar tests
python -m pytest tests/ -v --tb=short

# 5. O probar scraping + email delivery desde consola
python -c "
from modulo_2_admin.core.client import ScrapperClient

client = ScrapperClient('http://127.0.0.1:8000')

# Scrape
resp = client.run_scrape({
    'source': 'http://httpbin.org/html',
    'source_type': 'web_page',
    'fields': [
        {'name': 'titulo', 'selector': 'h1', 'type': 'text'},
    ],
})
print(f'Scrape: {resp.operation_id} | {resp.status} | {resp.total_found} items')

# Email delivery
deliver = client.deliver_results(resp.operation_id, emails=['tu@email.com'])
print(f'Email enviado: {deliver[\"email_sent\"]}')
client.close()
"
```

---

## ⚙️ Stack instalado

| Paquete | Estado |
|---------|--------|
| Python 3.12.1 | ✅ |
| FastAPI 0.136.1 | ✅ |
| httpx 0.28.1 | ✅ |
| uvicorn 0.46.0 | ✅ |
| PySide6-Essentials 6.11.1 | ✅ |
| pytest 9.0.3 | ✅ |
| beautifulsoup4 4.14.3 | ✅ |
| lxml 6.1.0 | ✅ |
| pydantic 2.13.3 | ✅ |
| python-dotenv 1.2.2 | ✅ |

---

## 📁 Archivos clave

```
modulo_1_servicio/
  main.py                        — Entry point FastAPI
  api/routes_scrape.py           — Endpoints /api/scrape y /api/results
  api/routes_deliver.py          — Endpoints /api/deliver
  deliveries/email_sender.py     — EmailDelivery con soporte .env
  scraping/engine.py             — Orchestrator + FilterEngine
  scraping/extractors/           — BaseExtractor + BeautifulSoupExtractor
  scraping/url_utils.py          — normalize_url() (Fase 1)
  scraping/anti_scraping.py      — UARotator, RetryPolicy, DomainDelay (Fase 1)
  scraping/adapters/models.py    — SiteAdapter, AdapterField (Pydantic)
  scraping/adapters/loader.py    — AdapterLoader (carga YAML)

modulo_2_admin/
  core/client.py                 — ScrapperClient (HTTP)
  core/models.py                 — ScrapeJobConfig, FieldConfig, etc.
  core/repository.py             — LocalRepository (SQLite)
  ui/main.py                     — PythonBridge + entry point PySide6
  ui/qml/main.qml                — UI completa (Pane-based, sin padding en Rectangles)

tests/
  modulo_2/test_integration.py   — 8 tests de integración admin ↔ scraper
  modulo_1/                      — 88 tests del servicio
    test_url_utils.py            — 9 tests para normalize_url
    test_anti_scraping.py        — 14 tests para UARotator/RetryPolicy/DomainDelay
    test_adapter_loader.py       — 9 tests para AdapterLoader

adapters/                        — Adaptadores YAML (ej: example_httpbin.yaml)
.env                             — Credenciales SMTP (no comitear)
.env.example                     — Template de configuración
CHECKPOINT.md                    — Este archivo
```

---

---

## 🏗️ Visión Arquitectónica — Sistema Genérico de Búsqueda

### Arquitectura en capas

```
USUARIO: "autos usados Mexico < 10000"
         │
         ▼
┌─────────────────────────────────┐
│    INTERPRETE DE CONSULTAS      │  🆕
│  Extrae: vertical=cars,         │
│  pais=mexico, max_price=10000   │
└──────────────┬──────────────────┘
               ▼
┌─────────────────────────────────┐
│    BUSCADOR DE PLANTILLAS       │  🆕
│  Encuentra adaptadores para     │
│  "cars" en sitios conocidos     │
└──────────────┬──────────────────┘
               ▼
┌─────────────────────────────────┐
│    ADAPTADOR DE SITIO (YAML)    │  🆕
│  Traduce consulta → URL         │
│  Conoce selectores, paginación  │
└──────────────┬──────────────────┘
               ▼
┌─────────────────────────────────┐
│    MOTOR DE SCRAPING            │  ✅ EXISTE
└──────────────┬──────────────────┘
               ▼
┌─────────────────────────────────┐
│    NORMALIZADOR DE RESULTADOS   │  🆕
│  Unifica datos de múltiples     │
│  fuentes en schema común        │
└──────────────┬──────────────────┘
               ▼
┌─────────────────────────────────┐
│    ENTREGA (Web/Email/WA)       │  ✅ EXISTE
└─────────────────────────────────┘
```

### Plan de implementación

| Fase | Qué incluye | Estado |
|------|------------|--------|
| **Fase 1** — Base sólida | URL normalizer, adaptadores YAML, anti-scraping, endpoint, tests | ✅ **Completada** |
| **Fase 2** — Biblioteca | Adaptadores para sitios comunes, schema canónico | ⏳ Siguiente |
| **Fase 3** — Intérprete | Parseo de consultas, buscador de plantillas | ⏳ |
| **Fase 4** — GUI | Navegación por verticales, búsqueda guiada | ⏳ |

---

## 🚧 Pendiente para próxima sesión

- [ ] **Fase 2**: Biblioteca de adaptadores para sitios comunes (ML, OLX, etc.)
- [ ] **Fase 2**: Schema canónico de resultados
- [ ] **Fase 2**: Normalizador de datos multi-fuente
- [ ] **Fase 3**: Intérprete de consultas en lenguaje natural
