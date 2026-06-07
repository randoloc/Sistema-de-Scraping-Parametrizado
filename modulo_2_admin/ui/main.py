"""Entry point de la app desktop (PySide6 + QML).

Uso:
    python -m modulo_2_admin.ui.main

O desde VSCode: presiona F5 con el launch config adecuado.
"""

from __future__ import annotations

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Asegurar que el proyecto está en el path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PySide6.QtCore import QObject, Signal, Property, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from modulo_2_admin.core.client import ScrapperClient
from modulo_2_admin.core.models import (
    DeliveryConfig,
    FieldConfig,
    FieldFilterDef,
    FilterConfig,
    PaginationConfig,
    ScrapeJobConfig,
    ServiceDefinition,
)
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
    servicesChanged = Signal()
    serviceRunsChanged = Signal()

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
        services = self._repository.get_services()
        total_runs = sum(
            len(self._repository.get_service_runs(s["service_id"]))
            for s in services
        )
        return json.dumps({
            "total_operations": total_ops,
            "total_services": len(services),
            "total_runs": total_runs,
            "connected": self._connected,
            "recent": history,
            "services": services[:4],
        })

    # ═══════════════════════════════════════════════════════════
    # SERVICIOS DE SCRAPING
    # ═══════════════════════════════════════════════════════════

    @Slot(result=str)
    def get_services(self) -> str:
        """Retorna la lista de servicios guardados."""
        return json.dumps(self._repository.get_services())

    @Slot(str, result=str)
    def get_service_detail(self, service_id: str) -> str:
        """Retorna el detalle completo de un servicio."""
        svc = self._repository.get_service(service_id)
        if svc is None:
            return json.dumps({"error": "Servicio no encontrado"})
        return json.dumps(svc.to_dict())

    @Slot(str, str, str, result=str)
    def save_service(
        self, service_id: str, name: str, config_json: str
    ) -> str:
        """Guarda (crea o actualiza) un servicio de scraping.

        Args:
            service_id: ID existente o "" para nuevo
            name: Nombre del servicio
            config_json: JSON con toda la configuración

        Returns:
            service_id del servicio guardado
        """
        try:
            data = json.loads(config_json)
            now = datetime.now(timezone.utc).isoformat()

            if service_id:
                # Actualizar existente
                existing = self._repository.get_service(service_id)
                if existing is None:
                    return json.dumps({"error": "Servicio no encontrado"})
                svc = ServiceDefinition.from_dict(data)
                svc.service_id = service_id
                svc.name = name
                svc.updated_at = now
                svc.created_at = existing.created_at
            else:
                # Crear nuevo
                svc = ServiceDefinition.from_dict(data)
                svc.service_id = svc.generate_id()
                svc.name = name
                svc.created_at = now
                svc.updated_at = now

            self._repository.save_service(svc)
            self.servicesChanged.emit()
            return json.dumps({"service_id": svc.service_id, "name": svc.name})
        except Exception as e:
            return json.dumps({"error": str(e)})

    @Slot(str, result=str)
    def delete_service(self, service_id: str) -> str:
        """Elimina un servicio y sus ejecuciones."""
        try:
            self._repository.delete_service(service_id)
            self.servicesChanged.emit()
            return json.dumps({"ok": True})
        except Exception as e:
            return json.dumps({"error": str(e)})

    # ─── Ejecutar Servicio ───────────────────────────────────

    @Slot(str, str, result=str)
    def run_service(self, service_id: str, filter_values_json: str) -> str:
        """Ejecuta un servicio de scraping con valores de filtro.

        Scrapea cada fuente configurada y combina los resultados.

        Args:
            service_id: ID del servicio a ejecutar
            filter_values_json: JSON con valores para los filtros

        Returns:
            JSON con operation_id y resultados
        """
        try:
            svc = self._repository.get_service(service_id)
            if svc is None:
                return json.dumps({"error": "Servicio no encontrado"})

            filter_values = json.loads(filter_values_json)

            if not svc.sources:
                return json.dumps({"error": "El servicio no tiene fuentes configuradas"})

            # Scrapear cada fuente
            all_items = []
            all_errors = []
            total_elapsed = 0.0
            first_op_id = None
            overall_status = "completed"

            # Construir campos base
            fields = [
                FieldConfig(
                    name=f.name,
                    selector=f.selector,
                    field_type=f.field_type,
                )
                for f in svc.fields
            ]

            for src in svc.sources:
                config = ScrapeJobConfig(
                    source=src.url,
                    source_type=src.source_type,
                    fields=fields,
                    delivery=DeliveryConfig(generate_web=False),
                    timeout=svc.timeout,
                )

                api_dict = config.to_api_dict()
                api_dict["user_filters"] = filter_values

                try:
                    response = self._client.run_scrape(api_dict)
                    if first_op_id is None:
                        first_op_id = response.operation_id

                    # Obtener resultados detallados
                    results = self._client.get_results(response.operation_id)
                    for item in results.items:
                        item["_source"] = src.name
                        all_items.append(item)

                    if results.errors:
                        all_errors.extend(results.errors)
                    if results.elapsed_seconds:
                        total_elapsed += results.elapsed_seconds

                    if response.status == "completed_with_errors":
                        overall_status = "completed_with_errors"

                except Exception as e:
                    all_errors.append(f"[{src.name}] {e}")
                    overall_status = "completed_with_errors"

            # Combinar resultados en una sola operación
            combined_op_id = uuid.uuid4().hex[:8]

            # Guardar en historial
            source_label = f"{svc.name} ({len(svc.sources)} fuentes)"
            self._repository.save_operation(
                operation_id=combined_op_id,
                source=source_label,
                config=svc.to_dict(),
            )

            # Actualizar con resultados combinados
            combined_results = {
                "items": all_items,
                "errors": all_errors,
                "sources": [{"name": s.name, "url": s.url} for s in svc.sources],
            }
            self._repository.update_results(
                operation_id=combined_op_id,
                total_found=len(all_items),
                errors_count=len(all_errors),
                results=combined_results,
            )

            # Guardar ejecución de servicio
            run_id = uuid.uuid4().hex[:12]
            self._repository.save_service_run(
                run_id=run_id,
                service_id=service_id,
                operation_id=combined_op_id,
                filter_values=filter_values,
                total_found=len(all_items),
                status=overall_status,
            )

            self._last_result = {
                "operation_id": combined_op_id,
                "status": overall_status,
                "total_found": len(all_items),
                "total_errors": len(all_errors),
                "service_name": svc.name,
                "sources_count": len(svc.sources),
            }
            self.lastResultChanged.emit(self.lastResult)
            self.historyChanged.emit()
            self.serviceRunsChanged.emit()

            return json.dumps({
                "operation_id": combined_op_id,
                "status": overall_status,
                "total_found": len(all_items),
                "total_errors": len(all_errors),
                "sources": [s.name for s in svc.sources],
            })
        except Exception as e:
            err = f"Error: {e}"
            self._last_result = {"error": str(e)}
            self.lastResultChanged.emit(self.lastResult)
            return json.dumps({"error": str(e)})

    @Slot(str, result=str)
    def get_service_runs(self, service_id: str) -> str:
        """Retorna las ejecuciones de un servicio."""
        return json.dumps(self._repository.get_service_runs(service_id))

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
            # Fallback: buscar en el repositorio local (resultados combinados)
            op = self._repository.get_operation(operation_id)
            if op and op.get("results"):
                r = op["results"]
                return json.dumps({
                    "operation_id": operation_id,
                    "source": op.get("source", ""),
                    "total_found": op.get("total_found", 0),
                    "errors": r.get("errors", []),
                    "elapsed_seconds": None,
                    "items": r.get("items", []),
                })
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
