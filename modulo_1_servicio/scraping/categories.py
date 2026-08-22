from __future__ import annotations

# Catálogo de categorías de búsqueda curadas para NovaSearch.
# Cada adaptador (adapters/*.yaml) declara en `categories:` los ids aquí listados
# bajo los cuales debe aparecer al buscar.

SEARCH_CATEGORIES: list[dict] = [
    {"id": "general",     "label": "🌐 Todo",             "emoji": "🌐", "description": "Búsqueda general en todos los clasificados"},
    {"id": "inmuebles",   "label": "🏠 Inmuebles",         "emoji": "🏠", "description": "Casas, apartamentos, terrenos y locales"},
    {"id": "vehiculos",   "label": "🚗 Vehículos",         "emoji": "🚗", "description": "Autos, motos, bicicletas y repuestos"},
    {"id": "electronica", "label": "💻 Electrónica",       "emoji": "💻", "description": "Laptops, celulares, TVs y cámaras"},
    {"id": "hogar",       "label": "🛋️ Hogar y Muebles",   "emoji": "🛋️", "description": "Muebles, electrodomésticos y decoración"},
    {"id": "moda",        "label": "👗 Moda y Accesorios", "emoji": "👗", "description": "Ropa, calzado y accesorios"},
    {"id": "empleo",      "label": "💼 Empleo y Servicios","emoji": "💼", "description": "Ofertas de trabajo y servicios"},
    {"id": "animales",    "label": "🐾 Animales",          "emoji": "🐾", "description": "Mascotas, venta y adopción"},
    {"id": "educacion",   "label": "📚 Educación",         "emoji": "📚", "description": "Libros, cursos y materiales"},
]

LABEL_TO_ID: dict[str, str] = {c["label"]: c["id"] for c in SEARCH_CATEGORIES}
