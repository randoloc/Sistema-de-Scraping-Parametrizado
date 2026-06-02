# Proposal: ScrapperGenérico Completo — Sistema de 3 Módulos

## Intent

Convertir el motor de scraping actual en un sistema completo de 3 módulos:
un servicio hosting gratuito (HF Spaces + cron-job), una app de administración
desktop (PySide6+QML preparada para Flutter), y un sistema de entregas
multi-canal (web, email, WhatsApp Meta Cloud API).

## Scope

### In Scope
- Módulo 1: Servicio FastAPI en HuggingFace Spaces con cron-job keep-alive
- Módulo 2: App desktop PySide6+QML con API layer separable para Flutter
- Módulo 3: Entrega de resultados vía web (HTML elegante), email (SMTP/SendGrid), WhatsApp (Meta Cloud API)
- Meta Cloud API con opt-in por email (link wa.me) para service = FREE
- SQLite como BD principal
- Scraping engine existente adaptado al Módulo 1

### Out of Scope
- App móvil Flutter nativa (solo preparación/guía)
- Dashboard web del Módulo 2 (solo desktop primero)
- Autenticación multi-usuario (V1 es monousuario)
- Despliegue a producción real (V1 es funcional, no escalada)

## Capabilities

### New Capabilities
- `servicio-scraping`: API REST para recibir configs, ejecutar scraping y entregar resultados
- `admin-desktop`: App PySide6+QML para configurar scraping y entregas
- `delivery-web`: Generar página HTML elegante con resultados
- `delivery-email`: Enviar resultados por correo con plantillas profesionales
- `delivery-whatsapp`: Enviar resultados por WhatsApp Meta Cloud API con opt-in

### Modified Capabilities
- None (proyecto desde cero, no hay specs previas)

## Approach

Arquitectura de 3 módulos comunicados por HTTP. Módulo 1 (FastAPI) se
aloja en HF Spaces con keep-alive via cron-job.org. Módulo 2 (PySide6+QML)
corre local y consume la API del Módulo 1. Módulo 3 son plantillas/servicios
de entrega dentro del Módulo 1. WhatsApp usa Meta Cloud API con opt-in
por email → link wa.me → service conversation FREE.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/scrapper_generico/` | Removed | Se reemplaza por estructura de 3 módulos |
| `modulo_1_servicio/` | New | FastAPI + scraping + deliveries |
| `modulo_2_admin/` | New | PySide6+QML desktop app |
| `modulo_3_resultados/` | New | Templates web, email, WhatsApp |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Cuenta WhatsApp bloqueada por uso no-oficial | Medium | Usar Meta Cloud API oficial, no whatsapp-web.js |
| HF Spaces se duerme si cron-job falla | Low | Cron-job cada 30 min, múltiples health checks |
| PySide6/QML complejidad en Windows | Low | Documentar setup en VSCode con venv |

## Rollback Plan

1. `git revert` del commit de implementación
2. Volver a estructura `src/scrapper_generico/` anterior
3. Los 3 módulos son independientes, no hay acoplamiento transversal

## Dependencies

- Python 3.11+
- HuggingFace account (gratis)
- Meta Developer account (gratis) para WhatsApp Cloud API
- SendGrid account (gratis, 100 emails/día) o SMTP propio
- cron-job.org account (gratis) para keep-alive

## Success Criteria

- [ ] Módulo 1 recibe config por API y ejecuta scraping → devuelve resultados
- [ ] Módulo 2 envía config al Módulo 1 y muestra resultados
- [ ] Resultados visibles en web elegante al abrir link
- [ ] Email con resultados llega a la bandeja de entrada
- [ ] WhatsApp envía notificación con link a resultados
- [ ] 40+ tests pasando
