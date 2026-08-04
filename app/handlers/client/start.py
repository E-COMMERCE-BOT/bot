from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.api.services import UsersAPI
from app.keyboards.client import main_keyboard


def build_router(users_api: UsersAPI) -> Router:
    router = Router()

    @router.message(CommandStart())
    async def start(message: Message, state: FSMContext) -> None:
        await state.clear()
        user = await users_api.get_or_create(message.from_user.id)
        name = user.get("name") or message.from_user.first_name
        await message.answer(
            f"Welcome to E-Commerce Bot, <b>{name}</b>!",
            reply_markup=main_keyboard(),
        )

    return router
