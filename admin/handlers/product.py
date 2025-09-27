import aiohttp
import logging
from datetime import datetime
from typing import Union
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.filters import IsAdminGroupMember
from utils.photo import download_photo_from_telegram, validate_photo
from admin.keyboards.inline import (
    admin_keyboard,
    admin_product_keyboard,
    admin_cancel_keyboard,
    admin_edit_product_keyboard,
)
from data.url import url_product, url_category
from data.config import config_settings

logger = logging.getLogger(__name__)

admin_product_router = Router()

# ======================================================================================
# FSM
# ======================================================================================

class ProductForm(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_photo = State()
    waiting_for_price = State()
    waiting_for_stock = State()
    waiting_for_category = State()               
    waiting_for_category_tree = State()          

class UpdateProductForm(StatesGroup):
    product_id = State()
    editing_field = State()
    waiting_for_value = State()
    waiting_for_category_tree = State()         

# ======================================================================================
# API helpers
# ======================================================================================

async def fetch_categories(parent: int | None = None) -> list:
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

async def fetch_category_by_id(category_id: int) -> dict | None:
    headers = {"X-Bot-Api-Key": config_settings.BOT_API_KEY.get_secret_value()}
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(f"{url_category}{category_id}/", headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.error(f"Failed to fetch category {category_id}, status={resp.status}")
                return None
    except Exception as e:
        logger.error(f"Error fetching category {category_id}: {e}")
        return None

async def fetch_products() -> list:
    headers = {"X-Bot-Api-Key": config_settings.BOT_API_KEY.get_secret_value()}
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(f"{url_product}", headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.error(f"Failed to fetch products, status={resp.status}")
                return []
    except aiohttp.ClientError as e:
        logger.error(f"Error fetching products: {e}")
        return []

async def get_product_by_id(product_id: int) -> dict | None:
    products = await fetch_products()
    for product in products:
        if product.get("id") == int(product_id):
            return product
    return None

async def create_new_product(product_data: dict, photo_file_id: str | None, bot: Bot) -> dict | None:
    headers = {"X-Bot-Api-Key": config_settings.BOT_API_KEY.get_secret_value()}
    form_data = aiohttp.FormData()

    for key, value in product_data.items():
        if value is not None:
            form_data.add_field(key, str(value).lower() if isinstance(value, bool) else str(value))

    if photo_file_id:
        try:
            photo_content = await download_photo_from_telegram(bot, photo_file_id)
            form_data.add_field(
                "photo",
                photo_content,
                filename=f"product_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
                content_type="image/jpeg"
            )
        except Exception as e:
            logger.error(f"Failed to download photo: {e}")
            return None

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url_product, headers=headers, data=form_data) as response:
                body = await response.text()
                if response.status == 201:
                    return await response.json()
                logger.error(f"Failed to create product, status={response.status}, body={body}")
                return None
    except aiohttp.ClientError as e:
        logger.error(f"Network error creating product: {e}")
        return None

async def update_product(product_id: int, updated_fields: dict, bot: Bot | None = None) -> dict | None:
    headers = {"X-Bot-Api-Key": config_settings.BOT_API_KEY.get_secret_value()}
    form_data = aiohttp.FormData()

    for key, value in updated_fields.items():
        if key == "photo" and value and bot:
            try:
                photo_content = await download_photo_from_telegram(bot, value)
                form_data.add_field(
                    "photo",
                    photo_content,
                    filename=f"product_{product_id}.jpg",
                    content_type="image/jpeg"
                )
            except Exception as e:
                logger.error(f"Failed to download photo for update: {e}")
                return None
        elif value is not None:
            form_data.add_field(key, str(value).lower() if isinstance(value, bool) else str(value))

    try:
        async with aiohttp.ClientSession() as session:
            async with session.patch(f"{url_product}{product_id}/", headers=headers, data=form_data) as response:
                body = await response.text()
                if response.status == 200:
                    return await response.json()
                logger.error(f"Failed to update product {product_id}, status={response.status}, body={body}")
                return None
    except Exception as e:
        logger.error(f"Error updating product {product_id}: {e}")
        return None

# ======================================================================================
# Category tree rendering and navigation
# ======================================================================================

async def get_category_path(category_id: int) -> str:
    path = []
    current_id = category_id

    while current_id:
        category = await fetch_category_by_id(current_id)
        if not category:
            break
        path.append(category["name"])
        current_id = category.get("parent")
    return " > ".join(reversed(path))

async def render_category_level(
    source: Union[CallbackQuery, Message],
    parent_id: int | None,
    mode: str,
    state: FSMContext
):
    categories = await fetch_categories(parent=parent_id)
    builder = InlineKeyboardBuilder()

    if categories:
        for cat in categories:
            cb_data = f"admin_cat_{cat['id']}" if mode == "create" else f"admin_cat_edit_{cat['id']}"
            builder.button(text=cat["name"], callback_data=cb_data)
        builder.adjust(1)

        text = "Choose a category:" if parent_id is None else "Choose a subcategory:"

        if isinstance(source, CallbackQuery):
            await source.message.edit_text(text, reply_markup=builder.as_markup())
        else:
            await source.answer(text, reply_markup=builder.as_markup())

    else:
        path_key = "cat_path_create" if mode == "create" else "cat_path_edit"
        data = await state.get_data()
        path: list[int] = data.get(path_key, [])
        if not path:
            if isinstance(source, CallbackQuery):
                await source.message.edit_text("No categories available.")
            else:
                await source.answer("No categories available.")
            return

        leaf_category_id = path[-1]

        if mode == "create":
            name = data.get("name")
            description = data.get("description")
            price = data.get("price")
            stock = data.get("stock")
            photo_file_id = data.get("photo")

            product_data = {
                "name": name,
                "description": description,
                "price": price,
                "stock": stock,
                "category_id": leaf_category_id,
            }

            created = await create_new_product(product_data, photo_file_id, source.bot)
            if created:
                category_path = await get_category_path(leaf_category_id)
                caption = (
                    "Product created successfully!\n\n"
                    f"{name}\n"
                    f"Price: ${price}\n"
                    f"Stock: {stock}\n"
                    f"Category: {category_path}\n\n"
                    f"{description}"
                )
                photo_url = created.get("photo")
                try:
                    if photo_url:
                        await source.message.answer_photo(
                            photo=photo_url,
                            caption=caption,
                        )
                        await source.message.answer(
                            "Products Management:", reply_markup=admin_product_keyboard()
                        )

                    else:
                        await source.message.answer(
                            caption, reply_markup=admin_keyboard()
                        )
                except TelegramBadRequest:
                    await source.message.answer(
                        caption + "\n(Missing photo)", reply_markup=admin_keyboard()
                    )
                await state.clear()
            else:
                await source.message.answer(
                    "Failed to create product. Please try again.",
                    reply_markup=admin_keyboard()
                )
                await state.clear()
        else:
            product_id = data.get("product_id")
            if not product_id:
                await source.message.answer("No product selected.")
                await state.clear()
                return

            result = await update_product(int(product_id), {"category_id": leaf_category_id}, bot=source.bot)
            if result:
                category_id = result["category"]["id"] if isinstance(result.get("category"), dict) else result.get("category")
                category_path = await get_category_path(category_id) if category_id else "Unknown"

                caption = (
                    "Category updated successfully!\n\n"
                    f"{result['name']}\n"
                    f"Price: ${result['price']}\n"
                    f"Stock: {result['stock']}\n"
                    f"Category: {category_path}\n\n"
                    f"{result['description']}"
                )

                photo_url = result.get("photo")
                try:
                    if photo_url:
                        await source.message.answer_photo(photo=photo_url, caption=caption)
                    else:
                        await source.message.answer(caption + "\n(Missing photo)")
                except TelegramBadRequest:
                    await source.message.answer(caption + "\n(Missing photo)")

                await source.message.answer("Products Management:", reply_markup=admin_product_keyboard())
            else:
                await source.message.answer("Failed to update category.")
            await state.clear()

# ======================================================================================
# Product menu
# ======================================================================================

@admin_product_router.callback_query(F.data == "products_menu", IsAdminGroupMember())
async def show_products_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "Products Management:", reply_markup=admin_product_keyboard()
    )
    await callback.answer()

@admin_product_router.callback_query(F.data == "back_to_admin", IsAdminGroupMember())
async def back_to_admin_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "Welcome back to the admin panel!", reply_markup=admin_keyboard()
    )
    await callback.answer()

@admin_product_router.callback_query(F.data == "cancel_action", IsAdminGroupMember())
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Action cancelled. Returning to admin panel.", reply_markup=admin_keyboard()
    )
    await callback.answer()

# ======================================================================================
# Create product
# ======================================================================================

@admin_product_router.callback_query(F.data == "create_product", IsAdminGroupMember())
async def create_product(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Enter the product name:", reply_markup=admin_cancel_keyboard()
    )
    await state.set_state(ProductForm.waiting_for_name)
    await callback.answer()

@admin_product_router.message(ProductForm.waiting_for_name, IsAdminGroupMember())
async def process_product_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(
        "Enter the product description:", reply_markup=admin_cancel_keyboard()
    )
    await state.set_state(ProductForm.waiting_for_description)

@admin_product_router.message(ProductForm.waiting_for_description, IsAdminGroupMember())
async def process_product_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer(
        "Send the product photo:", reply_markup=admin_cancel_keyboard()
    )
    await state.set_state(ProductForm.waiting_for_photo)

@admin_product_router.message(ProductForm.waiting_for_photo, IsAdminGroupMember(), F.photo)
async def process_product_photo(message: Message, state: FSMContext):
    is_valid, result = await validate_photo(message)
    if not is_valid:
        await message.answer(result, reply_markup=admin_cancel_keyboard())
        return
    await state.update_data(photo=result)
    await message.answer(
        "Enter the product price:", reply_markup=admin_cancel_keyboard()
    )
    await state.set_state(ProductForm.waiting_for_price)

@admin_product_router.message(ProductForm.waiting_for_price, IsAdminGroupMember())
async def process_product_price(message: Message, state: FSMContext):
    try:
        await state.update_data(price=float(message.text))
        await message.answer(
            "Enter the product stock quantity:", reply_markup=admin_cancel_keyboard()
        )
        await state.set_state(ProductForm.waiting_for_stock)
    except ValueError:
        await message.answer("Please enter a valid price (e.g., 19.99).")

@admin_product_router.message(ProductForm.waiting_for_stock, IsAdminGroupMember())
async def process_product_stock(message: Message, state: FSMContext):
    try:
        await state.update_data(stock=int(message.text))
    except ValueError:
        await message.answer("Please enter a valid stock quantity (e.g., 100).")
        return

    await state.update_data(cat_path_create=[])
    await state.set_state(ProductForm.waiting_for_category_tree)
    await render_category_level(message, parent_id=None, mode="create", state=state)


@admin_product_router.callback_query(F.data.startswith("admin_cat_"), ProductForm.waiting_for_category_tree, IsAdminGroupMember())
async def admin_tree_create_forward(callback: CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split("_")[-1])
    data = await state.get_data()
    path = data.get("cat_path_create", [])
    path.append(cat_id)
    await state.update_data(cat_path_create=path)
    await render_category_level(callback, parent_id=cat_id, mode="create", state=state)
    await callback.answer()

@admin_product_router.callback_query(F.data == "admin_back_create", ProductForm.waiting_for_category_tree, IsAdminGroupMember())
async def admin_tree_create_back(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    path: list[int] = data.get("cat_path_create", [])
    if path:
        path.pop()
    await state.update_data(cat_path_create=path)
    parent_id = path[-1] if path else None
    await render_category_level(callback, parent_id=parent_id, mode="create", state=state)
    await callback.answer()

# ======================================================================================
# Edit product (change fields, including category via tree)
# ======================================================================================

@admin_product_router.callback_query(F.data == "edit_product", IsAdminGroupMember())
async def show_products_for_edit(callback: CallbackQuery):
    products = await fetch_products()
    if not products:
        await callback.message.edit_text("No products found.", reply_markup=admin_product_keyboard())
        return

    builder = InlineKeyboardBuilder()
    for product in products:
        builder.button(
            text=f"{product['name']} (ID {product['id']})",
            callback_data=f"edit_product_{product['id']}"
        )
    builder.button(text="Back", callback_data="products_menu")
    builder.adjust(1)

    await callback.message.edit_text("Choose a product to edit:", reply_markup=builder.as_markup())

@admin_product_router.callback_query(F.data.startswith("edit_product_"), IsAdminGroupMember())
async def edit_product(callback: CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[-1])
    await state.update_data(product_id=product_id)

    product = await get_product_by_id(product_id)
    if not product:
        await callback.message.answer("Product not found or deleted.")
        await state.clear()
        return

    caption = (
        f"{product['name']}\n"
        f"Price: ${product['price']}\n"
        f"Stock: {product['stock']}\n"
        f"Category: {product.get('category')}\n\n"
        f"{product['description']}"
    )

    await callback.message.edit_text(
        caption,
        reply_markup=admin_edit_product_keyboard()
    )
    await callback.answer()

@admin_product_router.callback_query(F.data.startswith("change_"), IsAdminGroupMember())
async def start_edit_field(callback: CallbackQuery, state: FSMContext):
    field = callback.data.replace("change_", "")
    await state.update_data(editing_field=field)

    if field == "category":
        await state.update_data(cat_path_edit=[])
        await state.set_state(UpdateProductForm.waiting_for_category_tree)
        await render_category_level(callback, parent_id=None, mode="edit", state=state)
    else:
        prompts = {
            "name": "Enter new product name:",
            "description": "Enter new product description:",
            "photo": "Send new product photo:",
            "price": "Enter new product price:",
            "stock": "Enter new stock quantity:",
        }
        await callback.message.edit_text(prompts.get(field, "Enter new value:"), reply_markup=admin_cancel_keyboard())
        await state.set_state(UpdateProductForm.waiting_for_value)

    await callback.answer()

@admin_product_router.callback_query(F.data.startswith("admin_cat_edit_"), UpdateProductForm.waiting_for_category_tree, IsAdminGroupMember())
async def admin_tree_edit_forward(callback: CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split("_")[-1])
    data = await state.get_data()
    path = data.get("cat_path_edit", [])
    path.append(cat_id)
    await state.update_data(cat_path_edit=path)
    await render_category_level(callback, parent_id=cat_id, mode="edit", state=state)
    await callback.answer()

@admin_product_router.callback_query(F.data == "admin_back_edit", UpdateProductForm.waiting_for_category_tree, IsAdminGroupMember())
async def admin_tree_edit_back(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    path: list[int] = data.get("cat_path_edit", [])
    if path:
        path.pop()
    await state.update_data(cat_path_edit=path)
    parent_id = path[-1] if path else None
    await render_category_level(callback, parent_id=parent_id, mode="edit", state=state)
    await callback.answer()

@admin_product_router.message(UpdateProductForm.waiting_for_value, IsAdminGroupMember())
async def process_update_field(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    product_id = data.get("product_id")
    field = data.get("editing_field")

    if not product_id or not field:
        await message.answer("Error: no product or field selected.")
        await state.clear()
        return

    updated_fields = {}
    if field == "photo":
        if not message.photo:
            await message.answer("Please send a photo.")
            return
        updated_fields["photo"] = message.photo[-1].file_id
    elif field in ("price", "stock"):
        try:
            updated_fields[field] = float(message.text) if field == "price" else int(message.text)
        except ValueError:
            await message.answer("Please enter a valid number.")
            return
    else:
        updated_fields[field] = message.text

    result = await update_product(int(product_id), updated_fields, bot=bot)

    if result:
        category_id = result["category"]["id"] if isinstance(result.get("category"), dict) else result.get("category")
        category_path = await get_category_path(category_id) if category_id else "Unknown"

        caption = (
            f"Product {field} updated successfully!\n\n"
            f"{result['name']}\n"
            f"Price: ${result['price']}\n"
            f"Stock: {result['stock']}\n"
            f"Category: {category_path}\n\n"
            f"{result['description']}"
        )

        photo_url = result.get("photo")
        try:
            if photo_url:
                await message.answer_photo(photo=photo_url, caption=caption)
            else:
                await message.answer(caption + "\n(Missing photo)")
        except TelegramBadRequest:
            await message.answer(caption + "\n(Missing photo)")

        await message.answer("Products Management:", reply_markup=admin_product_keyboard())
    else:
        await message.answer(f"Failed to update product {field}")

    await state.clear()
