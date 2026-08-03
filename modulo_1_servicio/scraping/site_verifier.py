"""Verificador de accesibilidad para nuevos sitios.

Permite probar si un dominio cubano de clasificados es accesible desde
la red actual (DNS resuelve + HTTP responde) ANTES de integrarlo como
adaptador. Esto evita agregar sitios que están caídos o bloqueados.

Uso:
    result = check_accessibility("itencel.com")
    # → {"domain": ..., "dns_ok": True, "http_status": 200, ...}

    yaml_text = build_adapter_yaml(
        name="itencel", site="itencel.com", vertical="general",
        search_url="https://itencel.com/?q={query}",
    )
"""

from __future__ import annotations

import logging
import socket
import time
from typing import Any
from urllib.parse import urlparse

import httpx

from modulo_1_servicio.scraping.anti_scraping import UARotator
from modulo_1_servicio.scraping.url_utils import normalize_url

logger = logging.getLogger(__name__)

# Umbral: HTML menor a esto sugiere una SPA que no renderiza contenido
# (ej: alaventa.com → 1KB, apululu.com → 114B).
SPA_EMPTY_THRESHOLD_BYTES = 2048

# Timeout corto para verificación rápida
CHECK_TIMEOUT = 10.0

_ua_rotator = UARotator()

# Códigos que indican bloqueo anti-bot / acceso denegado
_FORBIDDEN_STATUS = {403, 429}
_REDIRECT_STATUS = {301, 302, 303, 307, 308}


def _resolve_dns(host: str) -> tuple[bool, list[str]]:
    """Intenta resolver el host a una IP.

    Returns:
        (ok, ip_list): si resolvió y las IPs encontradas.
    """
    try:
        infos = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
        ips = sorted({info[4][0] for info in infos})
        return (True, ips)
    except socket.gaierror as exc:
        logger.info("DNS falló para %s: %s", host, exc)
        return (False, [])


async def check_accessibility(domain: str) -> dict[str, Any]:
    """Verifica si un dominio es accesible (DNS + HTTP).

    Args:
        domain: Dominio o URL (ej: ``itencel.com`` o ``https://itencel.com``).

    Returns:
        Diccionario con el resultado de la verificación:
        - ``domain``: dominio normalizado
        - ``dns_ok``: si el DNS resolvió
        - ``ips``: IPs resueltas
        - ``http_ok``: si el HTTP respondió
        - ``http_status``: código de estado (0 si falló)
        - ``response_time_ms``: tiempo de respuesta
        - ``content_length``: tamaño del HTML
        - ``likely_spa``: True si el HTML es demasiado pequeño (SPA vacío)
        - ``blocked``: True si respondió 403/429 (anti-bot)
        - ``message``: mensaje legible en español
        - ``accessible``: booleano final (usable como adaptador BS4)
    """
    try:
        url = normalize_url(domain)
    except ValueError as exc:
        return {
            "domain": domain,
            "accessible": False,
            "dns_ok": False,
            "http_ok": False,
            "http_status": 0,
            "response_time_ms": 0,
            "content_length": 0,
            "likely_spa": False,
            "blocked": False,
            "message": f"URL inválida: {exc}",
        }

    parsed = urlparse(url)
    host = parsed.netloc.split(":")[0]

    # 1. DNS
    dns_ok, ips = _resolve_dns(host)
    if not dns_ok:
        return {
            "domain": host,
            "accessible": False,
            "dns_ok": False,
            "http_ok": False,
            "http_status": 0,
            "response_time_ms": 0,
            "content_length": 0,
            "likely_spa": False,
            "blocked": False,
            "message": f"❌ DNS no resuelve '{host}'. El dominio no existe o está bloqueado.",
        }

    # 2. HTTP
    headers = {"User-Agent": _ua_rotator.get_ua()}
    http_ok = False
    http_status = 0
    content_length = 0
    response_time_ms = 0
    redirected_to: str | None = None
    message = ""

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(CHECK_TIMEOUT),
            follow_redirects=True,
        ) as client:
            started = time.monotonic()
            resp = await client.get(url, headers=headers)
            elapsed_ms = (time.monotonic() - started) * 1000
            response_time_ms = round(elapsed_ms)

            http_ok = True
            http_status = resp.status_code
            content_length = len(resp.text.encode("utf-8"))
            if str(resp.url) != url:
                redirected_to = str(resp.url)

            if http_status in _FORBIDDEN_STATUS:
                message = (
                    f"⚠️ HTTP {http_status} — el sitio responde pero bloquea el acceso "
                    f"(anti-bot). Puede funcionar desde un datacenter (HF), no desde Cuba."
                )
                blocked = True
            elif http_status >= 400:
                message = f"❌ HTTP {http_status} — el sitio responde con error."
                blocked = False
            elif content_length < SPA_EMPTY_THRESHOLD_BYTES:
                message = (
                    f"⚠️ HTTP {http_status} pero HTML muy pequeño ({content_length} bytes). "
                    f"Probablemente es una SPA que renderiza con JS — requiere adaptador Python."
                )
                blocked = False
            else:
                message = f"✅ HTTP {http_status} — sitio accesible con contenido real."
                blocked = False

    except httpx.TimeoutException:
        message = f"❌ Timeout después de {CHECK_TIMEOUT}s. Sitio lento o sin respuesta."
        blocked = False
    except httpx.RequestError as exc:
        message = f"❌ Error de red: {exc}"
        blocked = False

    return {
        "domain": host,
        "accessible": (
            dns_ok and http_ok and http_status < 400
            and http_status not in _FORBIDDEN_STATUS
            and content_length >= SPA_EMPTY_THRESHOLD_BYTES
        ),
        "dns_ok": dns_ok,
        "http_ok": http_ok,
        "http_status": http_status,
        "response_time_ms": response_time_ms,
        "content_length": content_length,
        "likely_spa": content_length < SPA_EMPTY_THRESHOLD_BYTES,
        "blocked": http_status in _FORBIDDEN_STATUS,
        "redirected_to": redirected_to,
        "ips": ips[:5],
        "message": message,
    }


def build_adapter_yaml(
    name: str,
    site: str,
    vertical: str,
    search_url: str,
    container_selector: str = "",
    fields: list[dict[str, str]] | None = None,
) -> str:
    """Genera el contenido YAML de un adaptador nuevo.

    Args:
        name: Identificador único del adaptador (ej: ``itencel``).
        site: Dominio (ej: ``itencel.com``).
        vertical: Categoría (ej: ``general``, ``cars``).
        search_url: URL de búsqueda con template ``{query}``.
        container_selector: Selector CSS del contenedor de resultados.
        fields: Lista de campos [{name, selector, type}]. Si es None,
            se generan campos por defecto (titulo, url).

    Returns:
        Contenido YAML listo para guardar en ``adapters/{name}.yaml``.
    """
    field_lines = []
    for f in fields or [{"name": "titulo", "selector": "", "type": "text"}]:
        required = "required: false" if f.get("required") is False else ""
        field_lines.append(
            f"  - name: {f['name']}\n"
            f"    selector: \"{f['selector']}\"\n"
            f"    type: {f.get('type', 'text')}"
            + (f"\n    {required}" if required else "")
        )

    container_line = (
        f'container_selector: "{container_selector}"'
        if container_selector
        else "# TODO: inspecciona el HTML y define el contenedor de resultados"
    )

    return (
        f"# Adaptador: {name} ({site})\n"
        f"# Vertical: {vertical}\n"
        f"# GENERADO DESDE LA UI (verificado por site_verifier)\n"
        f"name: {name}\n"
        f"site: {site}\n"
        f"vertical: {vertical}\n"
        f'search_url: "{search_url}"\n'
        f"{container_line}\n"
        f"fields:\n"
        + "\n".join(field_lines)
        + "\n"
    )
