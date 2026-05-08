import asyncio
from typing import Any, Literal

from fastmcp import FastMCP

from osrs_mcp.prices import PricesClient
from osrs_mcp.runelite import RuneLiteSyncClient, RuneLiteSyncError
from osrs_mcp.wiki import WikiClient
from osrs_mcp.wiseoldman import WiseOldManClient, WiseOldManError

Section = Literal[
    "overview",
    "skills",
    "bosses",
    "activities",
    "quests",
    "diaries",
    "combat_achievements",
    "music",
    "collection_log",
]

DEFAULT_SECTIONS: list[Section] = [
    "overview",
    "skills",
    "bosses",
    "activities",
    "quests",
    "diaries",
    "combat_achievements",
]

WOM_SECTIONS = {"overview", "skills", "bosses", "activities"}
WIKI_SECTIONS = {"quests", "diaries", "combat_achievements", "music", "collection_log"}

Period = Literal["5min", "day", "week", "month", "year"]
CompetitionStatus = Literal["upcoming", "ongoing", "finished"]
PageFormat = Literal["wikitext", "html"]
Timestep = Literal["5m", "1h", "6h", "24h"]

mcp: FastMCP = FastMCP("osrs-mcp")
_wom = WiseOldManClient.build()
_runelite = RuneLiteSyncClient.build()
_wiki = WikiClient.build()
_prices = PricesClient.build()


@mcp.tool
async def get_player(
    username: str,
    sections: list[Section] | None = None,
) -> dict[str, Any]:
    """Combined player snapshot from WiseOldMan and RuneLite Sync.

    WiseOldMan is authoritative for stats (skills, bosses, activities).
    RuneLite Sync is authoritative for progression flags (quests, diaries,
    combat achievements, music, collection log) and only has data if the player
    has uploaded via the RuneLite plugin.

    Sections: overview, skills, bosses, activities (WOM);
    quests, diaries, combat_achievements, music, collection_log (wiki).
    Defaults exclude music and collection_log (large + low signal).
    """
    selected: set[Section] = set(sections or DEFAULT_SECTIONS)
    need_wom = bool(selected & WOM_SECTIONS)
    need_wiki = bool(selected & WIKI_SECTIONS)

    wom_task = _wom.player(username) if need_wom else _noop()
    wiki_task = _runelite.sync(username) if need_wiki else _noop()
    wom_data, wiki_data = await asyncio.gather(wom_task, wiki_task)

    out: dict[str, Any] = {"username": username}

    if "overview" in selected and wom_data:
        out["overview"] = {
            "id": wom_data.get("id"),
            "displayName": wom_data.get("displayName"),
            "type": wom_data.get("type"),
            "build": wom_data.get("build"),
            "country": wom_data.get("country"),
            "status": wom_data.get("status"),
            "patron": wom_data.get("patron"),
            "exp": wom_data.get("exp"),
            "ehp": wom_data.get("ehp"),
            "ehb": wom_data.get("ehb"),
            "ttm": wom_data.get("ttm"),
            "tt200m": wom_data.get("tt200m"),
            "combatLevel": wom_data.get("combatLevel"),
            "registeredAt": wom_data.get("registeredAt"),
            "updatedAt": wom_data.get("updatedAt"),
            "lastChangedAt": wom_data.get("lastChangedAt"),
        }

    snapshot_data = ((wom_data or {}).get("latestSnapshot") or {}).get("data") or {}
    if "skills" in selected:
        out["skills"] = snapshot_data.get("skills")
    if "bosses" in selected:
        out["bosses"] = snapshot_data.get("bosses")
    if "activities" in selected:
        out["activities"] = snapshot_data.get("activities")

    if need_wiki:
        if wiki_data is None:
            out["wiki_sync_status"] = "not_found"
            for s in selected & WIKI_SECTIONS:
                out[s] = None
        else:
            out["wiki_sync_status"] = "ok"
            out["wiki_synced_at"] = wiki_data.get("timestamp")
            if "quests" in selected:
                out["quests"] = wiki_data.get("quests")
            if "diaries" in selected:
                out["diaries"] = wiki_data.get("achievement_diaries")
            if "combat_achievements" in selected:
                out["combat_achievements"] = wiki_data.get("combat_achievements")
            if "music" in selected:
                out["music"] = wiki_data.get("music_tracks")
            if "collection_log" in selected:
                out["collection_log"] = {
                    "items": wiki_data.get("collection_log"),
                    "count": wiki_data.get("collectionLogItemCount"),
                }

    return out


@mcp.tool
async def get_player_gains(
    username: str,
    period: Period | None = None,
    metric: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> Any:
    """Experience/kill/score gains for a player.

    Provide either `period` (5min, day, week, month, year) or both
    `start_date` and `end_date` as ISO 8601 strings. Optionally filter to a
    single `metric` (e.g. 'attack', 'zulrah', 'clue_scrolls_all').
    """
    return await _wom.gained(
        username,
        period=period,
        metric=metric,
        start_date=start_date,
        end_date=end_date,
    )


@mcp.tool
async def get_player_records(
    username: str,
    period: Period | None = None,
    metric: str | None = None,
) -> Any:
    """Personal best records for a player, optionally filtered by period or metric."""
    return await _wom.records(username, period=period, metric=metric)


@mcp.tool
async def get_player_achievements(
    username: str,
    include_progress: bool = False,
) -> Any:
    """WiseOldMan achievement milestones (e.g. '99 Attack', '500m exp').

    If `include_progress` is true, also returns progress toward incomplete
    achievements alongside the completed ones.
    """
    if not include_progress:
        return await _wom.achievements(username)
    completed, progress = await asyncio.gather(
        _wom.achievements(username),
        _wom.achievements_progress(username),
    )
    return {"completed": completed, "progress": progress}


@mcp.tool
async def get_player_competitions(
    username: str,
    status: CompetitionStatus | None = None,
) -> Any:
    """Competitions the player participates in. Optionally filter by status."""
    data = await _wom.competitions(username)
    if status and isinstance(data, list):
        return [
            entry
            for entry in data
            if (entry.get("competition") or {}).get("status") == status
        ]
    return data


@mcp.tool
async def get_player_groups(username: str) -> Any:
    """Groups (clans) the player is a member of."""
    return await _wom.groups(username)


@mcp.tool
async def get_player_name_history(username: str) -> Any:
    """Name change history for the player."""
    return await _wom.names(username)


@mcp.tool
async def update_player(username: str) -> Any:
    """Trigger a WiseOldMan refresh from the OSRS hiscores for this player.

    WiseOldMan rate-limits this to roughly once per 60 seconds per player and
    will surface its own error if called too frequently.
    """
    try:
        return await _wom.update(username)
    except WiseOldManError as e:
        return {"error": e.message, "status": e.status}


@mcp.tool
async def wiki_search(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search the OSRS Wiki (oldschool.runescape.wiki) for matching pages.

    Returns a list of {title, snippet, sectiontitle} entries. Use `wiki_page`
    to fetch the contents of a result.
    """
    return await _wiki.search(query, limit=limit)


@mcp.tool
async def wiki_page(
    title: str, format: PageFormat = "wikitext"
) -> dict[str, Any] | None:
    """Fetch a single OSRS Wiki page by title.

    `format`:
    - `wikitext` (default) — wiki markup source. Smaller and easier for an LLM
      to parse than HTML.
    - `html` — fully rendered HTML. Use only when you specifically need
      formatting/templates expanded.

    Returns null if the page does not exist. Redirects are followed
    automatically.
    """
    return await _wiki.page(title, fmt=format)


@mcp.tool
async def ge_item(name_or_id: str) -> dict[str, Any]:
    """Grand Exchange data for an item by name or numeric ID.

    Resolves the name against the OSRS Wiki real-time prices mapping (also
    accepts substrings, e.g. 'whip' → 'Abyssal whip'). Returns metadata
    (members flag, examine, alch values, GE buy limit) plus the latest
    high/low price ticks with timestamps.
    """
    item = await _prices.resolve(name_or_id)
    if item is None:
        return {"error": f"item not found: {name_or_id}"}
    latest = await _prices.latest(item["id"])
    return {"item": item, "latest": latest}


@mcp.tool
async def ge_item_history(name_or_id: str, timestep: Timestep = "1h") -> dict[str, Any]:
    """Historical Grand Exchange price timeseries for an item.

    `timestep`: `5m`, `1h`, `6h`, or `24h`. Each point has timestamp,
    avgHighPrice, avgLowPrice, highPriceVolume, lowPriceVolume.
    """
    item = await _prices.resolve(name_or_id)
    if item is None:
        return {"error": f"item not found: {name_or_id}"}
    series = await _prices.timeseries(item["id"], timestep=timestep)
    return {"item": item, "timestep": timestep, "data": series}


async def _noop() -> None:
    return None


def get_mcp() -> FastMCP:
    return mcp


__all__ = ["mcp", "get_mcp", "WiseOldManError", "RuneLiteSyncError"]
