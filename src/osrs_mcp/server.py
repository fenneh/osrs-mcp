from fastmcp import FastMCP

mcp: FastMCP = FastMCP("osrs-mcp")


def _register_tools() -> None:
    import osrs_mcp.tools  # noqa: F401  (side effects: each submodule registers)


_register_tools()


__all__ = ["mcp"]
