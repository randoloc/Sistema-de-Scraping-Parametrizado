# Proposal: Fase 1 — Base del Sistema Genérico de Búsqueda

## Intent

El sistema actual requiere URL + selectores CSS manuales. Necesitamos una capa de abstracción que permita definir PLANTILLAS de scraping reutilizables (adaptadores YAML), normalice URLs automáticamente, y maneje anti-scraping básico. Sin esto, el usuario siempre debe conocer la estructura interna de cada sitio web.

## Scope

### In Scope
- URL normalizer: agrega `https://` si falta protocolo
- Sistema de SiteAdapters: definición YAML de sitios (URL base, selectores, paginación)
- Cargador de adaptadores desde directorio `adapters/`
- Anti-scraping básico: retry (3 intentos), User-Agent rotativo (pool de 5 UAs), delay configurable entre requests
- Modificar `BeautifulSoupExtractor.fetch_content` para usar el nuevo sistema
- Endpoint API `/api/adapters` para listar adaptadores disponibles
- Tests para todas las nuevas funcionalidades

### Out of Scope
- Intérprete de consultas en lenguaje natural (Fase 3)
- Normalizador de resultados a schema canónico (Fase 2)
- Biblioteca de adaptadores para sitios reales (Fase 2)
- Cambios en la GUI (Fase 4)
- WhatsApp delivery (no se toca)

## Capabilities

### New Capabilities
- `site-adapters`: Definición YAML de scraping configs reutilizables por sitio
- `url-normalizer`: Corrección automática de URLs (protocolo, saneamiento)
- `anti-scraping`: Retry, User-Agent rotativo, delays configurables

### Modified Capabilities
- None (cambios son internos al scraping engine, no afectan specs previas)

## Approach

1. Crear `modulo_1_servicio/scraping/adapters/` con: `SiteAdapter` (modelo Pydantic), `AdapterLoader` (carga YAML), pool de adaptadores
2. Crear `modulo_1_servicio/scraping/anti_scraping.py` con: `UARotator`, `RetryPolicy`
3. Crear `modulo_1_servicio/scraping/url_utils.py` con: `normalize_url()`
4. Modificar `BeautifulSoupExtractor.fetch_content()` para integrar anti-scraping
5. Exponer `/api/adapters` GET en routes_scrape.py
6. Escribir tests unitarios para cada componente

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `modulo_1_servicio/scraping/adapters/` | New | SiteAdapter model + YAML loader + pool |
| `modulo_1_servicio/scraping/anti_scraping.py` | New | UA rotation, retry policy |
| `modulo_1_servicio/scraping/url_utils.py` | New | URL normalization |
| `modulo_1_servicio/scraping/extractors/beautifulsoup_extractor.py` | Modified | Integrar anti-scraping + URL normalization |
| `modulo_1_servicio/api/routes_scrape.py` | Modified | Nuevo endpoint /api/adapters |
| `adapters/` | New | Directorio con ejemplos de adaptadores YAML |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Cambios en fetch_content rompen scraping existente | Low | Tests de integración existentes verifican comportamiento |
| YAML parsing de adaptadores inválidos | Low | Pydantic valida schema; tests cubren casos borde |
| Anti-scraping muy agresivo o muy lento | Med | Configurable por adaptador (retry, delay como defaults sensatos) |

## Rollback Plan

Revertir commit de la fase. Si solo falla un componente (ej. adapters), el motor de scraping sigue funcionando sin cambios — `fetch_content` usa defaults si no hay adaptadores cargados.

## Dependencies

- PyYAML (ya instalado vía `modulo_1_servicio/config/schema.py`)
- Ninguna externa nueva

## Success Criteria

- [ ] `normalize_url("revolico.com")` → `"https://revolico.com"`
- [ ] Adaptador YAML se carga y valida correctamente
- [ ] `fetch_content` retry funciona: 3 intentos con UA rotativo
- [ ] `GET /api/adapters` lista adaptadores disponibles
- [ ] Tests existentes de scraping siguen pasando (regresión)
- [ ] Tests nuevos cubren URL normalizer, adapters, anti-scraping
