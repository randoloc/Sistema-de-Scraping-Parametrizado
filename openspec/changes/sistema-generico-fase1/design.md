# Design: Fase 1 — Base del Sistema Genérico

## URL Normalizer (`url_utils.py`)

```
modulo_1_servicio/scraping/url_utils.py
```

```python
from urllib.parse import urlparse, urlunparse

def normalize_url(url: str) -> str:
    """Agrega https:// si falta, sanitiza whitespace, valida."""
    url = url.strip()
    if not url:
        raise ValueError("URL cannot be empty")
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url
    # Re-parse to validate
    parsed = urlparse(url)
    if not parsed.netloc:
        raise ValueError(f"Invalid URL: {url}")
    return url
```

Llamado en `BeautifulSoupExtractor.fetch_content()` antes de `client.get()`.

## Site Adapters (`adapters/`)

### Modelo Pydantic

```
modulo_1_servicio/scraping/adapters/models.py
```

```python
from pydantic import BaseModel, Field
from typing import Optional

class AdapterField(BaseModel):
    name: str
    selector: str
    type: str = "text"
    transform: Optional[str] = None

class SiteAdapter(BaseModel):
    name: str
    site: str
    vertical: str
    search_url: str = Field(..., description="URL template with {query} and {page}")
    pagination: Optional[str] = None
    fields: list[AdapterField] = Field(min_length=1)
```

### Cargador de adaptadores

```
modulo_1_servicio/scraping/adapters/loader.py
```

- Escanea `adapters/` buscando `*.yaml`/`*.yml`
- Parsea con PyYAML, valida con `SiteAdapter.model_validate()`
- Expone `AdapterLoader.get_all()` y `AdapterLoader.get_by_vertical()`

### Directorio de adaptadores

```
adapters/
  example_httpbin.yaml    # Ejemplo didáctico
```

## Anti-Scraping (`anti_scraping.py`)

```
modulo_1_servicio/scraping/anti_scraping.py
```

### UARotator

- Pool de 5 User-Agents realistas (Chrome, Firefox, Edge, Safari variantes)
- `get_ua()` → rota secuencialmente (índice circular)

### RetryPolicy

```python
class RetryPolicy:
    max_retries: int = 3
    base_delay: float = 1.0  # seconds
    
    async def execute(self, func, *args, **kwargs):
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                if attempt == self.max_retries:
                    raise
                delay = self.base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
```

### DomainDelay

- `asyncio.Lock` + timestamp por dominio
- `wait_if_needed(domain)` → espera si fue < 1s desde último request

## Integración en el extractor

`BeautifulSoupExtractor.fetch_content()` modificado:

1. `config.source = normalize_url(config.source)`
2. `headers.setdefault("User-Agent", ua_rotator.get_ua())`
3. Llamar a `retry_policy.execute(client.get, ...)`
4. Aplicar `domain_delay.wait_if_needed(domain)` entre requests

## API Endpoint

En `routes_scrape.py`:

```python
@router.get("/api/adapters")
async def list_adapters(vertical: str | None = None):
    if vertical:
        return [a.model_dump() for a in loader.get_by_vertical(vertical)]
    return [a.model_dump() for a in loader.get_all()]
```
