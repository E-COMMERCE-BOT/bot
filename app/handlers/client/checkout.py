from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.api.services import OrdersAPI, UsersAPI
from app.keyboards.client import main_keyboard
from app.states.checkout import CheckoutState
from app.utils.validation import NAME_PATTERN, normalize_phone_number


def build_router(
    users_api: UsersAPI,
    orders_api: OrdersAPI,
) -> Router:
    router = Router()

    @router.callback_query(F.data == "checkout")
    async def start(callback: CallbackQuery, state: FSMContext) -> None:
        user = await users_api.get(callback.from_user.id)
        await state.update_data(
            name=user.get("name", ""),
            lastname=user.get("lastname", ""),
            surname=user.get("surname", ""),
            phone=user.get("phone", ""),
            address=user.get("address", ""),
        )
        await callback.message.edit_text("Enter your first name:")
        await state.set_state(CheckoutState.name)
        await callback.answer()

    @router.message(CheckoutState.name)
    async def name(message: Message, state: FSMContext) -> None:
        value = message.text.strip()
        if not NAME_PATTERN.fullmatch(value):
            await message.answer("Enter a valid first name.")
            return
        await state.update_data(name=value)
        await message.answer("Enter your last name:")
        await state.set_state(CheckoutState.lastname)

    @router.message(CheckoutState.lastname)
    async def lastname(message: Message, state: FSMContext) -> None:
        value = message.text.strip()
        if not NAME_PATTERN.fullmatch(value):
            await message.answer("Enter a valid last name.")
            return
        await state.update_data(lastname=value)
        await message.answer("Enter middle name or '-':")
        await state.set_state(CheckoutState.surname)

    @router.message(CheckoutState.surname)
    async def surname(message: Message, state: FSMContext) -> None:
        value = message.text.strip()
        if value != "-" and not NAME_PATTERN.fullmatch(value):
            await message.answer("Enter a valid middle name.")
            return
        await state.update_data(surname="" if value == "-" else value)
        await message.answer("Enter phone number:")
        await state.set_state(CheckoutState.phone)

    @router.message(CheckoutState.phone)
    async def phone(message: Message, state: FSMContext) -> None:
        value = normalize_phone_number(message.text)
        if value is None:
            await message.answer("Enter a valid international phone.")
            return
        await state.update_data(phone=value)
        await message.answer("Enter delivery address:")
        await state.set_state(CheckoutState.address)

    @router.message(CheckoutState.address)
    async def address(message: Message, state: FSMContext) -> None:
        await state.update_data(address=message.text.strip())
        deliveries = await orders_api.deliveries()
        builder = InlineKeyboardBuilder()
        for delivery in deliveries:
            builder.button(
                text=f"{delivery['name']} (+${delivery['price']})",
                callback_data=f"delivery:{delivery['id']}",
            )
        builder.adjust(1)
        await message.answer(
            "Choose delivery:",
            reply_markup=builder.as_markup(),
        )
        await state.set_state(CheckoutState.delivery)

    @router.callback_query(
        F.data.startswith("delivery:"),
        CheckoutState.delivery,
    )
    async def delivery(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        delivery_id = int(callback.data.split(":")[1])
        await state.update_data(delivery_id=delivery_id)
        data = await state.get_data()
        cart = await orders_api.cart(callback.from_user.id)

        builder = InlineKeyboardBuilder()
        builder.button(text="Confirm", callback_data="confirm")
        builder.button(text="Cancel", callback_data="cancel")
        builder.adjust(2)

        await callback.message.edit_text(
            (
                f"Customer: {data['name']} {data['lastname']}\n"
                f"Phone: {data['phone']}\n"
                f"Address: {data['address']}\n"
                f"Cart total: ${cart['total']}"
            ),
            reply_markup=builder.as_markup(),
        )
        await state.set_state(CheckoutState.confirm)
        await callback.answer()

    @router.callback_query(F.data == "confirm", CheckoutState.confirm)
    async def confirm(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        data = await state.get_data()
        await users_api.update(
            callback.from_user.id,
            {
                "name": data["name"],
                "lastname": data["lastname"],
                "surname": data["surname"],
                "phone": data["phone"],
                "address": data["address"],
            },
        )
        cart = await orders_api.cart(callback.from_user.id)
        order = await orders_api.checkout(
            cart["id"],
            data["delivery_id"],
        )
        await callback.message.edit_text(
            f"Order {order['number']} created!",
            reply_markup=main_keyboard(),
        )
        await state.clear()
        await callback.answer()

    @router.callback_query(F.data == "cancel")
    async def cancel(
        callback: CallbackQuery,
        state: FSMContext,
    ) -> None:
        await state.clear()
        await callback.message.edit_text(
            "Checkout cancelled.",
            reply_markup=main_keyboard(),
        )
        await callback.answer()

    return router
