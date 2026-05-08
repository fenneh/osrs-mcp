import httpx
import pytest
import respx

from osrs_mcp.runelite import BASE_URL as RUNELITE_BASE
from osrs_mcp.runelite import RuneLiteSyncClient
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
