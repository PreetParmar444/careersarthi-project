"""
mcp_server.tools
───────────────────
Individual Career MCP tool implementations. Each module is plain,
dependency-light Python with no MCP-specific code, so every tool is
directly unit-testable (see tests/test_core.py) without spinning up
the MCP server itself. mcp_server/server.py wraps these as MCP tools.
"""
