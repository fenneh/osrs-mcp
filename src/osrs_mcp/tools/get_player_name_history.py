from typing import Any

from osrs_mcp.clients import wom
from osrs_mcp.server import mcp


@mcp.tool
async def get_player_name_history(username: str) -> Any:
    """Name change history for the player."""
    return await wom.names(username)
