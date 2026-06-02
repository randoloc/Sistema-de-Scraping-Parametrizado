# Tasks: Fase 1 — Base del Sistema Genérico

## Infrastructure

- [x] 1.1 Crear `modulo_1_servicio/scraping/url_utils.py` con `normalize_url()`
- [x] 1.2 Crear `modulo_1_servicio/scraping/anti_scraping.py` con `UARotator`, `RetryPolicy`, `DomainDelay`
- [x] 1.3 Crear `modulo_1_servicio/scraping/adapters/__init__.py`
- [x] 1.4 Crear `modulo_1_servicio/scraping/adapters/models.py` con `SiteAdapter`, `AdapterField`
- [x] 1.5 Crear `modulo_1_servicio/scraping/adapters/loader.py` con `AdapterLoader`
- [x] 1.6 Crear `adapters/example_httpbin.yaml` (adaptador de ejemplo)
- [x] 1.7 Modificar `BeautifulSoupExtractor.fetch_content()` para integrar URL normalization + anti-scraping

## Implementation

- [x] 1.8 Agregar endpoint `GET /api/adapters` en `routes_scrape.py`
- [x] 1.9 Inicializar adapter loader en startup del FastAPI

## Testing

- [x] 1.10 Tests para `normalize_url()` — 9 tests en `tests/modulo_1/test_url_utils.py`
- [x] 1.11 Tests para `UARotator` — 5 tests en `tests/modulo_1/test_anti_scraping.py`
- [x] 1.12 Tests para `RetryPolicy` — 4 tests en `tests/modulo_1/test_anti_scraping.py`
- [x] 1.13 Tests para `AdapterLoader` — 9 tests en `tests/modulo_1/test_adapter_loader.py`
- [x] 1.14 Tests para endpoint `/api/adapters` — 4 tests en `tests/modulo_1/test_api.py`
- [x] 1.15 Verificar tests existentes siguen pasando — **96 tests, 0 fallas**
