from typing import Any

import httpx

BASE_URL = "https://api.wiseoldman.net/v2"
USER_AGENT = "osrs-mcp/0.1 (+https://github.com/fenneh/osrs-mcp)"


class WiseOldManError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(f"WOM {status}: {message}")
        self.status = status
        self.message = message


class WiseOldManClient:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    @classmethod
    def build(cls) -> "WiseOldManClient":
        client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            timeout=httpx.Timeout(20.0, connect=5.0),
        )
        return cls(client)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        resp = await self._client.get(path, params=params)
        if resp.status_code >= 400:
            raise WiseOldManError(resp.status_code, _message(resp))
        return resp.json()

    async def _post(self, path: str, json: dict[str, Any] | None = None) -> Any:
        resp = await self._client.post(path, json=json or {})
        if resp.status_code >= 400:
            raise WiseOldManError(resp.status_code, _message(resp))
        return resp.json()

    async def player(self, username: str) -> dict[str, Any]:
        return await self._get(f"/players/{username}")

    async def gained(
        self,
        username: str,
        period: str | None = None,
        metric: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> Any:
        params: dict[str, Any] = {}
        if period:
            params["period"] = period
        if metric:
            params["metric"] = metric
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        return await self._get(f"/players/{username}/gained", params=params)

    async def records(
        self, username: str, period: str | None = None, metric: str | None = None
    ) -> Any:
        params: dict[str, Any] = {}
        if period:
            params["period"] = period
        if metric:
            params["metric"] = metric
        return await self._get(f"/players/{username}/records", params=params)

    async def achievements(self, username: str) -> Any:
        return await self._get(f"/players/{username}/achievements")

    async def achievements_progress(self, username: str) -> Any:
        return await self._get(f"/players/{username}/achievements/progress")

    async def competitions(self, username: str) -> Any:
        return await self._get(f"/players/{username}/competitions")

    async def groups(self, username: str) -> Any:
        return await self._get(f"/players/{username}/groups")

    async def names(self, username: str) -> Any:
        return await self._get(f"/players/{username}/names")

    async def update(self, username: str) -> Any:
        return await self._post(f"/players/{username}")


def _message(resp: httpx.Response) -> str:
    try:
        data = resp.json()
    except ValueError:
        return resp.text or resp.reason_phrase
    if isinstance(data, dict):
        return data.get("message") or data.get("error") or resp.text
    return resp.text
