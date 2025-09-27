import aiohttp
import logging
import re
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from data.config import config_settings
from data.url import url_order, url_delivery, url_users
from client.keyboards.inline import main_keyboard

logger = logging.getLogger(__name__)
order_router = Router()

name_pattern = re.compile(r"^[А-Яа-яA-Za-zёЁ\-]{2,}$")
email_pattern = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$")


def normalize_phone_number(phone: str) -> str | None:
    phone = re.sub(r"[^\d+]", "", phone)

    if phone.startswith("8") and len(phone) == 11:
        normalized = "+7" + phone[1:]
    elif phone.startswith("7") and len(phone) == 11:
        normalized = "+7" + phone[1:]
    elif phone.startswith("+") and 11 <= len(re.sub(r"\D", "", phone)) <= 15:
        normalized = phone
    else:
        return None
    
    if not re.fullmatch(r"^\+\d{11,15}$", normalized):
        return None
    return normalized

# =================================================================================================
# API Helpers
# =================================================================================================
async def _headers() -> dict:
    return {"X-Bot-Api-Key": config_settings.BOT_API_KEY.get_secret_value()}

async def get_cart(user_id: int) -> dict | None:
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

async def get_user_by_tg_id(tg_id: int) -> dict | None:
    headers = await _headers()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{url_users}{tg_id}/", headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
    except Exception as e:
        logger.error(f"Error fetching user {tg_id}: {e}")
    return None

# =================================================================================================
# FSM
# =================================================================================================

class CheckoutState(StatesGroup):
    waiting_for_name = State()
    waiting_for_lastname = State()
    waiting_for_surname = State()
    waiting_for_phone = State()
    waiting_for_address = State()
    choosing_delivery = State()
    confirming = State()

# =================================================================================================
# Checkout handlers
# =================================================================================================

@order_router.callback_query(F.data == "checkout")
async def start_checkout(callback: CallbackQuery, state: FSMContext):
    tg_id = callback.from_user.id
    user = await get_user_by_tg_id(tg_id)

    if user:
        await state.update_data(
            name=user.get("name"),
            lastname=user.get("lastname"),
            surname=user.get("surname"),
            phone=user.get("phone"),
            address=user.get("address"),
        )

        lines = [
            f"First name: {user.get('name') or '-'}",
            f"Last name: {user.get('lastname') or '-'}",
        ]
        if user.get("surname") not in (None, "", "-"):
            lines.append(f"Middle name: {user['surname']}")
        lines.extend([
            f"Phone: {user.get('phone') or '-'}",
            f"Address: {user.get('address') or '-'}",
        ])

        builder = InlineKeyboardBuilder()
        builder.button(text="Continue", callback_data="skip_to_delivery")
        builder.button(text="Edit information", callback_data="edit_user_data")
        builder.adjust(1)

        await callback.message.edit_text(
            "Your saved details:\n\n" + "\n".join(lines),
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text("Enter your first name:")
        await state.set_state(CheckoutState.waiting_for_name)

    await callback.answer()

@order_router.callback_query(F.data == "skip_to_delivery")
async def skip_to_delivery(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Enter your address:")
    await state.set_state(CheckoutState.waiting_for_address)

@order_router.callback_query(F.data == "edit_user_data")
async def edit_user_data(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Enter your first name:")
    await state.set_state(CheckoutState.waiting_for_name)

@order_router.message(CheckoutState.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    if not name_pattern.fullmatch(message.text.strip()):
        await message.answer("First name must contain only letters and be at least 2 characters. Please try again:")
        return
    await state.update_data(name=message.text.strip())
    await message.answer("Enter your last name:")
    await state.set_state(CheckoutState.waiting_for_lastname)

@order_router.message(CheckoutState.waiting_for_lastname)
async def process_lastname(message: Message, state: FSMContext):
    if not name_pattern.fullmatch(message.text.strip()):
        await message.answer("Last name must contain only letters and be at least 2 characters. Please try again:")
        return
    await state.update_data(lastname=message.text.strip())
    await message.answer("Enter your middle name (or '-' if none):")
    await state.set_state(CheckoutState.waiting_for_surname)

@order_router.message(CheckoutState.waiting_for_surname)
async def process_surname(message: Message, state: FSMContext):
    surname = None if message.text.strip() == "-" else message.text.strip()
    if surname and not name_pattern.fullmatch(surname):
        await message.answer("Middle name must contain only letters and be at least 2 characters. Please try again:")
        return
    await state.update_data(surname=surname)
    await message.answer("Enter your phone number in the format +79991234567:")
    await state.set_state(CheckoutState.waiting_for_phone)

@order_router.message(CheckoutState.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    normalized = normalize_phone_number(message.text.strip())
    if not normalized:
        await message.answer("Enter a valid phone number, for example: +79001234567")
        return
    await state.update_data(phone=normalized)
    await message.answer("Enter your address:")
    await state.set_state(CheckoutState.waiting_for_address)

@order_router.message(CheckoutState.waiting_for_address)
async def process_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)

    headers = await _headers()
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{url_delivery}", headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                deliveries = data.get("results", data) if isinstance(data, dict) else data
            else:
                deliveries = []

    if not deliveries:
        await message.answer("No delivery methods available")
        return

    builder = InlineKeyboardBuilder()
    for d in deliveries:
        builder.button(
            text=f"{d['name']} (+{d['price']}$)",
            callback_data=f"choose_delivery_{d['id']}"
        )
    builder.adjust(1)

    await message.answer("Choose a delivery method:", reply_markup=builder.as_markup())
    await state.set_state(CheckoutState.choosing_delivery)

@order_router.callback_query(F.data.startswith("choose_delivery_"), CheckoutState.choosing_delivery)
async def choose_delivery(callback: CallbackQuery, state: FSMContext):
    delivery_id = int(callback.data.split("_")[-1])
    await state.update_data(delivery_id=delivery_id)

    user_id = callback.from_user.id
    cart = await get_cart(user_id)
    data = await state.get_data()

    headers = await _headers()
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{url_delivery}{delivery_id}/", headers=headers) as resp:
            delivery = await resp.json() if resp.status == 200 else None

    lines = [f"Order:"]
    for it in cart["items"]:
        p = it["product"]
        lines.append(f"{p['name']} — {it['quantity']} pcs ({float(p['price']) * it['quantity']}$)")

    lines.append(f"\nCustomer: {data['name']} {data['lastname']}")
    lines.append(f"Phone: {data['phone']}")
    lines.append(f"Address: {data['address']}")

    if delivery:
        lines.append(f"\nDelivery: {delivery['name']} (+{delivery['price']}$)")
        total = cart["total"] + float(delivery["price"])
    else:
        total = cart["total"]

    lines.append(f"\nTotal: {total}$")

    builder = InlineKeyboardBuilder()
    builder.button(text="Confirm", callback_data="confirm_order")
    builder.button(text="Cancel", callback_data="cancel_order")
    builder.adjust(2)

    await callback.message.edit_text("\n".join(lines), reply_markup=builder.as_markup())
    await state.set_state(CheckoutState.confirming)

@order_router.callback_query(F.data == "confirm_order", CheckoutState.confirming)
async def confirm_order(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    cart = await get_cart(user_id)
    if not cart:
        await callback.message.edit_text("Cart not found.")
        await state.clear()
        return

    data = await state.get_data()
    
    user = cart.get("user")
    if user:
        try:
            async with aiohttp.ClientSession() as session:
                await session.patch(
                    f"{url_users}{user['tg_id']}/",
                    headers=await _headers(),
                    json={
                        "name": data.get("name"),
                        "lastname": data.get("lastname"),
                        "surname": data.get("surname"),
                        "phone": data.get("phone"),
                        "address": data.get("address"),
                    },
                )
        except Exception as e:
            logger.exception("Error updating user: %s", e)

    payload = {
        "status_id": 2,  # Created
        "delivery_id": data.get("delivery_id"),
        "user_id": user["id"] if user else None,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.patch(f"{url_order}{cart['id']}/", headers=await _headers(), json=payload) as resp:
                if resp.status not in (200, 202):
                    logger.error("Failed to confirm order, status=%s, body=%s", resp.status, await resp.text())
    except Exception as e:
        logger.exception("Error confirming order: %s", e)

    await callback.message.edit_text(f"Order created! Number: ORD-{int(cart['id']):06d}")
    await state.clear()

@order_router.callback_query(F.data == "cancel_order", CheckoutState.confirming)
async def cancel_order(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Checkout canceled.", reply_markup=main_keyboard())
    await state.clear()
