from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Products", callback_data="admin:products")
    builder.button(text="Create product", callback_data="admin:create_product")
    builder.button(text="Orders", callback_data="admin:orders")
    builder.adjust(1)
    return builder.as_markup()
