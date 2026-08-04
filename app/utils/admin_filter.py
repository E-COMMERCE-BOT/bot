from aiogram import Bot
from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message


class IsAdminGroupMember(BaseFilter):
    def __init__(self, admin_chat_id: int) -> None:
        self._admin_chat_id = admin_chat_id

    async def __call__(
        self,
        event: Message | CallbackQuery,
        bot: Bot,
    ) -> bool:
        try:
            member = await bot.get_chat_member(
                self._admin_chat_id,
                event.from_user.id,
            )
        except Exception:
            return False

        return member.status in {"administrator", "creator"}
