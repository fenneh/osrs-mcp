from typing import Any, Literal

from osrs_mcp.clients import prices
from osrs_mcp.server import mcp

Timestep = Literal["5m", "1h", "6h", "24h"]


@mcp.tool
async def ge_item_history(name_or_id: str, timestep: Timestep = "1h") -> dict[str, Any]:
    """Historical Grand Exchange price timeseries for an item.

    `timestep`: `5m`, `1h`, `6h`, or `24h`. Each point has timestamp,
    avgHighPrice, avgLowPrice, highPriceVolume, lowPriceVolume.
    """
    item = await prices.resolve(name_or_id)
    if item is None:
        return {"error": f"item not found: {name_or_id}"}
    series = await prices.timeseries(item["id"], timestep=timestep)
    return {"item": item, "timestep": timestep, "data": series}
