"""Rutas de la API para entrega de resultados por canales."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from modulo_1_servicio.api.routes_scrape import _results_store
from modulo_1_servicio.deliveries.email_sender import EmailDelivery
from modulo_1_servicio.deliveries.web import generate_results_page
from modulo_1_servicio.deliveries.whatsapp import WhatsAppDelivery

router = APIRouter(prefix="/api", tags=["delivery"])

_email_delivery = EmailDelivery()
_whatsapp_delivery = WhatsAppDelivery()


@router.post("/deliver/{operation_id}")
async def deliver_results(
    operation_id: str, config: dict[str, Any]
) -> dict[str, Any]:
    """Envía los resultados de una operación por los canales configurados.

    Body:
        {
            "emails": ["user@example.com"],
            "whatsapp_numbers": ["521234567890"],
            "generate_web": true
        }
    """
    result = _results_store.get(operation_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Operación no encontrada")

    results_url = config.get("results_url", f"/api/results/{operation_id}/web")
    emails = config.get("emails", [])
    whatsapp_numbers = config.get("whatsapp_numbers", [])
    generate_web = config.get("generate_web", True)

    delivery_errors: dict[str, list[str]] = {}

    # Web
    web_url = None
    if generate_web:
        _ = generate_results_page(result, operation_id)
        web_url = results_url

    # Email
    if emails:
        errs = _email_delivery.send_results(
            result, operation_id, tuple(emails), results_url
        )
        if errs:
            delivery_errors["email"] = errs

    # WhatsApp
    if whatsapp_numbers:
        for number in whatsapp_numbers:
            try:
                await _whatsapp_delivery.send_results(
                    result, operation_id, number, results_url
                )
            except Exception as e:
                delivery_errors.setdefault("whatsapp", []).append(
                    f"{number}: {e}"
                )

    return {
        "operation_id": operation_id,
        "web_url": web_url,
        "email_sent": len(emails) > 0 and "email" not in delivery_errors,
        "whatsapp_sent": len(whatsapp_numbers) > 0
        and "whatsapp" not in delivery_errors,
        "delivery_errors": delivery_errors or None,
    }


@router.post("/whatsapp/send-activation")
async def send_whatsapp_activation(data: dict[str, Any]) -> dict[str, Any]:
    """Envía email de activación de WhatsApp con link wa.me."""
    email = data.get("email", "")
    phone = data.get("phone", "")
    if not email or not phone:
        raise HTTPException(status_code=400, detail="Email y phone son requeridos")

    wa_link = f"https://wa.me/{phone}?text=ActivarScrapper"
    _email_delivery.send_activation(email, wa_link)

    return {"message": "Email de activación enviado", "wa_link": wa_link}
