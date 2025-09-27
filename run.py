"""Entrypoint to run the Telegram bot using aiogram.

Initializes the bot, registers routers, sets public commands, and starts
long polling. Logs critical failures and ensures the session is closed.
"""

import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, types
from data.config import config_settings
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

from cmds.bot_cmds_list import bot_cmds_list
from client.handlers.start import start_router
from client.handlers.catalog import catalog_router
from client.handlers.cart import cart_router
from client.handlers.order import order_router
from admin.handlers.admin import admin_router
from admin.handlers.product import admin_product_router
from admin.handlers.order import admin_order_router

logger = logging.getLogger(__name__)

# Load environment variables from .env (optional convenience).
load_dotenv()

# Token may be present in env; the bot uses the value from config_settings.
TOKEN = os.getenv("TOKEN")

# Default properties for all messages sent by the bot (e.g., HTML parsing).
PROPERTIES = DefaultBotProperties(parse_mode=ParseMode.HTML)

# Global bot instance used by the dispatcher.
bot = Bot(token=config_settings.TOKEN.get_secret_value(), default=PROPERTIES)


def setup_routers(dp: Dispatcher) -> None:
    """Register all routers (admin first, then client flows)."""
    routers = (
        # Admin routers
        admin_router,
        admin_product_router,
        admin_order_router,
        # Client routers
        start_router,
        order_router,
        cart_router,
        catalog_router,
    )
    for router in routers:
        dp.include_router(router)


async def main():
    """Configure commands, include routers, and start polling."""
    dp = Dispatcher()

    await bot.set_my_commands(
        commands=bot_cmds_list, scope=types.BotCommandScopeAllPrivateChats()
    )
    setup_routers(dp)

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Bot crashed: {e}")
    finally:
        logger.info("Bot stopped")
        await bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
