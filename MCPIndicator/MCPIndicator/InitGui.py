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
import traceback

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

# Import managers needed early, using absolute paths
from MCPIndicator.config_manager import ConfigManager
FreeCAD.Console.PrintMessage("DEBUG: Successfully executed 'from MCPIndicator.config_manager import ConfigManager'\n")

from MCPIndicator.path_finder import PathFinder
from MCPIndicator.process_manager import ProcessManager
from MCPIndicator.status_checker import StatusChecker
from MCPIndicator.ui_manager import UIManager
from MCPIndicator.dependency_manager import DependencyManager
# Import rpc_server functions needed by command classes
from MCPIndicator.rpc_server import start_rpc_server, stop_rpc_server

class MCPIndicatorWorkbench(FreeCADGui.Workbench):
    """MCP Connection Indicator Workbench"""

    MenuText = "MCP Indicator"
    ToolTip = "Shows MCP connection status and controls server"

    def __init__(self):
        """Initialize the workbench attributes."""
        global MODULE_DIR
        if MODULE_DIR and os.path.isdir(MODULE_DIR):
            self.Icon = os.path.join(MODULE_DIR, "resources", "icons", "mcp_icon.svg")
        else:
            self.Icon = ""
            FreeCAD.Console.PrintError("MCP Indicator: Cannot set workbench icon, MODULE_DIR is invalid.\n")

        # Initialize attributes to None, they will be assigned in Initialize
        self._timer = None
        self.config_manager = None
        self.path_finder = None
        self.process_manager = None
        self.status_checker = None
        self.ui_manager = None
        self.dependency_manager = None
        FreeCAD.Console.PrintMessage("MCP Indicator Workbench __init__ called\n")


    def Initialize(self):
        """Initialize the workbench when it is activated."""
        FreeCAD.Console.PrintMessage("DEBUG: Starting workbench initialization\n")

        # --- Define Command Classes Locally ---
        # (Uses imports defined above the main class)

        class InitStart_FreeCAD_Server:
            def GetResources(self): # Use MODULE_DIR directly
                return {
                    "Pixmap": os.path.join(MODULE_DIR, "resources", "icons", "fc_server_running.svg"),
                    "MenuText": "Start FreeCAD Server",
                    "ToolTip": "Start the FreeCAD RPC server"
                }
            def Activated(self):
                try:
                    # Use imported start_rpc_server directly
                    start_rpc_server()
                    FreeCAD.Console.PrintMessage("FreeCAD RPC server started\n")
                except Exception as e:
                    FreeCAD.Console.PrintError(f"Error starting RPC server: {e}\n")
            def IsActive(self):
                # Simplified: Let UIManager handle enabling/disabling based on StatusChecker
                return True

        class InitStop_FreeCAD_Server:
            def GetResources(self): # Use MODULE_DIR directly
                return {
                    "Pixmap": os.path.join(MODULE_DIR, "resources", "icons", "fc_server_stopped.svg"),
                    "MenuText": "Stop FreeCAD Server",
                    "ToolTip": "Stop the FreeCAD RPC server"
                }
            def Activated(self):
                try:
                    # Use imported stop_rpc_server directly
                    stop_rpc_server()
                    FreeCAD.Console.PrintMessage("FreeCAD RPC server stopped\n")
                except Exception as e:
                    FreeCAD.Console.PrintError(f"Error stopping RPC server: {e}\n")
            def IsActive(self):
                # Simplified: Let UIManager handle enabling/disabling based on StatusChecker
                return True

        class InitStart_MCP_Server:
            def GetResources(self): # Use MODULE_DIR directly
                return {
                    "Pixmap": os.path.join(MODULE_DIR, "resources", "icons", "mcp_server_running.svg"),
                    "MenuText": "Start MCP Server",
                    "ToolTip": "Start the MCP server"
                }
            def Activated(self):
                try:
                    FreeCAD.Console.PrintMessage("Starting MCP server...\n")
                    # Create temporary managers for this command activation
                    # (Uses imports defined above the main class)
                    temp_config_manager = ConfigManager()
                    temp_path_finder = PathFinder(temp_config_manager)
                    temp_process_manager = ProcessManager(temp_config_manager, temp_path_finder)
                    temp_process_manager.start_mcp_server()
                except Exception as e:
                    FreeCAD.Console.PrintError(f"Error starting MCP server: {e}\n")
            def IsActive(self): return True # Simplified

        class InitStop_MCP_Server:
            def GetResources(self): # Use MODULE_DIR directly
                return {
                    "Pixmap": os.path.join(MODULE_DIR, "resources", "icons", "mcp_server_stopped.svg"),
                    "MenuText": "Stop MCP Server",
                    "ToolTip": "Stop the MCP server"
                }
            def Activated(self):
                try:
                    FreeCAD.Console.PrintMessage("Stopping MCP server...\n")
                    # Create temporary managers for this command activation
                    # (Uses imports defined above the main class)
                    temp_config_manager = ConfigManager()
                    temp_path_finder = PathFinder(temp_config_manager)
                    temp_process_manager = ProcessManager(temp_config_manager, temp_path_finder)
                    temp_process_manager.stop_mcp_server()
                except Exception as e:
                    FreeCAD.Console.PrintError(f"Error stopping MCP server: {e}\n")
            def IsActive(self): return True # Simplified

        # --- Create Manager Instances ---
        FreeCAD.Console.PrintMessage(f"DEBUG: sys.path = {sys.path}\n")
        FreeCAD.Console.PrintMessage(f"DEBUG: globals keys before manager creation = {list(globals().keys())}\n")
        FreeCAD.Console.PrintMessage(f"DEBUG: Is ConfigManager in globals? {'ConfigManager' in globals()}\n")
        try:
            # (Uses imports defined above the main class)
            self.config_manager = ConfigManager()
            self.path_finder = PathFinder(self.config_manager)
            self.process_manager = ProcessManager(self.config_manager, self.path_finder)
            self.status_checker = StatusChecker(self.config_manager, self.process_manager)
            self.ui_manager = UIManager(self.config_manager, self.process_manager, self.status_checker, self.path_finder)
            self.dependency_manager = DependencyManager()
            FreeCAD.Console.PrintMessage("DEBUG: Successfully created manager instances.\n")
        except NameError as ne:
            FreeCAD.Console.PrintError(f"DEBUG: Caught NameError during manager creation: {ne}\n")
            FreeCAD.Console.PrintError(f"DEBUG: Globals at time of error: {list(globals().keys())}\n")
            # Raise the error again so FreeCAD knows initialization failed
            raise ne
        except Exception as e:
            FreeCAD.Console.PrintError(f"DEBUG: Caught unexpected error during manager creation: {e}\n")
            raise e

        # --- Register Commands ---
        try:
            FreeCAD.Console.PrintMessage("DEBUG: Trying to register commands\n")
            FreeCADGui.addCommand("Start_FreeCAD_Server", InitStart_FreeCAD_Server())
            FreeCADGui.addCommand("Stop_FreeCAD_Server", InitStop_FreeCAD_Server())
            FreeCADGui.addCommand("Start_MCP_Server", InitStart_MCP_Server())
            FreeCADGui.addCommand("Stop_MCP_Server", InitStop_MCP_Server())
            FreeCAD.Console.PrintMessage("DEBUG: Successfully registered commands\n")
        except Exception as e:
            FreeCAD.Console.PrintError(f"DEBUG: Error registering commands: {str(e)}\n")
            # Handle fallback if necessary (keep existing fallback logic if desired)
            # ...

        # --- Setup UI ---
        self.ui_manager.setup_ui(self)

        # --- Connect Dependency Installation ---
        # Connect the install action from the UI manager to the dependency manager
        if self.ui_manager.install_deps_action_mainmenu:
            try:
                self.ui_manager.install_deps_action_mainmenu.triggered.connect(
                    self.dependency_manager.install_dependencies_dialog
                )
                # Also connect the potential status bar action if it exists and isn't the same object
                if (self.ui_manager.install_deps_action_statusbar and
                        self.ui_manager.install_deps_action_statusbar is not self.ui_manager.install_deps_action_mainmenu):
                     self.ui_manager.install_deps_action_statusbar.triggered.connect(
                        self.dependency_manager.install_dependencies_dialog
                     )
            except AttributeError:
                 FreeCAD.Console.PrintError("MCP Indicator: Could not connect dependency installer action.\n")


        # --- Start Status Update Timer ---
        # Moved to the end of Initialize to ensure managers are ready
        self.start_status_timer()

        FreeCAD.Console.PrintMessage("MCP Indicator Workbench Initialized\n")


    def start_status_timer(self):
        """Starts the periodic timer for status checks."""
        if self._timer is None:
            self._timer = QtCore.QTimer()
            self._timer.timeout.connect(self._check_status)
        # Use interval from config or default (e.g., 5000 ms)
        interval = self.config_manager.get_setting("status_check_interval", 5000) if self.config_manager else 5000
        self._timer.start(interval)
        FreeCAD.Console.PrintMessage(f"MCP Indicator: Status timer started with interval {interval}ms.\n")

    def stop_status_timer(self):
        """Stops the periodic timer."""
        if self._timer and self._timer.isActive():
            self._timer.stop()
            FreeCAD.Console.PrintMessage("MCP Indicator: Status timer stopped.\n")

    def _check_status(self):
        """Periodically called by the timer to update status."""
        # Guard against running before initialization is complete
        if not hasattr(self, 'status_checker') or self.status_checker is None:
            FreeCAD.Console.PrintWarning("MCP Indicator: Status checker not ready, skipping status update.\n")
            return
        if not hasattr(self, 'ui_manager') or self.ui_manager is None:
            FreeCAD.Console.PrintWarning("MCP Indicator: UI manager not ready, skipping status update.\n")
            return

        try:
            # Perform checks
            self.status_checker.check_all() # Let status_checker handle individual checks

            # Update UI elements via UIManager
            QtCore.QMetaObject.invokeMethod(self.ui_manager, "update_ui", QtCore.Qt.QueuedConnection)

        except Exception as e:
            FreeCAD.Console.PrintError(f"MCP Indicator: Error during status check: {e}\n")
            # Optionally stop the timer on repeated errors?
            # self.stop_status_timer()

    def Activated(self):
        """Called when the workbench is activated."""
        # Timer is now started at the end of Initialize
        # self.start_status_timer() # <--- REMOVED FROM HERE
        FreeCAD.Console.PrintMessage("MCP Indicator Workbench Activated\n")
        # Trigger an immediate UI update on activation
        if hasattr(self, 'ui_manager') and self.ui_manager:
             QtCore.QMetaObject.invokeMethod(self.ui_manager, "update_ui", QtCore.Qt.QueuedConnection)

    def Deactivated(self):
        """Called when the workbench is deactivated."""
        self.stop_status_timer()
        FreeCAD.Console.PrintMessage("MCP Indicator Workbench Deactivated\n")

    def ContextMenu(self, recipient):
        """Create context menu based on the recipient."""
        # Example: Add actions relevant to the selected object type
        # menu = [Start_FreeCAD_Server, Stop_FreeCAD_Server, ...]
        # self.appendContextMenu(recipient, menu)
        pass # No specific context menu for now

    def GetClassName(self):
        """Return the class name."""
        return "Gui::PythonWorkbench" # Standard for Python workbenches

    def __del__(self):
        """Ensure timer is stopped when workbench is deleted."""
        self.stop_status_timer()
        FreeCAD.Console.PrintMessage("MCP Indicator Workbench deleted.\n")


# Register the workbench
FreeCADGui.addWorkbench(MCPIndicatorWorkbench())
