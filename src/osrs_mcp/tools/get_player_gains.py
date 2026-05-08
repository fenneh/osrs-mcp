from typing import Any, Literal

from osrs_mcp.clients import wom
from osrs_mcp.server import mcp

Period = Literal["5min", "day", "week", "month", "year"]


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
    return await wom.gained(
        username,
        period=period,
        metric=metric,
        start_date=start_date,
        end_date=end_date,
    )
