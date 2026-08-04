from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.api.services import OrdersAPI
from app.keyboards.client import cart_keyboard, main_keyboard


def build_router(orders_api: OrdersAPI) -> Router:
    router = Router()

    async def render_cart(callback: CallbackQuery) -> None:
        cart = await orders_api.cart(callback.from_user.id)
        items = cart["items"]

        if not items:
            await callback.message.edit_text(
                "Your cart is empty.",
                reply_markup=main_keyboard(),
            )
            return

        lines = [f"Cart {cart['number']}:"]
        for item in items:
            product = item["product"]
            lines.append(
                f"• {product['name']} × {item['quantity']} "
                f"= ${item['total']}"
            )
        lines.append(f"\nTotal: ${cart['total']}")

        await callback.message.edit_text(
            "\n".join(lines),
            reply_markup=cart_keyboard(cart["id"], items),
        )

    @router.callback_query(F.data == "cart")
    async def cart(callback: CallbackQuery) -> None:
        await render_cart(callback)
        await callback.answer()

    @router.callback_query(F.data.startswith("cart:add:"))
    async def add(callback: CallbackQuery) -> None:
        product_id = int(callback.data.split(":")[2])
        cart_data = await orders_api.cart(callback.from_user.id)
        await orders_api.add_item(cart_data["id"], product_id)
        await callback.answer("Added to cart.")

    @router.callback_query(F.data.startswith("cart:set:"))
    async def set_quantity(callback: CallbackQuery) -> None:
        _, _, order_id, product_id, quantity = callback.data.split(":")
        await orders_api.update_item(
            int(order_id),
            int(product_id),
            int(quantity),
        )
        await render_cart(callback)
        await callback.answer()

    @router.callback_query(F.data.startswith("cart:remove:"))
    async def remove(callback: CallbackQuery) -> None:
        _, _, order_id, product_id = callback.data.split(":")
        await orders_api.remove_item(
            int(order_id),
            int(product_id),
        )
        await render_cart(callback)
        await callback.answer()

    return router
