#!/usr/bin/env python3
"""
Simple test client for MCP-FreeCAD server
"""

import asyncio
import logging
import json
import sys
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.types import JSONRPCRequest, JSONRPCResponse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-test-client")

async def main():
    # Configure the server command
    server_command = ["python", "freecad_mcp_server.py"]
    server_parameters = StdioServerParameters(
        command=server_command[0],
        args=server_command[1:],
    )

    # Connect to the server
    async with stdio_client(server_parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            logger.info("Initializing session")

            # Send initialization request
            request_id = await session.send_json_rpc_request({
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "serverInfo": {
                        "name": "mcp-test-client",
                        "version": "0.1.0"
                    }
                },
                "id": 1
            })

            response = await session.get_json_rpc_response(request_id)
            logger.info(f"Initialization response: {response}")

            # List available tools
            request_id = await session.send_json_rpc_request({
                "jsonrpc": "2.0",
                "method": "list_tools",
                "params": {},
                "id": 2
            })

            tools_response = await session.get_json_rpc_response(request_id)
            tools = tools_response.get("result", {}).get("tools", [])
            logger.info(f"Available tools ({len(tools)}):")
            for tool in tools:
                logger.info(f"- {tool['name']}: {tool['description']}")

            # List available resources
            request_id = await session.send_json_rpc_request({
                "jsonrpc": "2.0",
                "method": "list_resources",
                "params": {},
                "id": 3
            })

            resources_response = await session.get_json_rpc_response(request_id)
            resources = resources_response.get("result", {}).get("resources", [])
            logger.info(f"Available resources ({len(resources)}):")
            for resource in resources:
                logger.info(f"- {resource['uri']}: {resource['name']}")

            # Test a tool if available
            if any(tool["name"] == "freecad.create_document" for tool in tools):
                logger.info("Testing create_document tool...")
                request_id = await session.send_json_rpc_request({
                    "jsonrpc": "2.0",
                    "method": "call_tool",
                    "params": {
                        "name": "freecad.create_document",
                        "arguments": {"name": "TestDocument"}
                    },
                    "id": 4
                })

                result = await session.get_json_rpc_response(request_id)
                logger.info(f"Result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)
