#!/usr/bin/env python3
"""
Fixed Live House Modeling Test Runner

This script properly uses the MCP-FreeCAD connection architecture to run the house
modeling test on a real FreeCAD instance with GUI enabled, without trying to import
FreeCAD modules directly.
"""

import asyncio
import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from src.mcp_freecad.client.freecad_connection_manager import (
        FreecadConnectionManager,
    )
except ImportError as e:
    print(f"Could not import FreecadConnectionManager: {e}")
    print("Make sure you're in the right directory and dependencies are installed.")
    sys.exit(1)


class FixedLiveHouseTestRunner:
    """
    Test runner that creates a house model using proper MCP-FreeCAD connection methods.
    """

    def __init__(self, step_delay: float = 2.0):
        """
        Initialize the fixed live test runner.

        Args:
            step_delay: Delay in seconds between modeling steps for visualization
        """
        self.step_delay = step_delay
        self.freecad_process = None
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
            await asyncio.sleep(8)  # Give more time for startup

            # Check if process is still running
            if self.freecad_process.poll() is not None:
                self.logger.error("FreeCAD process exited unexpectedly")
                return False

            self.logger.info("✅ FreeCAD started successfully!")
            return True

        except Exception as e:
            self.logger.error(f"Failed to start FreeCAD: {e}")
            return False

    async def setup_connection(self) -> bool:
        """
        Set up connection to FreeCAD using the connection manager.

        Returns:
            True if setup successful, False otherwise
        """
        try:
            self.logger.info("🔧 Setting up connection to FreeCAD...")

            # Create connection manager
            self.connection_manager = FreecadConnectionManager()

            # Try different connection methods
            connection_methods = ["launcher", "wrapper", "bridge"]

            for method in connection_methods:
                self.logger.info(f"Trying connection method: {method}")
                try:
                    if method == "launcher":
                        success = await self.connection_manager.connect_to_freecad(
                            method=method,
                            freecad_path=str(Path(__file__).parent / "FreeCAD_1.0.0-conda-Linux-x86_64-py311.AppImage")
                        )
                    else:
                        success = await self.connection_manager.connect_to_freecad(method=method)

                    if success:
                        self.logger.info(f"✅ Connected using {method} method!")
                        break

                except Exception as e:
                    self.logger.warning(f"Method {method} failed: {e}")
                    continue
            else:
                self.logger.error("Failed to connect using any method")
                return False

            # Test the connection with a simple command
            test_result = await self.execute_freecad_command("""
print("Connection test successful!")
""")

            if "successful" in test_result:
                self.logger.info("✅ Connection test passed!")
                return True
            else:
                self.logger.error("Connection test failed")
                return False

        except Exception as e:
            self.logger.error(f"Failed to setup connection: {e}")
            return False

    async def execute_freecad_command(self, command: str) -> str:
        """
        Execute a command in FreeCAD.

        Args:
            command: Python command to execute in FreeCAD

        Returns:
            Command output
        """
        try:
            if self.connection_manager is None:
                raise Exception("Connection manager not initialized")

            result = await self.connection_manager.execute_freecad_command(command)
            return result

        except Exception as e:
            self.logger.error(f"Failed to execute command: {e}")
            return f"ERROR: {e}"

    async def create_foundation(self, foundation_spec: Dict[str, Any]) -> str:
        """Create the house foundation."""
        self.logger.info("🏗️  Creating foundation...")

        command = f"""
import FreeCAD
import Part

# Create or get active document
doc = FreeCAD.activeDocument()
if doc is None:
    doc = FreeCAD.newDocument("LiveHouseTest")
    FreeCAD.setActiveDocument(doc.Name)
    FreeCAD.Gui.runCommand('Std_ViewIsometric')

# Create foundation box
foundation = doc.addObject("Part::Box", "Foundation")
foundation.Length = {foundation_spec["length"]}
foundation.Width = {foundation_spec["width"]}
foundation.Height = {foundation_spec["height"]}

# Set foundation color (brown for concrete)
if hasattr(foundation, 'ViewObject'):
    foundation.ViewObject.ShapeColor = (0.6, 0.4, 0.2)

doc.recompute()
FreeCAD.Gui.runCommand('Std_ViewFitAll')

print(f"FOUNDATION_CREATED:{foundation.Name}")
"""

        result = await self.execute_freecad_command(command)

        if "FOUNDATION_CREATED:" in result:
            foundation_id = result.split("FOUNDATION_CREATED:")[-1].strip()
            self.logger.info(f"✅ Foundation created: {foundation_id}")
            await asyncio.sleep(self.step_delay)
            return foundation_id
        else:
            raise Exception(f"Failed to create foundation: {result}")

    async def create_wall(self, wall_name: str, wall_params: Dict[str, float], translation: List[float]) -> str:
        """Create and position a single wall."""
        self.logger.info(f"Creating {wall_name}...")

        command = f"""
import FreeCAD

doc = FreeCAD.activeDocument()

# Create wall box
wall = doc.addObject("Part::Box", "{wall_name.replace(' ', '_').title()}")
wall.Length = {wall_params["length"]}
wall.Width = {wall_params["width"]}
wall.Height = {wall_params["height"]}

# Position the wall
wall.Placement.Base.x = {translation[0]}
wall.Placement.Base.y = {translation[1]}
wall.Placement.Base.z = {translation[2]}

# Set wall color (red for brick)
if hasattr(wall, 'ViewObject'):
    wall.ViewObject.ShapeColor = (0.8, 0.3, 0.2)

doc.recompute()
FreeCAD.Gui.runCommand('Std_ViewFitAll')

print(f"WALL_CREATED:{wall.Name}")
"""

        result = await self.execute_freecad_command(command)

        if "WALL_CREATED:" in result:
            wall_id = result.split("WALL_CREATED:")[-1].strip()
            self.logger.info(f"✅ {wall_name} created: {wall_id}")
            await asyncio.sleep(self.step_delay)
            return wall_id
        else:
            raise Exception(f"Failed to create {wall_name}: {result}")

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
            wall_id = await self.create_wall(
                wall_config["name"],
                wall_config["params"],
                wall_config["translation"]
            )
            wall_ids.append(wall_id)

        self.logger.info(f"✅ All walls created: {wall_ids}")
        return wall_ids

    async def create_opening(self, opening_name: str, opening_params: Dict[str, float], position: List[float]) -> str:
        """Create a window or door opening."""
        self.logger.info(f"Creating {opening_name}...")

        command = f"""
import FreeCAD

doc = FreeCAD.activeDocument()

# Create opening box
opening = doc.addObject("Part::Box", "{opening_name.replace(' ', '_').title()}")
opening.Length = {opening_params["length"]}
opening.Width = {opening_params["width"]}
opening.Height = {opening_params["height"]}

# Position the opening
opening.Placement.Base.x = {position[0]}
opening.Placement.Base.y = {position[1]}
opening.Placement.Base.z = {position[2]}

# Set opening color (blue for openings)
if hasattr(opening, 'ViewObject'):
    opening.ViewObject.ShapeColor = (0.2, 0.5, 0.8)
    opening.ViewObject.Transparency = 50

doc.recompute()
FreeCAD.Gui.runCommand('Std_ViewFitAll')

print(f"OPENING_CREATED:{opening.Name}")
"""

        result = await self.execute_freecad_command(command)

        if "OPENING_CREATED:" in result:
            opening_id = result.split("OPENING_CREATED:")[-1].strip()
            self.logger.info(f"✅ {opening_name} created: {opening_id}")
            await asyncio.sleep(self.step_delay)
            return opening_id
        else:
            raise Exception(f"Failed to create {opening_name}: {result}")

    async def create_openings(self, windows: List[Dict], doors: List[Dict], wall_thickness: float) -> List[str]:
        """Create window and door openings."""
        self.logger.info("🪟 Creating windows and doors...")

        opening_ids = []

        # Create windows
        for window in windows:
            opening_id = await self.create_opening(
                f"window {window['id']}",
                {
                    "length": window["width"],
                    "width": wall_thickness + 0.1,
                    "height": window["height"]
                },
                [window["position"]["x"], window["position"]["y"], window["position"]["z"]]
            )
            opening_ids.append(opening_id)

        # Create doors
        for door in doors:
            opening_id = await self.create_opening(
                f"door {door['id']}",
                {
                    "length": door["width"],
                    "width": wall_thickness + 0.1,
                    "height": door["height"]
                },
                [door["position"]["x"], door["position"]["y"], door["position"]["z"]]
            )
            opening_ids.append(opening_id)

        self.logger.info(f"✅ All openings created: {opening_ids}")
        return opening_ids

    async def finalize_model(self):
        """Add final touches to the model."""
        self.logger.info("🎨 Finalizing model...")

        command = """
import FreeCAD

doc = FreeCAD.activeDocument()

# Fit all objects in view
FreeCAD.Gui.runCommand('Std_ViewFitAll')

# Switch to isometric view for better visualization
FreeCAD.Gui.runCommand('Std_ViewIsometric')

print("MODEL_FINALIZED")
"""

        result = await self.execute_freecad_command(command)

        if "MODEL_FINALIZED" in result:
            self.logger.info("✅ Model finalized!")

        await asyncio.sleep(1)

    async def run_house_test(self):
        """Run the complete house modeling test."""
        try:
            self.logger.info("🏠 Starting Fixed Live House Modeling Test")
            self.logger.info("=" * 60)

            # Start FreeCAD
            if not await self.start_freecad():
                return False

            # Setup connection
            if not await self.setup_connection():
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

            # Finalize the model
            await self.finalize_model()

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
        description="Fixed Live House Modeling Test - Proper MCP-FreeCAD connection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_live_house_test_fixed.py                    # Run with default 2s delay
  python run_live_house_test_fixed.py --delay 1.0        # Run with 1s delay between steps
  python run_live_house_test_fixed.py --delay 5.0        # Run with 5s delay for slower viewing
        """
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Delay in seconds between modeling steps (default: 2.0)"
    )

    args = parser.parse_args()

    runner = FixedLiveHouseTestRunner(step_delay=args.delay)
    success = await runner.run_house_test()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
