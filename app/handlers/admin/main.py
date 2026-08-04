from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.keyboards.admin import admin_keyboard


def build_router(admin_filter) -> Router:
    router = Router()

    @router.message(Command("admin"), admin_filter)
    async def admin(message: Message) -> None:
        await message.answer(
            "Admin panel",
            reply_markup=admin_keyboard(),
        )

    return router
