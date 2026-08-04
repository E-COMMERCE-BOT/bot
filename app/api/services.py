from typing import Any

import aiohttp

from .client import EcommerceAPI


class UsersAPI:
    def __init__(self, client: EcommerceAPI) -> None:
        self._client = client

    async def get_or_create(self, tg_id: int) -> dict[str, Any]:
        return await self._client.request(
            "POST",
            "users/",
            json={"tg_id": tg_id},
        )

    async def get(self, tg_id: int) -> dict[str, Any]:
        return await self._client.request("GET", f"users/{tg_id}/")

    async def update(
        self,
        tg_id: int,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        return await self._client.request(
            "PATCH",
            f"users/{tg_id}/",
            json=data,
        )


class CatalogAPI:
    def __init__(self, client: EcommerceAPI) -> None:
        self._client = client

    async def categories(
        self,
        parent: int | None = None,
    ) -> list[dict[str, Any]]:
        params = {"parent": parent} if parent is not None else None
        return await self._client.request(
            "GET",
            "catalog/categories/",
            params=params,
        )

    async def products(
        self,
        category_id: int | None = None,
    ) -> list[dict[str, Any]]:
        params = (
            {"category_id": category_id}
            if category_id is not None
            else None
        )
        return await self._client.request(
            "GET",
            "catalog/products/",
            params=params,
        )

    async def product(self, product_id: int) -> dict[str, Any]:
        return await self._client.request(
            "GET",
            f"catalog/products/{product_id}/",
        )

    async def create_product(
        self,
        data: aiohttp.FormData,
    ) -> dict[str, Any]:
        return await self._client.request(
            "POST",
            "catalog/products/",
            data=data,
        )

    async def update_product(
        self,
        product_id: int,
        data: aiohttp.FormData,
    ) -> dict[str, Any]:
        return await self._client.request(
            "PATCH",
            f"catalog/products/{product_id}/",
            data=data,
        )


class OrdersAPI:
    def __init__(self, client: EcommerceAPI) -> None:
        self._client = client

    async def cart(self, tg_id: int) -> dict[str, Any]:
        return await self._client.request(
            "GET",
            "orders/cart/",
            params={"tg_id": tg_id},
        )

    async def add_item(
        self,
        order_id: int,
        product_id: int,
        quantity: int = 1,
    ) -> dict[str, Any]:
        return await self._client.request(
            "POST",
            f"orders/{order_id}/add_item/",
            json={
                "product_id": product_id,
                "quantity": quantity,
            },
        )

    async def update_item(
        self,
        order_id: int,
        product_id: int,
        quantity: int,
    ) -> dict[str, Any]:
        return await self._client.request(
            "POST",
            f"orders/{order_id}/update_item/",
            json={
                "product_id": product_id,
                "quantity": quantity,
            },
        )

    async def remove_item(
        self,
        order_id: int,
        product_id: int,
    ) -> dict[str, Any]:
        return await self._client.request(
            "POST",
            f"orders/{order_id}/remove_item/",
            json={"product_id": product_id},
        )

    async def deliveries(self) -> list[dict[str, Any]]:
        return await self._client.request(
            "GET",
            "orders/deliveries/",
        )

    async def checkout(
        self,
        order_id: int,
        delivery_id: int,
    ) -> dict[str, Any]:
        return await self._client.request(
            "POST",
            f"orders/{order_id}/checkout/",
            json={"delivery_id": delivery_id},
        )

    async def orders(self) -> list[dict[str, Any]]:
        return await self._client.request("GET", "orders/")

    async def set_status(
        self,
        order_id: int,
        status: str,
    ) -> dict[str, Any]:
        return await self._client.request(
            "POST",
            f"orders/{order_id}/set_status/",
            json={"status": status},
        )
