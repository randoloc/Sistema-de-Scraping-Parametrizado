"""Bot de Telegram para búsqueda multi-adaptador.

Flujo:
1. Usuario envía mensaje al bot (ej: "casa en La Habana")
2. El bot busca en todos los adaptadores cargados
3. El bot responde con los resultados formateados

Requiere:
- TELEGRAM_BOT_TOKEN: Token del bot (de @BotFather)
- Opcional: TELEGRAM_BOT_MODE=polling|webhook (defecto: polling)
- Opcional: TELEGRAM_ALLOWED_USERS: lista de user_ids separados por coma
  (si no se especifica, se permite a cualquier usuario)
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx

from modulo_1_servicio.scraping.adapters.loader import AdapterLoader
from modulo_1_servicio.scraping.engine import Orchestrator
from modulo_1_servicio.scraping.extractors.beautifulsoup_extractor import (
    BeautifulSoupExtractor,
)
from modulo_1_servicio.scraping.models import (
    FieldDefinition,
    FieldType,
    ScrapeConfig,
    SourceType,
)
from modulo_1_servicio.scraping.normalizer import ResultNormalizer

logger = logging.getLogger(__name__)

API_BASE = "https://api.telegram.org/bot"
MAX_RESULTS = 10  # resultados máximos por búsqueda
MAX_MSG_LEN = 4000  # Telegram max message length


class TelegramBot:
    """Bot de Telegram que busca en múltiples adaptadores.

    Uso:
        bot = TelegramBot()
        asyncio.run(bot.polling_loop())  # modo polling

    O con webhook (requiere URL pública):
        await bot.set_webhook("https://midominio.com/webhook")
    """

    def __init__(self) -> None:
        self._token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self._allowed_users: list[int] | None = None
        raw = os.environ.get("TELEGRAM_ALLOWED_USERS", "")
        if raw:
            self._allowed_users = [int(u.strip()) for u in raw.split(",") if u.strip()]

        # Motor de búsqueda compartido
        self._adapter_loader = AdapterLoader()
        self._adapter_loader.load_all()
        self._orchestrator = Orchestrator()
        self._orchestrator.register_engine("web_page", BeautifulSoupExtractor())
        self._normalizer = ResultNormalizer()

        self._last_update_id = 0

    # ─── API Calls ─────────────────────────────────────────────────

    async def _api_request(
        self,
        method: str,
        params: dict | None = None,
        json_body: dict | None = None,
    ) -> dict[str, Any]:
        """Hace una llamada a la API de Telegram."""
        url = f"{API_BASE}{self._token}/{method}"
        async with httpx.AsyncClient() as client:
            if json_body:
                resp = await client.post(url, json=json_body, timeout=30)
            else:
                resp = await client.get(url, params=params, timeout=30)
            data = resp.json()
            if not data.get("ok"):
                logger.error("Telegram API error [%s]: %s", method, data.get("description"))
            return data

    async def get_me(self) -> dict[str, Any]:
        """Obtiene información del bot."""
        data = await self._api_request("getMe")
        return data.get("result", {})

    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "HTML",
    ) -> dict[str, Any]:
        """Envía un mensaje de texto."""
        return await self._api_request(
            "sendMessage",
            json_body={
                "chat_id": chat_id,
                "text": text[:MAX_MSG_LEN],
                "parse_mode": parse_mode,
            },
        )

    async def send_typing(self, chat_id: int) -> None:
        """Muestra 'escribiendo...' en el chat."""
        await self._api_request(
            "sendChatAction",
            json_body={"chat_id": chat_id, "action": "typing"},
        )

    async def get_updates(self, timeout: int = 30) -> list[dict[str, Any]]:
        """Obtiene actualizaciones (modo polling)."""
        data = await self._api_request(
            "getUpdates",
            params={
                "offset": self._last_update_id + 1,
                "timeout": timeout,
                "allowed_updates": ["message"],
            },
        )
        return data.get("result", [])

    async def set_webhook(self, url: str) -> dict[str, Any]:
        """Configura webhook (modo producción)."""
        return await self._api_request(
            "setWebhook",
            json_body={"url": url},
        )

    async def delete_webhook(self) -> dict[str, Any]:
        """Elimina webhook."""
        return await self._api_request("deleteWebhook")

    # ─── Lógica de Búsqueda ───────────────────────────────────────

    async def _search(self, query: str) -> str:
        """Ejecuta búsqueda en todos los adaptadores y formatea resultado."""
        matching = self._adapter_loader.get_all()
        if not matching:
            return "😕 No hay adaptadores configurados. Agrega archivos YAML en adapters/."

        items: list[dict] = []
        total_rank = 0

        for adapter in matching:
            search_url = adapter.search_url
            if "{query}" in search_url:
                from urllib.parse import quote
                search_url = search_url.replace("{query}", quote(query))

            fields = tuple(
                FieldDefinition(
                    name=f.name,
                    selector=f.selector,
                    field_type=(
                        FieldType(f.type)
                        if f.type in ("text", "price", "url", "number", "date", "image")
                        else FieldType.TEXT
                    ),
                    required=f.required,
                )
                for f in adapter.fields
            )

            config = ScrapeConfig(
                source_type=SourceType.WEB_PAGE,
                source=search_url,
                fields=fields,
                container_selector=adapter.container_selector,
                rate_limit=1.0,
            )

            try:
                result = await self._orchestrator.run(config)
                if not result.items:
                    continue

                raw_items = [item.data for item in result.items]
                if adapter.canonical_map:
                    canonical = self._normalizer.normalize(
                        canonical_map=adapter.canonical_map,
                        raw_items=raw_items,
                        source_site=adapter.name,
                        source_url=search_url,
                        start_rank=total_rank,
                    )
                    for item in canonical:
                        items.append({
                            "rank": item.rank + 1,
                            "title": item.title or "(Sin título)",
                            "description": (item.description or "")[:120],
                            "price": f"${item.price:,.2f}" if item.price is not None else "",
                            "site": item.source_site,
                            "url": item.url or "",
                        })
                    total_rank += len(canonical)
                else:
                    first_field = adapter.fields[0].name if adapter.fields else ""
                    for j, raw in enumerate(raw_items):
                        items.append({
                            "rank": total_rank + j + 1,
                            "title": raw.get(first_field, "(Sin título)"),
                            "description": "",
                            "price": "",
                            "site": adapter.name,
                            "url": "",
                        })
                    total_rank += len(raw_items)
            except Exception as exc:
                logger.error("Error en adaptador %s: %s", adapter.name, exc)

        if not items:
            return f"😕 No encontré resultados para '<b>{query}</b>'."

        # Limitar resultados
        items = items[:MAX_RESULTS]

        # Formatear como HTML
        lines = [
            f"🔍 <b>Resultados para:</b> {query}",
            f"📊 <b>Total:</b> {total_rank} items ({len(items)} mostrados)",
            "",
        ]
        for it in items:
            line = f"<b>{it['rank']}. {it['title']}</b>"
            if it.get("price"):
                line += f"\n💰 {it['price']}"
            if it.get("description"):
                line += f"\n📝 {it['description']}"
            line += f"\n📍 {it['site']}"
            if it.get("url"):
                line += f"\n🔗 {it['url']}"
            lines.append(line)
            lines.append("—" * 20)

        return "\n".join(lines)

    # ─── Manejador de Mensajes ────────────────────────────────────

    def _is_allowed(self, user_id: int) -> bool:
        """Verifica si el usuario está autorizado."""
        if self._allowed_users is None:
            return True  # todos permitidos
        return user_id in self._allowed_users

    async def _handle_message(self, msg: dict[str, Any]) -> None:
        """Procesa un mensaje entrante."""
        chat_id = msg.get("chat", {}).get("id")
        user_id = msg.get("from", {}).get("id")
        text = (msg.get("text") or "").strip()
        first_name = msg.get("from", {}).get("first_name", "Usuario")

        if not chat_id or not text:
            return

        # Verificar autorización
        if not self._is_allowed(user_id):
            await self.send_message(
                chat_id,
                f"⛔ Lo siento, {first_name}. No estás autorizado para usar este bot.",
            )
            return

        # Comandos
        if text.startswith("/"):
            await self._handle_command(chat_id, text, first_name)
            return

        # Si no es comando, tratar como búsqueda
        await self.send_typing(chat_id)
        result = await self._search(text)
        await self.send_message(chat_id, result)

    async def _handle_command(
        self, chat_id: int, text: str, first_name: str
    ) -> None:
        """Maneja comandos del bot."""
        cmd = text.split()[0].lower()

        if cmd == "/start":
            await self.send_message(
                chat_id,
                f"👋 Hola <b>{first_name}</b>!\n\n"
                "Soy el bot de <b>ScrapperGenérico</b>. 🔍\n\n"
                "📌 <b>¿Cómo usarme?</b>\n"
                "Solo escríbeme lo que buscas y te traeré resultados\n"
                "de múltiples sitios de clasificados.\n\n"
                "Ejemplos:\n"
                "• <i>casa 3 habitaciones La Habana</i>\n"
                "• <i>laptop usada Cuba</i>\n"
                "• <i>Chevrolet 1955</i>\n\n"
                "Comandos:\n"
                "/search &lt;query&gt; — Buscar explícitamente\n"
                "/sites — Listar sitios disponibles\n"
                "/help — Esta ayuda",
            )
        elif cmd == "/help":
            await self.send_message(
                chat_id,
                "📖 <b>Ayuda</b>\n\n"
                "Escribe cualquier texto para buscar.\n\n"
                "Comandos:\n"
                "/start — Iniciar bot\n"
                "/search &lt;consulta&gt; — Buscar\n"
                "/sites — Ver sitios disponibles\n"
                "/help — Mostrar ayuda\n\n"
                "💡 <b>Tips:</b>\n"
                "• Sé específico en tu búsqueda\n"
                "• Incluye ubicación si aplica\n"
                "• Los resultados se limitan a 10 items",
            )
        elif cmd == "/sites":
            adapters = self._adapter_loader.get_all()
            if not adapters:
                await self.send_message(
                    chat_id, "📭 No hay sitios configurados aún."
                )
                return
            lines = ["🌐 <b>Sitios Disponibles:</b>\n"]
            for a in adapters:
                lines.append(f"• <b>{a.name}</b> — {a.site} ({a.vertical})")
            lines.append(
                f"\n📊 Total: {len(adapters)} sitios"
            )
            await self.send_message(chat_id, "\n".join(lines))
        elif cmd.startswith("/search"):
            query = text[len("/search"):].strip()
            if not query:
                await self.send_message(
                    chat_id,
                    "🔍 Usa: /search &lt;lo que buscas&gt;\n"
                    "Ej: /search casa La Habana",
                )
                return
            await self.send_typing(chat_id)
            result = await self._search(query)
            await self.send_message(chat_id, result)
        else:
            await self.send_message(
                chat_id,
                f"❌ Comando no reconocido: {cmd}\n"
                "Usa /help para ver los comandos disponibles.",
            )

    # ─── Bucle Principal ──────────────────────────────────────────

    async def polling_loop(self, interval: float = 1.0) -> None:
        """Bucle infinito de polling.

        Args:
            interval: Segundos entre cada poll (default: 1.0).
        """
        if not self._token:
            logger.error(
                "TELEGRAM_BOT_TOKEN no configurado. "
                "Define la variable de entorno."
            )
            return

        try:
            me = await self.get_me()
            logger.info(
                "Bot iniciado: @%s (ID: %s)",
                me.get("username", "?"),
                me.get("id", "?"),
            )
        except Exception as exc:
            logger.error("No pude conectar con Telegram: %s", exc)
            return

        logger.info("Modo polling activo (intervalo=%ss)", interval)

        while True:
            try:
                updates = await self.get_updates()
                for update in updates:
                    self._last_update_id = update.get("update_id", 0)
                    msg = update.get("message")
                    if msg:
                        await self._handle_message(msg)
            except Exception as exc:
                logger.error("Error en polling loop: %s", exc)

            await asyncio.sleep(interval)

    # ─── Entry point para script independiente ────────────────────

    @staticmethod
    def run_polling() -> None:
        """Entry point para correr el bot en modo polling."""
        bot = TelegramBot()
        asyncio.run(bot.polling_loop())
