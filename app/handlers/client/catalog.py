from aiogram import F, Router
from aiogram.types import CallbackQuery, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.api.services import CatalogAPI
from app.keyboards.client import product_keyboard


def build_router(catalog_api: CatalogAPI) -> Router:
    router = Router()

    @router.callback_query(F.data == "catalog")
    async def catalog(callback: CallbackQuery) -> None:
        categories = await catalog_api.categories()
        builder = InlineKeyboardBuilder()
        for category in categories:
            builder.button(
                text=category["name"],
                callback_data=f"category:{category['id']}",
            )
        builder.button(text="Back", callback_data="main")
        builder.adjust(1)
        await callback.message.edit_text(
            "Choose a category:",
            reply_markup=builder.as_markup(),
        )
        await callback.answer()

    @router.callback_query(F.data.startswith("category:"))
    async def category(callback: CallbackQuery) -> None:
        category_id = int(callback.data.split(":")[1])
        children = await catalog_api.categories(category_id)
        builder = InlineKeyboardBuilder()

        if children:
            for child in children:
                builder.button(
                    text=child["name"],
                    callback_data=f"category:{child['id']}",
                )
            text = "Choose a subcategory:"
        else:
            products = await catalog_api.products(category_id)
            for product in products:
                if product["is_available"]:
                    builder.button(
                        text=product["name"],
                        callback_data=(
                            f"product:{product['id']}:{category_id}"
                        ),
                    )
            text = "Choose a product:"

        builder.button(text="Back", callback_data="catalog")
        builder.adjust(1)
        await callback.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
        )
        await callback.answer()

    @router.callback_query(F.data.startswith("product:"))
    async def product(callback: CallbackQuery) -> None:
        _, product_id, category_id = callback.data.split(":")
        product_data = await catalog_api.product(int(product_id))
        caption = (
            f"<b>{product_data['name']}</b>\n"
            f"Price: ${product_data['price']}\n\n"
            f"{product_data['description']}"
        )
        try:
            await callback.message.edit_media(
                InputMediaPhoto(
                    media=product_data["photo"],
                    caption=caption,
                ),
                reply_markup=product_keyboard(
                    int(product_id),
                    int(category_id),
                ),
            )
        except Exception:
            await callback.message.answer_photo(
                product_data["photo"],
                caption=caption,
                reply_markup=product_keyboard(
                    int(product_id),
                    int(category_id),
                ),
            )
        await callback.answer()

    return router
