# osrs-mcp

An MCP server for looking up Old School RuneScape players, items, and wiki pages. Talks to four upstreams:

- WiseOldMan for stats, gains, records, competitions, groups, name history
- RuneLite Sync for quests, diaries, combat achievements, music, collection log (only populated if the player has uploaded via the RuneLite plugin)
- The OSRS Wiki API for search and page lookup
- The OSRS Wiki real-time prices API for Grand Exchange data

## Tools

### Player

- `get_player(username, sections?)`. Combined snapshot. `sections` picks from `overview`, `skills`, `bosses`, `activities` (WOM) and `quests`, `diaries`, `combat_achievements`, `music`, `collection_log` (wiki). Defaults skip `music` and `collection_log` because they're huge and rarely useful.
- `get_player_gains(username, period?, metric?, start_date?, end_date?)`
- `get_player_records(username, period?, metric?)`
- `get_player_achievements(username, include_progress?)`
- `get_player_competitions(username, status?)`
- `get_player_groups(username)`
- `get_player_name_history(username)`
- `update_player(username)`. Kicks WOM into refreshing from the hiscores. Rate-limited upstream to roughly once per 60s per player.

### Wiki

- `wiki_search(query, limit?)`
- `wiki_page(title, format?)`. `wikitext` (default) or `html`. Follows redirects.

### Grand Exchange

- `ge_item(name_or_id)`. Current price plus item metadata. Names match exactly first, then fall back to substring, so `whip` finds `Abyssal whip`.
- `ge_item_history(name_or_id, timestep?)`. Price timeseries. `timestep` is `5m`, `1h`, `6h`, or `24h`.

## Hosted endpoint

A public instance runs at `https://osrs.mcp.fen.gg/mcp` with no auth. Add it as a custom connector in any MCP client. If you're going to hammer it, please run your own.

## Local install (stdio)

```bash
git clone https://github.com/fenneh/osrs-mcp ~/git/osrs-mcp
cd ~/git/osrs-mcp
uv sync
```

Wire it into Claude Code:

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
```

Endpoint at `http://localhost:3000/mcp`.

## Tests

```bash
uv run pytest
```
