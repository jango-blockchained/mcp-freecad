"""
MCP Connection Indicator Workbench - GUI initialization
This file is executed when FreeCAD starts in GUI mode
"""

import os
import sys
import FreeCAD
import FreeCADGui
import MCPIndicator # Import the main module of your Addon

# Try to get the path using __file__ (might work in some contexts)
# If it fails, use FreeCAD's knowledge of the Mod path
try:
    # This assumes InitGui.py is directly in the MCPIndicator directory
    __dir__ = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # Fallback: Get the path from FreeCAD's Mod folder knowledge
    # Assumes the workbench name matches the directory name ('MCPIndicator')
    # And the Mod directory follows the structure '.../Mod/freecad_addon/MCPIndicator'
    # We get the 'freecad_addon' path and append 'MCPIndicator'
    mod_path = FreeCAD.getHomePath() + "Mod/freecad_addon" # Path to the addon root
    __dir__ = os.path.join(mod_path, "MCPIndicator") # Path to the MCPIndicator subdirectory

# Add the directory containing InitGui.py to Python path
# This allows importing sibling modules like config_manager.py
if os.path.isdir(__dir__) and __dir__ not in sys.path:
    sys.path.append(__dir__)
elif not os.path.isdir(__dir__):
     FreeCAD.Console.PrintError(f"MCP Indicator: Calculated module directory '{__dir__}' does not exist.\\n")

# Import local modules
try:
    from config_manager import ConfigManager
    from path_finder import PathFinder
    from process_manager import ProcessManager
    from status_checker import StatusChecker
    from ui_manager import UIManager
    from dependency_manager import DependencyManager
    import flow_visualization
    FreeCAD.Console.PrintMessage("MCP Indicator: All modules loaded successfully\n")
except ImportError as e:
    FreeCAD.Console.PrintError(f"MCP Indicator: Failed to import module: {e}\n")

# Print initialization message
FreeCAD.Console.PrintMessage("Initializing MCP Connection Indicator GUI...\n")

class MCPIndicatorWorkbench(FreeCADGui.Workbench):
    """MCP Connection Indicator Workbench"""

    MenuText = "MCP Indicator"
    ToolTip = "Shows MCP connection status and controls server"
    Icon = os.path.join(__dir__, "resources", "icons", "mcp_icon.svg")

    def __init__(self):
        """Initialize the workbench with modular components."""
        # Initialize manager components
        self.config_manager = ConfigManager()
        self.path_finder = PathFinder(self.config_manager)
        self.process_manager = ProcessManager(self.config_manager, self.path_finder)
        self.status_checker = StatusChecker(self.config_manager, self.process_manager)
        self.ui_manager = UIManager(self.config_manager, self.process_manager, self.status_checker, self.path_finder)
        self.dependency_manager = DependencyManager()

        # Timer for status checking
        self._timer = None

        FreeCAD.Console.PrintMessage("MCP Indicator Workbench initialized\n")

    def Initialize(self):
        """Initialize the workbench when it is activated."""
        # Set up UI elements
        self.ui_manager.setup_ui(self)

        # Connect dependency manager to UI
        if hasattr(self.ui_manager, 'action_list'):
            for action in self.ui_manager.action_list:
                if isinstance(action, FreeCADGui.Action) and action.text() == "Install MCP Dependencies":
                    action.triggered.connect(self.dependency_manager.install_dependencies)

        # Setup status check timer
        from PySide2 import QtCore
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self._check_status)
        self._timer.start(2000)  # 2-second interval for status check

        # Perform initial status check
        self._check_status()

        FreeCAD.Console.PrintMessage("MCP Indicator Workbench activated\n")

    def _check_status(self):
        """Check connection/server status and update UI."""
        # Use status checker to check status
        connection_changed = self.status_checker.check_status()

        # Update UI
        self.ui_manager.update_ui()

    def Activated(self):
        """Called when the workbench is activated."""
        # Restart the timer if it was stopped
        if self._timer and not self._timer.isActive():
            self._timer.start()

        # Force update
        self._check_status()

    def Deactivated(self):
        """Called when the workbench is deactivated."""
        # Optionally stop the timer when workbench is inactive
        # Commenting out to keep monitoring even when workbench is inactive
        # if self._timer and self._timer.isActive():
        #     self._timer.stop()
        pass

    def ContextMenu(self, recipient):
        """Context menu entries when workbench is active."""
        # For future use, if specific context menu entries are needed
        pass

    def GetClassName(self):
        """Return the Python class name of the workbench."""
        return "Gui::PythonWorkbench"

    def __del__(self):
        """Clean up when the workbench is deleted."""
        if self._timer:
            self._timer.stop()

# Register the workbench with FreeCAD
FreeCADGui.addWorkbench(MCPIndicatorWorkbench())
FreeCAD.Console.PrintMessage("MCP Indicator Workbench registration complete\n")
