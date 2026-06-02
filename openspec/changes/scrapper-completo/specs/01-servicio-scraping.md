# Spec: Servicio de Scraping

## Description

API REST alojada en HuggingFace Spaces (CPU Basic) que recibe configuraciones
de scraping, ejecuta el motor, y entrega resultados por los canales configurados.
Mantenido vivo mediante cron-job.org (ping cada 30 min).

## Scenarios

### S-01: Recibir configuración y ejecutar scraping
**Given** una configuración válida con source, campos, y filtros
**When** se envía POST /api/scrape
**Then** el servicio ejecuta el scraping
**And** devuelve un ID de operación (202 Accepted)
**And** el resultado está disponible en GET /api/results/{id}

### S-02: Configurar entrega de resultados
**Given** un ID de operación de scraping completada
**When** se envía POST /api/deliver con canales (web, email, whatsapp)
**Then** el servicio entrega los resultados por cada canal configurado

### S-03: Health check
**When** se consulta GET /api/health
**Then** devuelve 200 OK con estado del servicio
