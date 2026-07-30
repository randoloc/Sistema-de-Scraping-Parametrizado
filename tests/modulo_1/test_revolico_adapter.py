"""Tests para el adaptador Revolico (mocked httpx, sin requests reales)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from modulo_1_servicio.scraping.adapters.revolico_adapter import (
    BuildIDNotFoundError,
    RevolicoAdapter,
    SearchResponseError,
)
from modulo_1_servicio.scraping.normalizer import CanonicalItem


# ── Helpers ──────────────────────────────────────────────────────────


def _mock_response(
    text: str = "",
    json_data: dict | None = None,
    status: int = 200,
) -> Mock:
    """Crea un Mock con la interfaz de httpx.Response.

    Args:
        text: HTML/text response body.
        json_data: Si se provee, ``.json()`` retorna esto.
        status: Código HTTP.
    """
    resp = Mock(spec=httpx.Response)
    resp.text = text
    resp.status_code = status

    if json_data is not None:
        resp.json = Mock(return_value=json_data)
    else:
        resp.json = Mock(side_effect=json.JSONDecodeError("No JSON", "", 0))

    resp.raise_for_status = Mock()
    if status >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            f"HTTP {status}", request=Mock(), response=resp
        )
    return resp


# Guardar referencia a la clase real antes de cualquier patch
_RealAsyncClient = httpx.AsyncClient


@pytest.fixture
def mock_http_client() -> AsyncMock:
    """Patcha httpx.AsyncClient para que devuelva un mock en lugar de hacer
    requests reales.

    Uso:
        mock_client.get.return_value = _mock_response(text="...")
        adapter = RevolicoAdapter()
        await adapter.extract_build_id()  # usa mock_client
    """
    with patch(
        "modulo_1_servicio.scraping.adapters.revolico_adapter.httpx.AsyncClient"
    ) as mock_cls:
        client = AsyncMock(spec=_RealAsyncClient)
        mock_cls.return_value = client
        yield client


# ── Tests: extract_build_id ──────────────────────────────────────────


class TestExtractBuildID:
    """Extracción del buildID desde la homepage de Revolico."""

    HOMEPAGE_WITH_BUILD = """<html>
<head></head>
<body>
<script id="__NEXT_DATA__" type="application/json">
{"buildId": "abc123xyz", "page": "/", "props": {}}
</script>
</body>
</html>"""

    async def test_success(self, mock_http_client: AsyncMock) -> None:
        """Extrae el buildID correctamente del script __NEXT_DATA__."""
        mock_http_client.get.return_value = _mock_response(
            text=self.HOMEPAGE_WITH_BUILD
        )

        adapter = RevolicoAdapter()
        build_id = await adapter.extract_build_id()

        assert build_id == "abc123xyz"
        assert adapter._build_id == "abc123xyz"
        mock_http_client.get.assert_awaited_once_with(
            "https://www.revolico.com"
        )

    async def test_no_next_data_script(self, mock_http_client: AsyncMock) -> None:
        """HTML sin __NEXT_DATA__ lanza BuildIDNotFoundError."""
        mock_http_client.get.return_value = _mock_response(
            text="<html><body>Sin datos</body></html>"
        )

        adapter = RevolicoAdapter()
        with pytest.raises(BuildIDNotFoundError, match="__NEXT_DATA__"):
            await adapter.extract_build_id()

    async def test_missing_build_id_key(self, mock_http_client: AsyncMock) -> None:
        """__NEXT_DATA__ sin clave ``buildId`` lanza BuildIDNotFoundError."""
        html = """<script id="__NEXT_DATA__" type="application/json">
{"page": "/", "props": {}}
</script>"""
        mock_http_client.get.return_value = _mock_response(text=html)

        adapter = RevolicoAdapter()
        with pytest.raises(BuildIDNotFoundError, match="buildId"):
            await adapter.extract_build_id()

    async def test_invalid_json_in_script(self, mock_http_client: AsyncMock) -> None:
        """__NEXT_DATA__ con contenido no-JSON lanza BuildIDNotFoundError."""
        html = """<script id="__NEXT_DATA__" type="application/json">
not-valid-json
</script>"""
        mock_http_client.get.return_value = _mock_response(text=html)

        adapter = RevolicoAdapter()
        with pytest.raises(BuildIDNotFoundError, match="JSON"):
            await adapter.extract_build_id()

    async def test_http_error(self, mock_http_client: AsyncMock) -> None:
        """Error HTTP al fetchear la homepage se propaga."""
        mock_http_client.get.return_value = _mock_response(status=500)

        adapter = RevolicoAdapter()
        with pytest.raises(httpx.HTTPStatusError):
            await adapter.extract_build_id()


# ── Tests: search ────────────────────────────────────────────────────


class TestSearch:
    """Búsqueda de anuncios en Revolico."""

    MOCK_ITEMS: list[dict] = [
        {
            "title": "iPhone 15 Pro Max 256GB",
            "description": "Teléfono en excelente estado, color titanio natural",
            "price": 1200,
            "currency": "USD",
            "url": "/anuncio/12345/iphone-15-pro-max",
            "images": ["https://img.revolico.com/iphone.jpg"],
            "created_at": "2024-06-15T10:00:00Z",
            "location": "La Habana",
        },
        {
            "title": "Samsung Galaxy S24 Ultra",
            "description": "Nuevo en caja, 512GB",
            "price": 800.50,
            "currency": "USD",
            "url": "/anuncio/67890/samsung-s24",
            "images": ["https://img.revolico.com/samsung.jpg"],
            "created_at": "2024-06-14T15:30:00Z",
            "location": "Santiago de Cuba",
        },
    ]

    HOMEPAGE = """<script id="__NEXT_DATA__" type="application/json">
{"buildId": "test-build-001"}
</script>"""

    async def _make_adapter(
        self, mock_client: AsyncMock
    ) -> RevolicoAdapter:
        """Crea adapter con buildID ya extraído para tests de search."""
        mock_client.get.return_value = _mock_response(text=self.HOMEPAGE)
        adapter = RevolicoAdapter()
        await adapter.extract_build_id()
        return adapter

    async def test_search_returns_canonical_items(
        self, mock_http_client: AsyncMock
    ) -> None:
        """Búsqueda exitosa retorna lista de CanonicalItem correctamente mapeados."""
        adapter = await self._make_adapter(mock_http_client)
        mock_http_client.get.reset_mock()

        mock_http_client.get.return_value = _mock_response(
            json_data={"pageProps": {"items": self.MOCK_ITEMS}}
        )

        items = await adapter.search("iphone")

        assert len(items) == 2
        assert all(isinstance(i, CanonicalItem) for i in items)

        first = items[0]
        assert first.title == "iPhone 15 Pro Max 256GB"
        assert first.description == "Teléfono en excelente estado, color titanio natural"
        assert first.price == 1200.0
        assert first.currency == "USD"
        assert first.url == "https://www.revolico.com/anuncio/12345/iphone-15-pro-max"
        assert first.image_url == "https://img.revolico.com/iphone.jpg"
        assert first.date == "2024-06-15T10:00:00Z"
        assert first.location == "La Habana"
        assert first.source_site == "revolico"
        assert first.rank == 0
        assert first.raw_data == self.MOCK_ITEMS[0]

        second = items[1]
        assert second.title == "Samsung Galaxy S24 Ultra"
        assert second.price == 800.50
        assert second.location == "Santiago de Cuba"
        assert second.rank == 1

    async def test_search_empty_results(
        self, mock_http_client: AsyncMock
    ) -> None:
        """Búsqueda sin resultados retorna lista vacía."""
        adapter = await self._make_adapter(mock_http_client)
        mock_http_client.get.reset_mock()

        mock_http_client.get.return_value = _mock_response(
            json_data={"pageProps": {"items": []}}
        )

        items = await adapter.search("zzzznotfound")
        assert items == []

    async def test_search_calls_correct_endpoint(
        self, mock_http_client: AsyncMock
    ) -> None:
        """Verifica que search() fetchea el endpoint correcto de Next.js."""
        adapter = await self._make_adapter(mock_http_client)
        mock_http_client.get.reset_mock()

        mock_http_client.get.return_value = _mock_response(
            json_data={"pageProps": {"items": [{"title": "Item"}]}}
        )

        await adapter.search("laptop", page=2)

        # Verificar URL y params
        call_args = mock_http_client.get.call_args
        assert call_args is not None
        url = call_args[0][0]
        params = call_args[1].get("params", {})
        assert "/_next/data/test-build-001/search.json" in url
        assert params.get("q") == "laptop"
        assert params.get("page") == "2"

    async def test_search_missing_page_props(
        self, mock_http_client: AsyncMock
    ) -> None:
        """Respuesta sin ``pageProps`` lanza SearchResponseError."""
        adapter = await self._make_adapter(mock_http_client)
        mock_http_client.get.reset_mock()

        mock_http_client.get.return_value = _mock_response(
            json_data={"notFound": True}
        )

        with pytest.raises(SearchResponseError, match="pageProps"):
            await adapter.search("iphone")

    async def test_search_invalid_json(
        self, mock_http_client: AsyncMock
    ) -> None:
        """Respuesta no-JSON lanza SearchResponseError."""
        adapter = await self._make_adapter(mock_http_client)
        mock_http_client.get.reset_mock()

        mock_http_client.get.return_value = _mock_response(text="not json at all")

        with pytest.raises(SearchResponseError, match="JSON"):
            await adapter.search("iphone")

    async def test_search_http_error(
        self, mock_http_client: AsyncMock
    ) -> None:
        """HTTP error en search se propaga."""
        adapter = await self._make_adapter(mock_http_client)
        mock_http_client.get.reset_mock()

        mock_http_client.get.return_value = _mock_response(status=503)

        with pytest.raises(httpx.HTTPStatusError):
            await adapter.search("iphone")

    async def test_search_auto_extracts_build_id(
        self, mock_http_client: AsyncMock
    ) -> None:
        """search() extrae buildID automáticamente si no se ha llamado antes."""
        homepage = """<script id="__NEXT_DATA__" type="application/json">
{"buildId": "auto-build"}
</script>"""
        search_json = {"pageProps": {"items": [{"title": "Auto Test"}]}}

        mock_http_client.get.side_effect = [
            _mock_response(text=homepage),
            _mock_response(json_data=search_json),
        ]

        adapter = RevolicoAdapter()
        items = await adapter.search("test")

        assert len(items) == 1
        assert items[0].title == "Auto Test"
        assert mock_http_client.get.await_count == 2

    async def test_search_with_alternative_fields(
        self, mock_http_client: AsyncMock
    ) -> None:
        """Items con nombres de campo alternativos (español) se mapean igual."""
        adapter = await self._make_adapter(mock_http_client)
        mock_http_client.get.reset_mock()

        items_data = [
            {
                "titulo": "Bicicleta GT",
                "descripcion": "Bicicleta montañera",
                "precio": 150,
                "moneda": "CUP",
                "link": "/anuncio/333/bici",
                "imagen": "https://img.revolico.com/bici.jpg",
                "fecha": "2024-05-01",
                "provincia": "Pinar del Río",
            }
        ]
        mock_http_client.get.return_value = _mock_response(
            json_data={"pageProps": {"items": items_data}}
        )

        items = await adapter.search("bicicleta")

        assert len(items) == 1
        item = items[0]
        assert item.title == "Bicicleta GT"
        assert item.description == "Bicicleta montañera"
        assert item.price == 150.0
        assert item.currency == "CUP"
        assert item.url == "https://www.revolico.com/anuncio/333/bici"
        assert item.image_url == "https://img.revolico.com/bici.jpg"
        assert item.date == "2024-05-01"
        assert item.location == "Pinar del Río"

    async def test_search_item_without_title_is_skipped(
        self, mock_http_client: AsyncMock
    ) -> None:
        """Items sin título se omiten del resultado."""
        adapter = await self._make_adapter(mock_http_client)
        mock_http_client.get.reset_mock()

        items_data = [
            {"title": "Item válido", "price": 100},
            {"description": "Sin título", "price": 200},
            {"title": "Otro válido", "price": 300},
        ]
        mock_http_client.get.return_value = _mock_response(
            json_data={"pageProps": {"items": items_data}}
        )

        items = await adapter.search("test")
        assert len(items) == 2
        assert items[0].title == "Item válido"
        assert items[1].title == "Otro válido"

    async def test_search_with_alternative_response_structure(
        self, mock_http_client: AsyncMock
    ) -> None:
        """Soporta estructura alternativa ``props.pageProps.items``."""
        adapter = await self._make_adapter(mock_http_client)
        mock_http_client.get.reset_mock()

        mock_http_client.get.return_value = _mock_response(
            json_data={
                "props": {
                    "pageProps": {
                        "items": [{"title": "From props"}]
                    }
                }
            }
        )

        items = await adapter.search("test")
        assert len(items) == 1
        assert items[0].title == "From props"

    async def test_search_with_results_key(
        self, mock_http_client: AsyncMock
    ) -> None:
        """Soporta estructura con clave ``results`` en lugar de ``items``."""
        adapter = await self._make_adapter(mock_http_client)
        mock_http_client.get.reset_mock()

        mock_http_client.get.return_value = _mock_response(
            json_data={
                "pageProps": {
                    "results": [{"title": "From results key"}]
                }
            }
        )

        items = await adapter.search("test")
        assert len(items) == 1
        assert items[0].title == "From results key"


# ── Tests: _parse_item (no requiere mocking de HTTP) ─────────────────


class TestParseItem:
    """Mapeo de items crudos a CanonicalItem."""

    def _parse(self, raw: dict | None) -> CanonicalItem | None:
        """Helper que crea un adapter y parsea un item."""
        adapter = RevolicoAdapter()
        return adapter._parse_item(raw, rank=0)

    def test_minimal_valid_item(self) -> None:
        """Item con solo ``title`` es válido."""
        item = self._parse({"title": "Anuncio de prueba"})
        assert item is not None
        assert item.title == "Anuncio de prueba"
        assert item.price is None
        assert item.url is None

    def test_missing_title_returns_none(self) -> None:
        """Item sin ``title`` retorna ``None``."""
        assert self._parse({"description": "sin título"}) is None
        assert self._parse({}) is None
        assert self._parse(None) is None

    def test_price_from_number(self) -> None:
        """Precio numérico se convierte a float."""
        item = self._parse({"title": "Item", "price": 500})
        assert item is not None
        assert item.price == 500.0

    def test_price_from_string_with_symbols(self) -> None:
        """Precio en string con símbolos se limpia."""
        item = self._parse({"title": "Item", "price": "$ 1,200 USD"})
        assert item is not None
        assert item.price == 1200.0

    def test_url_relative_is_completed(self) -> None:
        """URL relativa se completa con base_url."""
        item = self._parse({"title": "Item", "url": "/anuncio/123/test"})
        assert item is not None
        assert item.url == "https://www.revolico.com/anuncio/123/test"

    def test_url_absolute_stays_unchanged(self) -> None:
        """URL absoluta no se modifica."""
        item = self._parse({
            "title": "Item",
            "url": "https://externo.com/item",
        })
        assert item is not None
        assert item.url == "https://externo.com/item"

    def test_url_from_slug(self) -> None:
        """URL desde campo ``slug``."""
        item = self._parse({"title": "Item", "slug": "/items/abc"})
        assert item is not None
        assert item.url == "https://www.revolico.com/items/abc"

    def test_url_from_id(self) -> None:
        """URL construida desde ``id`` cuando no hay ``url`` ni ``slug``."""
        item = self._parse({"title": "Item", "id": "999"})
        assert item is not None
        assert item.url == "https://www.revolico.com/anuncio/999"

    def test_image_from_direct_field(self) -> None:
        """Imagen desde campo directo ``image``."""
        item = self._parse({
            "title": "Item",
            "image": "https://img.revolico.com/photo.jpg",
        })
        assert item is not None
        assert item.image_url == "https://img.revolico.com/photo.jpg"

    def test_image_from_list(self) -> None:
        """Imagen desde ``images[0]``."""
        item = self._parse({
            "title": "Item",
            "images": [
                "https://img.revolico.com/first.jpg",
                "https://img.revolico.com/second.jpg",
            ],
        })
        assert item is not None
        assert item.image_url == "https://img.revolico.com/first.jpg"

    def test_image_from_dict_in_list(self) -> None:
        """Imagen desde ``images[0].url`` cuando son dicts."""
        item = self._parse({
            "title": "Item",
            "images": [{"url": "https://img.revolico.com/dict.jpg"}],
        })
        assert item is not None
        assert item.image_url == "https://img.revolico.com/dict.jpg"

    def test_string_location(self) -> None:
        """Ubicación desde campo ``location``."""
        item = self._parse({"title": "Item", "location": "Centro Habana"})
        assert item is not None
        assert item.location == "Centro Habana"

    def test_spanish_field_names(self) -> None:
        """Campos en español (titulo, descripcion, precio, etc.) se mapean."""
        item = self._parse({
            "titulo": "Artículo en español",
            "descripcion": "Descripción larga del artículo",
            "precio": 100,
            "moneda": "CUP",
            "slug": "/anuncio/555/articulo",
            "imagen": "https://img.revolico.com/art.jpg",
            "fecha": "2024-07-01",
            "provincia": "Matanzas",
        })
        assert item is not None
        assert item.title == "Artículo en español"
        assert item.description == "Descripción larga del artículo"
        assert item.price == 100.0
        assert item.currency == "CUP"
        assert item.url == "https://www.revolico.com/anuncio/555/articulo"
        assert item.image_url == "https://img.revolico.com/art.jpg"
        assert item.date == "2024-07-01"
        assert item.location == "Matanzas"

    def test_raw_data_preserved(self) -> None:
        """raw_data contiene el dict original completo."""
        raw = {"title": "Test", "price": 50, "extra_field": "valor"}
        item = self._parse(raw)
        assert item is not None
        assert item.raw_data == raw


# ── Tests: Gestión de ciclo de vida ──────────────────────────────────


class TestLifecycle:
    """Tests para close y context manager."""

    async def test_close_closes_http_client(self) -> None:
        """close() cierra el cliente HTTP subyacente."""
        with patch(
            "modulo_1_servicio.scraping.adapters.revolico_adapter.httpx.AsyncClient"
        ) as mock_cls:
            client = AsyncMock(spec=_RealAsyncClient)
            mock_cls.return_value = client

            adapter = RevolicoAdapter()
            await adapter.close()

            client.aclose.assert_awaited_once()

    async def test_async_context_manager(self) -> None:
        """async with cierra el cliente automáticamente al salir."""
        with patch(
            "modulo_1_servicio.scraping.adapters.revolico_adapter.httpx.AsyncClient"
        ) as mock_cls:
            client = AsyncMock(spec=_RealAsyncClient)
            mock_cls.return_value = client

            async with RevolicoAdapter() as adapter:
                assert adapter._http_client is client

            client.aclose.assert_awaited_once()

    async def test_multiple_close_is_safe(self) -> None:
        """Llamar close() múltiples veces no lanza error."""
        with patch(
            "modulo_1_servicio.scraping.adapters.revolico_adapter.httpx.AsyncClient"
        ) as mock_cls:
            client = AsyncMock(spec=_RealAsyncClient)
            mock_cls.return_value = client

            adapter = RevolicoAdapter()
            await adapter.close()
            await adapter.close()
            await adapter.close()

            assert client.aclose.await_count == 3


# ── Tests: Casos borde y errores ─────────────────────────────────────


class TestEdgeCases:
    """Casos borde del adaptador."""

    async def test_search_no_items_key_returns_empty(
        self, mock_http_client: AsyncMock
    ) -> None:
        """pageProps sin clave items/results retorna lista vacía."""
        adapter = await self._make_adapter(mock_http_client)
        mock_http_client.get.reset_mock()

        mock_http_client.get.return_value = _mock_response(
            json_data={"pageProps": {"other_data": "value"}}
        )

        items = await adapter.search("test")
        assert items == []

    async def test_build_id_cached_after_extraction(
        self, mock_http_client: AsyncMock
    ) -> None:
        """extract_build_id() cachea el resultado, segunda llamada no refetch."""
        mock_http_client.get.return_value = _mock_response(
            text="""<script id="__NEXT_DATA__" type="application/json">
{"buildId": "cached-build"}
</script>"""
        )

        adapter = RevolicoAdapter()
        first = await adapter.extract_build_id()
        second = await adapter.extract_build_id()

        assert first == "cached-build"
        assert second == "cached-build"
        # Solo debería haber una llamada HTTP
        mock_http_client.get.assert_awaited_once()

    async def _make_adapter(
        self, mock_client: AsyncMock
    ) -> RevolicoAdapter:
        homepage = """<script id="__NEXT_DATA__" type="application/json">
{"buildId": "test-build"}
</script>"""
        mock_client.get.return_value = _mock_response(text=homepage)
        adapter = RevolicoAdapter()
        await adapter.extract_build_id()
        return adapter
