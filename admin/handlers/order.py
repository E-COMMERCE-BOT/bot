import aiohttp
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from utils.filters import IsAdminGroupMember
from admin.keyboards.inline import admin_keyboard
from data.url import url_order, url_status
from data.config import config_settings

logger = logging.getLogger(__name__)

admin_order_router = Router()

# =================================================================================================
# API Helpers
# =================================================================================================

async def fetch_orders() -> list:
    headers = {"X-Bot-Api-Key": config_settings.BOT_API_KEY.get_secret_value()}
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url_order, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.error(f"Failed to fetch orders, status={resp.status}")
                return []
    except aiohttp.ClientError as e:
        logger.error(f"Error fetching orders: {e}")
        return []


async def get_order_by_id(order_id: int) -> dict | None:
    headers = {"X-Bot-Api-Key": config_settings.BOT_API_KEY.get_secret_value()}
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(f"{url_order}{order_id}/", headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.error(f"Failed to fetch order {order_id}, status={resp.status}")
                return None
    except aiohttp.ClientError as e:
        logger.error(f"Error fetching order {order_id}: {e}")
        return None


async def fetch_statuses() -> list:
    headers = {"X-Bot-Api-Key": config_settings.BOT_API_KEY.get_secret_value()}
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get(url_status, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.error(f"Failed to fetch statuses, status={resp.status}")
                return []
    except aiohttp.ClientError as e:
        logger.error(f"Error fetching statuses: {e}")
        return []


async def update_order_status(order_id: int, status_id: int) -> dict | None:
    headers = {"X-Bot-Api-Key": config_settings.BOT_API_KEY.get_secret_value()}
    payload = {"status_id": status_id}
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.patch(f"{url_order}{order_id}/", json=payload, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.error(f"Failed to update order status, status={resp.status}")
                return None
    except aiohttp.ClientError as e:
        logger.error(f"Error updating order status: {e}")
        return None

# =================================================================================================
# Orders Menu Handlers
# =================================================================================================

@admin_order_router.callback_query(F.data == "orders_menu", IsAdminGroupMember())
async def show_orders(callback: CallbackQuery):
    orders = await fetch_orders()
    if not orders:
        await callback.message.edit_text("No orders found.", reply_markup=admin_keyboard())
        await callback.answer()
        return

    builder = InlineKeyboardBuilder()
    for order in orders:
        status_name = (order.get("status") or {}).get("name", "").lower()
        if status_name == "cart":
            continue

        number = order.get("number") or f"ORD-{int(order['id']):06d}"
        status = (order.get("status") or {}).get("name", "N/A")
        builder.button(
            text=f"{number} ({status})",
            callback_data=f"order_{order['id']}"
        )
    builder.button(text="Back", callback_data="back_to_admin")
    builder.adjust(1)

    await callback.message.edit_text(
        "Orders list:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@admin_order_router.callback_query(F.data.startswith("order_"), IsAdminGroupMember())
async def view_order(callback: CallbackQuery, state: FSMContext):
    order_id = callback.data.split("_")[-1]
    order = await get_order_by_id(order_id)
    if not order:
        await callback.message.answer("Order not found.")
        await callback.answer()
        return
    user = order.get("user", {})
    number = order.get("number") or f"ORD-{int(order['id']):06d}"
    status = (order.get("status") or {}).get("name", "N/A")
    customer_name = str(user.get("name"))
    customer_lastname = str(user.get("lastname"))
    surname = user.get("surname")
    customer_surname = "" if surname is None else str(surname)
    customer_phone = str(user.get("phone"))
    customer_address = str(user.get("address"))
    delivery = (order.get("delivery_type") or {}).get("name", "N/A")
    total = order.get("total")
    created_at = order.get("created_at")

    caption = (
        f"*Order {number}*\n"
        f"Status: {status}\n"
        f"Customer: {customer_name} {customer_lastname} {customer_surname}\n"
        f"Phone: {customer_phone}\n"
        f"Address: {customer_address}\n"
        f"Delivery: {delivery}\n"
        f"Total: ${total}\n"
        f"Date: {created_at}\n\n"
        f"*Items:*\n"
    )
    for item in order.get("items", []):
        product = item.get("product", {})
        caption += f"- {product.get('name')} x{item['quantity']} (${product.get('price')})\n"

    builder = InlineKeyboardBuilder()
    builder.button(text="Update Status", callback_data=f"choose_status_{order_id}")
    builder.button(text="Back", callback_data="orders_menu")
    builder.adjust(1)

    await callback.message.edit_text(
        caption,
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()


@admin_order_router.callback_query(F.data.startswith("choose_status_"), IsAdminGroupMember())
async def choose_status(callback: CallbackQuery):
    order_id = callback.data.split("_")[-1]
    statuses = await fetch_statuses()

    builder = InlineKeyboardBuilder()
    for s in statuses:
        if s["name"].lower() == "cart":
            continue
        builder.button(
            text=s["name"],
            callback_data=f"update_status_{order_id}_{s['id']}"
        )
    builder.button(text="Back", callback_data=f"order_{order_id}")
    builder.adjust(1)

    await callback.message.edit_text(
        f"Select new status for order {order_id}:",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@admin_order_router.callback_query(F.data.startswith("update_status_"), IsAdminGroupMember())
async def handle_update_order_status(callback: CallbackQuery):
    _, _, order_id, status_id = callback.data.split("_")
    result = await update_order_status(int(order_id), int(status_id))

    if result:
        order = await get_order_by_id(order_id)
        if order:
            number = order.get("number") or f"ORD-{int(order['id']):06d}"
            status = (order.get("status") or {}).get("name", "N/A")
            await callback.message.edit_text(
                f"Order *{number}* status updated to *{status}*",
                parse_mode="Markdown",
                reply_markup=admin_keyboard()
            )
    else:
        await callback.message.answer("Failed to update order status.")

    await callback.answer()
