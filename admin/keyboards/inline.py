from aiogram.utils.keyboard import InlineKeyboardBuilder

def admin_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Products", callback_data="products_menu")
    builder.button(text="Orders", callback_data="orders_menu")
    builder.adjust(1)
    return builder.as_markup()

def admin_product_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Create", callback_data="create_product")
    builder.button(text="Edit", callback_data="edit_product")
    builder.button(text="Back", callback_data="back_to_admin")
    builder.adjust(1)
    return builder.as_markup()

def admin_cancel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Cancel", callback_data="cancel_action")
    builder.adjust(1)
    return builder.as_markup()

def admin_edit_product_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Change Name", callback_data="change_name")
    builder.button(text="Change Description", callback_data="change_description")
    builder.button(text="Change Photo", callback_data="change_photo")
    builder.button(text="Change Price", callback_data="change_price")
    builder.button(text="Change Stock", callback_data="change_stock")
    builder.button(text="Change Category", callback_data="change_category")
    builder.button(text="Back", callback_data="back_to_admin")
    builder.adjust(2)
    return builder.as_markup()