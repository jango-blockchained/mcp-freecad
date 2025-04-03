#!/usr/bin/env python3
"""
Comprehensive Test Suite for FreeCAD MCP Server Tools

This script tests all available tools in the FreeCAD MCP server, including
primitive creation, boolean operations, transformations, and document management.
"""

import asyncio
import json
import logging
import sys
import time
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("mcp-test-tools")

class MCPTestClient:
    """Test client for MCP-FreeCAD server."""

    def __init__(self):
        """Initialize the test client."""
        self.server_command = ["python", "freecad_mcp_server.py"]
        self.request_counter = 0
        self.session = None
        self.read_stream = None
        self.write_stream = None
        self.created_objects = []
        self.tools = []

    async def connect(self):
        """Connect to the MCP server."""
        logger.info("Connecting to MCP server...")
        server_parameters = StdioServerParameters(
            command=self.server_command[0],
            args=self.server_command[1:],
        )

        self.read_stream, self.write_stream = await stdio_client(server_parameters).__aenter__()
        self.session = ClientSession(self.read_stream, self.write_stream)
        await self.session.__aenter__()

        # Initialize connection
        await self.initialize()
        logger.info("Connected to MCP server")

    async def initialize(self):
        """Initialize the session."""
        logger.info("Initializing session...")
        self.request_counter += 1
        request_id = await self.session.send_json_rpc_request({
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "serverInfo": {
                    "name": "mcp-test-tools",
                    "version": "0.1.0"
                }
            },
            "id": self.request_counter
        })

        response = await self.session.get_json_rpc_response(request_id)
        logger.info(f"Initialization response: {response.get('result', {}).get('serverInfo', {}).get('name', 'Unknown')}")

    async def list_tools(self):
        """List all available tools."""
        logger.info("Listing all tools...")
        self.request_counter += 1
        request_id = await self.session.send_json_rpc_request({
            "jsonrpc": "2.0",
            "method": "list_tools",
            "params": {},
            "id": self.request_counter
        })

        response = await self.session.get_json_rpc_response(request_id)
        tools = response.get("result", {}).get("tools", [])
        self.tools = tools
        logger.info(f"Found {len(tools)} tools")
        return tools

    async def call_tool(self, tool_name, arguments):
        """Call a tool with the specified arguments."""
        logger.info(f"Calling tool: {tool_name}")
        self.request_counter += 1
        request_id = await self.session.send_json_rpc_request({
            "jsonrpc": "2.0",
            "method": "call_tool",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": self.request_counter
        })

        response = await self.session.get_json_rpc_response(request_id)
        result = response.get("result", {})

        # Check for error
        if "error" in result:
            logger.error(f"Error calling tool {tool_name}: {result['error']}")
            return None

        logger.info(f"Tool result: {result.get('message', 'No message')}")
        return result

    async def disconnect(self):
        """Disconnect from the MCP server."""
        logger.info("Disconnecting from MCP server...")
        try:
            if self.session:
                await self.session.__aexit__(None, None, None)
            if self.read_stream and self.write_stream:
                await stdio_client(None).__aexit__(None, None, None)
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")

    async def test_document_creation(self):
        """Test document creation."""
        logger.info("=== Testing Document Creation ===")
        result = await self.call_tool("freecad.create_document", {"name": "TestDoc"})
        if not result or not result.get("success"):
            logger.error("Document creation failed")
            return False
        logger.info("Document creation successful")
        return True

    async def test_primitives(self):
        """Test creating primitive shapes."""
        logger.info("=== Testing Primitive Creation ===")

        # Create a box
        box_result = await self.call_tool("freecad.create_box", {
            "length": 50,
            "width": 30,
            "height": 20,
            "name": "TestBox",
            "position_x": 0,
            "position_y": 0,
            "position_z": 0
        })
        if box_result and box_result.get("success"):
            self.created_objects.append(box_result.get("object_name"))

        # Create a cylinder
        cylinder_result = await self.call_tool("freecad.create_cylinder", {
            "radius": 20,
            "height": 50,
            "name": "TestCylinder",
            "position_x": 100,
            "position_y": 0,
            "position_z": 0
        })
        if cylinder_result and cylinder_result.get("success"):
            self.created_objects.append(cylinder_result.get("object_name"))

        # Create a sphere
        sphere_result = await self.call_tool("freecad.create_sphere", {
            "radius": 25,
            "name": "TestSphere",
            "position_x": 0,
            "position_y": 100,
            "position_z": 0
        })
        if sphere_result and sphere_result.get("success"):
            self.created_objects.append(sphere_result.get("object_name"))

        # Create a cone
        cone_result = await self.call_tool("freecad.create_cone", {
            "radius1": 20,
            "radius2": 5,
            "height": 40,
            "name": "TestCone",
            "position_x": 100,
            "position_y": 100,
            "position_z": 0
        })
        if cone_result and cone_result.get("success"):
            self.created_objects.append(cone_result.get("object_name"))

        # Check if we have created all primitives
        if len(self.created_objects) == 4:
            logger.info("All primitives created successfully")
            return True
        else:
            logger.error(f"Failed to create all primitives. Created: {self.created_objects}")
            return False

    async def test_boolean_operations(self):
        """Test boolean operations."""
        logger.info("=== Testing Boolean Operations ===")

        # First create two overlapping boxes
        box1_result = await self.call_tool("freecad.create_box", {
            "length": 30,
            "width": 30,
            "height": 30,
            "name": "BoolBox1",
            "position_x": 0,
            "position_y": 0,
            "position_z": 0
        })

        box2_result = await self.call_tool("freecad.create_box", {
            "length": 30,
            "width": 30,
            "height": 30,
            "name": "BoolBox2",
            "position_x": 15,
            "position_y": 15,
            "position_z": 15
        })

        if box1_result and box2_result:
            box1_name = box1_result.get("object_name")
            box2_name = box2_result.get("object_name")

            # Test union
            union_result = await self.call_tool("freecad.boolean_union", {
                "object1": box1_name,
                "object2": box2_name,
                "name": "TestUnion"
            })

            # Create new boxes for the next operations
            box3_result = await self.call_tool("freecad.create_box", {
                "length": 30,
                "width": 30,
                "height": 30,
                "name": "BoolBox3",
                "position_x": 100,
                "position_y": 0,
                "position_z": 0
            })

            box4_result = await self.call_tool("freecad.create_box", {
                "length": 30,
                "width": 30,
                "height": 30,
                "name": "BoolBox4",
                "position_x": 115,
                "position_y": 15,
                "position_z": 15
            })

            if box3_result and box4_result:
                box3_name = box3_result.get("object_name")
                box4_name = box4_result.get("object_name")

                # Test cut
                cut_result = await self.call_tool("freecad.boolean_cut", {
                    "object1": box3_name,
                    "object2": box4_name,
                    "name": "TestCut"
                })

                # Create new boxes for the next operation
                box5_result = await self.call_tool("freecad.create_box", {
                    "length": 30,
                    "width": 30,
                    "height": 30,
                    "name": "BoolBox5",
                    "position_x": 0,
                    "position_y": 100,
                    "position_z": 0
                })

                box6_result = await self.call_tool("freecad.create_box", {
                    "length": 30,
                    "width": 30,
                    "height": 30,
                    "name": "BoolBox6",
                    "position_x": 15,
                    "position_y": 115,
                    "position_z": 15
                })

                if box5_result and box6_result:
                    box5_name = box5_result.get("object_name")
                    box6_name = box6_result.get("object_name")

                    # Test intersection
                    intersection_result = await self.call_tool("freecad.boolean_intersection", {
                        "object1": box5_name,
                        "object2": box6_name,
                        "name": "TestIntersection"
                    })

                    if union_result and cut_result and intersection_result:
                        logger.info("All boolean operations completed successfully")
                        return True

        logger.error("Boolean operations test failed")
        return False

    async def test_transformations(self):
        """Test transformation operations."""
        logger.info("=== Testing Transformations ===")

        # Create a box to transform
        box_result = await self.call_tool("freecad.create_box", {
            "length": 20,
            "width": 20,
            "height": 20,
            "name": "TransformBox",
            "position_x": 0,
            "position_y": 0,
            "position_z": 0
        })

        if box_result:
            box_name = box_result.get("object_name")

            # Test move operation
            move_result = await self.call_tool("freecad.move_object", {
                "object_name": box_name,
                "position_x": 50,
                "position_y": 50,
                "position_z": 50
            })

            # Test rotate operation
            rotate_result = await self.call_tool("freecad.rotate_object", {
                "object_name": box_name,
                "rotation_x": 45,
                "rotation_y": 0,
                "rotation_z": 0
            })

            if move_result and rotate_result:
                logger.info("All transformation operations completed successfully")
                return True

        logger.error("Transformation tests failed")
        return False

    async def test_document_management(self):
        """Test document management operations."""
        logger.info("=== Testing Document Management ===")

        # List objects in the current document
        list_objects_result = await self.call_tool("freecad.list_objects", {})

        # List documents
        list_documents_result = await self.call_tool("freecad.list_documents", {})

        if list_objects_result and list_documents_result:
            objects = list_objects_result.get("objects", [])
            documents = list_documents_result.get("documents", [])

            logger.info(f"Found {len(objects)} objects in active document")
            logger.info(f"Found {len(documents)} open documents")
            return True

        logger.error("Document management tests failed")
        return False

    async def test_export(self):
        """Test export functionality."""
        logger.info("=== Testing Export Functionality ===")

        if len(self.created_objects) > 0:
            # Export one of the created objects
            export_result = await self.call_tool("freecad.export_stl", {
                "file_path": "test_export.stl",
                "object_name": self.created_objects[0]
            })

            if export_result and export_result.get("success"):
                logger.info(f"Successfully exported {self.created_objects[0]} to STL")
                return True

        logger.error("Export test failed")
        return False

    async def run_all_tests(self):
        """Run all tests in sequence."""
        try:
            await self.connect()

            # Get all available tools
            tools = await self.list_tools()

            # Run all tests
            doc_test = await self.test_document_creation()
            prim_test = await self.test_primitives()
            bool_test = await self.test_boolean_operations()
            trans_test = await self.test_transformations()
            mgmt_test = await self.test_document_management()
            export_test = await self.test_export()

            # Display test results
            results = {
                "Document Creation": doc_test,
                "Primitives": prim_test,
                "Boolean Operations": bool_test,
                "Transformations": trans_test,
                "Document Management": mgmt_test,
                "Export": export_test
            }

            logger.info("\n=== Test Results ===")
            for test_name, result in results.items():
                status = "PASSED" if result else "FAILED"
                logger.info(f"{test_name}: {status}")

            success = all(results.values())
            logger.info(f"\nOverall Test Result: {'PASSED' if success else 'FAILED'}")

        except Exception as e:
            logger.error(f"Error during testing: {e}", exc_info=True)
        finally:
            await self.disconnect()


async def main():
    """Run the test suite."""
    logger.info("Starting MCP-FreeCAD Tools Test Suite")

    client = MCPTestClient()
    await client.run_all_tests()

    logger.info("Test suite completed")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)
