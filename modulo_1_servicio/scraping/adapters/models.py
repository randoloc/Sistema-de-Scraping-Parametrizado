"""Modelos Pydantic para SiteAdapters."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class AdapterField(BaseModel):
    """Define un campo a extraer en un adaptador de sitio."""

    name: str = Field(description="Nombre del campo en el resultado")
    selector: str = Field(description="Selector CSS para localizar el elemento")
    type: str = Field(default="text", description="Tipo de dato: text|price|url|number|date|image")
    transform: Optional[str] = Field(default=None, description="Transformación opcional del valor")


class SiteAdapter(BaseModel):
    """Configuración completa de scraping para un sitio web."""

    name: str = Field(description="Identificador único del adaptador")
    site: str = Field(description="Dominio del sitio (ej: mercadolibre.com.mx)")
    vertical: str = Field(description="Categoría vertical (ej: cars, real_estate, jobs)")
    search_url: str = Field(
        description="URL de búsqueda con templates {query} y {page}",
    )
    pagination: Optional[str] = Field(
        default=None,
        description="Template para paginación (ej: ?page={page})",
    )
    container_selector: Optional[str] = Field(
        default=None,
        description="Selector CSS para el contenedor de cada resultado",
    )
    fields: list[AdapterField] = Field(
        min_length=1,
        description="Campos a extraer de cada resultado",
    )
