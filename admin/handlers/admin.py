from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from utils.filters import IsAdminGroupMember
from admin.keyboards.inline import admin_keyboard

admin_router = Router()

@admin_router.message(Command("admin"), IsAdminGroupMember())
async def admin_panel(message: Message):
    await message.answer("Welcome to the admin panel!", reply_markup=admin_keyboard())