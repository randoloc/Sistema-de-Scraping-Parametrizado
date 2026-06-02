"""Modelos de dominio del motor de scraping genérico.

Define los contratos fundamentales del sistema:
qué configurar, qué extraer y cómo reportar errores.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum, auto
from typing import Any


class FieldType(StrEnum):
    """Tipos de datos que se pueden extraer de una fuente."""

    TEXT = auto()
    URL = auto()
    IMAGE = auto()
    PRICE = auto()
    DATE = auto()
    NUMBER = auto()
    BOOLEAN = auto()
    HTML = auto()


class OutputFormat(StrEnum):
    """Formatos de salida soportados."""

    JSON = auto()
    CSV = auto()
    YAML = auto()
    JSONL = auto()


class SourceType(StrEnum):
    """Tipo de fuente a scrapear."""

    WEB_PAGE = auto()
    API = auto()
    HTML_FILE = auto()
    SITEMAP = auto()


@dataclass(frozen=True)
class FieldDefinition:
    """Define UN campo a extraer.

    Attributes:
        name: Nombre del campo en el resultado.
        selector: Selector CSS/XPath para localizar el elemento.
        field_type: Tipo de dato del campo.
        transform: Función de transformación opcional (formato string).
        required: Si el campo es obligatorio.
        default: Valor por defecto si no se encuentra.
    """

    name: str
    selector: str
    field_type: FieldType = FieldType.TEXT
    transform: str | None = None
    required: bool = True
    default: Any = None


@dataclass(frozen=True)
class FilterConfig:
    """Filtros para refinar los resultados del scraping.

    Attributes:
        include_patterns: Patrones de inclusión (regex).
        exclude_patterns: Patrones de exclusión (regex).
        min_length: Longitud mínima del contenido extraído.
        max_length: Longitud máxima del contenido extraído.
        deduplicate: Si se deben eliminar duplicados.
        max_results: Número máximo de resultados a devolver.
    """

    include_patterns: tuple[str, ...] = ()
    exclude_patterns: tuple[str, ...] = ()
    min_length: int | None = None
    max_length: int | None = None
    deduplicate: bool = True
    max_results: int | None = None


@dataclass(frozen=True)
class PaginationConfig:
    """Configuración para navegación entre páginas.

    Supports:
        - URL-based: next_page_url = template.format(page=N)
        - Selector-based: selector que contiene el link a siguiente página
        - Infinite scroll: scroll hasta que desaparezca el selector
    """

    strategy: str = "url"  # url | selector | infinite_scroll
    url_template: str | None = None
    next_selector: str | None = None
    max_pages: int = 1
    page_param: str = "page"
    start_page: int = 1
    step: int = 1


@dataclass(frozen=True)
class ScrapeConfig:
    """Configuración completa de una operación de scraping.

    Este es el contrato de entrada: TODO lo que el scraper necesita saber.

    Attributes:
        source_type: Tipo de fuente.
        source: URL o ruta al archivo fuente.
        fields: Lista de campos a extraer.
        container_selector: Selector del contenedor de cada item (para listas).
        filters: Filtros a aplicar a los resultados.
        pagination: Configuración de paginación.
        output_format: Formato de salida deseado.
        output_path: Ruta donde guardar los resultados.
        headers: Headers HTTP personalizados.
        timeout: Timeout en segundos para cada request.
        user_agent: User-Agent a utilizar.
        respect_robots_txt: Si debe respetar robots.txt.
        rate_limit: Delay entre requests en segundos.
    """

    source_type: SourceType
    source: str
    fields: tuple[FieldDefinition, ...]
    container_selector: str | None = None
    filters: FilterConfig = field(default_factory=FilterConfig)
    pagination: PaginationConfig = field(default_factory=PaginationConfig)
    output_format: OutputFormat = OutputFormat.JSON
    output_path: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    timeout: int = 30
    user_agent: str | None = None
    respect_robots_txt: bool = True
    rate_limit: float = 1.0


@dataclass(frozen=True)
class ExtractedItem:
    """Un item individual extraído de la fuente."""

    data: dict[str, Any]
    source_url: str
    extracted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    rank: int = 0


@dataclass(frozen=True)
class ScrapeResult:
    """Resultado completo de una operación de scraping.

    Attributes:
        config: La config que se usó para generar este resultado.
        items: Items extraídos (ya filtrados y procesados).
        total_found: Total de items encontrados antes de filtrar.
        errors: Errores ocurridos durante el scraping.
        started_at: Timestamp de inicio.
        completed_at: Timestamp de finalización.
        pages_scraped: Cantidad de páginas scrapeadas.
    """

    config: ScrapeConfig
    items: tuple[ExtractedItem, ...] = ()
    total_found: int = 0
    errors: tuple[str, ...] = ()
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    pages_scraped: int = 0

    @property
    def elapsed(self) -> float | None:
        """Tiempo transcurrido en segundos (None si no ha terminado)."""
        if self.completed_at is None:
            return None
        return (self.completed_at - self.started_at).total_seconds()

    @property
    def success_count(self) -> int:
        return len(self.items)

    @property
    def error_count(self) -> int:
        return len(self.errors)


class ScraperError(Exception):
    """Error base del sistema de scraping."""

    def __init__(self, message: str, source: str | None = None) -> None:
        self.source = source
        super().__init__(f"[{source}] {message}" if source else message)


class ScraperConnectionError(ScraperError):
    """Error de conexión con la fuente."""


class ScraperParseError(ScraperError):
    """Error al parsear el contenido de la fuente."""


class ScraperValidationError(ScraperError):
    """Error de validación de configuración."""
