"""Entrega de resultados por WhatsApp usando Meta Cloud API.

Estrategia de costo cero:
1. Usuario recibe email con link wa.me y envía "ActivarScrapper"
2. Eso abre una Service Window (GRATIS, 24h)
3. El servicio responde confirmación (GRATIS)
4. Cuando el usuario envía "Check", se abre NUEVA ventana (GRATIS)
5. El servicio responde con resultados (GRATIS)

Para notificaciones proactivas: usar Utility template (~$0.001-0.004 c/u)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from dataclasses import dataclass, field
from typing import Any

import httpx

from modulo_1_servicio.scraping.models import ScrapeResult

logger = logging.getLogger(__name__)

WHATSAPP_API_VERSION = "v21.0"
WHATSAPP_GRAPH_URL = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}"


@dataclass
class WhatsAppDelivery:
    """Entrega de resultados por WhatsApp vía Meta Cloud API.

    Requiere configuración vía atributos de clase o variables de entorno:
        - phone_number_id: ID del número de teléfono en Meta Business
        - access_token: Token de acceso de la app de Meta
        - verify_token: Token para verificación del webhook
        - business_account_id: ID de la cuenta de negocio
    """

    phone_number_id: str = ""
    access_token: str = ""
    verify_token: str = "scrapper_generico_verify_2026"
    business_account_id: str = ""

    # Números activados (en producción: SQLite)
    activated_numbers: set[str] = field(default_factory=set)

    async def send_results(
        self, result: ScrapeResult, result_id: str, to_number: str, results_url: str
    ) -> dict[str, Any]:
        """Envía resultados a un número.

        Si el número está activo dentro de service window, el mensaje es GRATIS.
        Si no, se intenta enviar como template Utility (pagado ~$0.001-0.004).
        """
        message = self._build_message(result, results_url)
        return await self._send_text(to_number, message)

    async def send_activation_confirmation(self, to_number: str) -> dict[str, Any]:
        """Responde a la activación del usuario (service = FREE)."""
        message = (
            "✅ *Activación exitosa* \\n\\n"
            "Has activado las notificaciones de ScrapperGenérico.\\n\\n"
            "📌 *¿Cómo funciona?*\\n"
            "Envía *Check* cuando quieras revisar si hay nuevos resultados.\\n"
            "Te responderé al instante.\\n\\n"
            "🙌 Gracias por activarte."
        )
        return await self._send_text(to_number, message)

    async def send_check_response(
        self, result: ScrapeResult, result_id: str, to_number: str, results_url: str
    ) -> dict[str, Any]:
        """Responde a un 'Check' del usuario con resultados (service = FREE)."""
        if result.success_count == 0:
            message = (
                "📭 *Sin resultados*\\n\\n"
                "No hay resultados nuevos disponibles.\\n"
                "Vuelve a intentar más tarde o configura un nuevo scraper."
            )
        else:
            message = self._build_message(result, results_url)
        return await self._send_text(to_number, message)

    def is_activation_message(self, text: str) -> bool:
        """Detecta si un mensaje es de activación."""
        return text.strip().lower() in (
            "activarscrapper", "activar", "start", "hola", "activate"
        )

    def is_check_message(self, text: str) -> bool:
        """Detecta si un mensaje es de consulta de resultados."""
        return text.strip().lower() in ("check", "resultados", "status", "ver")

    def register_number(self, number: str) -> None:
        """Marca un número como activado (recibió el opt-in)."""
        self.activated_numbers.add(self._clean_number(number))

    def verify_webhook(self, mode: str, token: str, challenge: str) -> str | None:
        """Verificación del webhook de Meta (GET /webhook)."""
        if mode == "subscribe" and token == self.verify_token:
            return challenge
        return None

    def process_webhook(self, body: dict[str, Any]) -> list[dict[str, Any]]:
        """Procesa un webhook entrante de Meta.

        Returns:
            Lista de mensajes procesados: {from_number, text, timestamp}
        """
        messages: list[dict[str, Any]] = []
        for entry in body.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for msg in value.get("messages", []):
                    if msg.get("type") == "text":
                        messages.append(
                            {
                                "from": msg["from"],
                                "text": msg["text"]["body"],
                                "timestamp": msg.get("timestamp", ""),
                                "msg_id": msg.get("id", ""),
                            }
                        )
        return messages

    def _build_message(self, result: ScrapeResult, results_url: str) -> str:
        items_summary = "\n".join(
            f"  {i+1}. {list(item.data.values())[0] if item.data else '—'}"
            for i, item in enumerate(result.items[:5])
        )
        more = f"... y {len(result.items) - 5} más" if len(result.items) > 5 else ""
        elapsed = f"{result.elapsed:.1f}s" if result.elapsed else "—"

        return (
            f"📊 *Resultados de scraping*\\n\\n"
            f"🔗 *Fuente:* {result.config.source}\\n"
            f"📦 *Items:* {result.success_count} encontrados\\n"
            f"⏱ *Tiempo:* {elapsed}\\n\\n"
            f"*Datos:*\\n{items_summary}\\n{more}\\n\\n"
            f"🌐 *Ver completo:*\\n{results_url}"
        )

    async def _send_text(
        self, to_number: str, text: str
    ) -> dict[str, Any]:
        """Envía un mensaje de texto vía Meta Cloud API."""
        url = f"{WHATSAPP_GRAPH_URL}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self._clean_number(to_number),
            "type": "text",
            "text": {"preview_url": True, "body": text},
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    @staticmethod
    def _clean_number(number: str) -> str:
        return number.replace("+", "").replace(" ", "").replace("-", "")
