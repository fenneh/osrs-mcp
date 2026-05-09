import json

import httpx
import pytest
import respx
from fastmcp import Client

from osrs_mcp.prices import BASE_URL as PRICES_BASE
from osrs_mcp.runelite import BASE_URL as RUNELITE_BASE
from osrs_mcp.server import mcp
from osrs_mcp.wiki import BASE_URL as WIKI_URL
from osrs_mcp.wiseoldman import BASE_URL as WOM_BASE


def _result_json(result) -> object:
    text = result.content[0].text
    return json.loads(text)


@pytest.fixture
def wom_player_payload():
    return {
        "id": 1,
        "username": "fensational",
        "displayName": "Fensational",
        "type": "regular",
        "build": "main",
        "country": None,
        "status": "active",
        "patron": False,
        "exp": 250000000,
        "ehp": 1000.0,
        "ehb": 200.0,
        "ttm": 50.0,
        "tt200m": 10000.0,
        "combatLevel": 123,
        "registeredAt": "2020-01-01T00:00:00.000Z",
        "updatedAt": "2026-05-01T00:00:00.000Z",
        "lastChangedAt": "2026-05-01T00:00:00.000Z",
        "latestSnapshot": {
            "data": {
                "skills": {"attack": {"level": 99, "experience": 13034431}},
                "bosses": {"zulrah": {"kills": 1234}},
                "activities": {"clue_scrolls_all": {"score": 500}},
                "computed": {},
            }
        },
    }


async def test_lists_all_twelve_tools():
    async with Client(mcp) as client:
        tools = await client.list_tools()
    names = sorted(t.name for t in tools)
    assert names == sorted(
        [
            "ge_item",
            "ge_item_history",
            "get_player",
            "get_player_achievements",
            "get_player_competitions",
            "get_player_gains",
            "get_player_groups",
            "get_player_name_history",
            "get_player_records",
            "update_player",
            "wiki_page",
            "wiki_search",
        ]
    )


async def test_get_player_merges_wom_and_wiki(wom_player_payload):
    async with respx.mock(assert_all_called=False) as mock:
        mock.get(f"{WOM_BASE}/players/fensational").mock(
            return_value=httpx.Response(200, json=wom_player_payload)
        )
        mock.get(f"{RUNELITE_BASE}/runelite/player/fensational/STANDARD").mock(
            return_value=httpx.Response(
                200,
                json={
                    "username": "fensational",
                    "timestamp": "2026-05-01T00:00:00Z",
                    "quests": {"Cook's Assistant": 2},
                    "achievement_diaries": {},
                    "combat_achievements": [1, 2, 3],
                    "music_tracks": {},
                    "collection_log": [],
                    "collectionLogItemCount": 0,
                },
            )
        )
        async with Client(mcp) as client:
            result = await client.call_tool(
                "get_player",
                {
                    "username": "fensational",
                    "sections": ["overview", "skills", "quests", "combat_achievements"],
                },
            )
    data = _result_json(result)
    assert data["overview"]["combatLevel"] == 123
    assert data["skills"]["attack"]["level"] == 99
    assert data["wiki_sync_status"] == "ok"
    assert data["quests"]["Cook's Assistant"] == 2
    assert data["combat_achievements"] == [1, 2, 3]


async def test_get_player_marks_wiki_not_found_when_synced_player_missing(
    wom_player_payload,
):
    async with respx.mock(assert_all_called=False) as mock:
        mock.get(f"{WOM_BASE}/players/fensational").mock(
            return_value=httpx.Response(200, json=wom_player_payload)
        )
        mock.get(f"{RUNELITE_BASE}/runelite/player/fensational/STANDARD").mock(
            return_value=httpx.Response(404)
        )
        async with Client(mcp) as client:
            result = await client.call_tool(
                "get_player",
                {"username": "fensational", "sections": ["overview", "quests"]},
            )
    data = _result_json(result)
    assert data["overview"]["combatLevel"] == 123
    assert data["wiki_sync_status"] == "not_found"
    assert data["quests"] is None


async def test_get_player_skips_wiki_when_only_wom_sections_requested(
    wom_player_payload,
):
    async with respx.mock(assert_all_called=False) as mock:
        wom_route = mock.get(f"{WOM_BASE}/players/fensational").mock(
            return_value=httpx.Response(200, json=wom_player_payload)
        )
        wiki_route = mock.get(
            f"{RUNELITE_BASE}/runelite/player/fensational/STANDARD"
        ).mock(return_value=httpx.Response(200, json={}))
        async with Client(mcp) as client:
            await client.call_tool(
                "get_player",
                {"username": "fensational", "sections": ["overview"]},
            )
    assert wom_route.called
    assert not wiki_route.called


async def test_wiki_search_tool():
    async with respx.mock(assert_all_called=False) as mock:
        mock.get(WIKI_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "query": {
                        "search": [
                            {"title": "Abyssal whip", "snippet": "weapon"},
                        ]
                    }
                },
            )
        )
        async with Client(mcp) as client:
            result = await client.call_tool(
                "wiki_search", {"query": "abyssal whip", "limit": 1}
            )
    data = _result_json(result)
    assert data[0]["title"] == "Abyssal whip"


async def test_ge_item_resolves_substring_and_returns_latest():
    async with respx.mock(assert_all_called=False) as mock:
        mock.get(f"{PRICES_BASE}/mapping").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": 4151,
                        "name": "Abyssal whip",
                        "members": True,
                        "examine": "A weapon from the Abyss.",
                    }
                ],
            )
        )
        mock.get(f"{PRICES_BASE}/latest").mock(
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
        async with Client(mcp) as client:
            result = await client.call_tool("ge_item", {"name_or_id": "whip"})
    data = _result_json(result)
    assert data["item"]["id"] == 4151
    assert data["latest"]["high"] == 1200000


async def test_ge_item_unknown_returns_error_payload():
    async with respx.mock(assert_all_called=False) as mock:
        mock.get(f"{PRICES_BASE}/mapping").mock(
            return_value=httpx.Response(200, json=[])
        )
        async with Client(mcp) as client:
            result = await client.call_tool("ge_item", {"name_or_id": "no such item"})
    data = _result_json(result)
    assert "error" in data


async def test_get_player_competitions_filters_by_status():
    async with respx.mock(assert_all_called=False) as mock:
        mock.get(f"{WOM_BASE}/players/fensational/competitions").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {"competition": {"title": "A", "status": "ongoing"}},
                    {"competition": {"title": "B", "status": "finished"}},
                ],
            )
        )
        async with Client(mcp) as client:
            result = await client.call_tool(
                "get_player_competitions",
                {"username": "fensational", "status": "ongoing"},
            )
    data = _result_json(result)
    assert len(data) == 1
    assert data[0]["competition"]["title"] == "A"
