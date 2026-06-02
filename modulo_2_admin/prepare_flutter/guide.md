# Guía de Migración a Flutter

## Estrategia

La app de administración (Módulo 2) está diseñada con separated:
- **`core/`** — Lógica de negocio pura Python, sin dependencias Qt
- **`ui/`** — Interfaz visual en QML + PySide6

Para migrar a Flutter:
1. **Reescribir `ui/`** en Dart/Flutter (Widgets en lugar de QML)
2. **Re-implementar `core/client.py`** en Dart (httpx → http package)
3. **Re-implementar `core/repository.py`** en Dart (sqlite3 → sqflite)
4. **Mantener la misma API** del Módulo 1

## Equivalencias

| Python (actual) | Dart (Flutter) |
|----------------|----------------|
| `modulo_2_admin/core/client.py` | `lib/core/api_client.dart` |
| `modulo_2_admin/core/models.py` | `lib/core/models.dart` |
| `modulo_2_admin/core/repository.py` | `lib/core/local_repo.dart` |
| `modulo_2_admin/ui/qml/main.qml` | `lib/ui/screens/` |
| `modulo_2_admin/ui/main.py` (bridge) | `lib/main.dart` |

## API Contract (no cambia)

El Módulo 1 expone endpoints REST. El cliente Flutter solo necesita
reemplazar `httpx` por `http` package de Dart:

```dart
// Python: httpx.Client().post(url, json=payload)
// Dart:   http.post(Uri.parse(url), body: jsonEncode(payload))
```

## Dependencias Flutter necesarias

```yaml
dependencies:
  http: ^1.0.0
  sqflite: ^2.3.0
  path_provider: ^2.1.0
  intl: ^0.19.0
  url_launcher: ^6.2.0  # para abrir wa.me links
  share_plus: ^7.0.0    # para compartir resultados
```

## Proceso de migración

1. `flutter create modulo_2_flutter`
2. Copiar `lib/core/` de este folder (traducido a Dart)
3. Re-implementar cada screen de `qml/` como Widgets
4. Probar contra el Módulo 1
