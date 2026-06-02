# Spec: Delivery WhatsApp (Meta Cloud API)

## Description

Envío de resultados por WhatsApp usando Meta Cloud API oficial.
El usuario hace opt-in vía email con link wa.me → service conversation FREE.
Después responde "Check" para abrir nueva ventana gratis.

## Scenarios

### S-01: Activación por opt-in
**Given** un usuario con número de WhatsApp configurado
**When** recibe email con link wa.me y hace clic
**And** envía "ActivarScrapper" por WhatsApp
**Then** el servicio recibe el webhook de Meta
**And** responde con "✅ Activado. Envía 'Check' para recibir resultados."
**And** se marca el número como activo (service window FREE)

### S-02: Recibir resultados
**Given** un usuario activo y scraping completado
**When** el usuario envía "Check"
**Then** el servicio responde con link a web de resultados + resumen
**And** todo dentro de service window = FREE

### S-03: Notificación proactiva
**Given** scraping completado y usuario activo
**When** NO hay service window abierta
**Then** se envía template Utility (pagado ~$0.001-0.004)
**Or** se espera a que el usuario envíe "Check"

### S-04: Error de número inválido
**Given** un número no registrado en WhatsApp
**When** se intenta enviar
**Then** Meta API devuelve error 400
**And** se marca el número como inválido
