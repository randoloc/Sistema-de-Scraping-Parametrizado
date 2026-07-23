# MEMORIA del Proyecto — ScrapperGenérico

> Archivo de persistencia local (reemplaza Engram). Se actualiza al final de cada sesión.
> **NO ELIMINAR**. Contiene el contexto de sesiones anteriores.

---

## Última actualización: 2026-07-23 (Sesión 6 - Cierre)

---

## 🧠 Contexto del Proyecto

**Visión final**: Sistema B2B SaaS de scraping genérico multi-vertical. Cualquier persona busca productos/servicios en múltiples sitios simultáneamente con filtros. Escalar a modelo de suscripción para agentes inmobiliarios, concesionarias, comercios.

**Stack actual**: Python 3.12, FastAPI, httpx, BeautifulSoup, PySide6+QML (desktop), Pydantic, pytest, SQLite.

**Repos**: `https://github.com/randoloc/Sistema-de-Scraping-Parametrizado`

---

## 📐 Arquitectura Actual (3 Módulos)

```
modulo_1_servicio/     → API FastAPI (scraping engine, adaptadores, entregas)
modulo_2_admin/        → GUI desktop PySide6+QML (para administración local)
modulo_3_resultados/   → Templates de entrega (email, web, WhatsApp)
```

**Flujo**: Usuario → Admin GUI (M2) → API (M1) → Scraping Engine → Adapters YAML → Extractors → Result → Delivery

---

## 📋 Historial de Sesiones

### Sesión 6 — 2026-07-23 (Cierre): Tests arreglados + Frontend Gradio
**Commit**: `c4d0b23`

**Qué se hizo**:
1. ✅ Arreglados 3 tests fallando (118/118):
   - `test_circular_rotation` — flaky por índice aleatorio (ahora no asume índice 0)
   - `_to_float("€ 50,00")` — bug de coma decimal europea (ahora soporta formatos US y EU)
   - `_to_float("$ 25,000 MXN")` — bug de texto residual (regex como último recurso)
2. ✅ Creado `modulo_1_servicio/ui/gradio_app.py` — Frontend Gradio completo:
   - Tab "🔍 Buscar": búsqueda multi-adaptador con tabla de resultados
   - Tab "📋 Adaptadores": lista todos los adaptadores cargados
   - Tab "⚙️ Estado": información del servicio + ayuda
   - Se conecta directamente con el engine interno (sin HTTP overhead)
3. ✅ Creado `app.py` — Entry point HF Spaces que monta Gradio sobre FastAPI
4. ✅ Actualizadas dependencias: Gradio 6.20.0 instalado
5. ✅ Actualizados `.gitignore`, `pyproject.toml`, `requirements-hf.txt`
6. ✅ Creados archivos de persistencia: `MEMORIA.md`, `PROPUESTA.md`

**Archivos creados**: 4 nuevos
- `app.py` — Entry point HF Spaces
- `modulo_1_servicio/ui/__init__.py`
- `modulo_1_servicio/ui/gradio_app.py` — Frontend Gradio
- `PROPUESTA.md` — Propuesta estratégica Cuba

**Archivos modificados**: 6
- `modulo_1_servicio/scraping/normalizer.py` — Fix _to_float
- `tests/modulo_1/test_anti_scraping.py` — Fix test flaky
- `pyproject.toml` — +gradio dep
- `modulo_1_servicio/requirements-hf.txt` — +gradio dep
- `.gitignore` — +google app password.png
- `MEMORIA.md` — Esta actualización

**Tests**: 118/118 pasando ✅

**Pendiente para próxima sesión**:
- [ ] Commitear el progreso actual
- [ ] Crear adapter real para Revolico (inspeccionar HTML)
- [ ] Crear adapter real para Porlalivre
- [ ] Integrar Telegram Bot (python-telegram-bot)
- [ ] Escribir tests para `routes_search.py`
- [ ] Desplegar en HF Spaces y probar

---

### Sesión 5 — 2026-07-23: Reevaluación estratégica completa

**Decisión CRÍTICA**: El usuario está en Cuba, sin acceso a USD ni tarjetas de crédito. **TODO el stack debe ser 100% gratuito.** No Stripe, no AWS, no Railway, no nada que requiera tarjeta.

**Nuevo target**:
1. **Agentes inmobiliarios en Cuba** (corredores de casas) — vertical real_estate
2. **Compradores/vendedores mayoristas en Cuba** — vertical wholesale
3. Plataformas objetivo: Revolico, Porlalivre, Telegram channels, Facebook Marketplace Cuba

**Stack gratuito redefinido**:
- Hosting: HF Spaces (FastAPI + Gradio) + GitHub Pages (frontend estático)
- Prod DB: SQLite (bien para escala pequeña-media)
- Bot/entrega: Telegram API (GRATIS, sin límites, sin tarjeta)
- Scraping: BeautifulSoup + httpx (sin Playwright por RAM limitada)
- CI/CD: GitHub Actions
- Dominio: subdominio de HF Spaces (gratis) o Freenom si funciona

**Problemas detectados**:
- 3 tests fallando (1 flaky, 2 bugs en `_to_float`)
- Fase 2 incompleta y sin commitear
- PySide6 no sirve para el público objetivo (no pueden instalar apps)
- WhatsApp API requiere Meta Business Account (no accesible desde Cuba)
- Playwright requiere muchos recursos (inviable en HF gratis)

---

### Sesión 4 — 2026-06-02: Fase 1 Completa

✅ Fase 1 completa: URL normalizer, adapters YAML, anti-scraping, endpoint, 36 tests
✅ Suite: 96 tests, 0 fallas (en ese momento)
✅ Email delivery configurado con Gmail SMTP
✅ QML UI corregida (padding bugs)
✅ PythonBridge funcionando

---

### Sesión 3 — 2026-06-02: Email + Fix QML

✅ Email delivery vía .env con Gmail SMTP
✅ Bug padding QML corregido (Rectangle → Pane)
✅ Prueba completa exitosa: scraping httpbin → email enviado

---

### Sesiones 1-2 — App Admin + Arranque

✅ PySide6-Essentials instalado
✅ PythonBridge + QML
✅ 8 tests de integración
✅ README creado
✅ GitHub repo creado

---

## 🐛 Bugs Conocidos

| # | Descripción | Archivo | Prioridad |
|---|-------------|---------|-----------|
| 1 | `test_circular_rotation` flaky — `UARotator` arranca con índice aleatorio, el test asume índice 0 | `test_anti_scraping.py:38` | 🟡 Medio |
| 2 | `_to_float` no maneja coma como decimal europea (`€ 50,00` → 5000.0) | `normalizer.py:73` | 🟢 Fácil |
| 3 | `_to_float` no limpia texto residual (`$ 25,000 MXN` → None) | `normalizer.py:73` | 🟢 Fácil |

---

## 📁 Archivos Estratégicos

| Archivo | Propósito |
|---------|-----------|
| `MEMORIA.md` | **Este archivo** — memoria persistente del proyecto |
| `CHECKPOINT.md` | Estado técnico detallado + instrucciones de prueba |
| `PROPUESTA.md` | Propuestas de producto y roadmap |
| `openspec/` | SDD (Spec-Driven Development) — cambios formales |

---

## 🚧 WIP: Cambios sin commitear (Fase 2 parcial)

**Nuevos:**
- `modulo_1_servicio/api/routes_search.py` — Endpoint `POST /api/search`
- `modulo_1_servicio/scraping/normalizer.py` — ResultNormalizer + CanonicalItem
- `tests/modulo_1/test_normalizer.py` — 19 tests (2 fallan por bugs en `_to_float`)

**Modificados:**
- `adapters/example_httpbin.yaml` — +canonical_map
- `modulo_1_servicio/main.py` — +search_router
- `modulo_1_servicio/scraping/adapters/models.py` — +canonical_map field
- `modulo_2_admin/core/client.py` — +search methods
- `modulo_2_admin/ui/main.py` — +search bridge
- `modulo_2_admin/ui/qml/main.qml` — +UI búsqueda

---

## ⚙️ Cómo Correr Tests

```powershell
# Todos los tests
python -m pytest tests/ -v --tb=short

# Tests específicos
python -m pytest tests/modulo_1/test_normalizer.py -v --tb=short
python -m pytest tests/modulo_1/test_anti_scraping.py -v --tb=short
```
