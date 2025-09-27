import os
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from aiogram import Bot
from dotenv import load_dotenv

load_dotenv()

ADMIN_GROUP_ID = os.getenv("ADMIN_CHAT_ID")


class IsAdminGroupMember(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery, bot: Bot) -> bool:
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        else:
            return False
        try:
            member = await bot.get_chat_member(ADMIN_GROUP_ID, user_id)
            return member.status in ("administrator", "creator")
        except Exception:
            return False
