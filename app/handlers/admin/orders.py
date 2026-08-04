from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.api.services import OrdersAPI

ORDER_STATUSES = (
    "created",
    "processing",
    "shipped",
    "completed",
    "cancelled",
)


def build_router(orders_api: OrdersAPI, admin_filter) -> Router:
    router = Router()

    @router.callback_query(F.data == "admin:orders", admin_filter)
    async def orders(callback: CallbackQuery) -> None:
        orders_data = await orders_api.orders()
        builder = InlineKeyboardBuilder()

        for order in orders_data:
            if order["status"] == "cart":
                continue
            builder.button(
                text=f"{order['number']} ({order['status']})",
                callback_data=f"admin:order:{order['id']}",
            )

        builder.adjust(1)
        await callback.message.edit_text(
            "Orders:",
            reply_markup=builder.as_markup(),
        )
        await callback.answer()

    @router.callback_query(
        F.data.startswith("admin:order:"),
        admin_filter,
    )
    async def order_details(callback: CallbackQuery) -> None:
        order_id = int(callback.data.split(":")[2])
        orders_data = await orders_api.orders()
        order = next(
            (item for item in orders_data if item["id"] == order_id),
            None,
        )
        if order is None:
            await callback.answer("Order not found.", show_alert=True)
            return

        builder = InlineKeyboardBuilder()
        for status in ORDER_STATUSES:
            builder.button(
                text=status.title(),
                callback_data=(
                    f"admin:set_status:{order_id}:{status}"
                ),
            )
        builder.adjust(2)

        await callback.message.edit_text(
            (
                f"Order {order['number']}\n"
                f"Status: {order['status']}\n"
                f"Total: ${order['total']}"
            ),
            reply_markup=builder.as_markup(),
        )
        await callback.answer()

    @router.callback_query(
        F.data.startswith("admin:set_status:"),
        admin_filter,
    )
    async def set_status(callback: CallbackQuery) -> None:
        _, _, _, order_id, status = callback.data.split(":")
        order = await orders_api.set_status(int(order_id), status)
        await callback.message.edit_text(
            f"Order {order['number']} status: {order['status']}"
        )
        await callback.answer()

    return router
