from typing import Any, Literal

from osrs_mcp.clients import wom
from osrs_mcp.server import mcp

CompetitionStatus = Literal["upcoming", "ongoing", "finished"]


@mcp.tool
async def get_player_competitions(
    username: str,
    status: CompetitionStatus | None = None,
) -> Any:
    """Competitions the player participates in. Optionally filter by status."""
    data = await wom.competitions(username)
    if status and isinstance(data, list):
        return [
            entry
            for entry in data
            if (entry.get("competition") or {}).get("status") == status
        ]
    return data
