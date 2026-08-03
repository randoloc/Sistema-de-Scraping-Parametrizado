"""Adaptador custom para Revolico (Next.js + Apollo GraphQL).

Revolico es una app Next.js. La página de búsqueda carga anuncios vía JavaScript.

Historia de formatos (IMPORTANTE):
- Antes: ``/_next/data/{buildId}/search.json`` devolvía JSON puro con ``pageProps.items``.
- AHORA (2026): ese mismo endpoint devuelve **HTML SSR** cuyo bloque
  ``__NEXT_DATA__`` contiene ``props.pageProps.__APOLLO_STATE__`` (GraphQL).
  Los anuncios viven en claves ``AdType:{id}``.

Este adaptador maneja AMBOS formatos:
1. Si la respuesta es JSON puro → ruta clásica ``pageProps.items``.
2. Si es HTML SSR → parsea ``__NEXT_DATA__`` y extrae los ``AdType:*``.

Datos reales por anuncio (clave ``AdType:{id}``):
- title, price, currency, permalink, mainImage.gcsKey
- provinceId, municipalityId → nombres en ``ProvinceType:{id}`` / ``MunicipalityType:{id}``
- updatedOnToOrder (fecha), contactInfo, viewCount, isPromoted

Imagen: ``https://pic.revolico.com/{gcsKey}_item_photo_desktop.jpg``
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
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

# Base de imágenes de Revolico
_PIC_BASE = "https://pic.revolico.com"

# Cache persistente del buildId (evita re-fetch de la homepage por búsqueda)
_DEFAULT_CACHE_DIR = Path(__file__).resolve().parent / ".cache"
_BUILD_ID_CACHE_FILE = "revolico_build_id.txt"


class RevolicoAdapterError(Exception):
    """Error base del adaptador Revolico."""


class BuildIDNotFoundError(RevolicoAdapterError):
    """No se pudo extraer el buildID."""


class SearchResponseError(RevolicoAdapterError):
    """Error al parsear la respuesta de búsqueda."""


class RevolicoAdapter:
    """Adaptador custom para Revolico (Next.js + Apollo GraphQL).

    Uso:
        async with RevolicoAdapter() as adapter:
            items = await adapter.search("iphone 15")
    """

    def __init__(
        self,
        base_url: str = "https://www.revolico.com",
        timeout: float = 20.0,
        user_agent: str = _DEFAULT_UA,
        cache_dir: str | Path | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._user_agent = user_agent
        self._build_id: str | None = None
        self._cache_dir = Path(cache_dir) if cache_dir else _DEFAULT_CACHE_DIR
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
        """Extrae el build ID de Next.js.

        Estrategia en orden:
        1. Memoria (``self._build_id``).
        2. Cache persistente en disco (evita re-fetch por búsqueda).
        3. Homepage (funciona desde datacenters).
        4. Página de búsqueda ``/search?q=`` (fallback).
        """
        if self._build_id is not None:
            return self._build_id

        # 2) Cache persistente
        cached = self._load_build_id_cache()
        if cached:
            self._build_id = cached
            logger.info("buildID usado del cache: %s", cached)
            return cached

        # 3) Homepage
        try:
            logger.info("Extrayendo buildID desde %s", self.base_url)
            resp = await self._http_client.get(self.base_url)
            resp.raise_for_status()
            build_id = self._parse_build_id(resp.text, self.base_url)
            self._save_build_id_cache(build_id)
            self._build_id = build_id
            logger.info("buildID extraído de homepage: %s", build_id)
            return build_id
        except (httpx.HTTPStatusError, httpx.RequestError, BuildIDNotFoundError) as exc:
            logger.warning("Homepage no disponible (%s) — intentando /search", exc)

        # 4) Página de búsqueda
        search_url = f"{self.base_url}/search?q="
        resp = await self._http_client.get(search_url)
        resp.raise_for_status()
        build_id = self._parse_build_id(resp.text, search_url)
        self._save_build_id_cache(build_id)
        self._build_id = build_id
        logger.info("buildID extraído de página de búsqueda: %s", build_id)
        return build_id

    # ------------------------------------------------------------------
    # Cache persistente del build ID
    # ------------------------------------------------------------------

    def _load_build_id_cache(self) -> str | None:
        """Lee el buildId desde el cache en disco si existe."""
        try:
            path = self._cache_dir / _BUILD_ID_CACHE_FILE
            if path.exists():
                value = path.read_text(encoding="utf-8").strip()
                if value:
                    logger.info("buildID cargado de disco: %s", value)
                    return value
        except OSError as exc:
            logger.warning("No se pudo leer cache de buildID: %s", exc)
        return None

    def _save_build_id_cache(self, build_id: str) -> None:
        """Persiste el buildId en disco para reutilizarlo entre búsquedas."""
        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            path = self._cache_dir / _BUILD_ID_CACHE_FILE
            path.write_text(build_id, encoding="utf-8")
            logger.info("buildID persistido en disco: %s", build_id)
        except OSError as exc:
            logger.warning("No se pudo guardar cache de buildID: %s", exc)

    @staticmethod
    def _parse_build_id(text: str, source: str) -> str:
        """Extrae el buildId de un HTML con ``__NEXT_DATA__``."""
        match = _NEXT_DATA_RE.search(text)
        if not match:
            raise BuildIDNotFoundError(
                f"No se encontró __NEXT_DATA__ en {source}. "
                "Posible cambio en la estructura de Revolico o bloqueo (403 anti-bot)."
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
        """Search Revolico and return normalized results."""
        build_id = await self._ensure_build_id()
        endpoint = f"{self.base_url}/_next/data/{build_id}/search.json"
        params: dict[str, str] = {"q": query}
        if page > 1:
            params["page"] = str(page)

        logger.info("Fetching search.json: %s?q=%s (page=%d)", endpoint, query, page)
        resp = await self._http_client.get(endpoint, params=params)
        resp.raise_for_status()

        page_data = self._parse_response(resp)
        items = self._extract_items(page_data)
        logger.info("Parseados %d items de Revolico para q=%s", len(items), query)
        return items

    def _parse_response(self, resp: httpx.Response) -> dict[str, Any]:
        """Interpreta la respuesta como JSON puro o como HTML SSR.

        Returns:
            Un dict con los datos de la página: pageProps (que puede incluir
            ``__APOLLO_STATE__``) o la estructura clásica ``items``.
        """
        text = resp.text
        ctype = resp.headers.get("content-type", "")

        # Caso 1: JSON puro (formato anterior)
        if "json" in ctype or not text.lstrip().startswith("<"):
            try:
                body: dict[str, Any] = resp.json()
            except json.JSONDecodeError as exc:
                raise SearchResponseError(
                    f"Respuesta de búsqueda no es JSON válido: {exc}"
                ) from exc
            return self._locate_page_props(body, raw=body)

        # Caso 2: HTML SSR con __NEXT_DATA__
        match = _NEXT_DATA_RE.search(text)
        if not match:
            raise SearchResponseError(
                "La respuesta de búsqueda es HTML pero no contiene __NEXT_DATA__ "
                "(posible bloqueo anti-bot)."
            )
        try:
            data: dict[str, Any] = json.loads(match.group(1))
        except json.JSONDecodeError as exc:
            raise SearchResponseError(
                f"__NEXT_DATA__ HTML no es JSON válido: {exc}"
            ) from exc
        return self._extract_page_props_from_next(data)

    @staticmethod
    def _locate_page_props(
        body: dict[str, Any], raw: Any = None
    ) -> dict[str, Any]:
        """Localiza el dict pageProps en un JSON (formato clásico)."""
        page_props: dict[str, Any] | None = None
        if "pageProps" in body:
            page_props = body["pageProps"]
        elif "props" in body and isinstance(body["props"], dict):
            page_props = body["props"].get("pageProps") or body["props"]
        elif "results" in body:
            page_props = {"items": body["results"]}
        elif "ads" in body:
            page_props = {"items": body["ads"]}
        if page_props is None:
            raise SearchResponseError(
                "No se encontró pageProps en la respuesta. "
                f"Keys del body: {list(body.keys())}"
            )
        return page_props

    @staticmethod
    def _extract_page_props_from_next(data: dict[str, Any]) -> dict[str, Any]:
        """Extrae pageProps desde el JSON de __NEXT_DATA__ (SSR)."""
        props = data.get("props", {})
        page_props = props.get("pageProps") if isinstance(props, dict) else None
        if not isinstance(page_props, dict):
            page_props = data.get("pageProps")
        if not isinstance(page_props, dict):
            raise SearchResponseError(
                "No se encontró pageProps en __NEXT_DATA__. "
                f"Keys del __NEXT_DATA__: {list(data.keys())}"
            )
        return page_props

    def _extract_items(self, page_data: dict[str, Any]) -> list[CanonicalItem]:
        """Extrae los anuncios del page_data (Apollo o lista clásica).

        Formato nuevo real: ``pageProps.__APOLLO_STATE__`` con claves
        ``AdType:{id}`` y ``ProvinceType``/``MunicipalityType`` de referencia.
        """
        apollo = page_data.get("__APOLLO_STATE__")
        if isinstance(apollo, dict):
            ads = [
                (k, v)
                for k, v in apollo.items()
                if isinstance(v, dict) and v.get("__typename") == "AdType"
            ]
            # Orden estable por clave para resultados consistentes
            ads.sort(key=lambda kv: kv[0])
            canonical: list[CanonicalItem] = []
            for i, (key, raw) in enumerate(ads):
                item = self._parse_item(raw, rank=i, apollo=apollo)
                if item is not None:
                    canonical.append(item)
            return canonical

        # Formato clásico: lista items/results/ads en pageProps
        raw_items: list[dict[str, Any]] | None = None
        for key in ("items", "results", "ads", "listings"):
            candidate = page_data.get(key)
            if isinstance(candidate, list):
                raw_items = candidate
                break
        if raw_items is None:
            return []

        canonical = []
        for i, raw in enumerate(raw_items):
            item = self._parse_item(raw, rank=i)
            if item is not None:
                canonical.append(item)
        return canonical

    def _parse_item(
        self,
        raw: dict[str, Any],
        rank: int = 0,
        apollo: dict[str, Any] | None = None,
    ) -> CanonicalItem | None:
        """Convierte un item de Revolico (AdType o clásico) a CanonicalItem.

        AdType real:
        - title, price, currency, permalink, mainImage.gcsKey
        - provinceId / municipalityId → nombres vía apollo
        - updatedOnToOrder, contactInfo
        """
        if not isinstance(raw, dict):
            return None

        title = self._get_str(raw, "title", "titulo")
        if not title:
            return None

        description = self._get_str(raw, "description", "descripcion", "body")
        price = self._get_price(raw)
        currency = self._get_str(raw, "currency", "moneda") or self._infer_currency(raw) or "USD"
        url = self._build_url(raw)
        image_url = self._get_image(raw)
        date = self._get_str(
            raw, "updatedOnToOrder", "created_at", "date", "fecha", "publicado", "createdAt"
        )
        location = self._get_location(raw, apollo)

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

    def _get_location(
        self, raw: dict[str, Any], apollo: dict[str, Any] | None
    ) -> str | None:
        """Resuelve la ubicación; string directo o por provinceId/municipalityId."""
        direct = self._get_str(
            raw, "location", "ubicacion", "city", "provincia", "province_name"
        )
        if direct:
            return direct

        prov_id = self._get_str(raw, "provinceId", "provincia_id", "province")
        mun_id = self._get_str(raw, "municipalityId", "municipalidad_id")

        if not apollo:
            if prov_id:
                return self._get_str(raw, "provincia", "province_name") or prov_id
            return None

        prov_name = mun_name = None
        if prov_id:
            p = apollo.get(f"ProvinceType:{prov_id}")
            if isinstance(p, dict):
                prov_name = p.get("name")
        if mun_id:
            m = apollo.get(f"MunicipalityType:{mun_id}")
            if isinstance(m, dict):
                mun_name = m.get("name")

        if mun_name and prov_name:
            return f"{mun_name}, {prov_name}"
        if mun_name:
            return mun_name
        if prov_name:
            return prov_name
        return None

    @staticmethod
    def _infer_currency(raw: dict[str, Any]) -> str | None:
        """Deduce la moneda del precio si no viene explícita."""
        for key in ("price", "price_usd", "price_cup", "monto"):
            val = raw.get(key)
            if isinstance(val, str) and "CUP" in val.upper():
                return "CUP"
            if isinstance(val, str) and "USD" in val.upper():
                return "USD"
        return None

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
        url = self._get_str(raw, "permalink", "url", "slug", "link", "adUrl")
        if url is None:
            item_id = self._get_str(raw, "id", "itemId", "ad_id", "listing_id")
            if item_id:
                url = f"/item/{item_id}"
            else:
                return None

        if url.startswith("/"):
            url = f"{self.base_url}{url}"
        return url

    def _get_image(self, raw: dict[str, Any]) -> str | None:
        """Extrae la primera URL de imagen disponible.

        Soporta el formato Apollo moderno (``mainImage.gcsKey``) y el clásico.
        """
        # Apollo: mainImage = {"gcsKey": "pics/hash"}
        main_image = raw.get("mainImage") or raw.get("coverImage")
        if isinstance(main_image, dict):
            gcs = main_image.get("gcsKey") or main_image.get("key") or main_image.get("path")
            if isinstance(gcs, str) and gcs:
                return f"{_PIC_BASE}/{gcs}_item_photo_desktop.jpg"

        # Campos directos
        for key in ("image", "imagen", "main_image", "image_url", "thumbnail", "photo", "pic"):
            val = raw.get(key)
            if isinstance(val, str) and val.startswith(("http://", "https://", "/")):
                if val.startswith("/"):
                    return f"{_PIC_BASE}{val}"
                return val

        # Lista de imágenes
        for key in ("images", "imagenes", "photos", "pictures", "gallery"):
            imgs = raw.get(key)
            if isinstance(imgs, list) and imgs:
                first = imgs[0]
                if isinstance(first, str):
                    return first
                if isinstance(first, dict):
                    for img_key in ("url", "src", "path", "gcsKey", "thumbnail", "full"):
                        val = first.get(img_key)
                        if isinstance(val, str):
                            if img_key == "gcsKey":
                                return f"{_PIC_BASE}/{val}"
                            return val
        return None
