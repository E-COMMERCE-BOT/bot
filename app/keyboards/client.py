from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Catalog", callback_data="catalog")
    builder.button(text="Cart", callback_data="cart")
    builder.adjust(1)
    return builder.as_markup()


def product_keyboard(product_id: int, category_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Add to cart",
        callback_data=f"cart:add:{product_id}",
    )
    builder.button(
        text="Back",
        callback_data=f"category:{category_id}",
    )
    builder.adjust(1)
    return builder.as_markup()


def cart_keyboard(order_id: int, items: list[dict]):
    builder = InlineKeyboardBuilder()
    for item in items:
        product = item["product"]
        builder.button(
            text=f"− {product['name']}",
            callback_data=(
                f"cart:set:{order_id}:{product['id']}:"
                f"{item['quantity'] - 1}"
            ),
        )
        builder.button(
            text=f"+ {product['name']}",
            callback_data=(
                f"cart:set:{order_id}:{product['id']}:"
                f"{item['quantity'] + 1}"
            ),
        )
        builder.button(
            text=f"Remove {product['name']}",
            callback_data=(
                f"cart:remove:{order_id}:{product['id']}"
            ),
        )
    builder.button(text="Checkout", callback_data="checkout")
    builder.button(text="Back", callback_data="main")
    builder.adjust(2)
    return builder.as_markup()
