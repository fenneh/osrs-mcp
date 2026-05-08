from typing import Any

from osrs_mcp.clients import wiki
from osrs_mcp.server import mcp


@mcp.tool
async def wiki_search(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search the OSRS Wiki (oldschool.runescape.wiki) for matching pages.

    Returns a list of {title, snippet, sectiontitle} entries. Use `wiki_page`
    to fetch the contents of a result.
    """
    return await wiki.search(query, limit=limit)
