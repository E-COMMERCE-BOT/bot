"""Admin panel entrypoint handlers.

Provides a simple command to open the admin panel inside Telegram.
This module registers the router and exposes a single handler that
shows the admin keyboard to authorized admin group members.
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from utils.filters import IsAdminGroupMember
from admin.keyboards.inline import admin_keyboard

admin_router = Router()

@admin_router.message(Command("admin"), IsAdminGroupMember())
async def admin_panel(message: Message):
    """Open the admin panel for authorized users.

    Sends the admin inline keyboard to the chat where the command was used.
    """
    await message.answer("Welcome to the admin panel!", reply_markup=admin_keyboard())
