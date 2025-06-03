"""
InitGui.py - FreeCAD GUI Initialization for MCP Integration Addon

This file is automatically loaded by FreeCAD when the addon is activated.
It registers the MCP workbench and initializes GUI components.
"""

import os
import sys
import FreeCAD
import FreeCADGui

# Add addon directory to Python path
try:
    # Try to get the directory from __file__ (works in most cases)
    addon_dir = os.path.dirname(__file__)
except NameError:
    # __file__ not available in FreeCAD's addon loading context
    # Use inspect to get the current file location
    import inspect
    current_file = inspect.getfile(inspect.currentframe())
    addon_dir = os.path.dirname(os.path.abspath(current_file))

if addon_dir not in sys.path:
    sys.path.insert(0, addon_dir)

# Import the main workbench class
try:
    FreeCAD.Console.PrintMessage("MCP Integration Addon: Starting initialization...\n")
    FreeCAD.Console.PrintMessage(f"MCP Integration Addon: Addon directory: {addon_dir}\n")

    from freecad_mcp_workbench import MCPWorkbench

    # Register the workbench with FreeCAD
    workbench = MCPWorkbench()
    FreeCADGui.addWorkbench(workbench)

    FreeCAD.Console.PrintMessage("MCP Integration Addon: Workbench registered successfully\n")

except ImportError as e:
    FreeCAD.Console.PrintError(f"MCP Integration Addon: Failed to import workbench: {e}\n")
    FreeCAD.Console.PrintError(f"MCP Integration Addon: Python path: {sys.path}\n")
except Exception as e:
    FreeCAD.Console.PrintError(f"MCP Integration Addon: Initialization error: {e}\n")
    import traceback
    FreeCAD.Console.PrintError(f"MCP Integration Addon: Traceback: {traceback.format_exc()}\n")

# Addon metadata for FreeCAD
__version__ = "0.7.11"
__title__ = "MCP Integration"
__author__ = "jango-blockchained"
__url__ = "https://github.com/jango-blockchained/mcp-freecad"
