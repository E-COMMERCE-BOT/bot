"""Inline keyboards used in the admin panel flows.

Each function builds and returns an InlineKeyboardMarkup for a specific
admin screen or action. Keep buttons' callback_data in sync with handlers
in `bot/admin/handlers/`.
"""

from aiogram.utils.keyboard import InlineKeyboardBuilder

def admin_keyboard():
    """Top-level admin menu (entry points like Products, Orders)."""
    builder = InlineKeyboardBuilder()
    builder.button(text="Products", callback_data="products_menu")
    builder.button(text="Orders", callback_data="orders_menu")
    builder.adjust(1)
    return builder.as_markup()

def admin_product_keyboard():
    """Products management menu (create/edit/back to admin)."""
    builder = InlineKeyboardBuilder()
    builder.button(text="Create", callback_data="create_product")
    builder.button(text="Edit", callback_data="edit_product")
    builder.button(text="Back", callback_data="back_to_admin")
    builder.adjust(1)
    return builder.as_markup()

def admin_cancel_keyboard():
    """Single-button keyboard to cancel current admin action."""
    builder = InlineKeyboardBuilder()
    builder.button(text="Cancel", callback_data="cancel_action")
    builder.adjust(1)
    return builder.as_markup()

def admin_edit_product_keyboard():
    """Keyboard with editable product fields and a back button.

    Provides shortcuts to change name, description, photo, price, stock,
    category, or go back to the main admin menu.
    """
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
