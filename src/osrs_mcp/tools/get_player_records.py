from typing import Any, Literal

from osrs_mcp.clients import wom
from osrs_mcp.server import mcp

Period = Literal["5min", "day", "week", "month", "year"]


@mcp.tool
async def get_player_records(
    username: str,
    period: Period | None = None,
    metric: str | None = None,
) -> Any:
    """Personal best records for a player, optionally filtered by period or metric."""
    return await wom.records(username, period=period, metric=metric)
