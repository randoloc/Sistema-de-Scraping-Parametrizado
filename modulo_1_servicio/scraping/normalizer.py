"""Normalización de resultados a schema canónico.

Permite que resultados de distintos sitios (cada uno con sus
propios nombres de campo) se unifiquen en un formato común
para mostrarlos side-by-side en la UI.
"""

from __future__ import annotations

import re as _re
from typing import Any, Optional

from pydantic import BaseModel, Field


class CanonicalItem(BaseModel):
    """Item normalizado con campos canónicos.

    Cualquier resultado de scraping, sin importar el sitio de origen,
    se mapea a este schema. Los campos no disponibles quedan como ``None``.
    """

    title: Optional[str] = Field(default=None, description="Título del item")
    description: Optional[str] = Field(default=None, description="Descripción textual")
    price: Optional[float] = Field(default=None, description="Precio numérico")
    currency: Optional[str] = Field(default=None, description="Código de moneda (MXN, USD, etc.)")
    url: Optional[str] = Field(default=None, description="URL del item original")
    image_url: Optional[str] = Field(default=None, description="URL de imagen principal")
    date: Optional[str] = Field(default=None, description="Fecha del listing")
    location: Optional[str] = Field(default=None, description="Ubicación geográfica")

    # Metadatos
    source_site: str = Field(description="Nombre del sitio/adaptador de origen")
    source_url: str = Field(description="URL de la página donde se encontró")
    rank: int = Field(default=0, description="Posición en resultados")

    # Datos crudos originales (por si se necesita depuración)
    raw_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Campos originales del adaptador",
    )


# Mapeo por defecto: nombre de campo canónico → función de transformación
# Estas funciones reciben el valor crudo y retornan el valor normalizado.
_DEFAULT_TRANSFORMS: dict[str, str] = {}


class ResultNormalizer:
    """Normaliza resultados de scraping usando el canonical_map del adaptador.

    Uso:
        normalizer = ResultNormalizer()
        items = normalizer.normalize(adapter, raw_items, source_url)
    """

    # Mapeo de tipos canónicos a funciones de transformación
    TYPE_TRANSFORMS: dict[str, str] = {
        "price": "price",
        "number": "number",
        "url": "url",
        "image": "image",
    }

    @staticmethod
    def _to_float(value: Any) -> float | None:
        """Convierte un valor a float, limpiando símbolos de moneda.

        Soporta formatos:
        - US: ``$1,234.56`` → 1234.56
        - Europeo: ``€ 50,00`` → 50.00
        - Mixto: ``$ 25,000 MXN`` → 25000.0
        - Sin formato: ``gratis`` → None
        """
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)

        s = str(value).strip()
        if not s:
            return None

        # Eliminar símbolos de moneda conocidos
        for ch in ("$", "€", "£", "¥"):
            s = s.replace(ch, "")
        s = s.strip()
        if not s:
            return None

        last_comma = s.rfind(",")
        last_dot = s.rfind(".")

        if last_dot < 0 and last_comma >= 0:
            # Sin puntos, con coma(s): determinar si coma es decimal o miles
            after_comma = s[last_comma + 1:]
            if _re.match(r"^\d{1,2}\D*$", after_comma):
                # Formato europeo: coma es decimal (ej: "50,00")
                s = s.replace(",", ".", 1)
                s = s.replace(",", "")
            else:
                # Formato US: coma es separador de miles (ej: "25,000")
                s = s.replace(",", "")
        elif last_dot >= 0 and last_comma >= 0:
            # Ambos separadores presentes
            if last_comma > last_dot:
                # Europeo: 1.234,56 → coma después del punto = decimal
                s = s.replace(".", "")
                s = s.replace(",", ".")
            else:
                # US: 1,234.56 → punto después de coma = decimal
                s = s.replace(",", "")
        # else: solo puntos o sin separadores, intentar directo

        try:
            return float(s)
        except (ValueError, TypeError):
            # Último recurso: extraer número con regex
            match = _re.search(r"-?\d+(?:\.\d+)?", s)
            if match:
                try:
                    return float(match.group())
                except (ValueError, TypeError):
                    return None
            return None

    @staticmethod
    def _to_str(value: Any) -> str | None:
        if value is None:
            return None
        return str(value).strip() or None

    @staticmethod
    def _extract_url(value: Any) -> str | None:
        """Extrae un href de un elemento si es necesario."""
        if value is None:
            return None
        val = str(value).strip()
        return val if val.startswith(("http://", "https://", "/")) else None

    def normalize(
        self,
        canonical_map: dict[str, str],
        raw_items: list[dict[str, Any]],
        source_site: str,
        source_url: str,
        start_rank: int = 0,
    ) -> list[CanonicalItem]:
        """Convierte items crudos a CanonicalItem usando el canonical_map.

        Args:
            canonical_map: Diccionario {campo_canónico: campo_origen}.
                Ej: {"title": "nombre", "price": "precio"}
            raw_items: Lista de items con campos del adaptador.
            source_site: Nombre del sitio/adaptador de origen.
            source_url: URL de la página escrapeada.
            start_rank: Ranking inicial (para paginación).

        Returns:
            Lista de CanonicalItem normalizados.
        """
        results: list[CanonicalItem] = []

        for rank_offset, raw in enumerate(raw_items):
            canonical_kwargs: dict[str, Any] = {
                "source_site": source_site,
                "source_url": source_url,
                "rank": start_rank + rank_offset,
                "raw_data": dict(raw),
            }

            # Mapear cada campo canónico
            for canon_field, source_field in canonical_map.items():
                raw_value = raw.get(source_field)
                if raw_value is None:
                    continue

                if canon_field == "price":
                    canonical_kwargs["price"] = self._to_float(raw_value)
                elif canon_field in ("url", "image_url"):
                    canonical_kwargs[canon_field] = self._extract_url(raw_value)
                else:
                    canonical_kwargs[canon_field] = self._to_str(raw_value)

            results.append(CanonicalItem(**canonical_kwargs))

        return results
