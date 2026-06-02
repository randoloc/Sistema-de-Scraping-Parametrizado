# URL Normalizer Specification

## Purpose

Normalizar URLs ingresadas por el usuario: agregar protocolo si falta, sanitizar formato, y validar estructura básica antes de enviarlas al extractor.

## Requirements

### Requirement: Auto-add HTTPS

The system MUST prepend `https://` to any URL that lacks a protocol scheme (`http://`, `https://`, `ftp://`).

#### Scenario: Missing protocol

- GIVEN a user provides the URL `revolico.com`
- WHEN the system normalizes it
- THEN it MUST return `https://revolico.com`

#### Scenario: Already has protocol

- GIVEN a user provides the URL `http://httpbin.org/html`
- WHEN the system normalizes it
- THEN it MUST return the URL unchanged

### Requirement: Sanitize whitespace

The system MUST strip leading/trailing whitespace from URLs before normalization.

#### Scenario: Leading whitespace

- GIVEN a user provides the URL `  https://example.com`
- WHEN the system normalizes it
- THEN it MUST return `https://example.com`

### Requirement: Invalid URL rejection

The system MUST raise an error for URLs that are empty, malformed, or contain invalid characters after normalization.

#### Scenario: Empty string

- GIVEN a user provides an empty URL
- WHEN the system normalizes it
- THEN it MUST raise a `ValueError`

### Requirement: Integration with scraping pipeline

The `BeautifulSoupExtractor.fetch_content` method MUST call `normalize_url()` on `config.source` before making the HTTP request.

#### Scenario: Normalized URL used for fetch

- GIVEN a scrape config with `source="revolico.com"`
- WHEN `fetch_content` is called
- THEN the HTTP request MUST be made to `https://revolico.com`
