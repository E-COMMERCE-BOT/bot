"""Inline keyboards used by the client-facing bot flows.

Each function builds and returns an InlineKeyboardMarkup for a specific
screen or action. Keep buttons' callback_data in sync with handlers.
"""

from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_keyboard():
    """Main menu keyboard (entry points like Catalog, Cart)."""
    builder = InlineKeyboardBuilder()
    builder.button(text="Catalog", callback_data="catalog_menu")
    builder.button(text="Cart", callback_data="view_cart")
    builder.adjust(1)
    return builder.as_markup()


def product_keyboard(product_id: int, category_id: int):
    """Keyboard for a single product card.

    Includes actions like Add to Cart and Back to the category.
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="Add to Cart", callback_data=f"add_to_cart_{product_id}")
    builder.button(text="Back", callback_data=f"back_to_{category_id}")
    builder.adjust(1)
    return builder.as_markup()


def cart_action_keyboard(order_id: int):
    """Actions available from the cart view.

    Lets user change quantities, remove items, proceed to checkout
    or go back to the main menu.
    """
    b = InlineKeyboardBuilder()
    b.button(text="Increase", callback_data=f"choose_increase_{order_id}")
    b.button(text="Decrease", callback_data=f"choose_decrease_{order_id}")
    b.button(text="Remove",   callback_data=f"choose_remove_{order_id}")
    b.button(text="Order", callback_data="checkout")
    b.button(text="Back",    callback_data="back_to_main")
    b.adjust(2)
    return b.as_markup()


def choose_product_keyboard(order_id: int, action: str, items: list[dict]):
    """Keyboard to choose a specific product from items list for an action."""
    b = InlineKeyboardBuilder()
    for it in items:
        p = it["product"]
        b.button(text=f"{p['name']} ({it['quantity']})", callback_data=f"{action}_{order_id}_{p['id']}")
    b.button(text="Back", callback_data="view_cart")
    b.adjust(1)
    return b.as_markup()


def confirmation_keyboard():
    """Generic Yes/No confirmation keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="Confirm", callback_data="confirm")
    builder.button(text="Cancel", callback_data="cancel")
    builder.adjust(2)
    return builder.as_markup()


def cancel_keyboard():
    """Single-button keyboard to cancel the current action."""
    builder = InlineKeyboardBuilder()
    builder.button(text="Cancel", callback_data="cancel")
    builder.adjust(1)
    return builder.as_markup()


def choose_product_keyboard(order_id: int, action: str, items: list[dict]):
    """Keyboard to choose product for an action (duplicated variant)."""
    builder = InlineKeyboardBuilder()
    for item in items:
        p = item["product"]
        builder.button(
            text=f"{p['name']} ({item['quantity']})",
            callback_data=f"{action}_{order_id}_{p['id']}",
        )
    builder.button(text="Back", callback_data="view_cart")
    builder.adjust(1)
    return builder.as_markup()
