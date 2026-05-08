import asyncio
from typing import Any, Literal

from osrs_mcp.clients import runelite, wom
from osrs_mcp.server import mcp

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

    wom_task = wom.player(username) if need_wom else _noop()
    wiki_task = runelite.sync(username) if need_wiki else _noop()
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


async def _noop() -> None:
    return None
