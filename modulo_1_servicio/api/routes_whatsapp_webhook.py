"""Webhook para recibir mensajes de WhatsApp Meta Cloud API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query, Request

from modulo_1_servicio.deliveries.whatsapp import WhatsAppDelivery

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])

_whatsapp = WhatsAppDelivery()


@router.get("/webhook")
async def verify_webhook(
    mode: str = Query("", alias="hub.mode"),
    token: str = Query("", alias="hub.verify_token"),
    challenge: str = Query("", alias="hub.challenge"),
) -> str | dict[str, str]:
    """Verificación inicial del webhook con Meta."""
    result = _whatsapp.verify_webhook(mode, token, challenge)
    if result:
        return result
    return {"error": "Verificación fallida"}


@router.post("/webhook")
async def receive_webhook(request: Request) -> dict[str, str]:
    """Recibe mensajes entrantes de WhatsApp."""
    body = await request.json()
    messages = _whatsapp.process_webhook(body)

    for msg in messages:
        number = msg["from"]
        text = msg["text"]

        if _whatsapp.is_activation_message(text):
            _whatsapp.register_number(number)
            await _whatsapp.send_activation_confirmation(number)

        elif _whatsapp.is_check_message(text):
            # Buscar último resultado para este número
            # TODO: obtener de SQLite según el número
            await _whatsapp.send_check_response(
                result=None,  # type: ignore[arg-type]
                result_id="",
                to_number=number,
                results_url="",
            )

    return {"status": "ok"}
