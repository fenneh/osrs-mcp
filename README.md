# osrs-mcp

MCP server for Old School RuneScape. Combines four data sources:

- **[WiseOldMan](https://wiseoldman.net)** — player stats, gains, records, competitions, groups, name history.
- **[RuneLite Sync](https://sync.runescape.wiki)** — quests, achievement diaries, combat achievements, music, collection log (only populated for players who have synced via the RuneLite plugin).
- **OSRS Wiki API** (`oldschool.runescape.wiki`) — wiki search and page lookup.
- **OSRS Wiki real-time prices** (`prices.runescape.wiki`) — live Grand Exchange prices and historical timeseries.

## Tools

### Player
- `get_player(username, sections?)` — combined snapshot. `sections` selects from `overview`, `skills`, `bosses`, `activities` (WOM) and `quests`, `diaries`, `combat_achievements`, `music`, `collection_log` (wiki). Defaults exclude `music` and `collection_log`.
- `get_player_gains(username, period?, metric?, start_date?, end_date?)`
- `get_player_records(username, period?, metric?)`
- `get_player_achievements(username, include_progress?)`
- `get_player_competitions(username, status?)`
- `get_player_groups(username)`
- `get_player_name_history(username)`
- `update_player(username)` — refresh WOM from hiscores (rate-limited upstream).

### Wiki
- `wiki_search(query, limit?)` — search the OSRS Wiki for matching pages.
- `wiki_page(title, format?)` — fetch a page as `wikitext` (default) or `html`. Follows redirects.

### Grand Exchange
- `ge_item(name_or_id)` — current GE price + item metadata. Resolves names (incl. substrings, e.g. `whip` → `Abyssal whip`) or numeric IDs.
- `ge_item_history(name_or_id, timestep?)` — price timeseries (`5m`/`1h`/`6h`/`24h`).

## Hosted endpoint

Public streamable-HTTP MCP at `https://osrs.mcp.fen.gg/mcp`. Add it as a custom connector in any MCP-aware client; no auth required.

## Local install (stdio)

```bash
git clone https://github.com/fenneh/osrs-mcp ~/git/osrs-mcp
cd ~/git/osrs-mcp
uv sync
```

Claude Code config (`~/.claude/claude_code_config.json` or via `claude mcp add`):

```json
{
  "mcpServers": {
    "osrs": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/osrs-mcp", "run", "python", "-m", "osrs_mcp"]
    }
  }
}
```

## Run HTTP locally

```bash
uv run python -m osrs_mcp --http --port 3000
# MCP endpoint: http://localhost:3000/mcp
```

## Tests

```bash
uv run pytest
```
