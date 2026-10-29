"""Entry point: the official Google Ads MCP server plus the write tools.

The read-only tools from google-ads-mcp (`search`, `get_resource_metadata`,
`list_accessible_customers`) and its resources stay exactly as upstream; the
write tools are mounted next to them under the `write_` prefix.
"""

from ads_mcp.server import mcp, run_server as _run_upstream_server

from ads_write_mcp.tools import campaigns_write_mcp

mcp.mount(campaigns_write_mcp, namespace="write")


def run_server() -> None:
    _run_upstream_server()


if __name__ == "__main__":
    run_server()
