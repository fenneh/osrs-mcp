from typing import Any

import httpx

BASE_URL = "https://oldschool.runescape.wiki/api.php"
USER_AGENT = "osrs-mcp/0.1 (+https://github.com/fenneh/osrs-mcp)"


class WikiError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(f"OSRS Wiki {status}: {message}")
        self.status = status
        self.message = message


class WikiClient:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    @classmethod
    def build(cls) -> "WikiClient":
        client = httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            timeout=httpx.Timeout(20.0, connect=5.0),
        )
        return cls(client)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _get(self, params: dict[str, Any]) -> dict[str, Any]:
        params = {"format": "json", **params}
        resp = await self._client.get(BASE_URL, params=params)
        if resp.status_code >= 400:
            raise WikiError(resp.status_code, resp.text or resp.reason_phrase)
        return resp.json()

    async def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        data = await self._get(
            {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": limit,
                "srprop": "snippet|sectiontitle",
            }
        )
        return ((data.get("query") or {}).get("search")) or []

    async def page(self, title: str, fmt: str = "wikitext") -> dict[str, Any] | None:
        if fmt not in {"wikitext", "html"}:
            raise ValueError("fmt must be 'wikitext' or 'html'")
        prop = "wikitext" if fmt == "wikitext" else "text"
        data = await self._get(
            {
                "action": "parse",
                "page": title,
                "prop": prop,
                "formatversion": 2,
                "redirects": 1,
            }
        )
        if "error" in data:
            return None
        parse = data.get("parse") or {}
        content_key = "wikitext" if fmt == "wikitext" else "text"
        return {
            "title": parse.get("title"),
            "pageid": parse.get("pageid"),
            "format": fmt,
            "content": parse.get(content_key),
        }
