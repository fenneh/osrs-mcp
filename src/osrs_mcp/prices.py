import asyncio
import time
from typing import Any

import httpx

BASE_URL = "https://prices.runescape.wiki/api/v1/osrs"
USER_AGENT = "osrs-mcp/0.1 (+https://github.com/fenneh/osrs-mcp)"

MAPPING_TTL_SECONDS = 24 * 3600


class PricesError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(f"OSRS prices {status}: {message}")
        self.status = status
        self.message = message


class PricesClient:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client
        self._mapping_cache: list[dict[str, Any]] | None = None
        self._mapping_loaded_at: float = 0.0
        self._by_id: dict[int, dict[str, Any]] = {}
        self._by_name_lower: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    @classmethod
    def build(cls) -> "PricesClient":
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
            raise PricesError(resp.status_code, resp.text or resp.reason_phrase)
        return resp.json()

    async def mapping(self) -> list[dict[str, Any]]:
        async with self._lock:
            now = time.time()
            if (
                self._mapping_cache is not None
                and now - self._mapping_loaded_at < MAPPING_TTL_SECONDS
            ):
                return self._mapping_cache
            data = await self._get("/mapping")
            assert isinstance(data, list)
            self._mapping_cache = data
            self._mapping_loaded_at = now
            self._by_id = {item["id"]: item for item in data}
            self._by_name_lower = {item["name"].lower(): item for item in data}
            return data

    async def resolve(self, name_or_id: str | int) -> dict[str, Any] | None:
        await self.mapping()
        if isinstance(name_or_id, int) or (
            isinstance(name_or_id, str) and name_or_id.isdigit()
        ):
            return self._by_id.get(int(name_or_id))
        key = str(name_or_id).strip().lower()
        if key in self._by_name_lower:
            return self._by_name_lower[key]
        for n, item in self._by_name_lower.items():
            if key in n:
                return item
        return None

    async def latest(self, item_id: int) -> dict[str, Any] | None:
        data = await self._get("/latest", params={"id": item_id})
        entry = (data.get("data") or {}).get(str(item_id))
        return entry

    async def timeseries(
        self, item_id: int, timestep: str = "1h"
    ) -> list[dict[str, Any]]:
        if timestep not in {"5m", "1h", "6h", "24h"}:
            raise ValueError("timestep must be one of: 5m, 1h, 6h, 24h")
        data = await self._get(
            "/timeseries", params={"timestep": timestep, "id": item_id}
        )
        return data.get("data") or []
