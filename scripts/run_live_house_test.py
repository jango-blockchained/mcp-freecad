#!/usr/bin/env python3
"""
Live House Modeling Test Runner

This script runs the house modeling test on a real FreeCAD instance with GUI enabled,
allowing you to watch the 3D house being built step by step in real-time.
"""

import asyncio
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.mcp_freecad.tools.model_manipulation import ModelManipulationToolProvider
from src.mcp_freecad.tools.primitives import PrimitiveToolProvider


class LiveHouseTestRunner:
    """
    Test runner that creates a house model on a real FreeCAD instance.
    """

    def __init__(self, step_delay: float = 2.0):
        """
        Initialize the live test runner.

        Args:
            step_delay: Delay in seconds between modeling steps for visualization
        """
        self.step_delay = step_delay
        self.freecad_process = None
        self.primitive_tool = None
        self.manipulation_tool = None

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
            self.logger.info("Starting FreeCAD with GUI...")

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
            time.sleep(5)

            # Check if process is still running
            if self.freecad_process.poll() is not None:
                self.logger.error("FreeCAD process exited unexpectedly")
                return False

            self.logger.info("FreeCAD started successfully!")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start FreeCAD: {e}")
            return False

    async def setup_tools(self) -> bool:
        """
        Set up the tool providers to connect to FreeCAD.

        Returns:
            True if setup successful, False otherwise
        """
        try:
            self.logger.info("Setting up tool providers...")

            # Import FreeCAD (should be available now that it's running)
            import FreeCAD

            # Create a new document
            doc = FreeCAD.newDocument("LiveHouseTest")
            FreeCAD.setActiveDocument(doc.Name)

            # Initialize tool providers
            self.primitive_tool = PrimitiveToolProvider(freecad_app=FreeCAD)
            self.manipulation_tool = ModelManipulationToolProvider(freecad_app=FreeCAD)

            self.logger.info("Tool providers setup successfully!")
            return True

        except Exception as e:
            self.logger.error(f"Failed to setup tools: {e}")
            return False

    async def create_foundation(self, foundation_spec: Dict[str, Any]) -> str:
        """
        Create the house foundation.

        Args:
            foundation_spec: Foundation specifications

        Returns:
            Object ID of the created foundation
        """
        self.logger.info("🏗️  Creating foundation...")

        result = await self.primitive_tool.execute_tool(
            "create_box",
            {
                "length": foundation_spec["length"],
                "width": foundation_spec["width"],
                "height": foundation_spec["height"]
            }
        )

        if result.status != "success":
            raise Exception(f"Failed to create foundation: {result.error}")

        foundation_id = result.result["object_id"]
        self.logger.info(f"✅ Foundation created: {foundation_id}")

        await asyncio.sleep(self.step_delay)
        return foundation_id

    async def create_walls(self, foundation_spec: Dict[str, Any], wall_spec: Dict[str, Any]) -> List[str]:
        """
        Create the house walls.

        Args:
            foundation_spec: Foundation specifications
            wall_spec: Wall specifications

        Returns:
            List of wall object IDs
        """
        self.logger.info("🧱 Creating walls...")

        wall_height = wall_spec["height"]
        wall_thickness = wall_spec["thickness"]

        wall_ids = []

        # Create front wall
        self.logger.info("Creating front wall...")
        front_wall_result = await self.primitive_tool.execute_tool(
            "create_box",
            {
                "length": foundation_spec["length"],
                "width": wall_thickness,
                "height": wall_height
            }
        )
        if front_wall_result.status != "success":
            raise Exception(f"Failed to create front wall: {front_wall_result.error}")

        front_wall_id = front_wall_result.result["object_id"]
        wall_ids.append(front_wall_id)

        # Position front wall
        await self.manipulation_tool.execute_tool(
            "transform",
            {
                "object": front_wall_id,
                "translation": [0, -wall_thickness/2, foundation_spec["height"]]
            }
        )

        await asyncio.sleep(self.step_delay)

        # Create back wall
        self.logger.info("Creating back wall...")
        back_wall_result = await self.primitive_tool.execute_tool(
            "create_box",
            {
                "length": foundation_spec["length"],
                "width": wall_thickness,
                "height": wall_height
            }
        )
        back_wall_id = back_wall_result.result["object_id"]
        wall_ids.append(back_wall_id)

        # Position back wall
        await self.manipulation_tool.execute_tool(
            "transform",
            {
                "object": back_wall_id,
                "translation": [0, foundation_spec["width"] + wall_thickness/2, foundation_spec["height"]]
            }
        )

        await asyncio.sleep(self.step_delay)

        # Create left wall
        self.logger.info("Creating left wall...")
        left_wall_result = await self.primitive_tool.execute_tool(
            "create_box",
            {
                "length": wall_thickness,
                "width": foundation_spec["width"],
                "height": wall_height
            }
        )
        left_wall_id = left_wall_result.result["object_id"]
        wall_ids.append(left_wall_id)

        # Position left wall
        await self.manipulation_tool.execute_tool(
            "transform",
            {
                "object": left_wall_id,
                "translation": [-wall_thickness/2, 0, foundation_spec["height"]]
            }
        )

        await asyncio.sleep(self.step_delay)

        # Create right wall
        self.logger.info("Creating right wall...")
        right_wall_result = await self.primitive_tool.execute_tool(
            "create_box",
            {
                "length": wall_thickness,
                "width": foundation_spec["width"],
                "height": wall_height
            }
        )
        right_wall_id = right_wall_result.result["object_id"]
        wall_ids.append(right_wall_id)

        # Position right wall
        await self.manipulation_tool.execute_tool(
            "transform",
            {
                "object": right_wall_id,
                "translation": [foundation_spec["length"] + wall_thickness/2, 0, foundation_spec["height"]]
            }
        )

        await asyncio.sleep(self.step_delay)

        self.logger.info(f"✅ All walls created: {wall_ids}")
        return wall_ids

    async def create_openings(self, windows: List[Dict], doors: List[Dict], wall_thickness: float) -> List[str]:
        """
        Create window and door openings.

        Args:
            windows: Window specifications
            doors: Door specifications
            wall_thickness: Thickness of walls

        Returns:
            List of opening object IDs
        """
        self.logger.info("🪟 Creating windows and doors...")

        opening_ids = []

        # Create windows
        for window in windows:
            self.logger.info(f"Creating window: {window['id']}")

            window_result = await self.primitive_tool.execute_tool(
                "create_box",
                {
                    "length": window["width"],
                    "width": wall_thickness + 0.1,  # Slightly thicker than wall
                    "height": window["height"]
                }
            )

            if window_result.status == "success":
                window_id = window_result.result["object_id"]
                opening_ids.append(window_id)

                # Position window
                pos = window["position"]
                await self.manipulation_tool.execute_tool(
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

            door_result = await self.primitive_tool.execute_tool(
                "create_box",
                {
                    "length": door["width"],
                    "width": wall_thickness + 0.1,
                    "height": door["height"]
                }
            )

            if door_result.status == "success":
                door_id = door_result.result["object_id"]
                opening_ids.append(door_id)

                # Position door
                pos = door["position"]
                await self.manipulation_tool.execute_tool(
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
        """
        Run the complete house modeling test.
        """
        try:
            self.logger.info("🏠 Starting Live House Modeling Test")
            self.logger.info("=" * 60)

            # Start FreeCAD
            if not await self.start_freecad():
                return False

            # Give extra time for GUI to load
            self.logger.info("Waiting for FreeCAD GUI to be ready...")
            await asyncio.sleep(3)

            # Setup tools
            if not await self.setup_tools():
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
        description="Live House Modeling Test - Watch a 3D house being built in FreeCAD",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_live_house_test.py                    # Run with default 2s delay
  python run_live_house_test.py --delay 1.0        # Run with 1s delay between steps
  python run_live_house_test.py --delay 5.0        # Run with 5s delay for slower viewing
        """
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Delay in seconds between modeling steps (default: 2.0)"
    )

    args = parser.parse_args()

    runner = LiveHouseTestRunner(step_delay=args.delay)
    success = await runner.run_house_test()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
