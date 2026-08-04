from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.keyboards.client import main_keyboard


def build_router() -> Router:
    router = Router()

    @router.callback_query(F.data == "main")
    async def main_menu(callback: CallbackQuery) -> None:
        await callback.message.edit_text(
            "Main menu",
            reply_markup=main_keyboard(),
        )
        await callback.answer()

    return router
