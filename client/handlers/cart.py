"""Cart-related client handlers and API helpers.

Provides async helpers to call the backend Order API and callback
handlers to let users view and manage their cart inside Telegram.
"""

import aiohttp
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery

from data.config import config_settings
from data.url import url_order
from client.keyboards.inline import cart_action_keyboard, main_keyboard, choose_product_keyboard

logger = logging.getLogger(__name__)
cart_router = Router()

# =================================================================================================
# API helpers
# =================================================================================================
async def _headers() -> dict:
    """Return headers with the bot API key for backend requests."""
    return {"X-Bot-Api-Key": config_settings.BOT_API_KEY.get_secret_value()}

async def get_cart(user_id: int) -> dict | None:
    """Fetch the current cart for the provided Telegram user id."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{url_order}cart/",
                headers=await _headers(),
                params={"user_id": user_id},
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.error("Failed to fetch cart, status=%s, body=%s", resp.status, await resp.text())
    except Exception as e:
        logger.exception("Error fetching cart: %s", e)
    return None

async def add_to_cart(order_id: int, product_id: int, quantity: int = 1) -> dict | None:
    """Add a product to the cart by product id and quantity."""
    payload = {"product_id": product_id, "quantity": quantity}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{url_order}{order_id}/add_item/",
                headers=await _headers(),
                json=payload,
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.error("Failed to add item, status=%s, body=%s", resp.status, await resp.text())
    except Exception as e:
        logger.exception("Error adding to cart: %s", e)
    return None

async def update_cart_item(order_id: int, product_id: int, delta: int | None = None, quantity: int | None = None) -> dict | None:
    """Update cart item either by delta increment or by setting absolute quantity."""
    payload = {"product_id": product_id}
    if delta is not None:
        payload["delta"] = delta
    if quantity is not None:
        payload["quantity"] = quantity
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{url_order}{order_id}/update_item/",
                headers=await _headers(),
                json=payload,
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.error("Failed to update item, status=%s, body=%s", resp.status, await resp.text())
    except Exception as e:
        logger.exception("Error updating cart item: %s", e)
    return None

async def remove_cart_item(order_id: int, product_id: int) -> dict | None:
    """Remove the specified product from the cart."""
    payload = {"product_id": product_id}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{url_order}{order_id}/remove_item/",
                headers=await _headers(),
                json=payload,
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.error("Failed to remove item, status=%s, body=%s", resp.status, await resp.text())
    except Exception as e:
        logger.exception("Error removing cart item: %s", e)
    return None

# =================================================================================================
# Cart handlers
# =================================================================================================
@cart_router.callback_query(F.data.startswith("add_to_cart_"))
async def add_product_to_cart(callback: CallbackQuery):
    """Handle 'add_to_cart_<product_id>' callback and ensure cart exists."""
    try:
        product_id = int(callback.data.split("_")[-1])
    except (IndexError, ValueError):
        await callback.answer("Error: invalid data", show_alert=True)
        return

    user_id = callback.from_user.id
    cart = await get_cart(user_id)

    if not cart:
        payload = {"user_id": user_id, "status_id": 2, "delivery_id": 1}  # 2 — Created, 1 — delivery placeholder
        async with aiohttp.ClientSession() as session:
            async with session.post(url_order, headers=await _headers(), json=payload) as resp:
                if resp.status == 201:
                    cart = await resp.json()
                else:
                    await callback.answer("Failed to create cart", show_alert=True)
                    return

    added = await add_to_cart(cart["id"], product_id, quantity=1)
    if added:
        await callback.answer("Added to cart")
    else:
        await callback.answer("Failed to add", show_alert=True)


@cart_router.callback_query(F.data == "view_cart")
async def view_cart(callback: CallbackQuery):
    """Show a formatted summary of the user's current cart."""
    user_id = callback.from_user.id
    cart = await get_cart(user_id)
    if not cart or not cart.get("items"):
        await callback.message.edit_text("Your cart is empty.", reply_markup=main_keyboard())
        return

    lines = [f"Cart #{cart['id']}:"]
    for it in cart["items"]:
        p = it["product"]
        lines.append(f"• {p['name']} — {it['quantity']} pcs (total: {float(p['price']) * it['quantity']}$)")
    lines.append(f"\nTotal: {float(cart['total'])}$")

    await callback.message.edit_text("\n".join(lines), reply_markup=cart_action_keyboard(cart["id"]))


@cart_router.callback_query(F.data.startswith("choose_"))
async def choose_product(callback: CallbackQuery):
    """Prompt the user to pick a specific product from the cart for an action."""
    try:
        _, action, order_id = callback.data.split("_", 2)
        order_id = int(order_id)
    except (ValueError, IndexError):
        await callback.answer("Invalid data", show_alert=True)
        return

    cart = await get_cart(callback.from_user.id)
    if not cart or not cart.get("items"):
        await callback.answer("Cart is empty", show_alert=True)
        return

    await callback.message.edit_text(
        f"Select an item for action: {action}",
        reply_markup=choose_product_keyboard(order_id, action, cart["items"]),
    )


@cart_router.callback_query(F.data.startswith("increase_"))
async def increase_item(callback: CallbackQuery):
    """Increase quantity for the selected cart item by 1."""
    try:
        _, order_id, product_id = callback.data.split("_")
        order_id, product_id = int(order_id), int(product_id)
    except (ValueError, IndexError):
        await callback.answer("Invalid data", show_alert=True)
        return

    updated = await update_cart_item(order_id, product_id, delta=1)
    if updated:
        await callback.answer("Increased")
        await view_cart(callback)
    else:
        await callback.answer("Failed", show_alert=True)


@cart_router.callback_query(F.data.startswith("decrease_"))
async def decrease_item(callback: CallbackQuery):
    """Decrease quantity for the selected cart item by 1."""
    try:
        _, order_id, product_id = callback.data.split("_")
        order_id, product_id = int(order_id), int(product_id)
    except (ValueError, IndexError):
        await callback.answer("Invalid data", show_alert=True)
        return

    updated = await update_cart_item(order_id, product_id, delta=-1)
    if updated:
        await callback.answer("Decreased")
        await view_cart(callback)
    else:
        await callback.answer("Failed", show_alert=True)


@cart_router.callback_query(F.data.startswith("remove_"))
async def remove_item(callback: CallbackQuery):
    """Remove the selected product from the cart."""
    try:
        _, order_id, product_id = callback.data.split("_")
        order_id, product_id = int(order_id), int(product_id)
    except (ValueError, IndexError):
        await callback.answer("Invalid data", show_alert=True)
        return

    updated = await remove_cart_item(order_id, product_id)
    if updated:
        await callback.answer("Removed")
        await view_cart(callback)
    else:
        await callback.answer("Failed", show_alert=True)


@cart_router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    """Return to the main menu keyboard from the cart screen."""
    await callback.message.edit_text("Welcome back to main menu", reply_markup=main_keyboard())
