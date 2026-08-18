# MEMORIA del Proyecto — ScrapperGenérico

> Archivo de persistencia local (reemplaza Engram). Se actualiza al final de cada sesión.
> **NO ELIMINAR**. Contiene el contexto de sesiones anteriores.

---

## Última actualización: 2026-08-18 (Sesión 11)

---

### Sesión 11 — 2026-08-18: Deploy HF Spaces + fixes pendientes

**Contexto**: El usuario pidió "proceder y hacer todo, al final levantar el website en HF". Se evaluó el estado del proyecto: 196 tests pasando, Space corriendo en HF, adaptadores funcionando (Revolico 120 items, Timbirichi 30, Itencel 50).

**Qué se hizo**:
1. ✅ Verificación de estado: 196/196 tests OK, HF Space HEALTHY
2. ✅ Fix porlalivre: marcado como deshabilitado (vertical: disabled) — el sitio está en renovación 2026 y es SPA, los selectores BS4 no funcionan
3. ✅ Fix logs cosméticos: `required: false` en campos imagen de adaptadores YAML (itencel, timbirichi)
4. ✅ Push a GitHub y HF Spaces
5. ✅ Verificación en producción

**Archivos**: `adapters/porlalivre.yaml`, `adapters/itencel.yaml`, `adapters/timbirichi.yaml`, `MEMORIA.md`

---

### Sesión 10 — 2026-08-13: Deploy HF Spaces con PWA + rediseño de tarjetas

**Contexto**: Retomando tras la Sesión 9b. El usuario probó dos tokens; el primero (`sk-...`) NO era de HF (OpenAI/DeepSeek/OpenRouter/Anthropic lo rechazaron; HF respondió "Invalid username or password"). El segundo, un token `hf_***` (token `NovaSearch`, rol write, cuenta `Randolo`, org `CromixSoft`), sí era válido. Se validó vía `GET https://huggingface.co/api/whoami-v2`.

**Qué se hizo**:
1. ✅ **Remote `hf-spaces` reconectado** — se había perdido (MEMORIA lo mencionaba, pero `git remote -v` solo tenía `origin`). Recreado con el token HF: `git remote add hf-spaces https://Randolo:<token>@huggingface.co/spaces/Randolo/novasearch`
2. ✅ **Push a HF Spaces**: `819692b..36b253c` (4 commits pendientes): `8c6a6d8` (fix Dockerfile.hf), `ad6db20` (rediseño tarjetas WCAG AA), `1916265` (PWA instalable), `36b253c` (filtro relevancia + tarjetas cyan)
3. ✅ **Push a GitHub**: `1916265..36b253c` (1 commit que faltaba)
4. ✅ **Build desplegado**: Space `Randolo/novasearch` pasó BUILDING → RUNNING (~1 min en cpu-basic)
5. ✅ **Verificación en producción**:
   - Raíz `/`: HTTP 200, 46KB, UI NovaSearch (Buscar/Categoría/Ayuda)
   - `GET /api/health` → `{"status":"ok","version":"0.1.0"}`
   - `POST /api/search {"query":"iphone"}` → **200 resultados reales**: itencel 50, revolico 120, timbirichi 30, porlalivre 0 (182 con precio, 184 con imagen, 200 con ubicación)
   - ⚠️ Nota API: la respuesta usa claves `items` y `total_found`, NO `results`/`data`

**Archivos**: `MEMORIA.md` (esta actualización), `.git/config` (remote hf-spaces, no se commitea)

**Pendiente (heredado de Sesión 9b)**:
- [ ] `porlalivre` sigue devolviendo 0 en producción (selectores de Sesión 7 nunca verificados contra HTML real) → **Resuelto Sesión 11: sitio deshabilitado (SPA en renovación 2026)**
- [ ] Logs cosméticos "Error extrayendo campo 'imagen'" (item se conserva con imagen=None) → **Resuelto Sesión 11: `required: false` en imagen de itencel/timbirichi**

---

## 🧠 Contexto del Proyecto

**Visión final**: Sistema B2B SaaS de scraping genérico multi-vertical. Cualquier persona busca productos/servicios en múltiples sitios simultáneamente con filtros. Escalar a modelo de suscripción para agentes inmobiliarios, concesionarias, comercios.

**Stack actual**: Python 3.14, FastAPI, httpx, BeautifulSoup, Gradio (web), Pydantic, pytest, SQLite.

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

### Sesión 9 — 2026-08-03: Datos reales (Timbirichi + Itencel) + Feature UI "Agregar sitio"

**Contexto**: Continuando la petición del usuario de **desactivar el modo demo y buscar datos reales de los sitios reales**. Revolico fue reescrito en la sesión previa (adapter Python con Apollo SSR + cache de buildID). Esta sesión se centró en: (1) razonar Timbirichi contra el HTML real hasta que filtrara correctamente, (2) crear el adaptador de Itencel, (3) implementar la feature pedida de **agregar sitios nuevos desde la UI con verificación automática de accesibilidad (DNS + HTTP)**.

**Qué se hizo**:

1. ✅ **Timbirichi razonado e implementado** (`adapters/timbirichi.yaml` reescrito):
   - El endpoint `?buscar=` NO filtra (devuelve homepage con anuncios random). El formulario real es `action=/buscar` con `input name=q` → URL correcta: `/buscar/pagina/{page}?q={query}`
   - Paginación path-based: `/buscar/pagina/2?q=...` (`&page=2` NO cambia resultados, verificado)
   - Contenedor `a.anuncio-list` (30/página) — el contenedor es el propio `<a>`, por lo que la URL se lee del href del contenedor
   - Precio: tag literal `<precio>$ 200</precio>`; imagen: `img.thumbnail.lazy-load` con `data-src` (src es blank.gif, ignorada)
   - 7 anuncios sin precio en "iphone" son tiendas (MultiTech, etc.) que genuinamente no publican precio → campo `required: false`
2. ✅ **Fix extractor base** (`extractors/base.py`): soporte de selector especial `self`/`@self` en `_extract_type_attr` (lee atributo del contenedor mismo — necesario porque bs4 4.14.3 no soporta `:scope`). También se amplió la lista de imágenes por defecto a ignorar (`default.jpg`, `noimage.jpg`, etc. — Itencel usa `web/img/default.jpg`)
3. ✅ **Campo `required` en el modelo**: `AdapterField.required: bool = True` en `adapters/models.py`, propagado a las 4 construcciones de FieldDefinition (`search_service.py`, `routes_search.py`, `gradio_app.py`, `telegram_bot.py`)
4. ✅ **Itencel implementado** (`adapters/itencel.yaml` nuevo):
   - WordPress con tema RTCL (Classified Listing); formulario real `action=/all-ads/` `input name=q`
   - URL: `/all-ads/page/{page}/?q={query}` — 1,109 resultados para "iphone", 50/página
   - Estructura: `.rtcl-listing-item`, `h3.rtin-title`, `.rtcl-price-amount` ("25 USD"), `img.rtcl-thumbnail`, `a.rtin-thumb-inner`, `li:has(.fa-map-marker)`
   - End-to-end: 50 items, 50/50 URL, 50/50 imagen, 46/50 precio, **50/50 ubicación**
5. ✅ **Verificador de accesibilidad** (`scraping/site_verifier.py` nuevo): `check_accessibility(domain)` → DNS (socket.getaddrinfo) + HTTP (httpx); detecta SPA vacío (<2KB), bloqueo anti-bot (403/429), DNS caído, timeout. Mensajes en español. Además `build_adapter_yaml(...)` genera el YAML del adaptador nuevo
6. ✅ **Feature UI "➕ Agregar sitio"** (`ui/gradio_app.py`):
   - Pestaña nueva con inputs: nombre, dominio, categoría, URL de búsqueda, selectores (contenedor/título/precio/enlace)
   - Botón "🔍 Verificar acceso" → `verify_site_action()` muestra tabla DNS/HTTP/tiempo/contenido/SPA
   - Botón "💾 Guardar adaptador" → `save_adapter_action()` valida (formato nombre, `{query}` en URL, dominio verificado antes), escribe `adapters/{name}.yaml` y recarga el loader
   - **Bug corregido**: la pestaña "❓ Ayuda" estaba anidada dentro del Accordion "Sitios disponibles" → ahora es pestaña independiente. FAQ actualizado (explica la nueva pestaña)
7. ✅ **Tests: 194/194** (antes 183): +4 en `test_extractor.py` (self/@self, required), +3 en `test_adapter_loader.py` (required), **+11 en `test_site_verifier.py`** (DNS/HTTP/SPA/blocked/timeout/YAML)

**Verificación en vivo**: prueba `_test_ui_flow.py` confirmó `verify_site_action("itencel.com")` muestra tabla correcta, `save_adapter_action` bloquea dominios no verificados, y el loader recarga y ve el adaptador nuevo.

**Archivos**:
- `adapters/timbirichi.yaml` — reescrito (estructura real verificada)
- `adapters/itencel.yaml` — nuevo
- `modulo_1_servicio/scraping/site_verifier.py` — nuevo (verificación accesibilidad + build_adapter_yaml)
- `modulo_1_servicio/scraping/extractors/base.py` — selector self/@self + imágenes por defecto
- `modulo_1_servicio/scraping/adapters/models.py` — campo `required`
- `modulo_1_servicio/ui/gradio_app.py` — pestaña Agregar sitio + fix pestaña Ayuda + required
- `modulo_1_servicio/bot/search_service.py`, `api/routes_search.py`, `bot/telegram_bot.py` — propagación required
- `tests/modulo_1/test_extractor.py`, `test_adapter_loader.py`, `test_site_verifier.py` — 194/194 verdes

**Pendiente**:
- [x] Commit + push a GitHub y HF Spaces de todo el progreso (commits `420377b`, `4b7ad39`)
- [x] Probar búsqueda multi-sitio desde la UI (timbirichi + itencel + revolico en una búsqueda)
- [ ] Sitios accesibles sin adaptador: `qvaventas.com` (141KB), `cubisima.com` (41KB), `anuncioscuba.com` (353KB); SPA que requieren adapter Python: `alaventa.com`, `apululu.com`
- [ ] Paginación multi-página en la UI (hoy siempre page=1; `max_pages` del SearchRequest no se usa en UI)
- [ ] Verificar selectores de `porlalivre` contra HTML real (devuelve 0 en producción — selectores de Sesión 7 nunca verificados) → **Resuelto Sesión 11: sitio deshabilitado (SPA en renovación 2026, selectores BS4 no funcionan)**

---

### Sesión 9b — 2026-08-03 (mismo día): Fix bot Telegram + verificación en producción real

**Contexto**: Al revisar el flujo para el commit, se detectó que el bot de Telegram NO buscaba en Revolico: el adaptador Python (`python_adapter`) solo se soportaba en la API (`routes_search.py`) y en la UI (`gradio_app.py`), pero no en `search_service.py` ni en `telegram_bot.py::_search`. Además `handlers.py` usaba vertical `"test"` por defecto, que solo matcheaba `demo_local` (los sitios reales son `general`).

**Qué se hizo**:
1. ✅ `search_service.py`: añadida ruta `python_adapter` (importa clase, ejecuta `search(query, page=1)`, cierra instancia) — idéntica a la de `routes_search.py`
2. ✅ `telegram_bot.py::_search`: misma ruta `python_adapter` vía helper `_search_python_adapter` + refactor del `try/except` del loop de adaptadores (antes el `try` solo envolvía el run del orchestrator, con la ruta nueva el bloqueo quedaba correctamente estructurado)
3. ✅ `handlers.py`: vertical por defecto `"test"` → `"general"`
4. ✅ Tests: +2 en `test_bot.py` (ruta python_adapter + error en adapter Python no aborta búsqueda) → **196/196 verdes**
5. ✅ Commits: `4b7ad39` pusheado a GitHub y HF; Space `RUNNING` con sha `4b7ad39`

**Verificación en producción (datos REALES desde HF Spaces)**:
- ✅ `POST /api/search {"query":"iphone","vertical":"general"}` → **200 resultados reales**:
  - itencel: 50, revolico: **120**, timbirichi: 30, porlalivre: 0
- ✅ **Revolico funciona desde el datacenter** (objetivo central de la Sesión 8/9) — 120 items con el adapter Apollo SSR + buildID cache
- ✅ Verificación local idéntica vía `search_service.search()` (misma ruta que usa el bot)

**Archivos**: `bot/search_service.py`, `bot/telegram_bot.py`, `bot/handlers.py`, `tests/modulo_1/test_bot.py`, `MEMORIA.md`

**Pendiente nuevo**:
- [ ] `porlalivre` devuelve 0 en producción: sus selectores (Sesión 7) nunca se verificaron contra HTML real → inspeccionar y crear YAML correcto o marcar como no accesible → **Resuelto Sesión 11: sitio deshabilitado (vertical: disabled)**
- [ ] Los avisos de log "Error extrayendo campo 'imagen'" son cosméticos (item se conserva con imagen=None) — opcional: `required: false` en imagen de timbirichi/itencel para logs limpios → **Resuelto Sesión 11**
- [ ] **🎨 Rediseñar las tarjetas de resultados en la UI** (`gradio_app.py`): los colores de los textos no contrastan bien con el color de fondo de las tarjetas → legibilidad deficiente. Hay que hacerlo más elegante y organizado (paleta coherente, jerarquía visual clara: título/precio/sitio/ubicación, espaciado y bordes definidos)
- [ ] **📱 App móvil Android/iOS**: crear una app para que el usuario final pueda acceder al servicio desde su teléfono (consumir la API `/api/search` de HF Spaces; evaluar PWA con el HTML de Gradio como alternativa rápida antes de una app nativa; recordar restricción: sin USD/tarjetas, todo gratuito)

---

### Sesión 8 — 2026-08-03: Fix crítico deploy HF — UI NovaSearch ahora visible en producción

**Contexto**: El Space de HF llevaba días "desplegado" pero la raíz servía solo el HTML
simple de FastAPI ("Servicio de scraping activo"), NO la UI de NovaSearch. El usuario
no podía hacer una prueba real.

**Causa raíz (verificada con evidencia)**:
- `Dockerfile` ejecuta `uvicorn modulo_1_servicio.main:app`
- `main.py` **no montaba Gradio en ningún lado** — el README prometía "Gradio montado sobre FastAPI" pero el montaje no existía en el código desplegado
- `gradio_app.py` tenía `build_app()` lista para usar, pero nadie la llamaba en el entry point real

**Qué se hizo**:
1. ✅ Montada la UI sobre FastAPI en `main.py`:
   `app = gr.mount_gradio_app(app, build_app(), path="/")`
   - Raíz `/` sirve la UI NovaSearch; API sigue en `/api/*`, `/docs`, `/api/health`
2. ✅ `gradio>=6.0` en `modulo_1_servicio/requirements-hf.txt` (antes >=4.0)
3. ✅ Actualizado `test_root_endpoint` — ahora valida que la raíz sirve "NovaSearch" (antes esperaba el HTML viejo)
4. ✅ Tests: **166/166 pasando**
5. ✅ Desplegado: commit `a16a580` pusheado a HF (`1a722ef..a16a580`), Space reconstruido, `RUNNING`

**Verificación en producción (todo confirmado)**:
- ✅ Raíz → HTML Gradio 27KB con NovaSearch, Buscar, Categoría, Ayuda
- ✅ Búsqueda real por API de Gradio → "5 resultados para 'casa'" con tarjetas completas (precios, badges, contactos, enlaces tel: y "Ver oferta")
- ✅ `/api/health` → `{"status":"ok","version":"0.1.0"}`
- ✅ `/gradio_api/info` y `/docs` → 200

**Estado actual de la búsqueda**: modo demostración (DEMO_MODE) — resultados simulados.
El usuario pidió desactivar el modo demo y buscar datos reales. Pendiente para próxima sesión.

**Archivos modificados**:
- `modulo_1_servicio/main.py` — Montaje Gradio sobre FastAPI (fix crítico)
- `modulo_1_servicio/requirements-hf.txt` — gradio>=6.0
- `tests/modulo_1/test_api.py` — test_root_endpoint actualizado
- `MEMORIA.md` — Esta actualización

**Pendiente**:
- [ ] Desactivar DEMO_MODE: buscar datos reales de Revolico/PorlaLivre desde HF
- [ ] Nota: los sitios cubanos (revolico.cu, porlalivre.com) NO son accesibles desde la red de desarrollo (DNS falla). Verificar si son accesibles desde los datacenters de HF
- [ ] Investigar si el fallback silencioso a demo cuando falla el scraping real es deseable (actualmente engaña: muestra demo sin avisar claro)

---

### Sesión 7 — 2026-07-23: Website Gradio funcional + Adaptadores reales + Telegram Bot

**Contexto**: El usuario quiere un producto para Cuba, 100% gratuito (sin USD, sin tarjetas).
PySide6/QML se reemplaza por Gradio web (accesible desde cualquier navegador).

**Qué se hizo**:
1. ✅ **Website Gradio rediseñado** para usuario final (sin tecnicismos):
   - Interfaz simple: "¿Qué quieres buscar?" + categoría + botón Buscar
   - Resultados en tabla clara: # Título, Descripción, Precio, Sitio, Enlace
   - Pestaña de ayuda para el usuario
   - Datos demo (DEMO_MODE=1) para probar sin conexión a sitios reales
2. ✅ **Adaptadores reales creados**:
   - `adapters/revolico.yaml` — Revolico.cu (clasificados Cuba, 7 campos)
   - `adapters/porlalivre.yaml` — Porlalivre.com (clasificados Cuba, 7 campos)
   - Nota: Ambos sitios no accesibles desde esta red (DNS), funcionales desde Cuba
3. ✅ **Telegram Bot** creado (`modulo_1_servicio/bot/telegram_bot.py`):
   - Bot conversacional: usuario escribe query → bot busca en todos los adaptadores
   - Soporta comandos: /start, /help, /search, /sites
   - Sin librerías extra (usa httpx + Telegram Bot API)
   - Modo polling o webhook
4. ✅ **Git actualizado**: rebase exitoso con última versión de GitHub (commit c43ab3b)
5. ✅ **Conflictos resueltos**: multi-source services UI mantenida sobre HEAD

**Archivos creados/modificados**:
- `modulo_1_servicio/ui/gradio_app.py` — Reescrib: UI usuario final + modo demo
- `adapters/revolico.yaml` — Nuevo: adaptador Revolico
- `adapters/porlalivre.yaml` — Nuevo: adaptador Porlalivre
- `modulo_1_servicio/bot/__init__.py` — Nuevo: paquete bot
- `modulo_1_servicio/bot/telegram_bot.py` — Nuevo: bot de Telegram
- `modulo_1_servicio/scraping/models.py` — Limpieza (se revertió TELEGRAM source type)
- `MEMORIA.md` — Esta actualización

**Tests**: 118/118 pasando ✅ (sin cambios en tests)

**Pendiente**:
- [ ] Desplegar en HF Spaces y probar con acceso a sitios reales
- [ ] Crear adaptadores adicionales (Revolico específico por categoría)
- [ ] Telegram Bot: obtener token de @BotFather y probar end-to-end
- [ ] Integrar demo mode como feature toggle en vez de env var
- [ ] Escribir tests para gradio_app.py y telegram_bot.py

---

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

| # | Descripción | Estado |
|---|-------------|--------|
| 1 | `test_circular_rotation` flaky — `UARotator` arranca con índice aleatorio | ✅ Resuelto (Sesión 6) |
| 2 | `_to_float` no manejaba coma decimal europea (`€ 50,00`) | ✅ Resuelto (Sesión 6) |
| 3 | `_to_float` no limpiaba texto residual (`$ 25,000 MXN`) | ✅ Resuelto (Sesión 6) |
| 4 | Timbirichi: `?buscar=` no filtraba (devuelve homepage) | ✅ Resuelto (Sesión 9) — endpoint real `/buscar/pagina/{page}?q=` |
| 5 | Revolico: 403 anti-bot desde red local en Cuba | ⚠️ Comportamiento esperado — funciona desde datacenters (HF) |

---

## 📁 Archivos Estratégicos

| Archivo | Propósito |
|---------|-----------|
| `MEMORIA.md` | **Este archivo** — memoria persistente del proyecto |
| `CHECKPOINT.md` | Estado técnico detallado + instrucciones de prueba |
| `PROPUESTA.md` | Propuestas de producto y roadmap |
| `openspec/` | SDD (Spec-Driven Development) — cambios formales |

---

## 🚧 WIP: Cambios sin commitear

Sin cambios pendientes — todo commiteado y pusheado tras Sesión 11.

---

## ⚙️ Cómo Correr Tests

```powershell
# Todos los tests
python -m pytest tests/ -v --tb=short

# Tests específicos
python -m pytest tests/modulo_1/test_normalizer.py -v --tb=short
python -m pytest tests/modulo_1/test_anti_scraping.py -v --tb=short
```
