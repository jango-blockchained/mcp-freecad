import inspect
import os
import platform
import FreeCAD
import FreeCADGui
from PySide2 import QtCore, QtGui, QtWidgets

# Import the refactored modules
from mcp_indicator.config_manager import ConfigManager
from mcp_indicator.path_finder import PathFinder
from mcp_indicator.process_manager import ProcessManager
from mcp_indicator.status_checker import StatusChecker
from mcp_indicator.ui_manager import UIManager
from mcp_indicator.dependency_manager import DependencyManager

# Import the flow visualization once to ensure it's available
try:
    from mcp_indicator import flow_visualization
except ImportError:
    FreeCAD.Console.PrintWarning("Failed to import flow_visualization module. Flow visualization may not work properly.\n")

# Check if running on Wayland to handle specific issues
RUNNING_ON_WAYLAND = os.environ.get('XDG_SESSION_TYPE', '').lower() == 'wayland'
if RUNNING_ON_WAYLAND:
    FreeCAD.Console.PrintWarning("Running on Wayland: Some UI features may be limited\n")

class MCPIndicatorWorkbench(FreeCADGui.Workbench):
    """MCP Connection Indicator Workbench"""

    MenuText = "MCP Indicator"
    ToolTip = "Shows MCP connection status and controls server"
    Icon = """
/* XPM */
static char * mcp_icon_xpm[] = {
"16 16 3 1",
" 	c None",
".	c #000000",
"+	c #FFFFFF",
"                ",
"     ......     ",
"   ..++++++..   ",
"  .+++++++++++. ",
" .+++++..+++++. ",
".++++.  ..++++. ",
".+++.    .++++. ",
".+++.    .++++. ",
".+++.    .++++. ",
".++++.  ..++++. ",
" .+++++..+++++. ",
"  .+++++++++++. ",
"   ..++++++..   ",
"     ......     ",
"                ",
"                "};
"""

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
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self._check_status)
        self._timer.start(2000)  # 2-second interval for status check

        # Perform initial status check
        self._check_status()

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
