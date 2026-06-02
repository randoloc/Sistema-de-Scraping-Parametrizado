"""Cargador de adaptadores YAML desde el directorio ``adapters/``."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml

from modulo_1_servicio.scraping.adapters.models import SiteAdapter

logger = __import__("logging").getLogger(__name__)

# Ruta por defecto: raíz del proyecto / adapters/
DEFAULT_ADAPTERS_DIR = Path(__file__).parent.parent.parent.parent / "adapters"


class AdapterLoader:
    """Carga y provee acceso a los SiteAdapters desde archivos YAML.

    Args:
        adapters_dir: Directorio donde buscar archivos ``.yaml``/``.yml``.
    """

    def __init__(self, adapters_dir: str | Path = DEFAULT_ADAPTERS_DIR) -> None:
        self._adapters_dir = Path(adapters_dir)
        self._adapters: dict[str, SiteAdapter] = {}

    def load_all(self) -> list[SiteAdapter]:
        """Escanea el directorio y carga todos los adaptadores YAML.

        Returns:
            Lista de adaptadores cargados y validados.
        """
        self._adapters = {}
        if not self._adapters_dir.exists():
            logger.warning("Directorio de adaptadores no encontrado: %s", self._adapters_dir)
            return []

        for path in sorted(self._adapters_dir.glob("*.yaml")) + sorted(self._adapters_dir.glob("*.yml")):
            try:
                adapter = self._load_file(path)
                self._adapters[adapter.name] = adapter
                logger.info("Adaptador cargado: %s (%s)", adapter.name, path.name)
            except Exception as exc:
                logger.error("Error cargando adaptador %s: %s", path.name, exc)

        return list(self._adapters.values())

    def _load_file(self, path: Path) -> SiteAdapter:
        """Carga y valida un único archivo YAML."""
        raw = path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
        if not isinstance(data, dict):
            raise ValueError(f"Archivo YAML inválido: {path.name}")
        return SiteAdapter.model_validate(data)

    def get_all(self) -> list[SiteAdapter]:
        """Retorna todos los adaptadores cargados."""
        return list(self._adapters.values())

    def get_by_vertical(self, vertical: str) -> list[SiteAdapter]:
        """Filtra adaptadores por vertical."""
        return [a for a in self._adapters.values() if a.vertical == vertical]

    def get(self, name: str) -> Optional[SiteAdapter]:
        """Obtiene un adaptador por su nombre."""
        return self._adapters.get(name)

    @property
    def count(self) -> int:
        return len(self._adapters)
