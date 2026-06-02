# Spec: Delivery Web

## Description

Página HTML elegante y profesional con los resultados del scraping.
Generada dinámicamente por Jinja2. Accesible mediante link único.

## Scenarios

### S-01: Ver resultados en web
**Given** un scraping completado con resultados
**When** se accede a GET /results/{id}
**Then** se muestra una página HTML responsive con los datos
**And** diseño profesional con Tailwind CSS (o CSS vanilla elegante)

### S-02: Resultados vacíos
**Given** un scraping que no encontró resultados
**When** se accede al link
**Then** se muestra "Sin resultados encontrados" con diseño coherente

### S-03: Error
**Given** un ID de resultados inexistente
**When** se accede al link
**Then** se muestra página de error 404 con diseño consistente
