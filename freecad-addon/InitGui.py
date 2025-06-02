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
addon_dir = os.path.dirname(__file__)
if addon_dir not in sys.path:
    sys.path.insert(0, addon_dir)

# Import the main workbench class
try:
    from freecad_mcp_workbench import MCPWorkbench

    # Register the workbench with FreeCAD
    FreeCADGui.addWorkbench(MCPWorkbench())

    FreeCAD.Console.PrintMessage("MCP Integration Addon: Workbench registered successfully\n")

except ImportError as e:
    FreeCAD.Console.PrintError(f"MCP Integration Addon: Failed to import workbench: {e}\n")
except Exception as e:
    FreeCAD.Console.PrintError(f"MCP Integration Addon: Initialization error: {e}\n")

# Addon metadata for FreeCAD
__version__ = "1.0.0"
__title__ = "MCP Integration"
__author__ = "jango-blockchained"
__url__ = "https://github.com/jango-blockchained/mcp-freecad"
