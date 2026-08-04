import aiohttp
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.api.services import CatalogAPI
from app.states.admin_product import ProductCreateState
from app.utils.photo import download_photo


def build_router(catalog_api: CatalogAPI, admin_filter) -> Router:
    router = Router()

    @router.callback_query(F.data == "admin:products", admin_filter)
    async def products(callback: CallbackQuery) -> None:
        products_data = await catalog_api.products()
        builder = InlineKeyboardBuilder()
        for product in products_data:
            builder.button(
                text=f"{product['name']} ({product['stock']})",
                callback_data=f"admin:product:{product['id']}",
            )
        builder.button(
            text="Create product",
            callback_data="admin:create_product",
        )
        builder.adjust(1)
        await callback.message.edit_text(
            "Products:",
            reply_markup=builder.as_markup(),
        )
        await callback.answer()

    @router.callback_query(
        F.data == "admin:create_product",
        admin_filter,
    )
    async def create_product(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        await state.clear()
        await callback.message.edit_text("Product name:")
        await state.set_state(ProductCreateState.name)
        await callback.answer()

    @router.message(ProductCreateState.name, admin_filter)
    async def product_name(
        message: Message,
        state: FSMContext,
    ) -> None:
        await state.update_data(name=message.text.strip())
        await message.answer("Description:")
        await state.set_state(ProductCreateState.description)

    @router.message(ProductCreateState.description, admin_filter)
    async def product_description(
        message: Message,
        state: FSMContext,
    ) -> None:
        await state.update_data(description=message.text.strip())
        await message.answer("Send product photo:")
        await state.set_state(ProductCreateState.photo)

    @router.message(ProductCreateState.photo, admin_filter)
    async def product_photo(
        message: Message,
        state: FSMContext,
    ) -> None:
        if not message.photo:
            await message.answer("Please send a photo.")
            return
        await state.update_data(photo=message.photo[-1].file_id)
        await message.answer("Price:")
        await state.set_state(ProductCreateState.price)

    @router.message(ProductCreateState.price, admin_filter)
    async def product_price(
        message: Message,
        state: FSMContext,
    ) -> None:
        try:
            price = float(message.text)
        except ValueError:
            await message.answer("Enter a valid price.")
            return
        if price <= 0:
            await message.answer("Price must be positive.")
            return
        await state.update_data(price=price)
        await message.answer("Stock:")
        await state.set_state(ProductCreateState.stock)

    @router.message(ProductCreateState.stock, admin_filter)
    async def product_stock(
        message: Message,
        state: FSMContext,
    ) -> None:
        try:
            stock = int(message.text)
        except ValueError:
            await message.answer("Enter a valid stock value.")
            return
        if stock < 0:
            await message.answer("Stock cannot be negative.")
            return

        await state.update_data(stock=stock)
        categories = await catalog_api.categories()
        builder = InlineKeyboardBuilder()
        for category in categories:
            builder.button(
                text=category["name"],
                callback_data=f"admin:category:{category['id']}",
            )
        builder.adjust(1)
        await message.answer(
            "Choose category:",
            reply_markup=builder.as_markup(),
        )
        await state.set_state(ProductCreateState.category)

    @router.callback_query(
        F.data.startswith("admin:category:"),
        ProductCreateState.category,
        admin_filter,
    )
    async def product_category(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        category_id = int(callback.data.split(":")[2])
        data = await state.get_data()
        photo = await download_photo(callback.bot, data["photo"])

        form = aiohttp.FormData()
        form.add_field("name", data["name"])
        form.add_field("description", data["description"])
        form.add_field("price", str(data["price"]))
        form.add_field("stock", str(data["stock"]))
        form.add_field("category_id", str(category_id))
        form.add_field(
            "photo",
            photo,
            filename="product.jpg",
            content_type="image/jpeg",
        )

        product = await catalog_api.create_product(form)
        await callback.message.edit_text(
            f"Product {product['name']} created."
        )
        await state.clear()
        await callback.answer()

    return router
