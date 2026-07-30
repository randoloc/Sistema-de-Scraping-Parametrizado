"""Bot de Telegram para ScrapperGenérico.

Permite a los usuarios buscar información a través de Telegram.
Usa la API de Telegram sin librerías externas (solo httpx).
"""

from modulo_1_servicio.bot.telegram_bot import TelegramBot

__all__ = ["TelegramBot"]
