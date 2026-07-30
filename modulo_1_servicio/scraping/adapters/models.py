"""Modelos Pydantic para SiteAdapters."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, model_validator


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
        default_factory=list,
        description="Campos a extraer de cada resultado",
    )
    canonical_map: Optional[dict[str, str]] = Field(
        default=None,
        description=(
            "Mapeo de campos del adaptador al schema canónico. "
            "Ej: {\"title\": \"nombre\", \"price\": \"precio\"}. "
            "Si es None, no se aplica normalización."
        ),
    )
    python_adapter: Optional[str] = Field(
        default=None,
        description=(
            "Ruta al módulo Python con un adaptador custom (ej: revolico_adapter.RevolicoAdapter). "
            "Cuando se especifica, el adaptador YAML se usa solo como registro — la ejecución "
            "usa la clase Python en lugar del flujo BS4+selectores."
        ),
    )

    @model_validator(mode="after")
    def _validate_fields_or_python_adapter(self) -> SiteAdapter:
        if not self.fields and not self.python_adapter:
            raise ValueError(
                "Debe especificar al menos un 'field' o un 'python_adapter'"
            )
        if self.fields and not all(isinstance(f, AdapterField) for f in self.fields):
            raise ValueError("Todos los elementos de 'fields' deben ser AdapterField")
        return self
