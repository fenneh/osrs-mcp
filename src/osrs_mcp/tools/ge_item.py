from typing import Any

from osrs_mcp.clients import prices
from osrs_mcp.server import mcp


@mcp.tool
async def ge_item(name_or_id: str) -> dict[str, Any]:
    """Grand Exchange data for an item by name or numeric ID.

    Resolves the name against the OSRS Wiki real-time prices mapping (also
    accepts substrings, e.g. 'whip' → 'Abyssal whip'). Returns metadata
    (members flag, examine, alch values, GE buy limit) plus the latest
    high/low price ticks with timestamps.
    """
    item = await prices.resolve(name_or_id)
    if item is None:
        return {"error": f"item not found: {name_or_id}"}
    latest = await prices.latest(item["id"])
    return {"item": item, "latest": latest}
