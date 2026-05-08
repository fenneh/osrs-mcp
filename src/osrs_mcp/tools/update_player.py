from typing import Any

from osrs_mcp.clients import wom
from osrs_mcp.server import mcp
from osrs_mcp.wiseoldman import WiseOldManError


@mcp.tool
async def update_player(username: str) -> Any:
    """Trigger a WiseOldMan refresh from the OSRS hiscores for this player.

    WiseOldMan rate-limits this to roughly once per 60 seconds per player and
    will surface its own error if called too frequently.
    """
    try:
        return await wom.update(username)
    except WiseOldManError as e:
        return {"error": e.message, "status": e.status}
