# Spec: Delivery Email

## Description

Envío de resultados por correo electrónico con plantillas HTML profesionales.
Usa SMTP directo o SendGrid como respaldo.

## Scenarios

### S-01: Enviar resultados por email
**Given** un scraping completado
**When** se solicita entrega por email con direcciones destino
**Then** se envía un correo con plantilla HTML profesional
**And** el correo incluye resumen de datos + link a web de resultados

### S-02: Múltiples destinatarios
**Given** una lista de N direcciones de email
**When** se envía el delivery
**Then** cada destinatario recibe el correo individualmente (BCC para privacidad)

### S-03: Error de entrega
**Given** un email inválido en la lista
**When** falla el envío
**Then** se registra el error pero continúa con los demás destinatarios
