#!/usr/bin/env python3
"""
Jyotish MCP Server entry point.
Usage: jyotish-mcp
"""
import sys
import os

# The actual MCP server is at repo root; delegate to it
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_mcp_server = os.path.join(_repo_root, "mcp_server.py")


def main():
    """Run the MCP server."""
    if not os.path.exists(_mcp_server):
        print(f"Error: MCP server not found at {_mcp_server}", file=sys.stderr)
        sys.exit(1)
    
    # Execute the root-level MCP server
    with open(_mcp_server, "r", encoding="utf-8") as f:
        code = compile(f.read(), _mcp_server, "exec")
    exec(code, {"__file__": _mcp_server, "__name__": "__main__"})


if __name__ == "__main__":
    main()
