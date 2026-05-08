import asyncio
from typing import Any

from osrs_mcp.clients import wom
from osrs_mcp.server import mcp


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
        return await wom.achievements(username)
    completed, progress = await asyncio.gather(
        wom.achievements(username),
        wom.achievements_progress(username),
    )
    return {"completed": completed, "progress": progress}
