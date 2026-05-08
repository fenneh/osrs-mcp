from typing import Any

import httpx

BASE_URL = "https://sync.runescape.wiki"
USER_AGENT = "osrs-mcp/0.1 (+https://github.com/fenneh/osrs-mcp)"


class RuneLiteSyncError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(f"RuneLite sync {status}: {message}")
        self.status = status
        self.message = message


class RuneLiteSyncClient:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    @classmethod
    def build(cls) -> "RuneLiteSyncClient":
        client = httpx.AsyncClient(
            base_url=BASE_URL,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            timeout=httpx.Timeout(20.0, connect=5.0),
        )
        return cls(client)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def sync(
        self, username: str, profile: str = "STANDARD"
    ) -> dict[str, Any] | None:
        resp = await self._client.get(f"/runelite/player/{username}/{profile}")
        if resp.status_code == 404:
            return None
        if resp.status_code >= 400:
            raise RuneLiteSyncError(resp.status_code, resp.text or resp.reason_phrase)
        return resp.json()
