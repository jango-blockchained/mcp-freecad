"""FreeCAD MCP Workbench - Main workbench implementation"""

import os
import FreeCAD
import FreeCADGui


class MCPWorkbench(FreeCADGui.Workbench):
    """MCP Integration Workbench for FreeCAD"""
    
    MenuText = "MCP Integration"
    ToolTip = "Model Context Protocol Integration for AI-powered CAD operations"
    Icon = os.path.join(os.path.dirname(__file__), "resources", "icons", "mcp_workbench.svg")
    
    def __init__(self):
        """Initialize the MCP workbench."""
        self.addon_dir = os.path.dirname(__file__)
        self.main_widget = None

    def Initialize(self):
        """Initialize the workbench GUI components."""
        FreeCAD.Console.PrintMessage("MCP Integration Workbench: Initializing...\n")
        FreeCAD.Console.PrintMessage("MCP Integration Workbench: Initialization complete\n")

    def Activated(self):
        """Called when the workbench is activated."""
        FreeCAD.Console.PrintMessage("MCP Integration Workbench: Activated\n")

    def Deactivated(self):
        """Called when the workbench is deactivated."""
        FreeCAD.Console.PrintMessage("MCP Integration Workbench: Deactivated\n")

    def GetClassName(self):
        """Return the workbench class name."""
        return "MCPWorkbench"