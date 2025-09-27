"""Custom aiogram filters used across the project.

Currently includes `IsAdminGroupMember` which verifies that the user is an
administrator of the configured admin group. Useful to gate admin routes.
"""

import os
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery
from aiogram import Bot
from dotenv import load_dotenv

# Load ADMIN_CHAT_ID from .env if present.
load_dotenv()

# Group identifier where admins are members (e.g., -1001234567890).
ADMIN_GROUP_ID = os.getenv("ADMIN_CHAT_ID")


class IsAdminGroupMember(BaseFilter):
    """Allow only users who are admins of the configured group."""

    async def __call__(self, event: Message | CallbackQuery, bot: Bot) -> bool:
        # Extract user id from Message or CallbackQuery events.
        if isinstance(event, (Message, CallbackQuery)):
            user_id = event.from_user.id
        else:
            return False

        try:
            # Check user's membership status in the admin group.
            member = await bot.get_chat_member(ADMIN_GROUP_ID, user_id)
            return member.status in ("administrator", "creator")
        except Exception:
            # If the chat is not found or any API error occurs, deny access.
            return False
