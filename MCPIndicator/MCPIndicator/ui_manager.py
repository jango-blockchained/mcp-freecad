import os
import time
import FreeCAD
import FreeCADGui
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtWidgets import QDockWidget, QTextEdit, QVBoxLayout, QPushButton, QWidget, QMenu, QAction
from PySide2.QtCore import QFileSystemWatcher, QTimer, QStandardPaths, Qt
import logging
import logging.handlers
import socket # Needed for external server check (will be used by status_checker later, but import here is fine)
# Corrected import: Use absolute import based on package name
from MCPIndicator.connection_status_dialog import ConnectionStatusDialog

# Icon paths (relative to resources folder) - Define constants
# Using Qt Resource System paths (if setup) or direct paths
ICON_PATH = os.path.join(os.path.dirname(__file__), "resources", "icons")

# Define icon paths (adjust filenames as needed)
ICON_CLIENT_CONNECTED = os.path.join(ICON_PATH, "mcp_client_connected.svg") # Example name
ICON_CLIENT_DISCONNECTED = os.path.join(ICON_PATH, "mcp_client_disconnected.svg") # Example name
ICON_FC_SERVER_RUNNING = os.path.join(ICON_PATH, "fc_server_running.svg") # Example name
ICON_FC_SERVER_STOPPED = os.path.join(ICON_PATH, "fc_server_stopped.svg") # Example name
ICON_FC_SERVER_STARTING = os.path.join(ICON_PATH, "fc_server_starting.svg") # Example name
ICON_FC_SERVER_STOPPING = os.path.join(ICON_PATH, "fc_server_stopping.svg") # Example name
ICON_MCP_SERVER_RUNNING = os.path.join(ICON_PATH, "mcp_server_running.svg") # Example name
ICON_MCP_SERVER_STOPPED = os.path.join(ICON_PATH, "mcp_server_stopped.svg") # Example name
ICON_MCP_SERVER_RUNNING_EXT = os.path.join(ICON_PATH, "mcp_server_running_external.svg") # Example name
ICON_MCP_SERVER_STARTING = os.path.join(ICON_PATH, "mcp_server_starting.svg") # Example name
ICON_MCP_SERVER_STOPPING = os.path.join(ICON_PATH, "mcp_server_stopping.svg") # Example name
ICON_WAITING = os.path.join(ICON_PATH, "waiting.svg") # Generic waiting/processing icon


# Helper to create QIcon with fallback
def create_qicon(primary_path, fallback_color=None):
    icon = QtGui.QIcon(primary_path)
    if not icon.isNull():
        return icon
    elif fallback_color:
        pixmap = QtGui.QPixmap(16, 16)
        pixmap.fill(QtGui.QColor(fallback_color))
        return QtGui.QIcon(pixmap)
    else:
        # Return an empty icon if no fallback
        return QtGui.QIcon()


class UIManager:
    """Manages UI elements for the MCP Indicator Workbench."""

    def __init__(self, config_manager, process_manager, status_checker, path_finder):
        """Initialize with the necessary manager instances."""
        self.config_manager = config_manager
        self.process_manager = process_manager
        self.status_checker = status_checker
        self.path_finder = path_finder

        # UI elements
        self.control_button = None # Client connection status / Main control menu
        self.freecad_server_status_button = None
        self.mcp_server_status_button = None
        self.connection_info_dialog = None
        self.flow_visualization_action = None
        self.server_status_label = None # Not currently used? Remove if so.
        self.main_menu_actions = {} # Store main menu actions for potential disabling

        # Store QActions from status bar menu for enabling/disabling
        self.mcp_start_action = None
        self.mcp_stop_action = None
        self.mcp_restart_action = None
        self.freecad_start_action = None
        self.freecad_stop_action = None
        self.freecad_restart_action = None
        self.install_deps_action_statusbar = None # Action in status bar menu
        self.install_deps_action_mainmenu = None # Action in main menu


        # Temporary state flags for immediate feedback
        self._mcp_server_busy = False
        self._fc_server_busy = False

        # Load icons with fallbacks
        self.icons = {
            "client_connected": create_qicon(ICON_CLIENT_CONNECTED, "green"),
            "client_disconnected": create_qicon(ICON_CLIENT_DISCONNECTED, "red"),
            "fc_running": create_qicon(ICON_FC_SERVER_RUNNING, "blue"),
            "fc_stopped": create_qicon(ICON_FC_SERVER_STOPPED, "orange"),
            "fc_starting": create_qicon(ICON_FC_SERVER_STARTING, "yellow"),
            "fc_stopping": create_qicon(ICON_FC_SERVER_STOPPING, "yellow"),
            "mcp_running": create_qicon(ICON_MCP_SERVER_RUNNING, "darkGreen"),
            "mcp_stopped": create_qicon(ICON_MCP_SERVER_STOPPED, "darkRed"),
            "mcp_running_external": create_qicon(ICON_MCP_SERVER_RUNNING_EXT, "cyan"),
            "mcp_starting": create_qicon(ICON_MCP_SERVER_STARTING, "yellow"),
            "mcp_stopping": create_qicon(ICON_MCP_SERVER_STOPPING, "yellow"),
            "waiting": create_qicon(ICON_WAITING, "gray")
        }


        # Configure logging to write to a file
        self._configure_socket_logging()

    def _configure_socket_logging(self, host="localhost", port=9020):
        """Configure the root logger to write logs to a file."""
        try:
            # Get the addon directory path
            addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if not os.path.isdir(addon_dir):
                addon_dir = os.path.dirname(os.path.abspath(__file__))

            # Create logs directory if it doesn't exist
            log_dir = os.path.join(addon_dir, "logs")
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            # Set up log file path
            log_file = os.path.join(log_dir, "mcpindicator.log")

            # Ensure logging is configured
            if not logging.getLogger().hasHandlers():
                logging.basicConfig(level=logging.INFO)

            root_logger = logging.getLogger()

            # Prevent adding handler multiple times
            if any(isinstance(h, logging.FileHandler) and h.baseFilename == log_file for h in root_logger.handlers):
                FreeCAD.Console.PrintMessage(f"File logging handler for {log_file} already configured.\n")
                return

            # Create a file handler
            file_handler = logging.FileHandler(log_file)

            # Set up formatter
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            file_handler.setFormatter(formatter)

            # Add the handler to the root logger
            root_logger.addHandler(file_handler)

            # Set level for the root logger
            if root_logger.level > logging.INFO or root_logger.level == logging.NOTSET:
                root_logger.setLevel(logging.INFO)

            # Log a message to confirm setup
            test_logger = logging.getLogger("MCPIndicator.SocketLogTest")
            test_logger.propagate = True
            test_logger.info(f"File logging configured for MCPIndicator, writing to {log_file}")
            FreeCAD.Console.PrintMessage(f"MCPIndicator logging configured to write to file: {log_file}\n")

        except Exception as e:
            FreeCAD.Console.PrintError(f"Failed to configure file logging handler: {e}\n")

    def setup_ui(self, workbench):
        """Set up all UI elements for the workbench."""
        self._create_status_buttons(workbench) # Creates buttons and their menus
        self._create_main_menu(workbench) # Creates the main "MCP Indicator" menu

    def _create_status_buttons(self, workbench):
        """Create status indicator buttons and their control menus in the status bar."""
        mw = FreeCADGui.getMainWindow()
        if not mw:
            FreeCAD.Console.PrintError("MCPIndicator: Could not get MainWindow.\n")
            return

        statusbar = mw.statusBar()

        # --- MCP Server Status Button ---
        self.mcp_server_status_button = QtWidgets.QToolButton()
        self.mcp_server_status_button.setAutoRaise(True)
        self.mcp_server_status_button.setPopupMode(QtWidgets.QToolButton.InstantPopup) # Show menu on click
        self.mcp_server_status_button.setToolTip("MCP Server Status (Loading...)") # Initial tooltip
        # Menu for MCP Server Controls
        mcp_menu = QMenu(self.mcp_server_status_button)
        self.mcp_start_action = mcp_menu.addAction("Start MCP Server")
        self.mcp_start_action.triggered.connect(self._handle_mcp_start)
        self.mcp_stop_action = mcp_menu.addAction("Stop MCP Server")
        self.mcp_stop_action.triggered.connect(self._handle_mcp_stop)
        self.mcp_restart_action = mcp_menu.addAction("Restart MCP Server")
        self.mcp_restart_action.triggered.connect(self._handle_mcp_restart)
        mcp_menu.addSeparator()
        mcp_info_action = mcp_menu.addAction("Show Info...")
        mcp_info_action.triggered.connect(self._show_mcp_server_info)
        self.mcp_server_status_button.setMenu(mcp_menu)
        statusbar.addPermanentWidget(self.mcp_server_status_button)


        # --- FreeCAD Socket Server Status Button ---
        self.freecad_server_status_button = QtWidgets.QToolButton()
        self.freecad_server_status_button.setAutoRaise(True)
        self.freecad_server_status_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.freecad_server_status_button.setToolTip("Socket Server Status (Loading...)") # Initial tooltip
        # Menu for FreeCAD Server Controls
        freecad_menu = QMenu(self.freecad_server_status_button)
        self.freecad_start_action = freecad_menu.addAction("Start Socket Server")
        self.freecad_start_action.triggered.connect(self._handle_fc_start)
        self.freecad_stop_action = freecad_menu.addAction("Stop Socket Server")
        self.freecad_stop_action.triggered.connect(self._handle_fc_stop)
        self.freecad_restart_action = freecad_menu.addAction("Restart Socket Server")
        self.freecad_restart_action.triggered.connect(self._handle_fc_restart)
        freecad_menu.addSeparator()
        fc_info_action = freecad_menu.addAction("Show Info...")
        fc_info_action.triggered.connect(self._show_freecad_server_info)
        self.freecad_server_status_button.setMenu(freecad_menu)
        statusbar.addPermanentWidget(self.freecad_server_status_button)


        # --- MCP Client / Main Control Button ---
        self.control_button = QtWidgets.QToolButton()
        self.control_button.setAutoRaise(True)
        self.control_button.setPopupMode(QtWidgets.QToolButton.InstantPopup) # Keep main control dropdown
        self.control_button.setToolTip("MCP Client Connection (Loading...)") # Initial tooltip

        # Create main control menu (attached to the client status button)
        control_menu = QMenu(self.control_button)
        client_info_action = control_menu.addAction("Show Client Info...")
        client_info_action.triggered.connect(self._show_connection_info)
        control_menu.addSeparator()
        # Add actions already present in other menus? Maybe just Settings/Flow Vis here?
        # Let's keep the server menus nested for now as per original design
        mcp_sub_menu = control_menu.addMenu("MCP Server")
        mcp_sub_menu.addAction(self.mcp_start_action) # Reuse action from mcp_server_status_button menu
        mcp_sub_menu.addAction(self.mcp_stop_action)
        mcp_sub_menu.addAction(self.mcp_restart_action)
        mcp_sub_menu.addSeparator()
        mcp_sub_menu.addAction(mcp_info_action) # Reuse info action

        freecad_sub_menu = control_menu.addMenu("Socket Server")
        freecad_sub_menu.addAction(self.freecad_start_action) # Reuse action
        freecad_sub_menu.addAction(self.freecad_stop_action)
        freecad_sub_menu.addAction(self.freecad_restart_action)
        freecad_sub_menu.addSeparator()
        freecad_sub_menu.addAction(fc_info_action) # Reuse info action

        control_menu.addSeparator()
        # Get Flow Vis action from main menu creation if already done, or create placeholder
        if "flow_vis" in self.main_menu_actions:
             control_menu.addAction(self.main_menu_actions["flow_vis"])
        else:
            # This case shouldn't happen if setup_ui calls create_status_buttons then create_main_menu
            fv_placeholder = control_menu.addAction("Flow Visualization (Unavailable)")
            fv_placeholder.setEnabled(False)


        # Get Settings action
        if "settings" in self.main_menu_actions:
             control_menu.addAction(self.main_menu_actions["settings"])
        else:
             settings_placeholder = control_menu.addAction("Settings (Unavailable)")
             settings_placeholder.setEnabled(False)

        # Log viewer (disabled)
        show_log_action = control_menu.addAction("Show MCP Log (Disabled)")
        show_log_action.setEnabled(False)
        show_log_action.setToolTip("Logs are now directed to the server's console output or socket.")

        # Dependencies Action (reusing from main menu if available)
        control_menu.addSeparator()
        if self.install_deps_action_mainmenu:
             self.install_deps_action_statusbar = control_menu.addAction(self.install_deps_action_mainmenu) # Link same action
        else:
            # Create it here if main menu hasn't been done yet (unlikely but safe)
             self.install_deps_action_statusbar = control_menu.addAction("Install MCP Dependencies")
             # Connection will be done in InitGui.py or _create_main_menu


        self.control_button.setMenu(control_menu)
        statusbar.addPermanentWidget(self.control_button)

        # Initial UI update
        self.update_ui()

    def _create_main_menu(self, workbench):
        """Create the main 'MCP Indicator' menu in the menu bar."""
        # Create a list to store actions for the main menu bar
        main_menu_action_list = []
        self.main_menu_actions = {} # Reset stored actions

        # --- Create Actions ---
        # Store actions in self.main_menu_actions for potential reuse/disabling

        # Flow visualization
        action = QtWidgets.QAction("Show Flow Visualization")
        action.setStatusTip("Show MCP message flow visualization")
        action.triggered.connect(self._show_flow_visualization)
        self.flow_visualization_action = action # Keep ref if needed elsewhere
        self.main_menu_actions["flow_vis"] = action
        main_menu_action_list.append(action)

        # Settings
        action = QtWidgets.QAction("Settings")
        action.setStatusTip("Configure MCP indicator settings")
        action.triggered.connect(self._show_settings)
        self.main_menu_actions["settings"] = action
        main_menu_action_list.append(action)

        # Install dependencies
        action = QtWidgets.QAction("Install MCP Dependencies")
        action.setStatusTip("Install Python dependencies for MCP server")
        # Connection to dependency_manager happens in InitGui.py or _create_main_menu
        self.install_deps_action_mainmenu = action # Store ref
        self.main_menu_actions["install_deps"] = action
        main_menu_action_list.append(action)

        # --- Add actions to workbench ---
        # Use unique names for toolbar/menu to avoid conflicts
        workbench.appendToolbar("MCP_Indicator_Toolbar", []) # Empty toolbar initially, maybe add icons later?
        workbench.appendMenu("MCP Indicator", main_menu_action_list)

        # Now that main menu actions exist, potentially update status bar menu if needed
        # (This assumes _create_status_buttons might be called before _create_main_menu,
        # which isn't the current flow but handles potential reordering)
        if self.control_button and self.control_button.menu():
            # Find and potentially replace placeholder actions in status bar menu
            for act in self.control_button.menu().actions():
                 if act.text() == "Flow Visualization (Unavailable)" and "flow_vis" in self.main_menu_actions:
                     # Replace placeholder if needed (more complex, might require rebuilding menu)
                     # Simpler: just ensure connection is set if placeholder was used
                     pass # Placeholder replacement is tricky, avoid for now
                 elif act.text() == "Settings (Unavailable)" and "settings" in self.main_menu_actions:
                     pass
                 elif act.text() == "Install MCP Dependencies" and self.install_deps_action_mainmenu:
                     # Ensure connection is established if not already linked
                     # Note: Connection is done in InitGui.py
                     pass


    # --- Action Handlers with Immediate Feedback ---

    def _handle_mcp_start(self):
        self._set_mcp_busy(True, "starting")
        try:
            self.process_manager.start_mcp_server()
            # Status will update via timer, but leave busy state until confirmed
        except Exception as e:
            FreeCAD.Console.PrintError(f"MCPIndicator: Error starting MCP server: {e}\\n")
            self._set_mcp_busy(False) # Reset busy state on immediate error

    def _handle_mcp_stop(self):
        self._set_mcp_busy(True, "stopping")
        try:
            self.process_manager.stop_mcp_server()
        except Exception as e:
            FreeCAD.Console.PrintError(f"MCPIndicator: Error stopping MCP server: {e}\\n")
            self._set_mcp_busy(False)

    def _handle_mcp_restart(self):
        self._set_mcp_busy(True, "restarting") # Show as stopping first perhaps? Or custom icon?
        try:
            self.process_manager.restart_mcp_server()
        except Exception as e:
            FreeCAD.Console.PrintError(f"MCPIndicator: Error restarting MCP server: {e}\\n")
            self._set_mcp_busy(False)

    def _handle_fc_start(self):
        self._set_fc_busy(True, "starting")
        try:
            self.process_manager.start_freecad_server()
        except Exception as e:
            FreeCAD.Console.PrintError(f"MCPIndicator: Error starting Socket server: {e}\\n")
            self._set_fc_busy(False)

    def _handle_fc_stop(self):
        self._set_fc_busy(True, "stopping")
        try:
            self.process_manager.stop_freecad_server()
        except Exception as e:
            FreeCAD.Console.PrintError(f"MCPIndicator: Error stopping Socket server: {e}\\n")
            self._set_fc_busy(False)

    def _handle_fc_restart(self):
        self._set_fc_busy(True, "restarting")
        try:
            self.process_manager.restart_freecad_server()
        except Exception as e:
            FreeCAD.Console.PrintError(f"MCPIndicator: Error restarting Socket server: {e}\\n")
            self._set_fc_busy(False)


    def _set_mcp_busy(self, busy, state="busy"):
        self._mcp_server_busy = busy
        if self.mcp_server_status_button:
             if busy:
                 icon_key = f"mcp_{state}" if state in ["starting", "stopping"] else "waiting"
                 self.mcp_server_status_button.setIcon(self.icons.get(icon_key, self.icons["waiting"]))
                 tooltip_suffix = f" ({state.capitalize()}...)"
                 # Update tooltip immediately if possible (will be overwritten by update_ui soon)
                 current_tooltip_base = self.mcp_server_status_button.toolTip().split(' (')[0]
                 self.mcp_server_status_button.setToolTip(current_tooltip_base + tooltip_suffix)

             # Disable/enable actions while busy
             if self.mcp_start_action: self.mcp_start_action.setEnabled(not busy)
             if self.mcp_stop_action: self.mcp_stop_action.setEnabled(not busy)
             if self.mcp_restart_action: self.mcp_restart_action.setEnabled(not busy)

             # If finished busy state, trigger a UI update to get final status
             if not busy:
                 QtCore.QTimer.singleShot(100, self.update_ui) # Schedule update slightly later


    def _set_fc_busy(self, busy, state="busy"):
        self._fc_server_busy = busy
        if self.freecad_server_status_button:
             if busy:
                 icon_key = f"fc_{state}" if state in ["starting", "stopping"] else "waiting"
                 self.freecad_server_status_button.setIcon(self.icons.get(icon_key, self.icons["waiting"]))
                 tooltip_suffix = f" ({state.capitalize()}...)"
                 current_tooltip_base = self.freecad_server_status_button.toolTip().split(' (')[0]
                 self.freecad_server_status_button.setToolTip(current_tooltip_base + tooltip_suffix)

             if self.freecad_start_action: self.freecad_start_action.setEnabled(not busy)
             if self.freecad_stop_action: self.freecad_stop_action.setEnabled(not busy)
             if self.freecad_restart_action: self.freecad_restart_action.setEnabled(not busy)

             if not busy:
                  QtCore.QTimer.singleShot(100, self.update_ui)


    # --- UI Update Methods ---

    def _update_client_icon_and_tooltip(self):
        """Update the client connection indicator icon and tooltip."""
        if not self.control_button or not self.status_checker:
            return

        # Client Connection Status (handled by control_button)
        if self.status_checker.is_client_connected(): # Assumes status_checker has this method
             self.control_button.setIcon(self.icons["client_connected"])
             self.control_button.setToolTip("MCP Client: Connected")
        else:
             self.control_button.setIcon(self.icons["client_disconnected"])
             self.control_button.setToolTip("MCP Client: Disconnected")
             # Show connection error in tooltip if disconnected and error exists
             error_msg = self.status_checker.get_connection_error()
             if error_msg:
                 self.control_button.setToolTip(f"MCP Client: Disconnected\\nError: {error_msg}")


    def _update_freecad_server_icon_and_tooltip(self):
        """Update the FC server status button icon and tooltip."""
        # Guard against uninitialized UI
        if not self.freecad_server_status_button or not self.status_checker:
            return

        # Get current server status
        server_status = self.status_checker.get_fc_server_status()
        running = server_status.get("running", False)
        server_type = server_status.get("type", "rpc")

        # Get PID info for tooltip if available
        pid_info = ""
        if running and server_status.get("pid"):
            pid_info = f" (PID: {server_status['pid']})"

        # Update icon and tooltip
        if running:
            self.freecad_server_status_button.setIcon(self.icons["fc_running"])
            self.freecad_server_status_button.setToolTip(f"RPC XML Server: Running{pid_info}")
        else:
            self.freecad_server_status_button.setIcon(self.icons["fc_stopped"])
            self.freecad_server_status_button.setToolTip("RPC XML Server: Stopped")

    def _update_mcp_server_icon_and_tooltip(self):
        """Update the MCP server indicator icon and tooltip."""
        if not self.mcp_server_status_button or not self.status_checker:
            return

        if self._mcp_server_busy:
            return

        status = self.status_checker.get_mcp_server_status() # e.g., {"status": "running_external", "pid": null} or {"status": "running_managed", "pid": 456} or {"status": "stopped"}

        status_type = status.get("status", "stopped")
        pid_info = f" (PID: {status.get('pid')})" if status.get('pid') else ""
        tooltip = "MCP Server: Unknown"
        icon = self.icons["mcp_stopped"] # Default

        if status_type == "running_managed":
            icon = self.icons["mcp_running"]
            tooltip = f"MCP Server: Running (Managed){pid_info}"
        elif status_type == "running_external":
             icon = self.icons["mcp_running_external"]
             tooltip = "MCP Server: Running (External)"
             # Optionally try to get external PID if possible, but might be hard
        elif status_type == "stopped":
            icon = self.icons["mcp_stopped"]
            tooltip = "MCP Server: Stopped"
        # Add handling for starting/stopping if status_checker provides it?

        self.mcp_server_status_button.setIcon(icon)
        self.mcp_server_status_button.setToolTip(tooltip)

        # Reset busy state once status is confirmed
        # self._set_mcp_busy(False) # Handled by update_ui now

    # Remove _update_tooltip as it's integrated now
    # def _update_tooltip(self): ...

    def update_ui(self):
        """Update all relevant UI elements based on current status."""
        if not self.status_checker:
            FreeCAD.Console.PrintWarning("MCPIndicator: Status checker not available, cannot update UI.\\n")
            return

        # Update icons and tooltips
        self._update_client_icon_and_tooltip()
        self._update_freecad_server_icon_and_tooltip()
        self._update_mcp_server_icon_and_tooltip()

        # Update enabled/disabled state of actions
        self._update_action_states()

        # Reset busy flags if the status reflects the completed action
        # Check MCP Server busy state
        mcp_status = self.status_checker.get_mcp_server_status()
        mcp_state = mcp_status.get("status", "stopped")
        if self._mcp_server_busy:
             # If it was starting/stopping, but now is in a stable state (running/stopped)
             if mcp_state != "starting" and mcp_state != "stopping": # Needs status_checker to report these?
                 self._set_mcp_busy(False)

        # Check FC Server busy state
        fc_status = self.status_checker.get_fc_server_status()
        fc_running = fc_status.get("running", False)
        if self._fc_server_busy:
            # If it was starting/stopping, but now is running or stopped
            # This simple check should suffice if we don't have explicit starting/stopping states
            if fc_running or not fc_running:
                self._set_fc_busy(False)


    def _update_action_states(self):
        """Enable/disable control actions based on server status."""
        if not self.status_checker: return

        # --- MCP Server Actions ---
        mcp_status = self.status_checker.get_mcp_server_status()
        mcp_running = mcp_status.get("status", "stopped") != "stopped"
        mcp_is_external = mcp_status.get("status") == "running_external"

        # Enable start only if stopped and not busy
        if self.mcp_start_action: self.mcp_start_action.setEnabled(not mcp_running and not self._mcp_server_busy)
        # Enable stop/restart only if running (managed) and not busy
        if self.mcp_stop_action: self.mcp_stop_action.setEnabled(mcp_running and not mcp_is_external and not self._mcp_server_busy)
        if self.mcp_restart_action: self.mcp_restart_action.setEnabled(mcp_running and not mcp_is_external and not self._mcp_server_busy)

        # --- Socket Server Actions ---
        fc_status = self.status_checker.get_fc_server_status()
        fc_running = fc_status.get("running", False)

        if self.freecad_start_action: self.freecad_start_action.setEnabled(not fc_running and not self._fc_server_busy)
        if self.freecad_stop_action: self.freecad_stop_action.setEnabled(fc_running and not self._fc_server_busy)
        if self.freecad_restart_action: self.freecad_restart_action.setEnabled(fc_running and not self._fc_server_busy)

        # --- Other Actions ---
        # Example: Disable Flow Vis if MCP server isn't running?
        if self.flow_visualization_action:
             self.flow_visualization_action.setEnabled(mcp_running) # Enable only if MCP server running


    # --- Dialog Display Methods ---

    def _show_connection_info(self):
        """Show dialog with MCP client connection details."""
        # Reuse or create dialog logic
        # Use get_detailed_connection_info for simplicity, or build from individual getters
        details = self.status_checker.get_detailed_connection_info()
        html_content = self._get_client_info_html(details)
        self._show_info_dialog("MCP Client Connection Info", html_content)

    def _show_freecad_server_info(self):
        """Show detailed information about the FreeCAD server."""
        # Get detailed information about the connection
        details = self.status_checker.get_detailed_connection_info()

        # Generate HTML content for the dialog
        html_content = self._get_freecad_server_info_html(details)

        # Create and show the dialog
        self._show_info_dialog("FreeCAD RPC Server Information", html_content)

    def _show_mcp_server_info(self):
        """Show dialog with MCP server details."""
        details = self.status_checker.get_detailed_connection_info()
        html_content = self._get_mcp_server_info_html(details)
        self._show_info_dialog("MCP Server Info", html_content)

    def _show_flow_visualization(self):
        """Launch the flow visualization dialog."""
        # Check if server is running first?
        mcp_status = self.status_checker.get_mcp_server_status()
        if mcp_status.get("status", "stopped") == "stopped":
             QtWidgets.QMessageBox.warning(None, "MCP Server Stopped", "The MCP Server must be running to show flow visualization.")
             return

        try:
            # Import dynamically
            from flow_visualization import MCPFlowDialog
            # Ensure config_manager is passed if needed by MCPFlowDialog constructor
            # Check constructor signature of MCPFlowDialog
            dialog = MCPFlowDialog(self.config_manager) # Example: Pass config
            dialog.exec_() # Show modal dialog
        except ImportError:
            FreeCAD.Console.PrintError("MCPIndicator: Failed to import MCPFlowDialog.\\n")
            QtWidgets.QMessageBox.critical(None, "Error", "Could not load the Flow Visualization module.")
        except Exception as e:
             FreeCAD.Console.PrintError(f"MCPIndicator: Error showing Flow Visualization: {e}\\n")
             QtWidgets.QMessageBox.critical(None, "Error", f"An error occurred while opening Flow Visualization:\\n{e}")


    def _show_info_dialog(self, title, html_content):
        """Generic method to display an information dialog with HTML content."""
        # Use a non-singleton dialog to avoid issues if closed externally
        dialog = QtWidgets.QDialog(FreeCADGui.getMainWindow())
        dialog.setWindowTitle(title)
        dialog.setMinimumWidth(450)
        dialog.setMinimumHeight(300)
        # Ensure dialog is deleted when closed to prevent memory leaks
        dialog.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        layout = QtWidgets.QVBoxLayout(dialog)

        text_edit = QtWidgets.QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml(html_content)
        layout.addWidget(text_edit)

        # Add a close button
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        # Use reject() which is standard for closing dialogs via button box
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)
        # Show non-modal so it doesn't block FreeCAD UI
        # dialog.show()
        # Let's keep it modal for now as per original implementation
        dialog.exec_()


    # --- HTML Content Generation ---

    def _get_client_info_html(self, details):
        """Generate HTML for the client connection info dialog."""
        # Use details passed from status_checker.get_detailed_connection_info()
        client_connected = details.get("connected", False)
        # client_details = self.status_checker.get_client_details() # Already in 'details' dict
        connection_time = details.get("connection_time")
        connection_duration = details.get("connection_duration", "N/A")
        connection_error = details.get("connection_error")

        status_color = "green" if client_connected else "red"
        status_text = "Connected" if client_connected else "Disconnected"

        html = f"<h2>MCP Client Status</h2>"
        html += f"<p><b>Status: <span style='color:{status_color};'>{status_text}</span></b></p>"

        if client_connected:
            # Extract details fetched from server if available
            server_details = details.get("details", {})
            peer_address = server_details.get("peer_address", "N/A") # Example field
            html += f"<p><b>Connected To Peer:</b> {peer_address}</p>"
            if connection_time:
                 time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(connection_time))
                 html += f"<p><b>Connected Since:</b> {time_str}</p>"
                 html += f"<p><b>Duration:</b> {connection_duration}</p>"
        elif connection_error:
            html += f"<p><b>Error: <span style='color:red;'>{connection_error}</span></b></p>"
        else:
            html += "<p>No active client connection.</p>"

        # Add configuration details
        mcp_host = self.config_manager.get_mcp_server_host() # Use specific getter
        mcp_port = self.config_manager.get_mcp_server_port() # Use specific getter
        html += f"<h3>Configuration</h3>"
        html += f"<p><b>Target MCP Server:</b> {mcp_host}:{mcp_port}</p>"

        return html


    def _get_freecad_server_info_html(self, details):
        """Generate HTML for the FreeCAD server info dialog."""
        html = "<html><head><style>body{font-family:sans-serif;margin:8px}h1{font-size:18px;color:#0066cc}h2{font-size:16px;color:#333}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ddd;padding:8px}tr:nth-child(even){background-color:#f2f2f2}tr:hover{background-color:#ddd}th{padding-top:12px;padding-bottom:12px;text-align:left;background-color:#4CAF50;color:white}.status-running{color:green;font-weight:bold}.status-stopped{color:red}.notes{font-size:12px;font-style:italic;color:#666}</style></head><body>"

        running = details.get("rpc_server_running", False)
        pid = details.get("rpc_server_pid")
        port = details.get("rpc_server_port", 9875)

        status_class = "status-running" if running else "status-stopped"
        status_text = "Running" if running else "Stopped"

        html += f"<h1>FreeCAD RPC XML Server Status</h1>"
        html += f"<p>The RPC XML server allows external applications to control FreeCAD remotely.</p>"

        html += f"<table>"
        html += f"<tr><th>Setting</th><th>Value</th></tr>"
        html += f"<tr><td>Status</td><td class='{status_class}'>{status_text}</td></tr>"

        if running and pid:
            html += f"<tr><td>Process ID</td><td>{pid}</td></tr>"

        html += f"<tr><td>Server Type</td><td>XML-RPC</td></tr>"
        html += f"<tr><td>Server Address</td><td>http://localhost:{port}</td></tr>"
        html += f"</table>"

        html += f"<h2>Usage</h2>"
        html += f"<p>The XML-RPC server provides the following functionality:</p>"
        html += f"<ul>"
        html += f"<li>Document creation and management</li>"
        html += f"<li>Object creation, editing, and deletion</li>"
        html += f"<li>Property manipulation</li>"
        html += f"<li>Screenshot capture</li>"
        html += f"<li>Remote code execution</li>"
        html += f"</ul>"

        html += f"<p class='notes'>See the README for more information about the RPC server functionality.</p>"
        html += "</body></html>"
        return html


    def _get_mcp_server_info_html(self, details):
        """Generate HTML for the MCP server info dialog."""
        # Use details passed from status_checker.get_detailed_connection_info()
        status_type = details.get("mcp_server_status", "stopped") # "stopped", "running_managed", "running_external"
        pid = details.get("mcp_server_pid") # Only for managed
        script_path = details.get("mcp_server_script", "N/A")
        config_path = details.get("mcp_server_config", "N/A")
        host = details.get("mcp_server_host", "N/A")
        port = details.get("mcp_server_port", "N/A")

        status_text = "Unknown"
        status_color = "gray"

        if status_type == "running_managed":
            status_text = "Running (Managed by Indicator)"
            status_color = "darkGreen"
        elif status_type == "running_external":
            status_text = "Running (External Process)"
            status_color = "cyan"
        elif status_type == "stopped":
            status_text = "Stopped"
            status_color = "darkRed"


        html = f"<h2>MCP Server Status</h2>"
        html += f"<p><b>Status: <span style='color:{status_color};'>{status_text}</span></b></p>"
        if status_type == "running_managed" and pid:
            html += f"<p><b>Process ID (PID):</b> {pid}</p>"

        # Show details fetched from the server (if available)
        server_details = details.get("details", {})
        if server_details and not server_details.get("error"):
             html += "<h3>Server Details</h3><ul>"
             for key, value in server_details.items():
                 # Simple display for now
                 html += f"<li><b>{key.replace('_', ' ').title()}:</b> {value}</li>"
             html += "</ul>"
        elif server_details.get("error"):
             html += f"<p><i>Could not fetch details from server: {server_details.get('error')}</i></p>"

        # Add uptime if available from status_checker
        # uptime = status.get("uptime")
        # if uptime:
        #    html += f"<p><b>Uptime:</b> {uptime}</p>"

        # Add Client Info if available
        # client_list = status.get("clients", [])
        # if client_list:
        #     html += "<h3>Connected Clients</h3><ul>"
        #     for client_addr in client_list:
        #         html += f"<li>{client_addr}</li>"
        #     html += "</ul>"


        html += "<h3>Configuration</h3>"
        html += f"<p><b>Script Path:</b> {script_path}</p>"
        html += f"<p><b>Config File:</b> {config_path}</p>"
        html += f"<p><b>Listening On:</b> {host}:{port}</p>"

        # Add Log Info
        # log_path = self.config_manager.get_setting("mcp_server_log_path", "N/A") # Example
        # html += f"<h3>Logging</h3>"
        # html += f"<p><b>Log File:</b> {log_path}</p>"
        html += f"<p><i>Note: Server logs are typically viewed in the console where it was started, or received via socket logging by this indicator.</i></p>"


        return html


    # --- Settings Dialog ---

    def _show_settings(self):
        """Display the settings configuration dialog."""
        dialog = QtWidgets.QDialog(FreeCADGui.getMainWindow())
        dialog.setWindowTitle("MCP Indicator Settings")
        dialog.setMinimumWidth(500)

        layout = QtWidgets.QVBoxLayout(dialog)
        tab_widget = QtWidgets.QTabWidget()

        # --- FreeCAD Server Tab ---
        fc_tab = QtWidgets.QWidget()
        fc_layout = QtWidgets.QFormLayout(fc_tab)

        # Use specific getters for initial values
        fc_script_edit = QtWidgets.QLineEdit(self.config_manager.get_server_script_path())
        fc_script_button = QtWidgets.QPushButton("Browse...")
        fc_script_button.clicked.connect(lambda: self._browse_server_path(fc_script_edit))
        fc_script_layout = QtWidgets.QHBoxLayout()
        fc_script_layout.addWidget(fc_script_edit)
        fc_script_layout.addWidget(fc_script_button)
        fc_layout.addRow("Socket Server Script:", fc_script_layout)

        # Need fc_host and fc_port getters/setters in ConfigManager
        fc_host_edit = QtWidgets.QLineEdit(getattr(self.config_manager, 'get_fc_server_host', lambda: 'localhost')())
        fc_layout.addRow("Host:", fc_host_edit)

        fc_port_edit = QtWidgets.QLineEdit(str(getattr(self.config_manager, 'get_fc_server_port', lambda: 12345)()))
        fc_port_edit.setValidator(QtGui.QIntValidator(1, 65535)) # Port range validation
        fc_layout.addRow("Port:", fc_port_edit)

        fc_tab.setLayout(fc_layout)
        tab_widget.addTab(fc_tab, "Socket Server")


        # --- MCP Server Tab ---
        mcp_tab = QtWidgets.QWidget()
        mcp_layout = QtWidgets.QFormLayout(mcp_tab)

        # Use specific getters
        mcp_script_edit = QtWidgets.QLineEdit(self.config_manager.get_mcp_server_script_path())
        mcp_script_button = QtWidgets.QPushButton("Browse...")
        mcp_script_button.clicked.connect(lambda: self._browse_mcp_server_path(mcp_script_edit))
        mcp_script_layout = QtWidgets.QHBoxLayout()
        mcp_script_layout.addWidget(mcp_script_edit)
        mcp_script_layout.addWidget(mcp_script_button)
        mcp_layout.addRow("MCP Server Script:", mcp_script_layout)

        mcp_config_edit = QtWidgets.QLineEdit(self.config_manager.get_mcp_server_config())
        mcp_config_button = QtWidgets.QPushButton("Browse...")
        mcp_config_button.clicked.connect(lambda: self._browse_config_path(mcp_config_edit))
        mcp_config_layout = QtWidgets.QHBoxLayout()
        mcp_config_layout.addWidget(mcp_config_edit)
        mcp_config_layout.addWidget(mcp_config_button)
        mcp_layout.addRow("MCP Config File:", mcp_config_layout)

        mcp_host_edit = QtWidgets.QLineEdit(self.config_manager.get_mcp_server_host())
        mcp_layout.addRow("Host:", mcp_host_edit)

        mcp_port_edit = QtWidgets.QLineEdit(str(self.config_manager.get_mcp_server_port()))
        mcp_port_edit.setValidator(QtGui.QIntValidator(1, 65535))
        mcp_layout.addRow("Port:", mcp_port_edit)

        mcp_tab.setLayout(mcp_layout)
        tab_widget.addTab(mcp_tab, "MCP Server")

        # --- General/Client Tab (Optional) ---
        # client_tab = QtWidgets.QWidget()
        # client_layout = QtWidgets.QFormLayout(client_tab)
        # ... add client specific settings if any ...
        # tab_widget.addTab(client_tab, "Client")

        layout.addWidget(tab_widget)

        # --- Save/Cancel Buttons ---
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)

        def save_settings():
            # Use specific setters
            # FC Server Settings
            self.config_manager.set_server_script_path(fc_script_edit.text())
            # Need setters for fc_host/fc_port in ConfigManager
            if hasattr(self.config_manager, 'set_fc_server_host'):
                 self.config_manager.set_fc_server_host(fc_host_edit.text())
            if hasattr(self.config_manager, 'set_fc_server_port'):
                 try:
                     self.config_manager.set_fc_server_port(int(fc_port_edit.text()))
                 except ValueError:
                     FreeCAD.Console.PrintWarning("Invalid Socket Server port entered, keeping previous value.\\n")

            # MCP Server Settings
            self.config_manager.set_mcp_server_script_path(mcp_script_edit.text())
            self.config_manager.set_mcp_server_config(mcp_config_edit.text())
            self.config_manager.set_mcp_server_host(mcp_host_edit.text())
            try:
                self.config_manager.set_mcp_server_port(int(mcp_port_edit.text()))
            except ValueError:
                 FreeCAD.Console.PrintWarning("Invalid MCP Server port entered, keeping previous value.\\n")

            self.config_manager.save_settings() # Call the save method in ConfigManager
            dialog.accept()
            # Trigger UI update after saving
            self.update_ui()


        button_box.accepted.connect(save_settings)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)
        dialog.exec_()


    # --- File Browser Helpers ---
    # Keep these as they are used by the settings dialog

    def _browse_repo_path(self, line_edit):
        # This seems unused now? Keep for reference or remove if confirmed unused.
        # If needed, ensure it uses specific getter/setter
        start_dir = self.config_manager.get_repo_path() or QStandardPaths.writableLocation(QStandardPaths.HomeLocation)
        directory = QtWidgets.QFileDialog.getExistingDirectory(None, "Select Repository Directory", start_dir)
        if directory:
            line_edit.setText(directory)
            # Automatically update server paths (optional)
            # self._apply_repo_path(directory, ...) # Pass relevant line edits

    def _apply_repo_path(self, repo_path, server_edit, mcp_edit):
         # This seems unused now? Keep for reference or remove if confirmed unused.
        if not os.path.isdir(repo_path):
            return

        potential_server = os.path.join(repo_path, "freecad_socket_server.py")
        potential_mcp = os.path.join(repo_path, "src", "mcp_freecad", "server", "freecad_mcp_server.py")

        if os.path.isfile(potential_server):
            server_edit.setText(potential_server)
        else:
            FreeCAD.Console.PrintWarning(f"Socket server not found at expected path: {potential_server}\\n")

        if os.path.isfile(potential_mcp):
            mcp_edit.setText(potential_mcp)
        else:
             FreeCAD.Console.PrintWarning(f"MCP server not found at expected path: {potential_mcp}\\n")


    def _browse_server_path(self, line_edit):
        """Browse for the FreeCAD socket server script."""
        # Start browsing in the directory of the current value, if valid
        start_dir = os.path.dirname(line_edit.text()) if os.path.exists(os.path.dirname(line_edit.text())) else QStandardPaths.writableLocation(QStandardPaths.HomeLocation)
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            None,
            "Select FreeCAD Socket Server Script",
            start_dir,
            "Python Scripts (*.py);;All Files (*)"
        )
        if file_path:
            line_edit.setText(file_path)

    def _browse_mcp_server_path(self, line_edit):
        """Browse for the MCP server script."""
        start_dir = os.path.dirname(line_edit.text()) if os.path.exists(os.path.dirname(line_edit.text())) else QStandardPaths.writableLocation(QStandardPaths.HomeLocation)
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            None,
            "Select MCP Server Script",
            start_dir,
            "Python Scripts (*.py);;All Files (*)"
        )
        if file_path:
            line_edit.setText(file_path)

    def _browse_config_path(self, line_edit):
        """Browse for the MCP server config file."""
        start_dir = os.path.dirname(line_edit.text()) if os.path.exists(os.path.dirname(line_edit.text())) else QStandardPaths.writableLocation(QStandardPaths.HomeLocation)
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            None,
            "Select MCP Server Configuration File",
            start_dir,
            "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            line_edit.setText(file_path)
