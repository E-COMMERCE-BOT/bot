import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.api.client import EcommerceAPI
from app.api.services import CatalogAPI, OrdersAPI, UsersAPI
from app.core.config import settings
from app.handlers.admin.main import build_router as build_admin_router
from app.handlers.admin.orders import build_router as build_admin_orders_router
from app.handlers.admin.products import build_router as build_admin_products_router
from app.handlers.client.cart import build_router as build_cart_router
from app.handlers.client.catalog import build_router as build_catalog_router
from app.handlers.client.checkout import build_router as build_checkout_router
from app.handlers.client.main_menu import build_router as build_main_menu_router
from app.handlers.client.start import build_router as build_start_router
from app.utils.admin_filter import IsAdminGroupMember


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    bot = Bot(
        token=settings.token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher()

    api_client = EcommerceAPI(
        base_url=settings.api_base_url,
        api_key=settings.bot_api_key.get_secret_value(),
        timeout=settings.request_timeout,
    )
    await api_client.start()

    users_api = UsersAPI(api_client)
    catalog_api = CatalogAPI(api_client)
    orders_api = OrdersAPI(api_client)
    admin_filter = IsAdminGroupMember(settings.admin_chat_id)

    dispatcher.include_router(build_admin_router(admin_filter))
    dispatcher.include_router(
        build_admin_products_router(catalog_api, admin_filter)
    )
    dispatcher.include_router(
        build_admin_orders_router(orders_api, admin_filter)
    )
    dispatcher.include_router(build_start_router(users_api))
    dispatcher.include_router(
        build_checkout_router(users_api, orders_api)
    )
    dispatcher.include_router(build_cart_router(orders_api))
    dispatcher.include_router(build_catalog_router(catalog_api))
    dispatcher.include_router(build_main_menu_router())

    try:
        await dispatcher.start_polling(bot)
    finally:
        await api_client.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
