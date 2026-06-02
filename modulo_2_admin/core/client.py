"""Cliente HTTP para comunicarse con el Módulo 1 (Servicio de Scraping).

Esta es la API layer que será reutilizada por Flutter en el futuro.
NO tiene dependencias de Qt — solo Python puro con httpx.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class ScrapeResponse:
    """Respuesta de una operación de scraping."""

    operation_id: str
    status: str
    total_found: int
    total_errors: int
    endpoint: str


@dataclass
class ResultsResponse:
    """Resultados de una operación de scraping."""

    operation_id: str
    source: str
    total_found: int
    errors: list[str]
    elapsed_seconds: float | None
    items: list[dict[str, Any]]


class ScrapperClient:
    """Cliente HTTP para el servicio de scraping.

    Preparado para migración a Flutter:
    - Mismos endpoints, mismo payload
    - En Flutter: reemplazar httpx por http package
    """

    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(timeout=60.0)

    def health(self) -> bool:
        """Verifica que el servicio esté activo."""
        try:
            r = self._client.get(f"{self.base_url}/api/health")
            return r.status_code == 200
        except Exception:
            return False

    def run_scrape(self, config: dict[str, Any]) -> ScrapeResponse:
        """Envía una configuración de scraping al servicio.

        Args:
            config: Diccionario con la configuración (source, fields, filters, etc.)

        Returns:
            ScrapeResponse con el ID de la operación.
        """
        r = self._client.post(
            f"{self.base_url}/api/scrape",
            json=config,
        )
        r.raise_for_status()
        data = r.json()
        return ScrapeResponse(
            operation_id=data["operation_id"],
            status=data["status"],
            total_found=data["total_found"],
            total_errors=data["total_errors"],
            endpoint=data["endpoint"],
        )

    def get_results(self, operation_id: str) -> ResultsResponse:
        """Obtiene los resultados de una operación."""
        r = self._client.get(
            f"{self.base_url}/api/results/{operation_id}"
        )
        r.raise_for_status()
        data = r.json()
        return ResultsResponse(
            operation_id=data["operation_id"],
            source=data["source"],
            total_found=data["total_found"],
            errors=data["errors"],
            elapsed_seconds=data["elapsed_seconds"],
            items=data["items"],
        )

    def get_results_web(self, operation_id: str) -> str:
        """Obtiene la página HTML de resultados."""
        r = self._client.get(
            f"{self.base_url}/api/results/{operation_id}/web"
        )
        r.raise_for_status()
        return r.text

    def deliver_results(
        self,
        operation_id: str,
        emails: list[str] | None = None,
        whatsapp_numbers: list[str] | None = None,
        generate_web: bool = True,
    ) -> dict[str, Any]:
        """Solicita la entrega de resultados por los canales configurados."""
        payload: dict[str, Any] = {"generate_web": generate_web}
        if emails:
            payload["emails"] = emails
        if whatsapp_numbers:
            payload["whatsapp_numbers"] = whatsapp_numbers

        r = self._client.post(
            f"{self.base_url}/api/deliver/{operation_id}",
            json=payload,
        )
        r.raise_for_status()
        return r.json()

    def send_whatsapp_activation(
        self, email: str, phone: str
    ) -> dict[str, Any]:
        """Solicita el envío de email de activación de WhatsApp."""
        r = self._client.post(
            f"{self.base_url}/api/whatsapp/send-activation",
            json={"email": email, "phone": phone},
        )
        r.raise_for_status()
        return r.json()

    def close(self) -> None:
        self._client.close()
