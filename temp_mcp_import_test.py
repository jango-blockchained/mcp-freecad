import sys

print("Attempting MCP SDK import...")
try:
    from mcp_sdk.server import Server, StdioServerTransport
    from mcp_sdk.server.requests import (
        ExecuteToolRequestSchema,
        GetResourceRequestSchema,
        ListResourcesRequestSchema,
        ListToolsRequestSchema,
    )
    from mcp_sdk.server.responses import ErrorResponse

    print("MCP SDK Import Successful!")
except ImportError as e:
    print(f"ImportError encountered: {e}")
    print("sys.path:")
    for p in sys.path:
        print(f"  - {p}")
except Exception as e:
    print(f"An unexpected error occurred during import: {e}")
