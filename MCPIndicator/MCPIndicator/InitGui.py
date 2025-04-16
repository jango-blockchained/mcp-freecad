"""
MCP Connection Indicator Workbench - GUI initialization
This file is executed when FreeCAD starts in GUI mode
"""

import os
import sys
import platform # Added for platform detection
import FreeCAD
import FreeCADGui
# Remove MCPIndicator import, it's not reliable here
# import MCPIndicator

# --- Robust Path Finding ---
__dir__ = None
try:
    # Try the standard __file__ attribute first
    __dir__ = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isdir(__dir__):
        __dir__ = None # Reset if path is invalid
except NameError:
    # __file__ is not defined, try searching common Mod directories
    pass # Handled below

if __dir__ is None:
    # Fallback: Search known Mod locations for 'freecad_addon/MCPIndicator'
    home_dir = os.path.expanduser("~")
    system = platform.system()
    possible_mod_parents = []

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
        potential_dir = os.path.join(parent_path, "Mod", "freecad_addon", "MCPIndicator")
        if os.path.isdir(potential_dir) and os.path.isfile(os.path.join(potential_dir, "InitGui.py")):
            __dir__ = potential_dir
            FreeCAD.Console.PrintMessage(f"MCP Indicator: Found module path via search: {__dir__}\n")
            break # Found it

if __dir__ is None:
    FreeCAD.Console.PrintError("MCP Indicator: ERROR - Could not determine the addon directory path.\n")
    # Attempt to continue might fail, but prevents immediate crash before class definition
    __dir__ = "" # Assign a dummy value to prevent NameError on Icon path

# Add the found directory (or dummy) to Python path
if __dir__ and __dir__ not in sys.path:
    sys.path.append(__dir__)
# --- End Path Finding ---

# Declare flag at module level
CORE_MODULES_IMPORTED = False

# Import local modules FIRST to ensure names are defined
# Errors due to their *internal* dependencies (like psutil) will be caught later
try:
    from config_manager import ConfigManager
    from path_finder import PathFinder
    from process_manager import ProcessManager
    from status_checker import StatusChecker
    from ui_manager import UIManager
    from dependency_manager import DependencyManager
    # flow_visualization might be less critical, keep separate?
    # import flow_visualization
    CORE_MODULES_IMPORTED = True # Set flag to True on success
    FreeCAD.Console.PrintMessage("MCP Indicator: Core local modules imported.\n")
except ImportError as e:
    FreeCAD.Console.PrintError(f"MCP Indicator: FAILED to import CORE local module: {e}\n")
    FreeCAD.Console.PrintError("MCP Indicator: Workbench may not function correctly.\n")
    # CORE_MODULES_IMPORTED remains False (default)

# Optional: Try importing modules that might have external deps separately
try:
    import flow_visualization # Example if this uses external libs
    FreeCAD.Console.PrintMessage("MCP Indicator: Optional modules potentially loaded.\n")
except ImportError as e:
    FreeCAD.Console.PrintMessage(f"MCP Indicator: Optional module import failed: {e}\n")

# Print initialization message
FreeCAD.Console.PrintMessage("Initializing MCP Connection Indicator GUI...\n")

class MCPIndicatorWorkbench(FreeCADGui.Workbench):
    """MCP Connection Indicator Workbench"""

    MenuText = "MCP Indicator"
    ToolTip = "Shows MCP connection status and controls server"
    # Icon = os.path.join(__dir__, "resources", "icons", "mcp_icon.svg") # Removed from class level

    def __init__(self):
        """Initialize the workbench with modular components."""
        global __dir__ # Ensure we're using the module-level variable
        global CORE_MODULES_IMPORTED # Access the module-level flag

        # Set Icon path here using the script-level __dir__ variable
        # Check if __dir__ is valid before using it
        if __dir__ and os.path.isdir(__dir__):
            self.Icon = os.path.join(__dir__, "resources", "icons", "mcp_icon.svg")
        else:
            self.Icon = "" # Default or empty icon path if __dir__ is invalid
            FreeCAD.Console.PrintError("MCP Indicator: Cannot set workbench icon, __dir__ is invalid.\n")

        # Initialize manager components only if core imports succeeded
        if CORE_MODULES_IMPORTED:
            self.config_manager = ConfigManager()
            self.path_finder = PathFinder(self.config_manager)
            self.process_manager = ProcessManager(self.config_manager, self.path_finder)
            self.status_checker = StatusChecker(self.config_manager, self.process_manager)
            self.ui_manager = UIManager(self.config_manager, self.process_manager, self.status_checker, self.path_finder)
            self.dependency_manager = DependencyManager()
        else:
            # Handle case where core modules failed to import
            FreeCAD.Console.PrintError("MCP Indicator: Cannot initialize managers - core modules failed to import.\n")
            # Set managers to None or dummy objects if needed, or expect errors
            self.config_manager = None
            self.path_finder = None
            self.process_manager = None
            self.status_checker = None
            self.ui_manager = None
            self.dependency_manager = None # Crucially, this might break dep install UI

        # Timer for status checking - Initialize self._timer regardless
        self._timer = None

        FreeCAD.Console.PrintMessage("MCP Indicator Workbench __init__ called\n")

    def Initialize(self):
        """Initialize the workbench when it is activated."""
        # Check if managers were initialized before using them
        if not self.dependency_manager:
             FreeCAD.Console.PrintError("MCP Indicator: Dependency Manager not available.\n")
             # Maybe show a message to the user?
             return # Stop initialization

        # Set up UI elements
        if self.ui_manager: # Check if ui_manager exists
            self.ui_manager.setup_ui(self)
        else:
            FreeCAD.Console.PrintError("MCP Indicator: UI Manager not available.\n")
            # Add a basic placeholder UI?

        # Connect dependency manager to UI
        # Ensure ui_manager and its action_list exist
        if hasattr(self.ui_manager, 'action_list'):
            for action in self.ui_manager.action_list:
                if isinstance(action, FreeCADGui.Action) and action.text() == "Install MCP Dependencies":
                    # Ensure dependency_manager exists before connecting
                    if self.dependency_manager:
                        action.triggered.connect(self.dependency_manager.install_dependencies)
                    else:
                        action.setEnabled(False) # Disable button if manager is missing
                        action.setToolTip("Dependency manager failed to load.")

        # Setup status check timer
        # Add check for status_checker
        if self.status_checker:
            try:
                from PySide2 import QtCore
                self._timer = QtCore.QTimer()
                self._timer.timeout.connect(self._check_status)
                self._timer.start(2000)  # 2-second interval for status check
                # Perform initial status check
                self._check_status()
            except ImportError as e:
                 FreeCAD.Console.PrintError(f"MCP Indicator: Failed to import PySide2.QtCore: {e}\n")
            except Exception as e:
                 FreeCAD.Console.PrintError(f"MCP Indicator: Error setting up timer: {e}\n")
        else:
            FreeCAD.Console.PrintError("MCP Indicator: Status Checker not available, timer not started.\n")

        FreeCAD.Console.PrintMessage("MCP Indicator Workbench activated\n")

    def _check_status(self):
        """Check connection/server status and update UI."""
        # Check if managers exist before using
        if self.status_checker and self.ui_manager:
            try:
                # Use status checker to check status
                connection_changed = self.status_checker.check_status()
                # Update UI
                self.ui_manager.update_ui()
            except Exception as e:
                # Catch errors during status check (e.g., if psutil is missing and check_status uses it)
                FreeCAD.Console.PrintError(f"MCP Indicator: Error during status check: {e}\n")
                # Optionally disable timer here to prevent repeated errors
                # if self._timer and self._timer.isActive():
                #     self._timer.stop()
                #     FreeCAD.Console.PrintMessage("MCP Indicator: Status check timer stopped due to errors.\n")
        else:
            # Don't try to check status if core components are missing
            pass

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
