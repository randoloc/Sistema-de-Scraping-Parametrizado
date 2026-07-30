"""Adaptador custom para Revolico (Next.js SPA).

Revolico es una app Next.js. La página de búsqueda carga anuncios vía JavaScript.
Los classnames de styled-components cambian con cada build, por lo que NO se
puede usar BS4 con selectores CSS.

En su lugar, este adaptador:
1. Extrae el buildID de la homepage (del script ``__NEXT_DATA__``)
2. Fetch el endpoint ``/_next/data/{buildID}/search.json?q={query}``
3. Parsea y normaliza los resultados al schema canónico
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

from modulo_1_servicio.scraping.normalizer import CanonicalItem

logger = logging.getLogger(__name__)

# User-Agent realista para evitar bloqueos
_DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

# Regex para extraer __NEXT_DATA__ del HTML
_NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
    re.DOTALL,
)


class RevolicoAdapterError(Exception):
    """Error base del adaptador Revolico."""


class BuildIDNotFoundError(RevolicoAdapterError):
    """No se pudo extraer el buildID de la homepage."""


class SearchResponseError(RevolicoAdapterError):
    """Error al parsear la respuesta de búsqueda."""


class RevolicoAdapter:
    """Adaptador custom para Revolico (Next.js SPA).

    Uso:
        async with RevolicoAdapter() as adapter:
            items = await adapter.search("iphone 15")
    """

    def __init__(
        self,
        base_url: str = "https://www.revolico.com",
        timeout: float = 15.0,
        user_agent: str = _DEFAULT_UA,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._user_agent = user_agent
        self._build_id: str | None = None
        self._http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={"User-Agent": user_agent},
            follow_redirects=True,
        )

    async def __aenter__(self) -> RevolicoAdapter:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Cierra el cliente HTTP subyacente."""
        await self._http_client.aclose()

    # ------------------------------------------------------------------
    # Build ID extraction
    # ------------------------------------------------------------------

    async def extract_build_id(self) -> str:
        """Fetch the homepage and extract the Next.js build ID.

        El resultado se cachea en ``self._build_id``. Llamadas sucesivas
        retornan el valor cacheado sin hacer otra petición HTTP.

        Returns:
            El build ID (string alfanumérico).

        Raises:
            BuildIDNotFoundError: si no puede extraer el buildID.
            httpx.HTTPError: si falla la petición HTTP.
        """
        if self._build_id is not None:
            return self._build_id

        logger.info("Extrayendo buildID desde %s", self.base_url)
        resp = await self._http_client.get(self.base_url)
        resp.raise_for_status()

        match = _NEXT_DATA_RE.search(resp.text)
        if not match:
            raise BuildIDNotFoundError(
                f"No se encontró __NEXT_DATA__ en {self.base_url}. "
                "Posible cambio en la estructura de Revolico."
            )

        try:
            data: dict[str, Any] = json.loads(match.group(1))
        except json.JSONDecodeError as exc:
            raise BuildIDNotFoundError(
                f"__NEXT_DATA__ no es JSON válido: {exc}"
            ) from exc

        build_id: str | None = data.get("buildId")
        if not build_id or not isinstance(build_id, str):
            raise BuildIDNotFoundError(
                f"buildId no encontrado en __NEXT_DATA__. "
                f"Keys disponibles: {list(data.keys())}"
            )

        self._build_id = build_id
        logger.info("buildID extraído: %s", build_id)
        return build_id

    async def _ensure_build_id(self) -> str:
        """Retorna el buildID, extrayéndolo si es necesario."""
        if self._build_id is None:
            self._build_id = await self.extract_build_id()
        return self._build_id

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def search(
        self,
        query: str,
        page: int = 1,
    ) -> list[CanonicalItem]:
        """Search Revolico and return normalized results.

        Args:
            query: Término de búsqueda.
            page: Número de página (empieza en 1).

        Returns:
            Lista de ``CanonicalItem`` con los resultados normalizados.
        """
        build_id = await self._ensure_build_id()
        endpoint = f"{self.base_url}/_next/data/{build_id}/search.json"
        params: dict[str, str] = {"q": query}
        if page > 1:
            params["page"] = str(page)

        logger.info("Fetching search.json: %s?q=%s (page=%d)", endpoint, query, page)
        resp = await self._http_client.get(endpoint, params=params)
        resp.raise_for_status()

        try:
            body: dict[str, Any] = resp.json()
        except json.JSONDecodeError as exc:
            raise SearchResponseError(
                f"Respuesta de búsqueda no es JSON válido: {exc}"
            ) from exc

        items = self._extract_items(body)
        logger.info("Parseados %d items de Revolico para q=%s", len(items), query)
        return items

    def _extract_items(self, body: dict[str, Any]) -> list[CanonicalItem]:
        """Extrae y normaliza los items del body de search.json.

        La estructura exacta de Revolico puede cambiar. Este método
        intenta varias rutas de acceso comunes en Next.js:
        - ``pageProps.items``
        - ``props.pageProps.items``
        - ``results``
        - ``ads``

        Sobrescribe este método si la estructura cambia.
        """
        page_props: dict[str, Any] | None = None

        # Intentar varias rutas comunes
        if "pageProps" in body:
            page_props = body["pageProps"]
        elif "props" in body and isinstance(body["props"], dict):
            page_props = body["props"].get("pageProps") or body["props"]
        elif "results" in body:
            page_props = {"items": body["results"]}
        elif "ads" in body:
            page_props = {"items": body["ads"]}

        if not page_props:
            raise SearchResponseError(
                "No se encontró pageProps en la respuesta. "
                f"Keys del body: {list(body.keys())}"
            )

        raw_items: list[dict[str, Any]] | None = None
        for key in ("items", "results", "ads", "listings"):
            candidate = page_props.get(key)
            if isinstance(candidate, list):
                raw_items = candidate
                break

        if raw_items is None:
            return []

        canonical_items: list[CanonicalItem] = []
        for i, raw in enumerate(raw_items):
            item = self._parse_item(raw, rank=i)
            if item is not None:
                canonical_items.append(item)

        return canonical_items

    def _parse_item(
        self,
        raw: dict[str, Any],
        rank: int = 0,
    ) -> CanonicalItem | None:
        """Convierte un item crudo de Revolico a CanonicalItem.

        Mapeo esperado (basado en estructura típica de clasificados):
        - title / titulo → title
        - description / descripcion / body → description
        - price / precio → price
        - currency / moneda → currency
        - url / slug / id → url (se completa con base_url si es relativo)
        - image / images[0] / main_image / imagen → image_url
        - created_at / date / fecha / publicado → date
        - location / ubicacion / provincia → location

        Si el item no tiene title, se omite (no es un resultado válido).
        """
        if not isinstance(raw, dict):
            return None

        title = self._get_str(raw, "title", "titulo")
        if not title:
            return None

        description = self._get_str(raw, "description", "descripcion", "body")
        price = self._get_price(raw)
        currency = self._get_str(raw, "currency", "moneda") or "USD"
        url = self._build_url(raw)
        image_url = self._get_image(raw)
        date = self._get_str(
            raw, "created_at", "date", "fecha", "publicado", "createdAt"
        )
        location = self._get_str(raw, "location", "ubicacion", "provincia", "city")

        return CanonicalItem(
            title=title,
            description=description,
            price=price,
            currency=currency,
            url=url,
            image_url=image_url,
            date=date,
            location=location,
            source_site="revolico",
            source_url=url or f"{self.base_url}/search?q=",
            rank=rank,
            raw_data=raw,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_str(raw: dict[str, Any], *keys: str) -> str | None:
        """Retorna el primer valor string encontrado para las keys dadas."""
        for key in keys:
            val = raw.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
            if isinstance(val, (int, float)):
                return str(val)
        return None

    @staticmethod
    def _get_price(raw: dict[str, Any]) -> float | None:
        """Extrae el precio numérico desde varias keys posibles."""
        import re as _re_price

        for key in ("price", "precio", "amount", "monto", "price_cuc", "price_usd"):
            val = raw.get(key)
            if val is None:
                continue
            if isinstance(val, (int, float)):
                return float(val)
            if isinstance(val, str):
                cleaned = _re_price.sub(r"[^\d.,-]", "", val)
                cleaned = cleaned.replace(",", "")
                try:
                    return float(cleaned) if cleaned else None
                except ValueError:
                    continue
        return None

    def _build_url(self, raw: dict[str, Any]) -> str | None:
        """Construye la URL absoluta del anuncio."""
        url = self._get_str(raw, "url", "slug", "link", "permalink")
        if url is None:
            item_id = self._get_str(raw, "id", "itemId", "ad_id", "listing_id")
            if item_id:
                url = f"/anuncio/{item_id}"
            else:
                return None

        if url.startswith("/"):
            url = f"{self.base_url}{url}"
        return url

    @staticmethod
    def _get_image(raw: dict[str, Any]) -> str | None:
        """Extrae la primera URL de imagen disponible."""
        # Campos directos
        for key in ("image", "imagen", "main_image", "image_url", "thumbnail", "photo"):
            val = raw.get(key)
            if isinstance(val, str) and val.startswith(("http://", "https://", "/")):
                return val

        # Lista de imágenes
        for key in ("images", "imagenes", "photos", "pictures", "gallery"):
            imgs = raw.get(key)
            if isinstance(imgs, list) and imgs:
                first = imgs[0]
                if isinstance(first, str):
                    return first
                if isinstance(first, dict):
                    for img_key in ("url", "src", "path", "thumbnail", "full"):
                        val = first.get(img_key)
                        if isinstance(val, str):
                            return val
        return None
