from typing import Any

from osrs_mcp.clients import wom
from osrs_mcp.server import mcp


@mcp.tool
async def get_player_groups(username: str) -> Any:
    """Groups (clans) the player is a member of."""
    return await wom.groups(username)
