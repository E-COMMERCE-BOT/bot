import aiohttp
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InputMediaPhoto


from data.config import config_settings
from data.url import url_category, url_product
from client.keyboards.inline import product_keyboard, main_keyboard

logger = logging.getLogger(__name__)
catalog_router = Router()

# =================================================================================================
# API Helpers
# =================================================================================================

async def fetch_categories(parent: int = None) -> list:
    headers = {"X-Bot-Api-Key": config_settings.BOT_API_KEY.get_secret_value()}
    params = {}
    if parent is not None:
        params["parent"] = parent
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url_category, headers=headers, params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.error(f"Failed to fetch categories, status={resp.status}")
                return []
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        return []

async def fetch_products(category_id: int) -> list:
    headers = {"X-Bot-Api-Key": config_settings.BOT_API_KEY.get_secret_value()}
    params = {"category_id": category_id}
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url_product, headers=headers, params=params) as resp:
                if resp.status == 200:
                    products = await resp.json()
                    return [p for p in products if p.get("is_available")]
                logger.error(f"Failed to fetch products, status={resp.status}")
                return []
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        return []

async def fetch_product_by_id(product_id: int) -> dict | None:
    headers = {"X-Bot-Api-Key": config_settings.BOT_API_KEY.get_secret_value()}
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(f"{url_product}{product_id}/", headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.error(f"Failed to fetch product {product_id}, status={resp.status}")
                return None
    except Exception as e:
        logger.error(f"Error fetching product {product_id}: {e}")
        return None

# =================================================================================================
# Catalog Handlers
# =================================================================================================

@catalog_router.callback_query(F.data == "catalog_menu")
async def show_root_categories(callback: CallbackQuery):
    categories = await fetch_categories()
    if not categories:
        await callback.message.edit_text("No categories available.")
        return

    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=cat["name"], callback_data=f"category_{cat['id']}")
    builder.button(text="Back", callback_data="back_to_0")  # возврат в главное меню
    builder.adjust(1)

    await callback.message.edit_text(
        "Choose a category:",
        reply_markup=builder.as_markup()
    )

@catalog_router.callback_query(F.data.startswith("category_"))
async def show_category(callback: CallbackQuery, new_message: bool = False):
    category_id = int(callback.data.split("_")[-1])
    subcategories = await fetch_categories(parent=category_id)

    builder = InlineKeyboardBuilder()

    if subcategories:
        for sub in subcategories:
            builder.button(text=sub["name"], callback_data=f"category_{sub['id']}")
        builder.button(text="Back", callback_data=f"back_to_{0 if category_id == 0 else category_id}")
        builder.adjust(1)
        text = "Choose a subcategory:"
    else:
        products = await fetch_products(category_id)
        if not products:
            text = "No products in this category."
            if new_message:
                await callback.message.answer(text)
            else:
                await callback.message.edit_text(text)
            return

        for product in products:
            builder.button(text=product["name"], callback_data=f"product_{product['id']}_{category_id}")

        # ⬇️ Вот тут правим:
        categories = await fetch_categories()
        parent_id = 0
        for c in categories:
            if c["id"] == category_id:
                parent_id = c.get("parent", 0)
                break

        builder.button(text="Back", callback_data=f"back_to_{parent_id}")
        builder.adjust(1)
        text = "Products in this category:"

    if new_message:
        await callback.message.answer(text, reply_markup=builder.as_markup())
    else:
        await callback.message.edit_text(text, reply_markup=builder.as_markup())

@catalog_router.callback_query(F.data.startswith("product_"))
async def show_product(callback: CallbackQuery):
    _, product_id, category_id = callback.data.split("_")
    product = await fetch_product_by_id(int(product_id))

    if not product:
        await callback.message.edit_text("Product not found.")
        return

    caption = (
        f"<b>{product['name']}</b>\n"
        f"Price: ${product['price']}\n\n"
        f"{product['description']}"
    )

    try:
        await callback.message.edit_media(
            media=InputMediaPhoto(
                media=product["photo"],
                caption=caption,
                parse_mode="HTML"
            ),
            reply_markup=product_keyboard(product_id, category_id)
        )
    except Exception as e:
        logger.error(f"Failed to edit media: {e}")
        # fallback, если сообщение не фото
        await callback.message.answer_photo(
            photo=product["photo"],
            caption=caption,
            parse_mode="HTML",
            reply_markup=product_keyboard(product_id, category_id)
        )

@catalog_router.callback_query(F.data.startswith("back_to_"))
async def go_back(callback: CallbackQuery):
    category_id = int(callback.data.split("_")[-1])

    try:
        if category_id == 0:
            # Корневая категория → главное меню
            await callback.message.edit_text(
                "Welcome back to main menu",
                reply_markup=main_keyboard()
            )
        else:
            # Если текущее сообщение с фото (карточка товара)
            if callback.message.photo:
                await callback.message.delete()
                # Создаём новое сообщение с категориями/товарами
                await show_category(callback, new_message=True)
            else:
                # Просто редактируем текст
                await show_category(callback)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback.answer()
        else:
            raise