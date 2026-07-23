"""Entry point de la app desktop (PySide6 + QML).

Uso:
    python -m modulo_2_admin.ui.main

O desde VSCode: presiona F5 con el launch config adecuado.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

# Asegurar que el proyecto está en el path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtCore import QObject, Signal, Property, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from modulo_2_admin.core.client import ScrapperClient
from modulo_2_admin.core.models import FieldConfig, FilterConfig, PaginationConfig, ScrapeJobConfig
from modulo_2_admin.core.repository import LocalRepository


class PythonBridge(QObject):
    """Puente entre Python (backend) y QML (frontend).

    Expone funciones y propiedades que QML puede consumir.
    Cuando se migre a Flutter, la lógica de negocio
    se mantiene aquí y QML se reemplaza por Dart/Flutter.
    """

    connectedChanged = Signal(bool)
    lastResultChanged = Signal(str)
    historyChanged = Signal()
    operationDetailChanged = Signal(str)
    searchResultsChanged = Signal(str)
    adaptersChanged = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._client = ScrapperClient()
        self._repository = LocalRepository()
        self._connected = False
        self._last_result: dict[str, Any] = {}
        self._operation_detail: dict[str, Any] = {}
        self._search_results: dict[str, Any] = {}
        self._adapters: list[dict[str, Any]] = []
        self._check_connection()
        self._refresh_adapters()

    # --- Propiedades expuestas a QML ---

    @Property(bool, notify=connectedChanged)
    def connected(self) -> bool:
        return self._connected

    @Property(str, notify=lastResultChanged)
    def lastResult(self) -> str:
        return json.dumps(self._last_result)

    @Property(str, notify=historyChanged)
    def history(self) -> str:
        return json.dumps(self._repository.get_history())

    @Property(str, notify=operationDetailChanged)
    def operationDetail(self) -> str:
        return json.dumps(self._operation_detail)

    # --- Conexión ---

    def _check_connection(self) -> None:
        was = self._connected
        self._connected = self._client.health()
        if was != self._connected:
            self.connectedChanged.emit(self._connected)

    @Slot()
    def check_connection(self) -> None:
        self._check_connection()

    @Slot(result=str)
    def get_dashboard_stats(self) -> str:
        history = self._repository.get_history(limit=5)
        total_ops = len(self._repository.get_history(limit=9999))
        return json.dumps({
            "total_operations": total_ops,
            "connected": self._connected,
            "recent": history,
        })

    # --- Scraping ---

    @Slot(str, str, str, result=str)
    def run_scrape(self, source: str, source_type: str, fields_json: str) -> str:
        """Ejecuta un scraping desde QML.

        Args:
            source: URL o fuente
            source_type: tipo de fuente
            fields_json: JSON con la lista de campos

        Returns:
            operation_id o mensaje de error
        """
        try:
            fields_data = json.loads(fields_json)
            fields = [
                FieldConfig(
                    name=f["name"],
                    selector=f["selector"],
                    field_type=f.get("fieldType", "text"),
                )
                for f in fields_data
            ]

            config = ScrapeJobConfig(
                source=source,
                source_type=source_type,
                fields=fields,
            )

            response = self._client.run_scrape(config.to_api_dict())

            self._repository.save_operation(
                operation_id=response.operation_id,
                source=source,
                config=config.to_api_dict(),
            )

            self._last_result = {
                "operation_id": response.operation_id,
                "status": response.status,
                "total_found": response.total_found,
            }
            self.lastResultChanged.emit(self.lastResult)
            self.historyChanged.emit()

            return response.operation_id
        except Exception as e:
            error_msg = f"Error: {e}"
            self._last_result = {"error": str(e)}
            self.lastResultChanged.emit(self.lastResult)
            return error_msg

    # --- Resultados ---

    @Slot(str, result=str)
    def get_results(self, operation_id: str) -> str:
        try:
            results = self._client.get_results(operation_id)
            self._repository.update_results(
                operation_id=operation_id,
                total_found=results.total_found,
                errors_count=len(results.errors),
                results={"items": results.items, "errors": results.errors},
            )
            self.historyChanged.emit()
            return json.dumps({
                "operation_id": results.operation_id,
                "source": results.source,
                "total_found": results.total_found,
                "errors": list(results.errors),
                "elapsed_seconds": results.elapsed_seconds,
                "items": results.items,
            })
        except Exception as e:
            return json.dumps({"error": str(e)})

    @Slot(str, result=str)
    def get_results_web(self, operation_id: str) -> str:
        try:
            return self._client.get_results_web(operation_id)
        except Exception as e:
            return f"<html><body><h3>Error: {e}</h3></body></html>"

    # --- Historial ---

    @Slot(result=str)
    def get_history(self) -> str:
        return json.dumps(self._repository.get_history())

    @Slot(str, result=str)
    def get_operation_detail(self, operation_id: str) -> str:
        op = self._repository.get_operation(operation_id)
        if op is None:
            return json.dumps({"error": "Operación no encontrada"})
        self._operation_detail = op
        self.operationDetailChanged.emit(self.operationDetail)
        return json.dumps(op)

    # --- Entregas ---

    @Slot(str, result=str)
    def deliver_results(self, operation_id: str, emails_json: str = "[]", whatsapp_json: str = "[]") -> str:
        try:
            emails = json.loads(emails_json)
            whatsapp = json.loads(whatsapp_json)
            result = self._client.deliver_results(
                operation_id=operation_id,
                emails=emails if emails else None,
                whatsapp_numbers=whatsapp if whatsapp else None,
            )
            return json.dumps(result)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @Slot(str, str, result=str)
    def send_whatsapp_activation(self, email: str, phone: str) -> str:
        try:
            result = self._client.send_whatsapp_activation(email, phone)
            return json.dumps(result)
        except Exception as e:
            return json.dumps({"error": str(e)})

    # --- Fase 2: Búsqueda por vertical ---

    @Property(str, notify=adaptersChanged)
    def adapters(self) -> str:
        return json.dumps(self._adapters)

    @Property(str, notify=searchResultsChanged)
    def searchResults(self) -> str:
        return json.dumps(self._search_results)

    def _refresh_adapters(self) -> None:
        try:
            self._adapters = self._client.list_adapters()
        except Exception:
            self._adapters = []
        self.adaptersChanged.emit(self.adapters)

    @Slot(result=str)
    def refresh_adapters(self) -> str:
        """Recarga la lista de adaptadores desde el servicio."""
        self._refresh_adapters()
        return self.adapters

    @Slot(result=str)
    def get_verticals(self) -> str:
        """Retorna la lista de verticales disponibles."""
        try:
            verticals = self._client.list_verticals()
            return json.dumps(verticals)
        except Exception as e:
            return json.dumps({"error": str(e)})

    @Slot(str, str, str, result=str)
    def search_adapters(self, query: str, vertical: str, site: str) -> str:
        """Ejecuta búsqueda multi-adaptador desde QML.

        Args:
            query: Término de búsqueda.
            vertical: Vertical (cars, real_estate, etc.).
            site: Nombre de adaptador específico (o vacío para todos).

        Returns:
            JSON con resultados normalizados.
        """
        try:
            site_param = site if site and site != "all" else None
            results = self._client.search(
                query=query,
                vertical=vertical,
                site=site_param,
            )
            self._search_results = results
            self.searchResultsChanged.emit(self.searchResults)
            return json.dumps(results)
        except Exception as e:
            error = {"error": str(e)}
            self._search_results = error
            self.searchResultsChanged.emit(self.searchResults)
            return json.dumps(error)


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
