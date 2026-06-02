# Anti-Scraping Specification

## Purpose

Mecanismos para evitar bloqueos por parte de sitios web: rotación de User-Agent, reintentos automáticos ante fallos transitorios, y delays configurables entre requests.

## Requirements

### Requirement: User-Agent rotation

The system MUST maintain a pool of at least 5 realistic User-Agent strings and rotate them on each HTTP request.

#### Scenario: UA rotation

- GIVEN the system makes 3 consecutive requests
- WHEN each request is inspected
- THEN each MUST have a different `User-Agent` header (unless pool exhausted)

### Requirement: Retry on transient errors

The system MUST retry failed requests up to 3 times with exponential backoff (1s, 2s, 4s) before raising an error.

#### Scenario: Retry succeeds

- GIVEN the first request to a site fails with a timeout
- AND the second request succeeds
- WHEN the fetch completes
- THEN the system MUST return the successful response
- AND MUST NOT raise an error

#### Scenario: Retry exhausted

- GIVEN all 3 requests to a site fail
- WHEN the fetch completes
- THEN the system MUST raise `ScraperConnectionError`

### Requirement: Configurable delay

The system SHOULD wait a configurable delay (default 1.0s) between consecutive requests to the same domain.

#### Scenario: Delay applied

- GIVEN the system scrapes 2 pages from the same domain
- WHEN the requests are timed
- THEN the interval between them MUST be at least 1.0s

### Requirement: Anti-scraping in fetch pipeline

`BeautifulSoupExtractor.fetch_content` MUST use the UA rotator and retry policy from `anti_scraping.py`.

#### Scenario: Integration

- GIVEN a scrape config with no custom headers
- WHEN `fetch_content` executes
- THEN it MUST use a rotated User-Agent from the pool
- AND MUST retry up to 3 times on transient errors
