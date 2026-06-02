"""Entry point de la app desktop (PySide6 + QML).

Uso:
    python -m modulo_2_admin.ui.main

O desde VSCode: presiona F5 con el launch config adecuado.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Asegurar que el proyecto está en el path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtCore import QObject, Signal, Property, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from modulo_2_admin.core.client import ScrapperClient


class PythonBridge(QObject):
    """Puente entre Python (backend) y QML (frontend).

    Expone funciones y propiedades que QML puede consumir.
    Cuando se migre a Flutter, la lógica de negocio
    se mantiene aquí y QML se reemplaza por Dart/Flutter.
    """

    connectedChanged = Signal(bool)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._client = ScrapperClient()
        self._connected = False
        self._check_connection()

    @Property(bool, notify=connectedChanged)
    def connected(self) -> bool:
        return self._connected

    def _check_connection(self) -> None:
        self._connected = self._client.health()
        self.connectedChanged.emit(self._connected)

    @Slot()
    def check_connection(self) -> None:
        self._check_connection()

    @Slot(str, str, str, result=str)
    def run_scrape(
        self, source: str, source_type: str, fields_json: str
    ) -> str:
        """Ejecuta un scraping desde QML.

        Args:
            source: URL o fuente
            source_type: tipo de fuente
            fields_json: JSON con la lista de campos

        Returns:
            operation_id o mensaje de error
        """
        import json

        fields = json.loads(fields_json)
        config = {
            "source": source,
            "source_type": source_type,
            "fields": fields,
        }
        try:
            response = self._client.run_scrape(config)
            return response.operation_id
        except Exception as e:
            return f"Error: {e}"


def main() -> None:
    app = QGuiApplication(sys.argv)
    app.setApplicationName("ScrapperGenérico")
    app.setOrganizationName("ScrapperGenérico")

    engine = QQmlApplicationEngine()

    # Exponer bridge a QML
    bridge = PythonBridge()
    engine.rootContext().setContextProperty("python", bridge)

    # Cargar QML
    qml_path = str(Path(__file__).parent / "qml" / "main.qml")
    engine.load(qml_path)

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
