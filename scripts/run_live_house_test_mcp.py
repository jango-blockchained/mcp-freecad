#!/usr/bin/env python3
"""
MCP Live House Modeling Test Runner

This script uses the MCP-FreeCAD server architecture to run the house modeling test
on a real FreeCAD instance with GUI enabled. It demonstrates the full MCP toolchain
in action while you watch the 3D house being built.
"""

import asyncio
import sys
import time
import logging
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.mcp_freecad.server.freecad_mcp_server import FreecadMcpServer
from src.mcp_freecad.client.freecad_connection_manager import FreecadConnectionManager


class MCPLiveHouseTestRunner:
    """
    Test runner that creates a house model using the full MCP-FreeCAD server architecture.
    """

    def __init__(self, step_delay: float = 2.0):
        """
        Initialize the MCP live test runner.

        Args:
            step_delay: Delay in seconds between modeling steps for visualization
        """
        self.step_delay = step_delay
        self.freecad_process = None
        self.mcp_server = None
        self.connection_manager = None

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

    def get_house_specification(self) -> Dict[str, Any]:
        """Get the house specifications for the test."""
        return {
            "foundation": {
                "length": 10.0,
                "width": 8.0,
                "height": 0.3,
                "material": "concrete"
            },
            "walls": {
                "height": 3.0,
                "thickness": 0.3,
                "material": "brick"
            },
            "windows": [
                {
                    "id": "front_window_1",
                    "width": 1.2,
                    "height": 1.5,
                    "position": {"x": 2.0, "y": 0.0, "z": 1.0},
                    "wall": "front"
                },
                {
                    "id": "front_window_2",
                    "width": 1.2,
                    "height": 1.5,
                    "position": {"x": 6.0, "y": 0.0, "z": 1.0},
                    "wall": "front"
                }
            ],
            "doors": [
                {
                    "id": "front_door",
                    "width": 0.9,
                    "height": 2.1,
                    "position": {"x": 4.5, "y": 0.0, "z": 0.0},
                    "wall": "front"
                }
            ]
        }

    async def start_freecad(self) -> bool:
        """
        Start FreeCAD with GUI enabled.

        Returns:
            True if started successfully, False otherwise
        """
        try:
            self.logger.info("🚀 Starting FreeCAD with GUI...")

            # Use the AppImage in the project root
            freecad_path = Path(__file__).parent / "FreeCAD_1.0.0-conda-Linux-x86_64-py311.AppImage"

            if not freecad_path.exists():
                self.logger.error(f"FreeCAD AppImage not found at: {freecad_path}")
                return False

            # Start FreeCAD in the background
            self.freecad_process = subprocess.Popen(
                [str(freecad_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Give FreeCAD time to start
            self.logger.info("Waiting for FreeCAD to start...")
            await asyncio.sleep(5)

            # Check if process is still running
            if self.freecad_process.poll() is not None:
                self.logger.error("FreeCAD process exited unexpectedly")
                return False

            self.logger.info("✅ FreeCAD started successfully!")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start FreeCAD: {e}")
            return False

    async def setup_mcp_server(self) -> bool:
        """
        Set up the MCP server and connect to FreeCAD.

        Returns:
            True if setup successful, False otherwise
        """
        try:
            self.logger.info("🔧 Setting up MCP server...")

            # Create connection manager
            self.connection_manager = FreecadConnectionManager()

            # Try to connect to FreeCAD using launcher method
            self.logger.info("Connecting to FreeCAD...")
            connection_success = await self.connection_manager.connect_to_freecad(
                method="launcher",
                freecad_path=str(Path(__file__).parent / "FreeCAD_1.0.0-conda-Linux-x86_64-py311.AppImage")
            )

            if not connection_success:
                self.logger.error("Failed to connect to FreeCAD via MCP")
                return False

            # Initialize MCP server
            self.mcp_server = FreecadMcpServer()

            # Create a new document
            result = await self.execute_tool("primitives", "create_box", {
                "length": 0.1,
                "width": 0.1,
                "height": 0.1
            })

            if result.get("status") == "success":
                # Delete the test box
                self.logger.info("✅ MCP server connected successfully!")
                return True
            else:
                self.logger.error("Failed to execute test command")
                return False

        except Exception as e:
            self.logger.error(f"Failed to setup MCP server: {e}")
            return False

    async def execute_tool(self, tool_type: str, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool via the MCP server.

        Args:
            tool_type: Type of tool (e.g., "primitives", "model_manipulation")
            tool_name: Name of the tool to execute
            params: Tool parameters

        Returns:
            Tool execution result
        """
        try:
            # Use the connection manager to execute the tool
            if tool_type == "primitives":
                if tool_name == "create_box":
                    return await self._create_box(params)
                elif tool_name == "create_cylinder":
                    return await self._create_cylinder(params)
            elif tool_type == "model_manipulation":
                if tool_name == "transform":
                    return await self._transform_object(params)
                elif tool_name == "boolean_operation":
                    return await self._boolean_operation(params)

            return {"status": "error", "error": f"Unknown tool: {tool_type}.{tool_name}"}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _create_box(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a box primitive."""
        try:
            # Execute via connection manager
            script = f"""
import FreeCAD
import Part

doc = FreeCAD.activeDocument()
if doc is None:
    doc = FreeCAD.newDocument("LiveHouseTest")
    FreeCAD.setActiveDocument(doc.Name)

# Create box
box = doc.addObject("Part::Box", "Box")
box.Length = {params.get('length', 1.0)}
box.Width = {params.get('width', 1.0)}
box.Height = {params.get('height', 1.0)}

doc.recompute()
print(f"BOX_CREATED:{box.Name}")
"""

            result = await self.connection_manager.execute_freecad_command(script)

            # Parse result to extract object name
            if "BOX_CREATED:" in result:
                object_name = result.split("BOX_CREATED:")[-1].strip()
                return {
                    "status": "success",
                    "result": {
                        "object_id": object_name,
                        "object_type": "Part::Box",
                        "message": f"Box {object_name} created successfully"
                    }
                }
            else:
                return {"status": "error", "error": "Failed to create box"}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _create_cylinder(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a cylinder primitive."""
        try:
            script = f"""
import FreeCAD
import Part

doc = FreeCAD.activeDocument()
if doc is None:
    doc = FreeCAD.newDocument("LiveHouseTest")

# Create cylinder
cylinder = doc.addObject("Part::Cylinder", "Cylinder")
cylinder.Radius = {params.get('radius', 1.0)}
cylinder.Height = {params.get('height', 1.0)}

doc.recompute()
print(f"CYLINDER_CREATED:{cylinder.Name}")
"""

            result = await self.connection_manager.execute_freecad_command(script)

            if "CYLINDER_CREATED:" in result:
                object_name = result.split("CYLINDER_CREATED:")[-1].strip()
                return {
                    "status": "success",
                    "result": {
                        "object_id": object_name,
                        "object_type": "Part::Cylinder",
                        "message": f"Cylinder {object_name} created successfully"
                    }
                }
            else:
                return {"status": "error", "error": "Failed to create cylinder"}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _transform_object(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transform an object."""
        try:
            object_name = params.get("object")
            translation = params.get("translation", [0, 0, 0])
            rotation = params.get("rotation", [0, 0, 0])

            script = f"""
import FreeCAD

doc = FreeCAD.activeDocument()
obj = doc.getObject("{object_name}")

if obj is not None:
    # Apply translation
    placement = obj.Placement
    placement.Base.x += {translation[0]}
    placement.Base.y += {translation[1]}
    placement.Base.z += {translation[2]}

    # Apply rotation if specified
    if {rotation} != [0, 0, 0]:
        import math
        placement.Rotation = FreeCAD.Rotation(
            math.radians({rotation[0]}),
            math.radians({rotation[1]}),
            math.radians({rotation[2]})
        )

    obj.Placement = placement
    doc.recompute()
    print(f"TRANSFORM_SUCCESS:{object_name}")
else:
    print(f"TRANSFORM_ERROR:Object {object_name} not found")
"""

            result = await self.connection_manager.execute_freecad_command(script)

            if "TRANSFORM_SUCCESS:" in result:
                return {
                    "status": "success",
                    "result": {
                        "object_id": object_name,
                        "message": f"Object {object_name} transformed successfully"
                    }
                }
            else:
                return {"status": "error", "error": f"Failed to transform {object_name}"}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _boolean_operation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform boolean operation."""
        try:
            object1 = params.get("object1")
            object2 = params.get("object2")
            operation = params.get("operation", "union")

            script = f"""
import FreeCAD

doc = FreeCAD.activeDocument()
obj1 = doc.getObject("{object1}")
obj2 = doc.getObject("{object2}")

if obj1 is not None and obj2 is not None:
    # Create boolean operation
    if "{operation}" == "union":
        result = doc.addObject("Part::Fuse", "Union")
    elif "{operation}" == "difference":
        result = doc.addObject("Part::Cut", "Difference")
    elif "{operation}" == "intersection":
        result = doc.addObject("Part::Common", "Intersection")
    else:
        print("BOOLEAN_ERROR:Invalid operation")

    result.Base = obj1
    result.Tool = obj2
    doc.recompute()
    print(f"BOOLEAN_SUCCESS:{result.Name}")
else:
    print("BOOLEAN_ERROR:Objects not found")
"""

            result = await self.connection_manager.execute_freecad_command(script)

            if "BOOLEAN_SUCCESS:" in result:
                object_name = result.split("BOOLEAN_SUCCESS:")[-1].strip()
                return {
                    "status": "success",
                    "result": {
                        "object_id": object_name,
                        "message": f"Boolean {operation} created: {object_name}"
                    }
                }
            else:
                return {"status": "error", "error": f"Failed to perform {operation}"}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def create_foundation(self, foundation_spec: Dict[str, Any]) -> str:
        """Create the house foundation."""
        self.logger.info("🏗️  Creating foundation...")

        result = await self.execute_tool(
            "primitives",
            "create_box",
            {
                "length": foundation_spec["length"],
                "width": foundation_spec["width"],
                "height": foundation_spec["height"]
            }
        )

        if result["status"] != "success":
            raise Exception(f"Failed to create foundation: {result.get('error', 'Unknown error')}")

        foundation_id = result["result"]["object_id"]
        self.logger.info(f"✅ Foundation created: {foundation_id}")

        await asyncio.sleep(self.step_delay)
        return foundation_id

    async def create_walls(self, foundation_spec: Dict[str, Any], wall_spec: Dict[str, Any]) -> List[str]:
        """Create the house walls."""
        self.logger.info("🧱 Creating walls...")

        wall_height = wall_spec["height"]
        wall_thickness = wall_spec["thickness"]
        wall_ids = []

        # Create and position each wall
        wall_configs = [
            {
                "name": "front wall",
                "params": {"length": foundation_spec["length"], "width": wall_thickness, "height": wall_height},
                "translation": [0, -wall_thickness/2, foundation_spec["height"]]
            },
            {
                "name": "back wall",
                "params": {"length": foundation_spec["length"], "width": wall_thickness, "height": wall_height},
                "translation": [0, foundation_spec["width"] + wall_thickness/2, foundation_spec["height"]]
            },
            {
                "name": "left wall",
                "params": {"length": wall_thickness, "width": foundation_spec["width"], "height": wall_height},
                "translation": [-wall_thickness/2, 0, foundation_spec["height"]]
            },
            {
                "name": "right wall",
                "params": {"length": wall_thickness, "width": foundation_spec["width"], "height": wall_height},
                "translation": [foundation_spec["length"] + wall_thickness/2, 0, foundation_spec["height"]]
            }
        ]

        for wall_config in wall_configs:
            self.logger.info(f"Creating {wall_config['name']}...")

            # Create wall
            wall_result = await self.execute_tool("primitives", "create_box", wall_config["params"])
            if wall_result["status"] != "success":
                raise Exception(f"Failed to create {wall_config['name']}: {wall_result.get('error')}")

            wall_id = wall_result["result"]["object_id"]
            wall_ids.append(wall_id)

            # Position wall
            await self.execute_tool(
                "model_manipulation",
                "transform",
                {
                    "object": wall_id,
                    "translation": wall_config["translation"]
                }
            )

            await asyncio.sleep(self.step_delay)

        self.logger.info(f"✅ All walls created: {wall_ids}")
        return wall_ids

    async def create_openings(self, windows: List[Dict], doors: List[Dict], wall_thickness: float) -> List[str]:
        """Create window and door openings."""
        self.logger.info("🪟 Creating windows and doors...")

        opening_ids = []

        # Create windows
        for window in windows:
            self.logger.info(f"Creating window: {window['id']}")

            window_result = await self.execute_tool(
                "primitives",
                "create_box",
                {
                    "length": window["width"],
                    "width": wall_thickness + 0.1,
                    "height": window["height"]
                }
            )

            if window_result["status"] == "success":
                window_id = window_result["result"]["object_id"]
                opening_ids.append(window_id)

                # Position window
                pos = window["position"]
                await self.execute_tool(
                    "model_manipulation",
                    "transform",
                    {
                        "object": window_id,
                        "translation": [pos["x"], pos["y"], pos["z"]]
                    }
                )

                await asyncio.sleep(self.step_delay)

        # Create doors
        for door in doors:
            self.logger.info(f"Creating door: {door['id']}")

            door_result = await self.execute_tool(
                "primitives",
                "create_box",
                {
                    "length": door["width"],
                    "width": wall_thickness + 0.1,
                    "height": door["height"]
                }
            )

            if door_result["status"] == "success":
                door_id = door_result["result"]["object_id"]
                opening_ids.append(door_id)

                # Position door
                pos = door["position"]
                await self.execute_tool(
                    "model_manipulation",
                    "transform",
                    {
                        "object": door_id,
                        "translation": [pos["x"], pos["y"], pos["z"]]
                    }
                )

                await asyncio.sleep(self.step_delay)

        self.logger.info(f"✅ Openings created: {opening_ids}")
        return opening_ids

    async def run_house_test(self):
        """Run the complete house modeling test."""
        try:
            self.logger.info("🏠 Starting MCP Live House Modeling Test")
            self.logger.info("=" * 60)

            # Start FreeCAD
            if not await self.start_freecad():
                return False

            # Give extra time for GUI to load
            self.logger.info("Waiting for FreeCAD GUI to be ready...")
            await asyncio.sleep(3)

            # Setup MCP server
            if not await self.setup_mcp_server():
                return False

            # Get house specifications
            house_spec = self.get_house_specification()

            # Create foundation
            foundation_id = await self.create_foundation(house_spec["foundation"])

            # Create walls
            wall_ids = await self.create_walls(
                house_spec["foundation"],
                house_spec["walls"]
            )

            # Create openings
            opening_ids = await self.create_openings(
                house_spec["windows"],
                house_spec["doors"],
                house_spec["walls"]["thickness"]
            )

            self.logger.info("🎉 House modeling completed successfully!")
            self.logger.info(f"Created objects:")
            self.logger.info(f"  - Foundation: {foundation_id}")
            self.logger.info(f"  - Walls: {wall_ids}")
            self.logger.info(f"  - Openings: {opening_ids}")

            # Keep FreeCAD open for inspection
            self.logger.info("🔍 FreeCAD will remain open for inspection...")
            self.logger.info("Press Ctrl+C to exit")

            # Wait for user interrupt
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                self.logger.info("Shutting down...")

            return True

        except Exception as e:
            self.logger.error(f"Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            # Cleanup
            if self.freecad_process:
                self.logger.info("Terminating FreeCAD...")
                self.freecad_process.terminate()
                self.freecad_process.wait()


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="MCP Live House Modeling Test - Watch a 3D house being built via MCP tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_live_house_test_mcp.py                    # Run with default 2s delay
  python run_live_house_test_mcp.py --delay 1.0        # Run with 1s delay between steps
  python run_live_house_test_mcp.py --delay 5.0        # Run with 5s delay for slower viewing
        """
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Delay in seconds between modeling steps (default: 2.0)"
    )

    args = parser.parse_args()

    runner = MCPLiveHouseTestRunner(step_delay=args.delay)
    success = await runner.run_house_test()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
