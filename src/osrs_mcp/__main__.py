import argparse
import os

from osrs_mcp.server import mcp


def main() -> None:
    parser = argparse.ArgumentParser(prog="osrs-mcp")
    parser.add_argument(
        "--http",
        action="store_true",
        help="Run streamable HTTP transport instead of stdio",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("OSRS_MCP_HOST", "0.0.0.0"),
        help="HTTP bind host (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", "3000")),
        help="HTTP bind port (default: 3000 or $PORT)",
    )
    args = parser.parse_args()

    if args.http:
        mcp.run(transport="http", host=args.host, port=args.port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
