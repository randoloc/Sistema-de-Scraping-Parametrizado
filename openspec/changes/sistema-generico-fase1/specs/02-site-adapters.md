# Site Adapters Specification

## Purpose

Definir configuraciones de scraping reutilizables en formato YAML. Cada adaptador describe un sitio web específico: URL base, selectores CSS para extraer datos, paginación, y parámetros de búsqueda. Los adaptadores se almacenan en `adapters/` y se cargan al iniciar el servicio.

## Requirements

### Requirement: YAML structure

A SiteAdapter MUST define at minimum: `name`, `site`, `vertical`, `search_url`, and at least one `field`.

#### Scenario: Valid adapter

- GIVEN a valid YAML adapter file with `name`, `site`, `vertical`, `search_url`, and `fields`
- WHEN the adapter loader parses it
- THEN it MUST return a validated `SiteAdapter` instance
- AND all fields MUST be available as Pydantic model attributes

### Requirement: Adapter directory loading

The `AdapterLoader` MUST scan the `adapters/` directory at startup and load all `.yaml`/`.yml` files.

#### Scenario: Load all adapters

- GIVEN the `adapters/` directory contains `mercadolibre.yaml` and `autocosmos.yaml`
- WHEN the loader scans the directory
- THEN it MUST return a list with 2 `SiteAdapter` instances

### Requirement: Field definition

Each adapter field MUST specify: `name` (string), `selector` (CSS selector string), and MAY specify: `type` (text|price|url|number|date|image), `transform` (optional transformation).

#### Scenario: Field with type

- GIVEN an adapter with field `{name: "precio", selector: "span.price", type: "price"}`
- WHEN the adapter is validated
- THEN `field.type` MUST equal `"price"`

### Requirement: Search URL templating

The `search_url` field MAY contain `{query}` and `{page}` template variables that get replaced at runtime.

#### Scenario: Query substitution

- GIVEN an adapter with `search_url: "https://example.com/search?q={query}"`
- WHEN search is invoked with `query="autos usados"`
- THEN the resulting URL MUST be `https://example.com/search?q=autos+usados`

### Requirement: API endpoint

The system MUST expose `GET /api/adapters` returning a JSON list of all loaded adapters (name, site, vertical, fields).

#### Scenario: List adapters

- GIVEN 2 adapters are loaded from `adapters/`
- WHEN a client calls `GET /api/adapters`
- THEN the response MUST be a JSON array with 2 items
- AND each item MUST contain `name`, `site`, `vertical`, and `fields`

### Requirement: Adapter search by vertical

The API MUST support filtering by vertical via `GET /api/adapters?vertical=cars`.

#### Scenario: Filter by vertical

- GIVEN adapters for verticals `cars` and `real_estate`
- WHEN a client calls `GET /api/adapters?vertical=cars`
- THEN the response MUST only include adapters with `vertical: cars`
