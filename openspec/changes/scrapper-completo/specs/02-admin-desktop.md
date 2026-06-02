# Spec: Admin Desktop (PySide6 + QML)

## Description

Aplicación de escritorio para configurar operaciones de scraping y entregas.
Construida con PySide6 + QML, con API layer en Python puro separable para
futura migración a Flutter.

## Scenarios

### S-01: Configurar scraping
**Given** el usuario abre la app
**When** completa los campos: source, campos a extraer, filtros, paginación
**And** hace clic en "Ejecutar"
**Then** la app envía la config al Módulo 1 vía HTTP
**And** muestra el progreso de la operación

### S-02: Configurar entregas
**Given** una operación de scraping completada
**When** el usuario configura canales: email, whatsapp, web
**And** hace clic en "Entregar"
**Then** la app envía la orden de entrega al Módulo 1

### S-03: Ver historial
**Given** operaciones previas ejecutadas
**When** el usuario navega a "Historial"
**Then** ve una lista con fecha, source, estado, resultados

### S-04: Preparado para Flutter
**Given** el módulo core/ no tiene dependencias de Qt
**When** se quiera migrar a Flutter
**Then** solo se reescribe la carpeta ui/ en Dart
