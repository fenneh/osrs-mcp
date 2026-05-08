from typing import Any, Literal

from osrs_mcp.clients import wiki
from osrs_mcp.server import mcp

PageFormat = Literal["wikitext", "html"]


@mcp.tool
async def wiki_page(
    title: str, format: PageFormat = "wikitext"
) -> dict[str, Any] | None:
    """Fetch a single OSRS Wiki page by title.

    `format`:
    - `wikitext` (default) — wiki markup source. Smaller and easier for an LLM
      to parse than HTML.
    - `html` — fully rendered HTML. Use only when you specifically need
      formatting/templates expanded.

    Returns null if the page does not exist. Redirects are followed
    automatically.
    """
    return await wiki.page(title, fmt=format)
