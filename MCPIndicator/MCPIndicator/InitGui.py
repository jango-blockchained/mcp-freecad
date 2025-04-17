"""
MCP Connection Indicator Workbench - GUI initialization
This file is executed when FreeCAD starts in GUI mode
"""

import os
import sys
import platform
import FreeCAD
import FreeCADGui
from PySide2 import QtCore, QtWidgets

# --- Robust Path Finding ---
MODULE_DIR = None
try:
    # Try the standard __file__ attribute first
    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isdir(MODULE_DIR):
        MODULE_DIR = None # Reset if path is invalid
except NameError:
    # __file__ is not defined, try searching common Mod directories
    pass # Handled below

if MODULE_DIR is None:
    # Fallback: Search known Mod locations for 'MCPIndicator'
    home_dir = os.path.expanduser("~")
    system = platform.system()
    possible_mod_parents = []
    FreeCAD.Console.PrintMessage(f"MCP Indicator: Fallback path search initiated. Home dir: {home_dir}, System: {system}\n")

    if system == "Windows":
        possible_mod_parents.extend([
            os.path.join(os.getenv('APPDATA', ''), "FreeCAD"),
            os.path.join(home_dir, "AppData", "Roaming", "FreeCAD")
        ])
    elif system == "Darwin": # macOS
        possible_mod_parents.extend([
            os.path.join(home_dir, "Library", "Preferences", "FreeCAD"),
            os.path.join(home_dir, ".FreeCAD")
        ])
    else: # Linux and others
        possible_mod_parents.extend([
            os.path.join(home_dir, ".local", "share", "FreeCAD"),
            os.path.join(home_dir, ".FreeCAD"),
            os.path.join(home_dir, ".freecad"),
            "/usr/share/freecad",
            "/usr/local/share/freecad"
        ])

    for parent_path in possible_mod_parents:
        potential_dir = os.path.join(parent_path, "Mod", "MCPIndicator", "MCPIndicator")
        FreeCAD.Console.PrintMessage(f"MCP Indicator: Checking fallback path: {potential_dir}\n")
        if os.path.isdir(potential_dir) and os.path.isfile(os.path.join(potential_dir, "InitGui.py")):
            MODULE_DIR = potential_dir
            FreeCAD.Console.PrintMessage(f"MCP Indicator: Found module path via search: {MODULE_DIR}\n")
            break

if MODULE_DIR is None:
    FreeCAD.Console.PrintError("MCP Indicator: ERROR - Could not determine the addon directory path.\n")
    MODULE_DIR = ""

# Add the found directory to Python path
if MODULE_DIR and MODULE_DIR not in sys.path:
    sys.path.append(MODULE_DIR)
# --- End Path Finding ---

# Print initialization message
FreeCAD.Console.PrintMessage("Initializing MCP Connection Indicator GUI...\n")

class MCPIndicatorWorkbench(FreeCADGui.Workbench):
    """MCP Connection Indicator Workbench"""

    MenuText = "MCP Indicator"
    ToolTip = "Shows MCP connection status and controls server"

    def __init__(self):
        """Initialize the workbench with modular components."""
        # Access the global MODULE_DIR directly
        global MODULE_DIR

        # Set Icon path
        if MODULE_DIR and os.path.isdir(MODULE_DIR):
            self.Icon = os.path.join(MODULE_DIR, "resources", "icons", "mcp_icon.svg")
        else:
            self.Icon = ""
            FreeCAD.Console.PrintError("MCP Indicator: Cannot set workbench icon, MODULE_DIR is invalid.\n")

        # Initialize timer attribute
        self._timer = None
        FreeCAD.Console.PrintMessage("MCP Indicator Workbench __init__ called\n")

    def Initialize(self):
        """Initialize the workbench when it is activated."""
        # Import managers only when needed
        from config_manager import ConfigManager
        from path_finder import PathFinder
        from process_manager import ProcessManager
        from status_checker import StatusChecker
        from ui_manager import UIManager
        from dependency_manager import DependencyManager

        # Create instances of the managers
        self.config_manager = ConfigManager()
        self.path_finder = PathFinder(self.config_manager)
        self.process_manager = ProcessManager(self.config_manager, self.path_finder)
        self.status_checker = StatusChecker(self.config_manager, self.process_manager)
        self.ui_manager = UIManager(self.config_manager, self.process_manager, self.status_checker, self.path_finder)
        self.dependency_manager = DependencyManager()

        # Set up UI elements
        self.ui_manager.setup_ui(self)

        # Connect dependency manager to UI
        if hasattr(self.ui_manager, 'main_menu_actions') and "install_deps" in self.ui_manager.main_menu_actions:
            deps_action = self.ui_manager.main_menu_actions["install_deps"]
            deps_action.triggered.connect(self.dependency_manager.install_dependencies)

        # Setup status check timer
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self._check_status)
        self._timer.start(2000)  # 2-second interval for status check

        # Perform initial status check
        self._check_status()

        FreeCAD.Console.PrintMessage("MCP Indicator Workbench activated\n")

    def _check_status(self):
        """Check connection/server status and update UI."""
        try:
            # Use status checker to check status
            connection_changed = self.status_checker.check_status()
            # Update UI
            self.ui_manager.update_ui()
        except Exception as e:
            FreeCAD.Console.PrintError(f"MCP Indicator: Error during status check: {e}\n")

    def Activated(self):
        """Called when the workbench is activated."""
        # Restart the timer if it was stopped
        if self._timer and not self._timer.isActive():
            self._timer.start()
        # Force update
        self._check_status()

    def Deactivated(self):
        """Called when the workbench is deactivated."""
        pass

    def ContextMenu(self, recipient):
        """Context menu entries when workbench is active."""
        pass

    def GetClassName(self):
        """Return the Python class name of the workbench."""
        return "Gui::PythonWorkbench"

    def __del__(self):
        """Clean up when the workbench is deleted."""
        if hasattr(self, '_timer') and self._timer:
            self._timer.stop()

# Register the workbench with FreeCAD
FreeCADGui.addWorkbench(MCPIndicatorWorkbench())
FreeCAD.Console.PrintMessage("MCP Indicator Workbench registration complete\n")
