from typing import Any

import aiohttp


class APIError(RuntimeError):
    def __init__(self, status: int, detail: str) -> None:
        self.status = status
        self.detail = detail
        super().__init__(detail)


class EcommerceAPI:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        timeout: float = 10.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = {"X-Bot-Api-Key": api_key}
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: aiohttp.ClientSession | None = None

    async def start(self) -> None:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers=self._headers,
                timeout=self._timeout,
            )

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            raise RuntimeError("API client is not started.")
        return self._session

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        data: Any = None,
    ) -> Any:
        async with self.session.request(
            method,
            f"{self._base_url}/{path.lstrip('/')}",
            params=params,
            json=json,
            data=data,
        ) as response:
            if response.status == 204:
                return None

            payload = await response.json(content_type=None)
            if response.status >= 400:
                detail = (
                    payload.get("detail", str(payload))
                    if isinstance(payload, dict)
                    else str(payload)
                )
                raise APIError(response.status, detail)

            return payload
