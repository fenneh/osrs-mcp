import httpx
import pytest
import respx

from osrs_mcp.prices import BASE_URL as PRICES_BASE
from osrs_mcp.prices import PricesClient
from osrs_mcp.runelite import BASE_URL as RUNELITE_BASE
from osrs_mcp.runelite import RuneLiteSyncClient
from osrs_mcp.wiki import BASE_URL as WIKI_URL
from osrs_mcp.wiki import WikiClient
from osrs_mcp.wiseoldman import BASE_URL as WOM_BASE
from osrs_mcp.wiseoldman import WiseOldManClient, WiseOldManError


@pytest.fixture
def wom_client():
    transport = httpx.MockTransport(lambda req: httpx.Response(404))
    http = httpx.AsyncClient(base_url=WOM_BASE, transport=transport)
    return WiseOldManClient(http), http


async def test_wom_player_success():
    async with respx.mock(base_url=WOM_BASE) as mock:
        mock.get("/players/fensational").mock(
            return_value=httpx.Response(200, json={"username": "fensational", "id": 1})
        )
        client = WiseOldManClient(httpx.AsyncClient(base_url=WOM_BASE))
        try:
            data = await client.player("fensational")
        finally:
            await client.aclose()
        assert data["username"] == "fensational"


async def test_wom_player_404_raises():
    async with respx.mock(base_url=WOM_BASE) as mock:
        mock.get("/players/nope").mock(
            return_value=httpx.Response(404, json={"message": "Player not found."})
        )
        client = WiseOldManClient(httpx.AsyncClient(base_url=WOM_BASE))
        try:
            with pytest.raises(WiseOldManError) as exc:
                await client.player("nope")
        finally:
            await client.aclose()
        assert exc.value.status == 404
        assert "not found" in exc.value.message.lower()


async def test_wom_gained_passes_params():
    async with respx.mock(base_url=WOM_BASE) as mock:
        route = mock.get("/players/fensational/gained").mock(
            return_value=httpx.Response(200, json={"data": {}})
        )
        client = WiseOldManClient(httpx.AsyncClient(base_url=WOM_BASE))
        try:
            await client.gained("fensational", period="week", metric="attack")
        finally:
            await client.aclose()
        assert route.called
        assert dict(route.calls.last.request.url.params) == {
            "period": "week",
            "metric": "attack",
        }


async def test_runelite_sync_404_returns_none():
    async with respx.mock(base_url=RUNELITE_BASE) as mock:
        mock.get("/runelite/player/ghost/STANDARD").mock(
            return_value=httpx.Response(404)
        )
        client = RuneLiteSyncClient(httpx.AsyncClient(base_url=RUNELITE_BASE))
        try:
            data = await client.sync("ghost")
        finally:
            await client.aclose()
        assert data is None


async def test_runelite_sync_success():
    async with respx.mock(base_url=RUNELITE_BASE) as mock:
        mock.get("/runelite/player/fensational/STANDARD").mock(
            return_value=httpx.Response(
                200,
                json={"username": "fensational", "quests": {"Cook's Assistant": 2}},
            )
        )
        client = RuneLiteSyncClient(httpx.AsyncClient(base_url=RUNELITE_BASE))
        try:
            data = await client.sync("fensational")
        finally:
            await client.aclose()
        assert data["username"] == "fensational"
        assert data["quests"]["Cook's Assistant"] == 2


async def test_wiki_search_returns_list():
    async with respx.mock() as mock:
        mock.get(WIKI_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "query": {
                        "search": [
                            {"title": "Abyssal whip", "snippet": "weapon"},
                            {"title": "Abyssal demon", "snippet": "monster"},
                        ]
                    }
                },
            )
        )
        client = WikiClient(httpx.AsyncClient())
        try:
            results = await client.search("abyssal", limit=2)
        finally:
            await client.aclose()
        assert len(results) == 2
        assert results[0]["title"] == "Abyssal whip"


async def test_wiki_page_wikitext():
    async with respx.mock() as mock:
        mock.get(WIKI_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "parse": {
                        "title": "Abyssal whip",
                        "pageid": 12345,
                        "wikitext": "{{Infobox|name=Abyssal whip}}",
                    }
                },
            )
        )
        client = WikiClient(httpx.AsyncClient())
        try:
            page = await client.page("Abyssal whip")
        finally:
            await client.aclose()
        assert page["format"] == "wikitext"
        assert "Infobox" in page["content"]


async def test_prices_resolve_by_name_substring():
    async with respx.mock(base_url=PRICES_BASE) as mock:
        mock.get("/mapping").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {"id": 4151, "name": "Abyssal whip", "members": True},
                    {"id": 1234, "name": "Bronze sword", "members": False},
                ],
            )
        )
        client = PricesClient(httpx.AsyncClient(base_url=PRICES_BASE))
        try:
            item = await client.resolve("whip")
            by_id = await client.resolve(4151)
            missing = await client.resolve("not a real item")
        finally:
            await client.aclose()
        assert item["id"] == 4151
        assert by_id["name"] == "Abyssal whip"
        assert missing is None


async def test_prices_latest_unwraps_id_key():
    async with respx.mock(base_url=PRICES_BASE) as mock:
        mock.get("/latest").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "4151": {
                            "high": 1200000,
                            "highTime": 1700000000,
                            "low": 1190000,
                            "lowTime": 1700000100,
                        }
                    }
                },
            )
        )
        client = PricesClient(httpx.AsyncClient(base_url=PRICES_BASE))
        try:
            entry = await client.latest(4151)
        finally:
            await client.aclose()
        assert entry["high"] == 1200000


async def test_prices_timeseries_rejects_bad_step():
    client = PricesClient(httpx.AsyncClient(base_url=PRICES_BASE))
    try:
        with pytest.raises(ValueError):
            await client.timeseries(4151, timestep="2h")
    finally:
        await client.aclose()
