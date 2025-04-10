import inspect
import os
import socket
import subprocess
import sys
import time
import json
import shutil
import signal # <-- Add import
import platform
import shlex
import threading
import logging # <-- Add this import

import FreeCAD
import FreeCADGui
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtWidgets import QDockWidget, QTextEdit, QVBoxLayout, QPushButton, QWidget, QMenu, QAction
from PySide2.QtCore import QFileSystemWatcher, QTimer, QStandardPaths, Qt # Add Qt

# Import the flow visualization once to ensure it's available
try:
    from mcp_indicator import flow_visualization
except ImportError:
    FreeCAD.Console.PrintWarning("Failed to import flow_visualization module. Flow visualization may not work properly.\n")

# Remove global path calculations and move to __init__
PYTHON_EXECUTABLE = sys.executable

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
        # Get stored path from FreeCAD parameters, or start with empty string
        self.params = FreeCAD.ParamGet(
            "User parameter:BaseApp/Preferences/Mod/MCPIndicator"
        )

        # Repository path (main path to the mcp-freecad repository)
        self.REPO_PATH = self.params.GetString("RepoPath", "")

        # FreeCAD Server path (freecad_server.py - for socket method)
        self.SERVER_SCRIPT_PATH = self.params.GetString("ServerScriptPath", "")

        # MCP Server path (freecad_mcp_server.py)
        self.MCP_SERVER_SCRIPT_PATH = self.params.GetString("MCPServerScriptPath", "")

        # If repository path is set but script paths are not, auto-set them
        if self.REPO_PATH and (not self.SERVER_SCRIPT_PATH or not self.MCP_SERVER_SCRIPT_PATH):
            self._update_script_paths_from_repo()

        # If not already set, try to determine default paths
        if not self.SERVER_SCRIPT_PATH or not self.MCP_SERVER_SCRIPT_PATH:
            try:
                # Try to find the scripts in the parent directory of the addon
                current_file_path = inspect.getfile(inspect.currentframe())
                current_dir = os.path.dirname(current_file_path)
                # Go up two levels to get to potential project root
                indicator_root = os.path.dirname(current_dir)
                project_root = os.path.dirname(indicator_root)

                # Try common locations for the legacy server script
                possible_server_paths = [
                    os.path.join(project_root, "freecad_server.py"),
                    os.path.join(
                        os.path.expanduser("~"),
                        "Git",
                        "mcp-freecad",
                        "freecad_server.py",
                    ),
                    "/usr/local/bin/freecad_server.py",
                ]

                # Try common locations for the MCP server script
                possible_mcp_paths = [
                    os.path.join(project_root, "src", "mcp_freecad", "server", "freecad_mcp_server.py"),
                    os.path.join(project_root, "freecad_mcp_server.py"), # Legacy check
                    os.path.join(
                        os.path.expanduser("~"),
                        "Git",
                        "mcp-freecad",
                        "src",
                        "mcp_freecad",
                        "server",
                        "freecad_mcp_server.py",
                    ),
                    os.path.join( # Legacy check
                        os.path.expanduser("~"),
                        "Git",
                        "mcp-freecad",
                        "freecad_mcp_server.py",
                    ),
                    "/usr/local/bin/freecad_mcp_server.py", # Legacy check
                ]

                # Find FreeCAD Server path (first that exists)
                if not self.SERVER_SCRIPT_PATH:
                    for path in possible_server_paths:
                        if os.path.exists(path):
                            self.SERVER_SCRIPT_PATH = path
                            self.params.SetString("ServerScriptPath", path)
                            break

                # Find MCP Server path (first that exists)
                if not self.MCP_SERVER_SCRIPT_PATH:
                    for path in possible_mcp_paths:
                        if os.path.exists(path):
                            self.MCP_SERVER_SCRIPT_PATH = path
                            self.params.SetString("MCPServerScriptPath", path)
                            break

            except Exception as e:
                FreeCAD.Console.PrintError(f"Error determining script paths: {str(e)}\n")

        # Log server paths (whether found, set by user, or empty)
        if self.SERVER_SCRIPT_PATH:
            FreeCAD.Console.PrintMessage(
                f"Socket Server script path (Legacy): {self.SERVER_SCRIPT_PATH}\n"
            )
        else:
            FreeCAD.Console.PrintWarning(
                "Socket Server script path not set. Configure in Settings if needed for 'server' connection method.\n"
            )

        if self.MCP_SERVER_SCRIPT_PATH:
            FreeCAD.Console.PrintMessage(
                f"MCP Server script path: {self.MCP_SERVER_SCRIPT_PATH}\n"
            )
        else:
            FreeCAD.Console.PrintWarning(
                "MCP Server script path not set. Start/Stop/Restart controls will be disabled.\n"
            )

        # MCP Client settings (for status checking)
        self.MCP_SERVER_HOST = self.params.GetString("MCPServerHost", "localhost")
        self.MCP_SERVER_PORT = self.params.GetInt("MCPServerPort", 8000)

        # MCP Server settings (config file for starting)
        self.MCP_SERVER_CONFIG = self.params.GetString("MCPServerConfig", "")

        # UI elements
        self._control_button = None
        self._freecad_server_status_button = None
        self._mcp_server_status_button = None
        self._connection_info_dialog = None
        self._flow_visualization_action = None

        # --- Log Viewer Elements ---
        self._mcp_log_dock_widget = None
        self._mcp_log_text_edit = None
        self._mcp_log_watcher = None
        self._mcp_log_file_path = None
        self._show_mcp_log_action = None

        # Determine MCP log file path if possible
        if self.MCP_SERVER_SCRIPT_PATH and os.path.exists(os.path.dirname(self.MCP_SERVER_SCRIPT_PATH)):
            script_dir = os.path.dirname(self.MCP_SERVER_SCRIPT_PATH)
            # The log file is expected in a 'logs' subdirectory relative to the script's dir
            self._mcp_log_file_path = os.path.normpath(os.path.join(script_dir, "logs", "freecad_mcp_server.log"))
            FreeCAD.Console.PrintMessage(f"MCP Log Viewer: Target log file path: {self._mcp_log_file_path}\\n")
        else:
             FreeCAD.Console.PrintWarning("MCP Log Viewer: MCP_SERVER_SCRIPT_PATH not set or invalid, log viewer will be disabled.\\n")
        # --------------------------

        # Process and status tracking
        self._freecad_server_process = None
        self._mcp_server_process = None
        self._timer = None
        self._connection_status = False
        self._freecad_server_running = False  # Track FreeCAD server running status
        self._mcp_server_running = False      # Track MCP server running status
        self._connection_details = {
            "type": "Unknown",
            "client_port": 0,
            "server_port": 0,
            "connected_clients": 0,
            "server_uptime": 0,
        }

    def _update_script_paths_from_repo(self):
        """Update script paths based on repository path"""
        if not self.REPO_PATH or not os.path.isdir(self.REPO_PATH):
            return

        # Set the script paths based on repo path
        server_path = os.path.join(self.REPO_PATH, "freecad_server.py")
        if os.path.exists(server_path):
            self.SERVER_SCRIPT_PATH = server_path
            self.params.SetString("ServerScriptPath", server_path)

        # Check if the shell script exists, otherwise use the Python script
        mcp_shell_path = os.path.join(self.REPO_PATH, "scripts", "start_mcp_server.sh")
        mcp_py_path = os.path.join(self.REPO_PATH, "src", "mcp_freecad", "server", "freecad_mcp_server.py")
        mcp_py_legacy_path = os.path.join(self.REPO_PATH, "freecad_mcp_server.py")

        # Prefer shell script, then new Python path, then legacy Python path
        preferred_mcp_path = None
        if os.path.exists(mcp_shell_path):
            preferred_mcp_path = mcp_shell_path
        elif os.path.exists(mcp_py_path):
            preferred_mcp_path = mcp_py_path
        elif os.path.exists(mcp_py_legacy_path):
            FreeCAD.Console.PrintWarning("Using legacy MCP server script path. Please ensure your setup is correct.\n")
            preferred_mcp_path = mcp_py_legacy_path

        if preferred_mcp_path:
            self.MCP_SERVER_SCRIPT_PATH = preferred_mcp_path
            self.params.SetString("MCPServerScriptPath", preferred_mcp_path)

        # Create start_mcp_server.sh script if it doesn't exist and the Python script exists
        if (os.path.exists(mcp_py_path) or os.path.exists(mcp_py_legacy_path)) and not os.path.exists(mcp_shell_path):
            python_script_to_use = mcp_py_path if os.path.exists(mcp_py_path) else mcp_py_legacy_path
            try:
                # Check for virtual environments
                venv_paths = []

                # Check for .venv directory (standard venv name)
                venv_path = os.path.join(self.REPO_PATH, ".venv")
                if os.path.isdir(venv_path):
                    venv_paths.append((".venv", venv_path))

                # Check for mcp_venv directory (alternative name)
                mcp_venv_path = os.path.join(self.REPO_PATH, "mcp_venv")
                if os.path.isdir(mcp_venv_path):
                    venv_paths.append(("mcp_venv", mcp_venv_path))

                # If we have at least one virtual environment, create the shell script
                if venv_paths:
                    # Use the first venv we found
                    venv_name, venv_path = venv_paths[0]

                    with open(mcp_shell_path, 'w') as f:
                        f.write('#!/bin/bash\n\n')
                        f.write('# Get the directory where this script is located\n')
                        f.write('SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"\n\n')
                        f.write('# Activate the virtual environment\n')
                        f.write(f'source "$SCRIPT_DIR/{venv_name}/bin/activate"\n\n')
                        f.write('# Start the MCP server with debug mode\n')
                        # Use the relative path from SCRIPT_DIR to the python script
                        relative_python_path = os.path.relpath(python_script_to_use, os.path.dirname(mcp_shell_path))
                        f.write(f'python "$SCRIPT_DIR/{relative_python_path}" --debug "$@"\n')

                    # Make the script executable
                    os.chmod(mcp_shell_path, 0o755)

                    # Update the MCP server path to use the shell script
                    self.MCP_SERVER_SCRIPT_PATH = mcp_shell_path
                    self.params.SetString("MCPServerScriptPath", mcp_shell_path)
                    FreeCAD.Console.PrintMessage(f"Created start_mcp_server.sh script to use {venv_name} virtual environment\n")
                else:
                    # Check for squashfs-root Python
                    squashfs_python = os.path.join(self.REPO_PATH, "squashfs-root", "usr", "bin", "python")
                    squashfs_apprun = os.path.join(self.REPO_PATH, "squashfs-root", "AppRun")
                    if os.path.exists(squashfs_apprun):
                        # Create a script that uses AppRun with --console and --run-script flags
                        with open(mcp_shell_path, 'w') as f:
                            f.write('#!/bin/bash\n\n')
                            f.write('# Get the directory where this script is located\n')
                            f.write('SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"\n\n')
                            f.write('# Use FreeCAD AppRun to execute the script with proper environment\n')
                            f.write('# Force X11 backend to avoid Wayland issues\n')
                            f.write('export QT_QPA_PLATFORM=xcb\n\n')
                            f.write('# Pass script path directly without --console flag\n')
                            relative_python_path = os.path.relpath(python_script_to_use, os.path.dirname(mcp_shell_path))
                            f.write(f'"$SCRIPT_DIR/squashfs-root/AppRun" "$SCRIPT_DIR/{relative_python_path}" -- "$@"\n')

                        # Make the script executable
                        os.chmod(mcp_shell_path, 0o755)

                        # Update the MCP server path to use the shell script
                        self.MCP_SERVER_SCRIPT_PATH = mcp_shell_path
                        self.params.SetString("MCPServerScriptPath", mcp_shell_path)
                        FreeCAD.Console.PrintMessage(f"Created start_mcp_server.sh script to use squashfs-root/AppRun\n")
                    elif os.path.exists(squashfs_python):
                        # Fall back to direct Python use if AppRun isn't available
                        with open(mcp_shell_path, 'w') as f:
                            f.write('#!/bin/bash\n\n')
                            f.write('# Get the directory where this script is located\n')
                            f.write('SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"\n\n')
                            f.write('# Use extracted Python interpreter\n')
                            relative_python_path = os.path.relpath(python_script_to_use, os.path.dirname(mcp_shell_path))
                            f.write(f'"$SCRIPT_DIR/squashfs-root/usr/bin/python" "$SCRIPT_DIR/{relative_python_path}" --debug "$@"\n')

                        # Make the script executable
                        os.chmod(mcp_shell_path, 0o755)

                        # Update the MCP server path to use the shell script
                        self.MCP_SERVER_SCRIPT_PATH = mcp_shell_path
                        self.params.SetString("MCPServerScriptPath", mcp_shell_path)
                        FreeCAD.Console.PrintMessage(f"Created start_mcp_server.sh script to use squashfs-root Python\n")
            except Exception as e:
                FreeCAD.Console.PrintError(f"Error creating start_mcp_server.sh script: {str(e)}\n")

    def Initialize(self):
        """Initialize the workbench"""
        # Import necessary PySide modules locally for this scope
        # Ensure QFileSystemWatcher and QDockWidget related classes are available
        from PySide2 import QtCore, QtWidgets
        from PySide2.QtWidgets import QDockWidget, QTextEdit, QVBoxLayout, QPushButton, QWidget, QMenu, QAction
        from PySide2.QtCore import QFileSystemWatcher, Qt

        # Create the main MCP client connection indicator
        self._control_button = QtWidgets.QToolButton()
        self._control_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self._control_button.setFixedSize(24, 24)
        self._control_button.setToolTip("MCP Client: Disconnected")
        self._control_button.setAutoRaise(True)

        # Create the FreeCAD server status indicator
        self._freecad_server_status_button = QtWidgets.QToolButton()
        self._freecad_server_status_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self._freecad_server_status_button.setFixedSize(24, 24)
        self._freecad_server_status_button.setToolTip("FreeCAD Server: Stopped")
        self._freecad_server_status_button.setAutoRaise(True)

        # Create the MCP server status indicator
        self._mcp_server_status_button = QtWidgets.QToolButton()
        self._mcp_server_status_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self._mcp_server_status_button.setFixedSize(24, 24)
        self._mcp_server_status_button.setToolTip("MCP Server: Stopped")
        self._mcp_server_status_button.setAutoRaise(True)

        # Make the buttons clickable
        self._control_button.clicked.connect(self._show_connection_info)
        self._freecad_server_status_button.clicked.connect(self._show_freecad_server_info)
        self._mcp_server_status_button.clicked.connect(self._show_mcp_server_info)

        # Create menu and actions
        self._control_menu = QtWidgets.QMenu(self._control_button)

        # Add settings action first
        self._settings_action = QtWidgets.QAction("Settings...", self._control_menu)
        self._settings_action.triggered.connect(self._show_settings)
        self._control_menu.addAction(self._settings_action)

        # Add flow visualization action
        self._flow_visualization_action = QtWidgets.QAction("Flow Visualization...", self._control_menu)
        self._flow_visualization_action.triggered.connect(self._show_flow_visualization)
        self._control_menu.addAction(self._flow_visualization_action)

        # Add install dependencies action
        self._install_deps_action = QtWidgets.QAction(
            "Install Dependencies...", self._control_menu
        )
        self._install_deps_action.triggered.connect(self._install_dependencies)
        self._control_menu.addAction(self._install_deps_action)

        # Add separator
        self._control_menu.addSeparator()

        # Create FreeCAD server control submenu
        self._freecad_server_menu = QtWidgets.QMenu("FreeCAD Server", self._control_menu)
        self._control_menu.addMenu(self._freecad_server_menu)

        # FreeCAD server control actions
        self._start_freecad_action = QtWidgets.QAction("Start FreeCAD Server (Standalone)", self._freecad_server_menu)
        self._start_freecad_action.triggered.connect(
            lambda: self._start_freecad_server(connect_mode=False)
        )
        self._freecad_server_menu.addAction(self._start_freecad_action)

        # Add start with connect mode
        self._start_freecad_connect_action = QtWidgets.QAction(
            "Start FreeCAD Server (Connect to FreeCAD)", self._freecad_server_menu
        )
        self._start_freecad_connect_action.triggered.connect(
            lambda: self._start_freecad_server(connect_mode=True)
        )
        self._freecad_server_menu.addAction(self._start_freecad_connect_action)

        self._stop_freecad_action = QtWidgets.QAction("Stop FreeCAD Server", self._freecad_server_menu)
        self._stop_freecad_action.triggered.connect(self._stop_freecad_server)
        self._stop_freecad_action.setEnabled(False)
        self._freecad_server_menu.addAction(self._stop_freecad_action)

        self._restart_freecad_action = QtWidgets.QAction("Restart FreeCAD Server", self._freecad_server_menu)
        self._restart_freecad_action.triggered.connect(self._restart_freecad_server)
        self._restart_freecad_action.setEnabled(False)
        self._freecad_server_menu.addAction(self._restart_freecad_action)

        # Create MCP server control submenu
        self._mcp_server_menu = QtWidgets.QMenu("MCP Server", self._control_menu)
        self._control_menu.addMenu(self._mcp_server_menu)

        # MCP server control actions
        self._start_mcp_action = QtWidgets.QAction("Start MCP Server", self._mcp_server_menu)
        self._start_mcp_action.triggered.connect(self._start_mcp_server)
        self._mcp_server_menu.addAction(self._start_mcp_action)

        self._stop_mcp_action = QtWidgets.QAction("Stop MCP Server", self._mcp_server_menu)
        self._stop_mcp_action.triggered.connect(self._stop_mcp_server)
        self._stop_mcp_action.setEnabled(False)
        self._mcp_server_menu.addAction(self._stop_mcp_action)

        self._restart_mcp_action = QtWidgets.QAction("Restart MCP Server", self._mcp_server_menu)
        self._restart_mcp_action.triggered.connect(self._restart_mcp_server)
        self._restart_mcp_action.setEnabled(False)
        self._mcp_server_menu.addAction(self._restart_mcp_action)

        # Add the menus to buttons
        self._freecad_server_status_button.setMenu(self._freecad_server_menu)
        self._mcp_server_status_button.setMenu(self._mcp_server_menu)
        self._control_button.setMenu(self._control_menu)

        # --- MCP Log Viewer Setup ---
        mw = FreeCADGui.getMainWindow()
        # Check if main window exists and if the log path was successfully determined in __init__
        if mw and self._mcp_log_file_path:
            try:
                # Create Dock Widget
                self._mcp_log_dock_widget = QDockWidget("MCP Server Log", mw)
                self._mcp_log_dock_widget.setObjectName("MCPLogDockWidget") # Important for saving layout state
                self._mcp_log_dock_widget.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)

                # Create container widget and layout for the dock contents
                log_container_widget = QWidget()
                log_layout = QVBoxLayout(log_container_widget) # Set layout on the container

                # Create Text Edit for log display
                self._mcp_log_text_edit = QTextEdit()
                self._mcp_log_text_edit.setReadOnly(True)
                self._mcp_log_text_edit.setFontFamily("monospace") # Use fixed-width font
                log_layout.addWidget(self._mcp_log_text_edit)

                # Create Refresh Button
                refresh_button = QPushButton("Refresh Log")
                # Use a lambda to avoid issues with default arguments if _load_mcp_log_content gains parameters later
                refresh_button.clicked.connect(lambda: self._load_mcp_log_content())
                log_layout.addWidget(refresh_button)

                # Set the container widget as the dock widget's main widget
                self._mcp_log_dock_widget.setWidget(log_container_widget)

                # Initially hide the dock widget (user can show it via menu)
                self._mcp_log_dock_widget.setVisible(False)
                # Add the dock widget to the main window (it starts hidden)
                mw.addDockWidget(Qt.BottomDockWidgetArea, self._mcp_log_dock_widget)

                # Create File System Watcher
                self._mcp_log_watcher = QFileSystemWatcher() # Initialize without parent
                log_dir = os.path.dirname(self._mcp_log_file_path)

                # Watch the directory to detect file creation/deletion
                if os.path.exists(log_dir):
                     if not self._mcp_log_watcher.addPath(log_dir):
                          FreeCAD.Console.PrintError(f"MCP Log Watcher: Failed to add directory {log_dir} to watcher.\\n")
                else:
                     FreeCAD.Console.PrintWarning(f"MCP Log Watcher: Log directory {log_dir} does not exist.\\n")

                # Watch the file itself if it exists
                if os.path.exists(self._mcp_log_file_path):
                    if not self._mcp_log_watcher.addPath(self._mcp_log_file_path):
                         FreeCAD.Console.PrintError(f"MCP Log Watcher: Failed to add file {self._mcp_log_file_path} to watcher.\\n")

                # Connect the watcher signal
                self._mcp_log_watcher.fileChanged.connect(self._handle_log_file_change)
                # Also connect directory changed to handle file creation/deletion within dir
                self._mcp_log_watcher.directoryChanged.connect(self._handle_log_directory_change)

                # Load initial content if file exists
                self._load_mcp_log_content()

            except Exception as e:
                 FreeCAD.Console.PrintError(f"Error initializing MCP Log Viewer UI: {e}\\n")
                 self._mcp_log_dock_widget = None # Ensure widget is None if setup failed

        # Add menu action for log viewer (AFTER the menu itself is created)
        # Ensure _control_menu exists before trying to add actions
        if hasattr(self, '_control_menu') and self._control_menu:
             self._control_menu.addSeparator() # Separator before log viewer action
             self._show_mcp_log_action = QAction("Show MCP Server Log", self._control_menu)
             self._show_mcp_log_action.setCheckable(True)
             self._show_mcp_log_action.setChecked(False) # Initially hidden

             # Only enable the action if the dock widget was successfully created
             if self._mcp_log_dock_widget:
                 self._show_mcp_log_action.toggled.connect(self._toggle_mcp_log_viewer)
             else:
                 self._show_mcp_log_action.setEnabled(False)
                 self._show_mcp_log_action.setToolTip("MCP log viewer setup failed or path is invalid.")

             self._control_menu.addAction(self._show_mcp_log_action)
        else:
            FreeCAD.Console.PrintError("Could not find _control_menu to add log viewer action.\\n")
        # --------------------------

        # Update both server and MCP indicator states
        self._update_indicator_icon()
        self._update_freecad_server_icon()
        self._update_mcp_server_icon()

        # Add buttons to status bar
        mw = FreeCADGui.getMainWindow()
        if mw:
            statusbar = mw.statusBar()
            statusbar.addPermanentWidget(self._freecad_server_status_button)
            statusbar.addPermanentWidget(self._mcp_server_status_button)
            statusbar.addPermanentWidget(self._control_button)

        # Setup timer for periodic connection check
        self._timer = QtCore.QTimer()  # Now QtCore should be defined
        self._timer.timeout.connect(self._check_status)
        self._timer.start(5000)

        # Initial check
        self._check_status()
        self._update_action_states()

    def _show_connection_info(self):
        """Show dialog with detailed MCP Client connection information"""
        self._show_info_dialog("MCP Client Connection Details", self._get_client_info_html())

    def _show_freecad_server_info(self):
        """Show dialog with detailed FreeCAD Server information"""
        self._show_info_dialog("FreeCAD Server Details", self._get_freecad_server_info_html())

    def _show_mcp_server_info(self):
        """Show dialog with detailed MCP Server information"""
        self._show_info_dialog("MCP Server Details", self._get_mcp_server_info_html())

    def _show_flow_visualization(self):
        """Show the MCP flow visualization dialog"""
        # Import locally to avoid circular imports
        from mcp_indicator.flow_visualization import mcp_flow_dialog
        mcp_flow_dialog.show()

    def _show_info_dialog(self, title, html_content):
        """Show a dialog with HTML content"""
        from PySide2 import QtWidgets, QtCore

        dialog = QtWidgets.QDialog(FreeCADGui.getMainWindow())
        dialog.setWindowTitle(title)
        dialog.setMinimumSize(400, 300)

        # Set dialog flags to avoid activation issues on Wayland
        if RUNNING_ON_WAYLAND:
            dialog.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowStaysOnTopHint)

        layout = QtWidgets.QVBoxLayout()
        dialog.setLayout(layout)

        text_browser = QtWidgets.QTextBrowser()
        text_browser.setHtml(html_content)
        layout.addWidget(text_browser)

        refresh_button = QtWidgets.QPushButton("Refresh")

        if "Client" in title:
            refresh_button.clicked.connect(lambda: text_browser.setHtml(self._get_client_info_html()))
        elif "FreeCAD Server" in title:
            refresh_button.clicked.connect(lambda: text_browser.setHtml(self._get_freecad_server_info_html()))
        else:
            refresh_button.clicked.connect(lambda: text_browser.setHtml(self._get_mcp_server_info_html()))

        layout.addWidget(refresh_button)

        # Add close button
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.exec_()

    def _get_client_info_html(self):
        """Generate HTML content for client connection details"""
        connection_status = "Connected" if self._connection_status else "Disconnected"
        status_color = "green" if self._connection_status else "red"

        html = f"""
        <h2>MCP Client Connection Status</h2>
        <p>Status: <span style='color:{status_color};font-weight:bold;'>{connection_status}</span></p>
        <p>Server Host: {self.MCP_SERVER_HOST}</p>
        <p>Server Port: {self.MCP_SERVER_PORT}</p>
        <p>Connection Type: {self._connection_details['type']}</p>
        <p>Client Port: {self._connection_details['client_port']}</p>
        """

        # Add additional information if available
        if self._connection_status:
            html += "<h3>Additional Details</h3>"
            try:
                # Attempt to get more connection details if connected
                connection_info = self._get_detailed_connection_info()
                if connection_info:
                    for key, value in connection_info.items():
                        html += f"<p>{key}: {value}</p>"
            except:
                html += "<p>Could not retrieve additional connection details</p>"

        return html

    def _get_freecad_server_info_html(self):
        """Generate HTML content for FreeCAD server details"""
        server_status = "Running" if self._freecad_server_running else "Stopped"
        status_color = "green" if self._freecad_server_running else "red"

        html = f"""
        <h2>FreeCAD Server Status</h2>
        <p>Status: <span style='color:{status_color};font-weight:bold;'>{server_status}</span></p>
        <p>Server Path: {self.SERVER_SCRIPT_PATH}</p>
        <p><strong>Server Type:</strong> Socket Server (freecad_server.py)</p>
        <p><strong>Purpose:</strong> Low-level socket server that executes FreeCAD Python commands</p>
        """

        if self._freecad_server_running:
            html += f"""
            <p>Server Port: 12345 (default)</p>
            <p>Uptime: {self._connection_details.get('freecad_server_uptime', 0)} seconds</p>
            <h3>Status</h3>
            <p>This server provides direct command execution within FreeCAD.</p>
            <p>It acts as the primary interface between the MCP Server and FreeCAD.</p>
            """
        else:
            html += """
            <h3>Status</h3>
            <p>Server is not running. Start the server to enable socket communication with FreeCAD.</p>
            """

        return html

    def _get_mcp_server_info_html(self):
        """Generate HTML content for MCP Server info dialog."""
        if self._mcp_server_running:
            status_text = "<span style='color: green; font-weight: bold;'>Running</span>"
        else:
            status_text = "<span style='color: red; font-weight: bold;'>Stopped</span>"

        html = f"""
            <html><body>
            <h2>MCP Server Status</h2>
            <p><strong>Status:</strong> {status_text}</p>
            <p><strong>Script Path:</strong> {self.MCP_SERVER_SCRIPT_PATH or 'Not Set'}</p>
            <p><strong>Config File:</strong> {self.MCP_SERVER_CONFIG or 'Not Set'}</p>
            <p><strong>Server Type:</strong> MCP Protocol Server (src/mcp_freecad/server/freecad_mcp_server.py)</p>
            <p><strong>Purpose:</strong> Allows AI assistants to interact with FreeCAD via the Model Context Protocol.</p>
            <p><strong>Process ID:</strong> {self._mcp_server_process.pid if self._mcp_server_process else 'N/A'}</p>
        """
        if self._mcp_server_running:
            html += f"""
            <h3>Status</h3>
            <p>This server provides MCP functionality to AI assistants.</p>
            <p>It exposes tools and resources through the Model Context Protocol.</p>
            <p>Server Port: {self.MCP_SERVER_PORT}</p>
            <p>Connected Clients: {self._connection_details['connected_clients']}</p>
            <p>Uptime: {self._connection_details['server_uptime']} seconds</p>
            """
            if self.MCP_SERVER_CONFIG:
                html += f"<p>Config File: {self.MCP_SERVER_CONFIG}</p>"

            html += "<h3>Active Connections</h3>"
            try:
                # Attempt to get active connections info
                connections = self._get_active_connections()
                if connections:
                    html += "<ul>"
                    for conn in connections:
                        html += f"<li>{conn['client_ip']}:{conn['client_port']} - {conn['type']}</li>"
                    html += "</ul>"
                else:
                    html += "<p>No active connections</p>"
            except:
                html += "<p>Could not retrieve active connections</p>"
        else:
            html += """
            <h3>Status</h3>
            <p>Server is not running. Start the server to enable MCP functionality.</p>
            """

        return html

    def _get_detailed_connection_info(self):
        """Get detailed connection information from MCP client"""
        # This is a placeholder - in a real implementation, you'd query the MCP client for details
        # Example return: {'protocol_version': '1.0', 'latency': '15ms', 'data_format': 'JSON'}
        return {}

    def _get_active_connections(self):
        """Get list of active connections to the MCP server"""
        # This is a placeholder - in a real implementation, you'd query the MCP server for connections
        # Example return: [{'client_ip': '127.0.0.1', 'client_port': 12345, 'type': 'WebSocket'}]
        return []

    def _show_settings(self):
        """Show settings dialog to configure server paths and client connection"""
        # Import locally to ensure Qt modules are available
        from PySide2 import QtCore, QtGui, QtWidgets

        # Create dialog
        dialog = QtWidgets.QDialog(FreeCADGui.getMainWindow())
        dialog.setWindowTitle("MCP Indicator Settings")
        dialog.setMinimumWidth(550)

        # Create layout
        layout = QtWidgets.QVBoxLayout()
        dialog.setLayout(layout)

        # Create tabs
        tabs = QtWidgets.QTabWidget()
        layout.addWidget(tabs)

        # ==== Repository Tab ====
        repo_tab = QtWidgets.QWidget()
        repo_layout = QtWidgets.QVBoxLayout()
        repo_tab.setLayout(repo_layout)

        # Label with description
        repo_desc_label = QtWidgets.QLabel(
            "<b>MCP-FreeCAD Repository Path:</b> Root directory of the mcp-freecad repository.\n"
            "Set this path to automatically configure server paths for both FreeCAD and MCP servers.\n"
            "This simplifies configuration by only requiring you to specify the repository location once."
        )
        repo_desc_label.setWordWrap(True)
        repo_layout.addWidget(repo_desc_label)

        # Add Repository path field with browse button
        repo_path_layout = QtWidgets.QHBoxLayout()
        repo_layout.addLayout(repo_path_layout)

        # Label for repository path
        repo_path_label = QtWidgets.QLabel("Repository Path:")
        repo_path_layout.addWidget(repo_path_label)

        # Text field for repository path
        self.repo_path_field = QtWidgets.QLineEdit()
        self.repo_path_field.setText(self.REPO_PATH)
        self.repo_path_field.setPlaceholderText("e.g., /home/user/Git/mcp-freecad")
        repo_path_layout.addWidget(self.repo_path_field)

        # Browse button for repository
        repo_browse_button = QtWidgets.QPushButton("Browse...")
        repo_browse_button.clicked.connect(self._browse_repo_path)
        repo_path_layout.addWidget(repo_browse_button)

        # Add Apply button to update paths based on repo path
        apply_button = QtWidgets.QPushButton("Auto-configure Server Paths")
        apply_button.clicked.connect(lambda: self._apply_repo_path(self.repo_path_field.text()))
        repo_layout.addWidget(apply_button)

        # Add note about what happens when applying
        apply_note = QtWidgets.QLabel(
            "<i>Note: The 'Auto-configure' button will:</i>\n"
            "- Set the Socket Server path to <repo>/freecad_server.py\n"
            "- Set the MCP Server path to <repo>/start_mcp_server.sh\n"
            "- Create start_mcp_server.sh if needed to use either:\n"
            "  • A virtual environment (.venv or mcp_venv) if found\n"
            "  • The FreeCAD AppImage executable (squashfs-root/AppRun) if available\n"
            "  • The FreeCAD AppImage Python as fallback"
        )
        apply_note.setWordWrap(True)
        repo_layout.addWidget(apply_note)

        repo_layout.addStretch() # Push elements to top

        # ==== MCP Server Tab ====
        mcp_server_tab = QtWidgets.QWidget()
        mcp_server_layout = QtWidgets.QVBoxLayout()
        mcp_server_tab.setLayout(mcp_server_layout)

        # Label with description
        mcp_desc_label = QtWidgets.QLabel(
            "<b>MCP Server (freecad_mcp_server.py):</b> Implements the Model Context Protocol.\n"
            "This is the main server AI assistants connect to. Set the path here to enable\n"
            "Start/Stop/Restart controls from within FreeCAD."
        )
        mcp_desc_label.setWordWrap(True)
        mcp_server_layout.addWidget(mcp_desc_label)

        # Add MCP path field with browse button
        mcp_path_layout = QtWidgets.QHBoxLayout()
        mcp_server_layout.addLayout(mcp_path_layout)

        # Label for MCP server path
        mcp_path_label = QtWidgets.QLabel("MCP Server Script Path:")
        mcp_path_layout.addWidget(mcp_path_label)

        # Text field for MCP path
        self.mcp_path_field = QtWidgets.QLineEdit()
        self.mcp_path_field.setText(self.MCP_SERVER_SCRIPT_PATH)
        mcp_path_layout.addWidget(self.mcp_path_field)

        # Browse button for MCP server
        mcp_browse_button = QtWidgets.QPushButton("Browse...")
        mcp_browse_button.clicked.connect(self._browse_mcp_server_path)
        mcp_path_layout.addWidget(mcp_browse_button)

        # MCP Server configuration file
        config_layout = QtWidgets.QHBoxLayout()
        mcp_server_layout.addLayout(config_layout)

        config_label = QtWidgets.QLabel("MCP Server Config File (Optional, passed via --config):")
        config_layout.addWidget(config_label)

        self.config_field = QtWidgets.QLineEdit()
        self.config_field.setPlaceholderText("Default: config.json in script directory")
        self.config_field.setText(self.MCP_SERVER_CONFIG)
        config_layout.addWidget(self.config_field)

        config_browse_button = QtWidgets.QPushButton("Browse...")
        config_browse_button.clicked.connect(self._browse_config_path)
        config_layout.addWidget(config_browse_button)

        mcp_server_layout.addStretch() # Push elements to top

        # ==== Client Tab ====
        client_tab = QtWidgets.QWidget()
        client_layout = QtWidgets.QVBoxLayout()
        client_tab.setLayout(client_layout)

        # Label with description
        client_desc_label = QtWidgets.QLabel(
            "<b>Client Connection Settings:</b> Used by this addon to check the MCP Server status."
        )
        client_desc_label.setWordWrap(True)
        client_layout.addWidget(client_desc_label)

        # MCP Server Host
        host_layout = QtWidgets.QHBoxLayout()
        client_layout.addLayout(host_layout)

        host_label = QtWidgets.QLabel("MCP Server Host:")
        host_layout.addWidget(host_label)

        self.host_field = QtWidgets.QLineEdit()
        self.host_field.setText(self.MCP_SERVER_HOST)
        host_layout.addWidget(self.host_field)

        # MCP Server Port
        port_layout = QtWidgets.QHBoxLayout()
        client_layout.addLayout(port_layout)

        port_label = QtWidgets.QLabel("MCP Server Port:")
        port_layout.addWidget(port_label)

        self.port_field = QtWidgets.QSpinBox()
        self.port_field.setMinimum(1)
        self.port_field.setMaximum(65535)
        self.port_field.setValue(self.MCP_SERVER_PORT)
        port_layout.addWidget(self.port_field)

        client_layout.addStretch()

        # ==== FreeCAD Server (Legacy) Tab ====
        freecad_server_tab = QtWidgets.QWidget()
        freecad_server_layout = QtWidgets.QVBoxLayout()
        freecad_server_tab.setLayout(freecad_server_layout)

        # Label with description
        desc_label = QtWidgets.QLabel(
            "<b>Socket Server (freecad_server.py):</b> Legacy socket server that runs inside FreeCAD.\n"
            "Only needed if using the older 'server' connection method in the MCP Server config.\n"
            "The recommended AppImage/Launcher method does <b>not</b> use this."
        )
        desc_label.setWordWrap(True)
        freecad_server_layout.addWidget(desc_label)

        # Add path field with browse button
        path_layout = QtWidgets.QHBoxLayout()
        freecad_server_layout.addLayout(path_layout)

        # Label for server path
        path_label = QtWidgets.QLabel("Socket Server Script Path:")
        path_layout.addWidget(path_label)

        # Text field for path
        self.path_field = QtWidgets.QLineEdit()
        self.path_field.setText(self.SERVER_SCRIPT_PATH)
        path_layout.addWidget(self.path_field)

        # Browse button
        browse_button = QtWidgets.QPushButton("Browse...")
        browse_button.clicked.connect(self._browse_server_path)
        path_layout.addWidget(browse_button)

        freecad_server_layout.addStretch() # Push elements to top

        # Add tabs to the tab widget
        tabs.addTab(repo_tab, "Repository Path")
        tabs.addTab(mcp_server_tab, "MCP Server Controls")
        tabs.addTab(client_tab, "Client Status Check")
        tabs.addTab(freecad_server_tab, "Socket Server (Legacy)")

        # Set Repository tab as the default selected tab
        tabs.setCurrentIndex(0)

        # Add button box
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        # Show dialog and process result
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            # Save the repository path
            new_repo_path = self.repo_path_field.text()
            if new_repo_path != self.REPO_PATH:
                self.REPO_PATH = new_repo_path
                self.params.SetString("RepoPath", new_repo_path)
                # Update paths based on new repo if needed
                self._update_script_paths_from_repo()

            # Save the legacy FreeCAD server path
            new_path = self.path_field.text()
            self.SERVER_SCRIPT_PATH = new_path
            self.params.SetString("ServerScriptPath", new_path)

            # Save the MCP server path
            new_mcp_path = self.mcp_path_field.text()
            self.MCP_SERVER_SCRIPT_PATH = new_mcp_path
            self.params.SetString("MCPServerScriptPath", new_mcp_path)

            # Save server config
            new_config = self.config_field.text()
            self.MCP_SERVER_CONFIG = new_config
            self.params.SetString("MCPServerConfig", new_config)

            # Save client settings
            new_host = self.host_field.text()
            self.MCP_SERVER_HOST = new_host
            self.params.SetString("MCPServerHost", new_host)

            new_port = self.port_field.value()
            self.MCP_SERVER_PORT = new_port
            self.params.SetInt("MCPServerPort", new_port)

            FreeCAD.Console.PrintMessage(f"MCP settings updated\n")

            # Update UI based on new settings
            self._update_action_states()
            self._check_status()

    def _browse_repo_path(self):
        """Open file dialog to select repository directory"""
        from PySide2 import QtWidgets

        # Start in the directory of the current path, or home dir if empty
        start_dir = (
            self.REPO_PATH
            if self.REPO_PATH
            else os.path.expanduser("~")
        )

        # Open directory dialog
        dir_path = QtWidgets.QFileDialog.getExistingDirectory(
            FreeCADGui.getMainWindow(),
            "Select MCP-FreeCAD Repository Directory",
            start_dir,
            QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontResolveSymlinks
        )

        if dir_path:
            self.repo_path_field.setText(dir_path)

    def _apply_repo_path(self, repo_path):
        """Apply the repository path and update script paths automatically"""
        if not repo_path or not os.path.isdir(repo_path):
            from PySide2 import QtWidgets
            QtWidgets.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Invalid Repository Path",
                "Please select a valid directory for the MCP-FreeCAD repository."
            )
            return

        # Store the old paths for comparison
        old_server_path = self.SERVER_SCRIPT_PATH
        old_mcp_path = self.MCP_SERVER_SCRIPT_PATH

        # Temporarily set the repo path
        self.REPO_PATH = repo_path

        # Call the function to update paths
        self._update_script_paths_from_repo()

        # Update UI fields to reflect any changes
        self.path_field.setText(self.SERVER_SCRIPT_PATH)
        self.mcp_path_field.setText(self.MCP_SERVER_SCRIPT_PATH)

        # Show results message
        from PySide2 import QtWidgets
        changes = []
        if old_server_path != self.SERVER_SCRIPT_PATH:
            changes.append(f"Socket Server path updated to: {self.SERVER_SCRIPT_PATH}")
        if old_mcp_path != self.MCP_SERVER_SCRIPT_PATH:
            changes.append(f"MCP Server path updated to: {self.MCP_SERVER_SCRIPT_PATH}")

        if changes:
            QtWidgets.QMessageBox.information(
                FreeCADGui.getMainWindow(),
                "Paths Updated",
                "The following paths were automatically configured:\n\n" + "\n".join(changes)
            )
        else:
            QtWidgets.QMessageBox.information(
                FreeCADGui.getMainWindow(),
                "No Changes",
                "No path changes were needed. The paths are already set correctly."
            )

    def _browse_server_path(self):
        """Open file dialog to select server script"""
        from PySide2 import QtWidgets

        # Start in the directory of the current path, or home dir if empty
        start_dir = (
            os.path.dirname(self.SERVER_SCRIPT_PATH)
            if self.SERVER_SCRIPT_PATH
            else os.path.expanduser("~")
        )

        # Open file dialog
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            FreeCADGui.getMainWindow(),
            "Select FreeCAD Server Script",
            start_dir,
            "Python Scripts (*.py);;All Files (*.*)",
        )

        if file_path:
            self.path_field.setText(file_path)

    def _browse_mcp_server_path(self):
        """Open file dialog to select MCP server script"""
        from PySide2 import QtWidgets

        # Start in the directory of the current path, or home dir if empty
        start_dir = (
            os.path.dirname(self.MCP_SERVER_SCRIPT_PATH)
            if self.MCP_SERVER_SCRIPT_PATH
            else os.path.expanduser("~")
        )

        # Open file dialog
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            FreeCADGui.getMainWindow(),
            "Select MCP Server Script",
            start_dir,
            "Python Scripts (*.py);;All Files (*.*)",
        )

        if file_path:
            self.mcp_path_field.setText(file_path)

    def _browse_config_path(self):
        """Open file dialog to select server config file"""
        from PySide2 import QtWidgets

        # Start in the directory of the current path, or home dir if empty
        start_dir = (
            os.path.dirname(self.MCP_SERVER_CONFIG)
            if self.MCP_SERVER_CONFIG
            else os.path.expanduser("~")
        )

        # Open file dialog
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            FreeCADGui.getMainWindow(),
            "Select MCP Server Config File",
            start_dir,
            "JSON Files (*.json);;All Files (*.*)",
        )

        if file_path:
            self.config_field.setText(file_path)

    def _update_indicator_icon(self):
        """Update the indicator icon based on connection status"""
        if not self._control_button:
            return

        # Ensure QtGui is imported
        from PySide2 import QtCore, QtGui

        # Create the icon based on connection status
        if self._connection_status:
            # Connected - green circle
            pixmap = QtGui.QPixmap(16, 16)
            pixmap.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter(pixmap)
            painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
            painter.setBrush(QtGui.QBrush(QtGui.QColor(0, 200, 0)))  # Green
            painter.setPen(QtGui.QPen(QtGui.QColor(0, 100, 0), 1))  # Dark green border
            painter.drawEllipse(2, 2, 12, 12)
            painter.end()
        else:
            # Disconnected - red circle
            pixmap = QtGui.QPixmap(16, 16)
            pixmap.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter(pixmap)
            painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
            painter.setBrush(QtGui.QBrush(QtGui.QColor(200, 0, 0)))  # Red
            painter.setPen(QtGui.QPen(QtGui.QColor(100, 0, 0), 1))  # Dark red border
            painter.drawEllipse(2, 2, 12, 12)
            painter.end()

        # Set the icon
        self._control_button.setIcon(QtGui.QIcon(pixmap))

        # Update tooltip
        self._update_tooltip()

    def _update_freecad_server_icon(self):
        """Update the FreeCAD server status icon based on server running status"""
        if not self._freecad_server_status_button:
            return

        # Ensure QtGui is imported
        from PySide2 import QtCore, QtGui

        # Create the icon based on server status
        if self._freecad_server_running:
            # Running - blue circle with 'FC' text
            pixmap = QtGui.QPixmap(16, 16)
            pixmap.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter(pixmap)
            painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
            painter.setBrush(QtGui.QBrush(QtGui.QColor(0, 100, 200)))  # Blue
            painter.setPen(QtGui.QPen(QtGui.QColor(0, 50, 100), 1))  # Dark blue border
            painter.drawEllipse(2, 2, 12, 12)

            # Add FC text
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255)))
            font = QtGui.QFont()
            font.setPixelSize(7)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(QtCore.QRect(2, 2, 12, 12), QtCore.Qt.AlignCenter, "FC")
            painter.end()
        else:
            # Stopped - orange circle with 'FC' text
            pixmap = QtGui.QPixmap(16, 16)
            pixmap.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter(pixmap)
            painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
            painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 165, 0)))  # Orange
            painter.setPen(QtGui.QPen(QtGui.QColor(200, 120, 0), 1))  # Dark orange border
            painter.drawEllipse(2, 2, 12, 12)

            # Add FC text
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255)))
            font = QtGui.QFont()
            font.setPixelSize(7)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(QtCore.QRect(2, 2, 12, 12), QtCore.Qt.AlignCenter, "FC")
            painter.end()

        # Set the icon
        self._freecad_server_status_button.setIcon(QtGui.QIcon(pixmap))

        # Update tooltip
        self._update_tooltip()

    def _update_mcp_server_icon(self):
        """Update the MCP server status icon based on server running status"""
        if not self._mcp_server_status_button:
            return

        # Ensure QtGui is imported
        from PySide2 import QtCore, QtGui

        # Create the icon based on server status
        if self._mcp_server_running:
            # Running - green circle with 'MCP' text
            pixmap = QtGui.QPixmap(16, 16)
            pixmap.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter(pixmap)
            painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
            painter.setBrush(QtGui.QBrush(QtGui.QColor(0, 180, 0)))  # Green
            painter.setPen(QtGui.QPen(QtGui.QColor(0, 100, 0), 1))  # Dark green border
            painter.drawEllipse(2, 2, 12, 12)

            # Add MCP text
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255)))
            font = QtGui.QFont()
            font.setPixelSize(6)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(QtCore.QRect(2, 2, 12, 12), QtCore.Qt.AlignCenter, "MCP")
            painter.end()
        else:
            # Stopped - red circle with 'MCP' text
            pixmap = QtGui.QPixmap(16, 16)
            pixmap.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter(pixmap)
            painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
            painter.setBrush(QtGui.QBrush(QtGui.QColor(200, 0, 0)))  # Red
            painter.setPen(QtGui.QPen(QtGui.QColor(100, 0, 0), 1))  # Dark red border
            painter.drawEllipse(2, 2, 12, 12)

            # Add MCP text
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255)))
            font = QtGui.QFont()
            font.setPixelSize(6)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(QtCore.QRect(2, 2, 12, 12), QtCore.Qt.AlignCenter, "MCP")
            painter.end()

        # Set the icon
        self._mcp_server_status_button.setIcon(QtGui.QIcon(pixmap))

        # Update tooltip
        self._update_tooltip()

    def _update_tooltip(self):
        """Update tooltips for all indicator buttons"""
        # Client indicator tooltip
        client_status = "Connected" if self._connection_status else "Disconnected"
        self._control_button.setToolTip(f"MCP Client: {client_status}")

        # FreeCAD Server indicator tooltip
        freecad_server_status = "Running" if self._freecad_server_running else "Stopped"
        self._freecad_server_status_button.setToolTip(f"FreeCAD Server (Socket): {freecad_server_status}")

        # MCP Server indicator tooltip
        mcp_server_status = "Running" if self._mcp_server_running else "Stopped"
        self._mcp_server_status_button.setToolTip(f"MCP Server: {mcp_server_status}")

    def _check_status(self):
        """Check all server and connection statuses"""
        try:
            # Check FreeCAD server status
            prev_freecad_status = self._freecad_server_running
            self._freecad_server_running = self._is_freecad_server_running()

            # Check MCP server status
            prev_mcp_status = self._mcp_server_running
            self._mcp_server_running = self._is_mcp_server_running()

            # Then check MCP connection
            prev_connection_status = self._connection_status
            self._connection_status = self._check_connection()

            # Update connection details if either server is running
            if self._freecad_server_running or self._mcp_server_running:
                try:
                    self._update_connection_details()
                except Exception as e:
                    FreeCAD.Console.PrintWarning(f"Failed to update connection details: {str(e)}\n")

            # Update icons if status changed
            if prev_freecad_status != self._freecad_server_running:
                self._update_freecad_server_icon()

            if prev_mcp_status != self._mcp_server_running:
                self._update_mcp_server_icon()

            if prev_connection_status != self._connection_status:
                self._update_indicator_icon()

            # Update all tooltips
            self._update_tooltip()

            # Update action states based on server status
            self._update_action_states()

        except Exception as e:
            FreeCAD.Console.PrintError(f"Error in status check: {str(e)}\n")

    def _update_connection_details(self):
        """Update connection details by querying the server API"""
        try:
            # Local import to ensure time module is available in this scope
            import time

            # If the FreeCAD server is running, update its details
            if self._freecad_server_running:
                # Only calculate uptime if we started it internally
                if hasattr(self, '_freecad_server_start_time') and self._freecad_server_process:
                    freecad_uptime = int(time.time() - self._freecad_server_start_time)
                    self._connection_details['freecad_server_uptime'] = freecad_uptime
                else:
                    # Indicate it was likely started externally
                    self._connection_details['freecad_server_uptime'] = "Externally Started"
            else:
                # Clear uptime if server stopped
                 if 'freecad_server_uptime' in self._connection_details:
                      del self._connection_details['freecad_server_uptime']
                 if hasattr(self, '_freecad_server_start_time'):
                     delattr(self, '_freecad_server_start_time')

            # If the MCP server is running, update its details
            if self._mcp_server_running:
                # Only calculate uptime if we started it internally
                if hasattr(self, '_mcp_server_start_time') and self._mcp_server_process:
                    mcp_uptime = int(time.time() - self._mcp_server_start_time)
                    self._connection_details["server_uptime"] = mcp_uptime
                else:
                    # Indicate it was likely started externally
                    self._connection_details["server_uptime"] = "Externally Started"

                # Set other connection details (some might need actual querying)
                self._connection_details.update({
                    "type": "WebSocket" if self._connection_status else "None",
                    "client_port": 9000 if self._connection_status else 0, # Example port
                    "server_port": self.MCP_SERVER_PORT,
                    "connected_clients": 1 if self._connection_status else 0, # Placeholder
                })
            else:
                # Reset MCP connection details when server is not running
                self._connection_details.update({
                    "type": "Unknown",
                    "client_port": 0,
                    "server_port": 0,
                    "connected_clients": 0,
                    "server_uptime": 0,
                })
                if hasattr(self, '_mcp_server_start_time'):
                    delattr(self, '_mcp_server_start_time')

        except Exception as e:
            FreeCAD.Console.PrintError(f"Error updating connection details: {str(e)}\n")

    def _is_freecad_server_running(self):
        """Check if the FreeCAD server process is running (internally or externally)."""
        # First check if we have an internal process running
        internal_running = False
        try:
            internal_running = bool(
                self._freecad_server_process is not None and self._freecad_server_process.poll() is None
            )
        except Exception:
            internal_running = False

        if internal_running:
            return True

        # If no internal process, check if the port (default 12345) is in use
        try:
            import socket # <-- Import socket inside the function
            # Assume default host/port for external check for now
            # TODO: Make this configurable if needed
            host = "localhost"
            port = 12345

            # Method 1: Try connecting
            connect_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            connect_socket.settimeout(0.5)
            result = connect_socket.connect_ex((host, port))
            connect_socket.close()
            port_in_use = (result == 0)

            # Method 2: Try binding (more reliable check if service exists but isn't accepting)
            if not port_in_use:
                try:
                    bind_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    bind_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    bind_socket.bind((host, port))
                    bind_socket.close()
                    port_in_use = False # Bind successful means port is NOT in use
                except socket.error:
                    port_in_use = True # Bind failed means port IS in use

            if port_in_use and self._freecad_server_process is None:
                 import time
                 if not hasattr(self, '_freecad_server_start_time'):
                     self._freecad_server_start_time = time.time() # Record approximate start
                     FreeCAD.Console.PrintMessage("External FreeCAD server detected on port {}. Not starting new instance.\n".format(port))

            return port_in_use
        except Exception as e:
            FreeCAD.Console.PrintWarning(f"Error checking FreeCAD server port: {e}\n")
            return False

    def _is_mcp_server_running(self):
        """
        Check if the MCP server process is running.

        This enhanced method checks two things:
        1. If we have an internal process handle that's running
        2. If the MCP server port is already in use by an external process

        This prevents duplicate MCP servers from being started,
        whether from FreeCAD itself or from external scripts like start_mcp_server.sh.
        """
        import socket

        # First check if we have an internal process running
        internal_running = False
        try:
            internal_running = bool(
                self._mcp_server_process is not None and self._mcp_server_process.poll() is None
            )
        except Exception:
            internal_running = False

        # If we have an internal process, we know it's running
        if internal_running:
            return True

        # If no internal process, check if the port is in use
        try:
            # Method 1: Try connecting to the port
            # This works if a service is already listening and accepting connections
            connect_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            connect_socket.settimeout(0.5)  # Short timeout to avoid hanging
            result = connect_socket.connect_ex((self.MCP_SERVER_HOST, self.MCP_SERVER_PORT))
            connect_socket.close()

            # If connection was successful, port is in use
            port_in_use = (result == 0)

            # Method 2: Try binding to the port
            # This works even if the service isn't accepting connections yet
            if not port_in_use:
                try:
                    bind_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    bind_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    bind_socket.bind((self.MCP_SERVER_HOST, self.MCP_SERVER_PORT))
                    bind_socket.close()
                    # If we successfully bound to the port, it's not in use
                    port_in_use = False
                except socket.error:
                    # If we couldn't bind to the port, it's in use
                    port_in_use = True

            # If we detect that the port is in use but we don't have a process handle,
            # update our UI state accordingly
            if port_in_use and self._mcp_server_process is None:
                # Record approximate start time for uptime display
                import time
                if not hasattr(self, '_mcp_server_start_time'):
                    self._mcp_server_start_time = time.time()
                    FreeCAD.Console.PrintMessage("External MCP server detected on port {}. Not starting a new instance.\n".format(
                        self.MCP_SERVER_PORT
                    ))

            return port_in_use
        except Exception as e:
            FreeCAD.Console.PrintWarning(f"Error checking if MCP server port is in use: {e}\n")
            return False

    def _update_action_states(self):
        """Enable/disable actions based on server states."""
        try:
            # Check if FreeCAD server is running
            freecad_running = bool(self._freecad_server_running)
            # Check if MCP server is running
            mcp_running = bool(self._mcp_server_running)

            # Check if paths are set
            freecad_path_exists = bool(self.SERVER_SCRIPT_PATH)
            mcp_path_exists = bool(self.MCP_SERVER_SCRIPT_PATH)

            # Update FreeCAD server actions
            if self._start_freecad_action:  # Check if actions exist
                # Only enable start if path is set and server not running
                self._start_freecad_action.setEnabled(not freecad_running and freecad_path_exists)

            if self._start_freecad_connect_action:
                # Only enable connect start if path is set and server not running
                self._start_freecad_connect_action.setEnabled(not freecad_running and freecad_path_exists)

            if self._stop_freecad_action:
                # Enable stop if server is running
                self._stop_freecad_action.setEnabled(freecad_running)

            if self._restart_freecad_action:
                # Only enable restart if path is set and server is running
                self._restart_freecad_action.setEnabled(freecad_running and freecad_path_exists)

            # Update MCP server actions
            if self._start_mcp_action:
                # Only enable start if path is set and server not running
                self._start_mcp_action.setEnabled(not mcp_running and mcp_path_exists)

            if self._stop_mcp_action:
                # Enable stop if server is running
                self._stop_mcp_action.setEnabled(mcp_running)

            if self._restart_mcp_action:
                # Only enable restart if path is set and server is running
                self._restart_mcp_action.setEnabled(mcp_running and mcp_path_exists)

            # Update all tooltips
            self._update_tooltip()

        except Exception as e:
            FreeCAD.Console.PrintError(f"Error updating action states: {str(e)}\n")

    def _check_connection(self):
        """Check MCP connection status"""
        # This is a placeholder - in a real implementation, you'd
        # actually check the connection to the MCP server
        # For now, we'll consider it connected if either server is running
        return self._freecad_server_running or self._mcp_server_running

    def _load_indicator_config(self):
        """Load config.json, primarily to find the Python path."""
        # Import json locally to ensure it's available in this scope
        import json

        config_path = self.MCP_SERVER_CONFIG
        if not config_path and self.MCP_SERVER_SCRIPT_PATH:
            config_path = os.path.join(os.path.dirname(self.MCP_SERVER_SCRIPT_PATH), "config.json")
        elif not config_path:
            # Fallback if MCP server script path is also not set
            config_path = "config.json"

        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config_data = json.load(f)
                    return config_data
            except Exception as e:
                FreeCAD.Console.PrintWarning(f"Failed to load config {config_path}: {str(e)}\n")
        return {}

    def _get_python_executable(self):
        """Find an appropriate Python executable to use for the server process.

        Priority:
        1. Python from squashfs-root/usr/bin/python
        2. Virtual environment in the repository
        3. System Python
        4. FreeCAD embedded Python as fallback
        """
        import sys
        import shutil
        import os

        python_candidates = []

        # First, check if we have access to squashfs-root/usr/bin/python
        squashfs_python = None
        if self.REPO_PATH and os.path.exists(self.REPO_PATH):
            # Check for squashfs-root in the repository directory
            squashfs_python = os.path.join(self.REPO_PATH, "squashfs-root", "usr", "bin", "python")
            if os.path.exists(squashfs_python):
                python_candidates.append(squashfs_python)
                FreeCAD.Console.PrintMessage(f"Found FreeCAD AppImage Python: {squashfs_python}\n")

        # Then check if we have a virtual environment in the repository
        if self.REPO_PATH and os.path.exists(self.REPO_PATH):
            # Check for standard virtual environment name (.venv)
            venv_python = os.path.join(self.REPO_PATH, ".venv", "bin", "python")
            if os.path.exists(venv_python):
                python_candidates.append(venv_python)

            # Check for mcp_venv directory (alternative venv name)
            mcp_venv_python = os.path.join(self.REPO_PATH, "mcp_venv", "bin", "python")
            if os.path.exists(mcp_venv_python):
                python_candidates.append(mcp_venv_python)

        # Then check if we can find a system Python
        python_candidates.extend([
            # System Python
            shutil.which("python3"),
            shutil.which("python"),
            "/usr/bin/python3",
            # FreeCAD's embedded Python as a fallback
            sys.executable,
        ])

        # Find the first valid executable
        python_exec = None
        for candidate in python_candidates:
            if candidate and os.path.exists(candidate):
                python_exec = candidate
                break

        if python_exec:
            FreeCAD.Console.PrintMessage(f"Using Python executable: {python_exec}\n")
        else:
            FreeCAD.Console.PrintError("Could not find a Python executable\n")

        return python_exec

    def _start_freecad_server(self, connect_mode=False):
        """Start the freecad_server.py script."""
        # Local imports to ensure modules are available in this scope
        import os
        import socket
        import subprocess
        import sys
        import time

        from PySide2 import QtCore, QtWidgets

        if self._is_freecad_server_running():
            FreeCAD.Console.PrintMessage("FreeCAD Server is already running.\n")
            return

        if not self.SERVER_SCRIPT_PATH or not os.path.exists(self.SERVER_SCRIPT_PATH):
            FreeCAD.Console.PrintError(
                f"FreeCAD Server script not found: {self.SERVER_SCRIPT_PATH}\n"
            )
            return

        # Check for wrapper script existence
        server_dir = os.path.dirname(self.SERVER_SCRIPT_PATH)
        wrapper_script = os.path.join(server_dir, "run-freecad-server.sh")
        use_wrapper = os.path.exists(wrapper_script) and os.access(
            wrapper_script, os.X_OK
        )

        if use_wrapper:
            FreeCAD.Console.PrintMessage(f"Found wrapper script: {wrapper_script}\n")
        else:
            # Find the Python executable using the new helper method
            python_exec = self._get_python_executable()
            if not python_exec:
                QtWidgets.QMessageBox.critical(
                    FreeCADGui.getMainWindow(), "Error", "Could not find Python executable."
                )
                return

        try:
            # Check if port is already in use (default port 12345)
            port_in_use = False
            try:
                # Try to bind to the port to see if it's available
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind(("localhost", 12345))
                s.close()
            except socket.error:
                port_in_use = True

            # If port is in use, ask user what to do
            if port_in_use:
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Warning)
                msg.setText("The FreeCAD server port (12345) is already in use.")
                msg.setInformativeText(
                    "There may be another FreeCAD server running. What would you like to do?"
                )
                killButton = msg.addButton(
                    "Kill Existing && Start New", QtWidgets.QMessageBox.ActionRole
                )
                cancelButton = msg.addButton(QtWidgets.QMessageBox.Cancel)
                msg.setDefaultButton(killButton)
                msg.exec_()

                if msg.clickedButton() == killButton:
                    # Try to kill existing processes
                    try:
                        # Find processes using the freecad_server.py script
                        cmd = f'pkill -f "python.*{os.path.basename(self.SERVER_SCRIPT_PATH)}"'
                        subprocess.run(cmd, shell=True)
                        FreeCAD.Console.PrintMessage(
                            "Killed existing FreeCAD server processes.\n"
                        )
                        # Wait a moment for the process to die and port to be freed
                        time.sleep(1)
                    except Exception as e:
                        FreeCAD.Console.PrintError(
                            f"Failed to kill existing processes: {str(e)}\n"
                        )
                        return
                else:
                    # User cancelled
                    return

            # Determine if we should run in connect mode
            mode_text = "connect mode" if connect_mode else "standalone mode"

            # Create log files in the same directory as the server script
            log_dir = os.path.dirname(self.SERVER_SCRIPT_PATH)
            stdout_log = os.path.join(log_dir, "freecad_server_stdout.log")
            stderr_log = os.path.join(log_dir, "freecad_server_stderr.log")

            # Create a modified environment with a variable to prevent GUI
            env = dict(os.environ)
            env["FREECAD_NO_GUI"] = "1"  # Custom environment variable to signal no GUI
            env["PYTHONUNBUFFERED"] = "1"  # Ensure Python output is unbuffered

            # Clear PYTHONHOME to avoid conflicts with FreeCAD AppImage Python
            if "PYTHONHOME" in env:
                del env["PYTHONHOME"]
                FreeCAD.Console.PrintMessage("Cleared PYTHONHOME environment variable to avoid conflicts\n")

            # Set up command with appropriate arguments
            if use_wrapper:
                FreeCAD.Console.PrintMessage(
                    f"Starting FreeCAD server using wrapper script: {wrapper_script}\n"
                )
                server_cmd = [wrapper_script]
                # The wrapper script already includes --connect, so only add it if not in connect mode
                if not connect_mode:
                    server_cmd.append("--no-connect")
            else:
                FreeCAD.Console.PrintMessage(
                    f"Starting Socket server in {mode_text}: {self.SERVER_SCRIPT_PATH} with Python: {python_exec}...\n"
                )
                server_cmd = [python_exec, self.SERVER_SCRIPT_PATH]
                # Add connect flag if requested
                if connect_mode:
                    server_cmd.append("--connect")

            # Open log files
            with open(stdout_log, "w") as out, open(stderr_log, "w") as err:
                # Start the server process
                self._freecad_server_process = subprocess.Popen(
                    server_cmd,
                    stdout=out,
                    stderr=err,
                    bufsize=1,
                    env=env,
                    cwd=os.path.dirname(self.SERVER_SCRIPT_PATH),
                )

            FreeCAD.Console.PrintMessage(
                f"FreeCAD server started with PID: {self._freecad_server_process.pid}\n"
            )
            FreeCAD.Console.PrintMessage(f"Stdout log: {stdout_log}\n")
            FreeCAD.Console.PrintMessage(f"Stderr log: {stderr_log}\n")

            # Give the server a moment to start up
            QtCore.QTimer.singleShot(1000, self._check_status)

        except Exception as e:
            FreeCAD.Console.PrintError(f"Failed to start FreeCAD server: {str(e)}\n")
            self._freecad_server_process = None

        self._update_action_states()

    def _stop_freecad_server(self):
        """Stop the running freecad_server.py script."""
        # Local import to ensure module is available in this scope
        import subprocess

        if not self._is_freecad_server_running():
            FreeCAD.Console.PrintMessage("FreeCAD Server is not running.\n")
            return

        try:
            FreeCAD.Console.PrintMessage(
                f"Stopping FreeCAD server (PID: {self._freecad_server_process.pid})...\n"
            )
            self._freecad_server_process.terminate()
            try:
                self._freecad_server_process.wait(timeout=2)
                FreeCAD.Console.PrintMessage("FreeCAD server stopped.\n")
            except subprocess.TimeoutExpired:
                FreeCAD.Console.PrintWarning(
                    "FreeCAD server did not terminate gracefully, killing...\n"
                )
                self._freecad_server_process.kill()
                self._freecad_server_process.wait()
                FreeCAD.Console.PrintMessage("FreeCAD server killed.\n")
        except Exception as e:
            FreeCAD.Console.PrintError(f"Failed to stop FreeCAD server: {str(e)}\n")

        self._freecad_server_process = None
        # Reset server start time
        if hasattr(self, '_freecad_server_start_time'):
            delattr(self, '_freecad_server_start_time')
        self._update_action_states()

    def _restart_freecad_server(self):
        """Restart the freecad_server.py script."""
        # Local import to ensure Qt module is available in this scope
        from PySide2 import QtCore

        FreeCAD.Console.PrintMessage("Restarting FreeCAD server...\n")
        if self._is_freecad_server_running():
            self._stop_freecad_server()
            QtCore.QTimer.singleShot(500, self._start_freecad_server)
        else:
            self._start_freecad_server()

    def _start_mcp_server(self):
        """Start the freecad_mcp_server.py script."""
        # ---> Add check if server is already running using the dedicated function
        if self._is_mcp_server_running():
            FreeCAD.Console.PrintMessage("MCP Server is already running (checked via _is_mcp_server_running).\\n")
            self._update_indicator_state(server_running=True) # Ensure UI reflects the state
            return
        # <---------------------\

        # ---> Add local imports
        import socket
        import subprocess
        from PySide2 import QtCore # <-- Add this import
        # <---------------------
        if self._mcp_server_running:
            FreeCAD.Console.PrintWarning("MCP Server is already running.\n")
            return

        if not self.MCP_SERVER_SCRIPT_PATH or not os.path.exists(self.MCP_SERVER_SCRIPT_PATH):
            FreeCAD.Console.PrintError(
                f"MCP Server script not found: {self.MCP_SERVER_SCRIPT_PATH}\n"
            )
            return

        # Check if we can create a shell script for better venv handling
        if self.REPO_PATH and self.MCP_SERVER_SCRIPT_PATH.endswith('.py'):
            script_dir = os.path.dirname(self.MCP_SERVER_SCRIPT_PATH)
            shell_script_path = os.path.join(self.REPO_PATH, "scripts", "start_mcp_server.sh")

            # Create scripts directory if it doesn't exist
            scripts_dir = os.path.join(self.REPO_PATH, "scripts")
            if not os.path.exists(scripts_dir):
                os.makedirs(scripts_dir)

            # Always create/update the shell script if the MCP server script is in the repo
            if os.path.dirname(self.MCP_SERVER_SCRIPT_PATH) == self.REPO_PATH:
                # Check for virtual environments
                venv_found = False

                # Check for .venv directory (standard venv name)
                venv_path = os.path.join(self.REPO_PATH, ".venv")
                if os.path.isdir(venv_path):
                    try:
                        FreeCAD.Console.PrintMessage(f"Creating shell script to use .venv virtual environment...\n")
                        with open(shell_script_path, 'w') as f:
                            f.write('#!/bin/bash\n\n')
                            f.write('# Get the directory where this script is located\n')
                            f.write('SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"\n\n')
                            f.write('# Activate the virtual environment\n')
                            f.write('source "$SCRIPT_DIR/.venv/bin/activate"\n\n')
                            f.write('# Start the MCP server with debug mode\n')
                            f.write('python "$SCRIPT_DIR/freecad_mcp_server.py" --debug "$@"\n')

                        # Make the script executable
                        os.chmod(shell_script_path, 0o755)

                        # Update the path
                        self.MCP_SERVER_SCRIPT_PATH = shell_script_path
                        self.params.SetString("MCPServerScriptPath", shell_script_path)
                        FreeCAD.Console.PrintMessage(f"Created and will use {shell_script_path}\n")
                        venv_found = True
                    except Exception as e:
                        FreeCAD.Console.PrintError(f"Error creating shell script: {str(e)}\n")

                # Check for mcp_venv directory (alternative name)
                if not venv_found:
                    mcp_venv_path = os.path.join(self.REPO_PATH, "mcp_venv")
                    if os.path.isdir(mcp_venv_path):
                        try:
                            FreeCAD.Console.PrintMessage(f"Creating shell script to use mcp_venv virtual environment...\n")
                            with open(shell_script_path, 'w') as f:
                                f.write('#!/bin/bash\n\n')
                                f.write('# Get the directory where this script is located\n')
                                f.write('SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"\n\n')
                                f.write('# Activate the virtual environment\n')
                                f.write('source "$SCRIPT_DIR/mcp_venv/bin/activate"\n\n')
                                f.write('# Start the MCP server with debug mode\n')
                                f.write('python "$SCRIPT_DIR/freecad_mcp_server.py" --debug "$@"\n')

                            # Make the script executable
                            os.chmod(shell_script_path, 0o755)

                            # Update the path
                            self.MCP_SERVER_SCRIPT_PATH = shell_script_path
                            self.params.SetString("MCPServerScriptPath", shell_script_path)
                            FreeCAD.Console.PrintMessage(f"Created and will use {shell_script_path}\n")
                            venv_found = True
                        except Exception as e:
                            FreeCAD.Console.PrintError(f"Error creating shell script: {str(e)}\n")

                # Check for squashfs-root Python if no venv was found
                if not venv_found:
                    squashfs_python = os.path.join(self.REPO_PATH, "squashfs-root", "usr", "bin", "python")
                    squashfs_apprun = os.path.join(self.REPO_PATH, "squashfs-root", "AppRun")
                    if os.path.exists(squashfs_apprun):
                        # Create a script that uses AppRun with --console and --run-script flags
                        with open(shell_script_path, 'w') as f:
                            f.write('#!/bin/bash\n\n')
                            f.write('# Get the directory where this script is located\n')
                            f.write('SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"\n\n')
                            f.write('# Use FreeCAD AppRun to execute the script with proper environment\n')
                            f.write('# Force X11 backend to avoid Wayland issues\n')
                            f.write('export QT_QPA_PLATFORM=xcb\n\n')
                            f.write('# Pass script path directly without --console flag\n')
                            f.write('"$SCRIPT_DIR/squashfs-root/AppRun" "$SCRIPT_DIR/freecad_mcp_server.py" -- "$@"\n')

                        # Make the script executable
                        os.chmod(shell_script_path, 0o755)

                        # Update the MCP server path to use the shell script
                        self.MCP_SERVER_SCRIPT_PATH = shell_script_path
                        self.params.SetString("MCPServerScriptPath", shell_script_path)
                        FreeCAD.Console.PrintMessage(f"Created start_mcp_server.sh script to use squashfs-root/AppRun\n")
                    elif os.path.exists(squashfs_python):
                        # Fall back to direct Python use if AppRun isn't available
                        with open(shell_script_path, 'w') as f:
                            f.write('#!/bin/bash\n\n')
                            f.write('# Get the directory where this script is located\n')
                            f.write('SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"\n\n')
                            f.write('# Use extracted Python interpreter\n')
                            f.write('"$SCRIPT_DIR/squashfs-root/usr/bin/python" "$SCRIPT_DIR/freecad_mcp_server.py" --debug "$@"\n')

                        # Make the script executable
                        os.chmod(shell_script_path, 0o755)

                        # Update the MCP server path to use the shell script
                        self.MCP_SERVER_SCRIPT_PATH = shell_script_path
                        self.params.SetString("MCPServerScriptPath", shell_script_path)
                        FreeCAD.Console.PrintMessage(f"Created start_mcp_server.sh script to use extracted Python\n")

        # Try to kill any existing MCP server processes
        try:
            # Find processes using the freecad_mcp_server.py script
            cmd = f'pkill -f "python.*{os.path.basename(self.MCP_SERVER_SCRIPT_PATH)}"'
            subprocess.run(cmd, shell=True)
            FreeCAD.Console.PrintMessage("Killed existing MCP server processes.\n")
            # Wait a moment for the processes to die
            time.sleep(1)
        except Exception as e:
            FreeCAD.Console.PrintWarning(f"Warning when killing existing processes: {str(e)}\n")

        # Find the Python executable using the new helper method
        python_exec = self._get_python_executable()
        if not python_exec:
            QtWidgets.QMessageBox.critical(
                FreeCADGui.getMainWindow(), "Error", "Could not find Python executable."
            )
            return

        try:
            # Check if port is already in use
            port_in_use = False
            try:
                # Try to bind to the port to see if it's available
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind((self.MCP_SERVER_HOST, self.MCP_SERVER_PORT))
                s.close()
            except socket.error:
                port_in_use = True

            # If port is in use, ask user what to do
            if port_in_use:
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Warning)
                msg.setText(f"The MCP server port ({self.MCP_SERVER_PORT}) is already in use.")
                msg.setInformativeText(
                    "There may be another MCP server running. What would you like to do?"
                )
                killButton = msg.addButton(
                    "Kill Existing && Start New", QtWidgets.QMessageBox.ActionRole
                )
                cancelButton = msg.addButton(QtWidgets.QMessageBox.Cancel)
                msg.setDefaultButton(killButton)
                msg.exec_()

                if msg.clickedButton() == killButton:
                    # Try to kill existing processes
                    try:
                        # Find processes using the freecad_mcp_server.py script
                        cmd = f'pkill -f "python.*{os.path.basename(self.MCP_SERVER_SCRIPT_PATH)}"'
                        subprocess.run(cmd, shell=True)
                        FreeCAD.Console.PrintMessage(
                            "Killed existing MCP server processes.\n"
                        )
                        # Wait a moment for the process to die and port to be freed
                        time.sleep(1)
                    except Exception as e:
                        FreeCAD.Console.PrintError(
                            f"Failed to kill existing processes: {str(e)}\n"
                        )
                        return
                else:
                    # User cancelled
                    return

            # Create log files in the same directory as the server script
            log_dir = os.path.dirname(self.MCP_SERVER_SCRIPT_PATH)
            stdout_log = os.path.join(log_dir, "freecad_mcp_server_stdout.log")
            stderr_log = os.path.join(log_dir, "freecad_mcp_server_stderr.log")

            # Create a modified environment
            env = dict(os.environ)
            env["PYTHONUNBUFFERED"] = "1"  # Ensure Python output is unbuffered

            # Clear PYTHONHOME to avoid conflicts with FreeCAD AppImage Python
            if "PYTHONHOME" in env:
                del env["PYTHONHOME"]
                FreeCAD.Console.PrintMessage("Cleared PYTHONHOME environment variable to avoid conflicts\n")

            # Set up command with appropriate arguments
            server_cmd = []

            # Check if we're dealing with a shell script or Python script
            is_shell_script = self.MCP_SERVER_SCRIPT_PATH.endswith('.sh')

            if is_shell_script:
                # For shell scripts, run them directly
                server_cmd = [self.MCP_SERVER_SCRIPT_PATH]
            else:
                # For Python scripts, use the Python executable
                python_exec = self._get_python_executable()
                if not python_exec:
                    QtWidgets.QMessageBox.critical(
                        FreeCADGui.getMainWindow(), "Error", "Could not find Python executable."
                    )
                    return
                server_cmd = [python_exec, self.MCP_SERVER_SCRIPT_PATH]

            # Add config file if specified
            if self.MCP_SERVER_CONFIG:
                server_cmd.extend(["--config", self.MCP_SERVER_CONFIG])

            # Add port if not default
            if self.MCP_SERVER_PORT != 8000:
                server_cmd.extend(["--port", str(self.MCP_SERVER_PORT)])

            # Add debug mode for more verbose output
            server_cmd.append("--debug")

            # Print the exact command for debugging
            FreeCAD.Console.PrintMessage(f"MCP server command: {' '.join(server_cmd)}\n")

            FreeCAD.Console.PrintMessage(
                f"Starting MCP server: {self.MCP_SERVER_SCRIPT_PATH} with Python: {python_exec}...\n"
            )

            # Open log files
            with open(stdout_log, "w") as out, open(stderr_log, "w") as err:
                # Start the server process
                self._mcp_server_process = subprocess.Popen(
                    server_cmd,
                    stdout=out,
                    stderr=err,
                    bufsize=1,
                    env=env,
                    cwd=os.path.dirname(self.MCP_SERVER_SCRIPT_PATH),
                )

            FreeCAD.Console.PrintMessage(
                f"MCP server started with PID: {self._mcp_server_process.pid}\n"
            )
            FreeCAD.Console.PrintMessage(f"Stdout log: {stdout_log}\n")
            FreeCAD.Console.PrintMessage(f"Stderr log: {stderr_log}\n")

            # Give the server a moment to start up
            QtCore.QTimer.singleShot(1000, self._check_status)

        except Exception as e:
            FreeCAD.Console.PrintError(f"Failed to start MCP server: {str(e)}\n")

            # Show a more helpful error message if 'no module named mcp' is in the error
            if 'module' in str(e).lower() and 'mcp' in str(e).lower():
                FreeCAD.Console.PrintError("It appears the MCP Python package is not installed in the Python environment being used.\n")

                # Check if we have squashfs-root Python
                squashfs_python = None
                if self.REPO_PATH and os.path.exists(self.REPO_PATH):
                    squashfs_python = os.path.join(self.REPO_PATH, "squashfs-root", "usr", "bin", "python")

                if squashfs_python and os.path.exists(squashfs_python):
                    FreeCAD.Console.PrintError(f"Try creating a virtual environment using the FreeCAD AppImage Python:\n")
                    FreeCAD.Console.PrintError(f"1. {squashfs_python} -m venv {self.REPO_PATH}/mcp_venv\n")
                    FreeCAD.Console.PrintError(f"2. source {self.REPO_PATH}/mcp_venv/bin/activate\n")
                    FreeCAD.Console.PrintError(f"3. pip install mcp\n")
                    FreeCAD.Console.PrintError(f"Then go to Settings and click Auto-configure Server Paths\n")
                else:
                    FreeCAD.Console.PrintError("You need to install the MCP package in your Python environment:\n")
                    FreeCAD.Console.PrintError("1. Create a virtual environment: python -m venv mcp_venv\n")
                    FreeCAD.Console.PrintError("2. Activate it: source mcp_venv/bin/activate\n")
                    FreeCAD.Console.PrintError("3. Install MCP: pip install mcp\n")

            self._mcp_server_process = None

        self._update_action_states()

    def _stop_mcp_server(self):
        """Stop the running freecad_mcp_server.py script."""
        stopped_count = 0
        stopped_pids = set()

        if self._mcp_server_process:
            process_to_stop = self._mcp_server_process
            pid_stopped = process_to_stop.pid # Get PID before trying to stop
            if self._stop_process(process_to_stop):
                stopped_count += 1
                stopped_pids.add(pid_stopped)
            self._mcp_server_process = None

        # Also try finding and stopping any other lingering processes
        lingering_processes = self._find_mcp_processes()
        if lingering_processes:
            FreeCAD.Console.PrintMessage(f"Found {len(lingering_processes)} potential lingering MCP server processes. Attempting to stop...\n")
            for proc_or_pid in lingering_processes:
                 # Get the current PID to check against the set of stopped PIDs
                 current_pid = -1
                 if hasattr(proc_or_pid, 'pid'):
                     current_pid = proc_or_pid.pid
                 elif isinstance(proc_or_pid, int):
                     current_pid = proc_or_pid

                 if current_pid > 0 and current_pid not in stopped_pids:
                    if self._stop_process(proc_or_pid):
                        stopped_count += 1
                        stopped_pids.add(current_pid)

        if stopped_count > 0:
             FreeCAD.Console.PrintMessage(f"Stopped {stopped_count} MCP server process(es).\n")
        else:
             FreeCAD.Console.PrintWarning("Could not find running MCP Server process to stop.\n")

        self._mcp_server_running = False
        self._update_mcp_server_icon()
        self._update_action_states()
        self._check_status()

    def _restart_mcp_server(self):
        """Restart the freecad_mcp_server.py script."""
        FreeCAD.Console.PrintMessage("Restarting MCP Server...\n")
        self._stop_mcp_server()
        # Add a small delay before restarting
        QtCore.QTimer.singleShot(500, self._start_mcp_server)

    def _install_dependencies(self):
        """Install required dependencies for the MCP modules."""
        import subprocess
        import sys

        from PySide2 import QtWidgets

        # Create dialog
        dialog = QtWidgets.QDialog(FreeCADGui.getMainWindow())
        dialog.setWindowTitle("Installing Dependencies")
        dialog.setMinimumWidth(500)

        # Layout
        layout = QtWidgets.QVBoxLayout()
        dialog.setLayout(layout)

        # Status message
        status_label = QtWidgets.QLabel("Select installation method")
        layout.addWidget(status_label)

        # Installation options
        options_group = QtWidgets.QGroupBox("Installation Options")
        options_layout = QtWidgets.QVBoxLayout()
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Normal install option
        normal_radio = QtWidgets.QRadioButton("Standard installation")
        normal_radio.setChecked(True)
        options_layout.addWidget(normal_radio)

        # Break system packages option
        break_system_radio = QtWidgets.QRadioButton(
            "Use --break-system-packages flag (may be required on Debian/Ubuntu)"
        )
        options_layout.addWidget(break_system_radio)

        # Required packages
        packages = ["fastapi", "uvicorn", "websockets", "aiofiles", "pydantic"]
        packages_label = QtWidgets.QLabel(f"Packages to install: {', '.join(packages)}")
        layout.addWidget(packages_label)

        # Log area
        log_text = QtWidgets.QTextEdit()
        log_text.setReadOnly(True)
        log_text.setMinimumHeight(200)
        layout.addWidget(log_text)

        # Instructions for manual installation
        instructions = (
            "<b>Alternative Installation Methods:</b><br>"
            "<ol>"
            "<li>Create a virtual environment:<br>"
            "<code>python3 -m venv ~/venv-freecad</code><br>"
            "<code>~/venv-freecad/bin/pip install fastapi uvicorn websockets aiofiles pydantic</code><br>"
            "Then run your server with: <code>~/venv-freecad/bin/python /path/to/freecad_server.py</code></li>"
            "<li>Use system packages:<br>"
            "<code>sudo apt install python3-fastapi python3-uvicorn python3-websockets python3-aiofiles python3-pydantic</code></li>"
            "</ol>"
        )
        help_label = QtWidgets.QLabel(instructions)
        help_label.setWordWrap(True)
        help_label.setOpenExternalLinks(True)  # Allow links to open
        layout.addWidget(help_label)

        # Button box
        button_box = QtWidgets.QDialogButtonBox()
        install_btn = button_box.addButton(
            "Install Packages", QtWidgets.QDialogButtonBox.AcceptRole
        )
        cancel_btn = button_box.addButton(QtWidgets.QDialogButtonBox.Cancel)
        layout.addWidget(button_box)

        # Connect signals
        cancel_btn.clicked.connect(dialog.reject)

        # Connect install button with the options
        install_btn.clicked.connect(
            lambda: self._run_pip_install(
                packages,
                log_text,
                status_label,
                install_btn,
                break_system_packages=break_system_radio.isChecked(),
            )
        )

        # Show dialog
        dialog.exec_()

    def _run_pip_install(
        self, packages, log_text, status_label, install_btn, break_system_packages=False
    ):
        """Run pip install with appropriate flags"""
        import os
        import subprocess
        import sys

        # Disable the install button to prevent multiple clicks
        install_btn.setEnabled(False)
        status_label.setText("Installing packages... (this may take a while)")

        # Find the actual Python executable, not FreeCAD
        # Check for FreeCAD's Python first
        freecad_python = None
        freecad_bin_dir = os.path.dirname(sys.executable)

        # Try to find Python in FreeCAD's directory
        for name in ["python3", "python"]:
            potential_path = os.path.join(freecad_bin_dir, name)
            if os.path.exists(potential_path):
                freecad_python = potential_path
                break

        # System Python executable locations
        python_candidates = [
            freecad_python,  # Try FreeCAD's Python first if found
            "/usr/bin/python3",
            "/usr/local/bin/python3",
            "/usr/bin/python",
            os.path.join(sys.prefix, "bin", "python3"),
            # Add more if needed
        ]

        # Filter out None entries
        python_candidates = [p for p in python_candidates if p]

        python_exec = None
        for candidate in python_candidates:
            if candidate and os.path.exists(candidate):
                python_exec = candidate
                break

        if not python_exec:
            log_text.append(
                "❌ Error: Could not find Python executable. Please install packages manually."
            )
            status_label.setText("Installation failed - Python not found")
            install_btn.setEnabled(True)
            return

        # Log info
        log_text.append(f"Using Python: {python_exec}\n")
        log_text.append("Starting installation...\n")

        try:
            # Prepare installation command
            cmd = [python_exec, "-m", "pip", "install", "--user"]

            # Add break-system-packages flag if requested
            if break_system_packages:
                cmd.append("--break-system-packages")
                log_text.append("⚠️ Using --break-system-packages flag\n")

            # Add packages
            cmd.extend(packages)

            log_text.append(f"Running command: {' '.join(cmd)}\n")

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )

            # Show the output
            log_text.append(result.stdout)

            if result.returncode == 0:
                status_label.setText(
                    "Packages installed successfully! Please restart FreeCAD."
                )
                log_text.append("\n✅ Installation successful!")
                log_text.append("\nPlease restart FreeCAD for changes to take effect.")
            else:
                # Check if this is an externally managed environment error
                if "externally-managed-environment" in result.stdout:
                    status_label.setText("Externally managed Python detected")
                    log_text.append(
                        "\n⚠️ Your Python is externally managed by your OS package manager."
                    )
                    log_text.append(
                        "\nPlease use a virtual environment or system packages."
                    )

                    # Try direct pip if not tried yet and not using break-system-packages
                    if not break_system_packages:
                        log_text.append(
                            "\n➡️ Try using the --break-system-packages option in the dialog."
                        )
                        log_text.append(
                            "\nOr follow the manual installation instructions below."
                        )
                    else:
                        log_text.append(
                            "\n❌ Installation with --break-system-packages also failed."
                        )
                        log_text.append(
                            "\nPlease follow the manual installation instructions below."
                        )
                else:
                    # Generic failure
                    status_label.setText("Installation failed. See log for details.")
                    log_text.append("\n❌ Installation failed for an unknown reason.")

                # Provide instructions for manual installation
                self._show_manual_install_instructions(log_text)

        except Exception as e:
            log_text.append(f"\nError during installation: {str(e)}")
            status_label.setText("Installation failed due to an error.")
            self._show_manual_install_instructions(log_text)

        # Re-enable the install button
        install_btn.setEnabled(True)

    def _show_manual_install_instructions(self, log_text):
        """Show instructions for manual installation"""
        log_text.append("\n\n--- MANUAL INSTALLATION INSTRUCTIONS ---")
        log_text.append("\nOption 1: Create a virtual environment:")
        log_text.append("python3 -m venv ~/venv-freecad")
        log_text.append("source ~/venv-freecad/bin/activate")
        log_text.append("pip install fastapi uvicorn websockets aiofiles pydantic")
        log_text.append("\nThen update your server path to point to:")
        log_text.append("~/venv-freecad/bin/python /path/to/freecad_server.py")

        log_text.append("\n\nOption 2: Install system packages (Ubuntu/Debian):")
        log_text.append(
            "sudo apt install python3-fastapi python3-uvicorn python3-websockets python3-aiofiles python3-pydantic"
        )

    def _find_mcp_processes(self):
        """Find processes running the MCP server script."""
        processes = []
        try:
            # Use psutil if available for cross-platform compatibility
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline'] and self.MCP_SERVER_SCRIPT_PATH in " ".join(proc.info['cmdline']):
                        processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass # Process might have died or we don't have permission
        except ImportError:
            FreeCAD.Console.PrintWarning("psutil not installed. Falling back to platform-specific process finding.\\n")
            if sys.platform == 'win32':
                try:
                    # Note: WMIC might require admin privileges for full details
                    # Construct command as list to avoid shell quoting issues
                    path_pattern = self.MCP_SERVER_SCRIPT_PATH.replace('\\\\', '\\\\\\\\') # Escape backslashes for WMIC LIKE
                    cmd_parts = [
                        'WMIC', 'PROCESS', 'WHERE',
                        f'CommandLine LIKE "%{path_pattern}%"', # Use % wildcard for LIKE
                        'GET', 'ProcessId,CommandLine', # Comma without space might be safer
                        '/FORMAT:LIST'
                    ]
                    # Using shell=False is generally safer
                    result = subprocess.run(cmd_parts, capture_output=True, text=True, check=True, shell=False, startupinfo=None) # Ensure startupinfo is None or correctly configured if needed, avoid CREATE_NO_WINDOW with shell=False

                    # Very basic parsing - assumes simple structure
                    pid = None
                    for line in result.stdout.splitlines():
                        line = line.strip()
                        if not line: continue # Skip empty lines
                        if '=' in line:
                            key, value = line.split('=', 1)
                            if key == "ProcessId":
                                try:
                                    pid = int(value)
                                except ValueError:
                                    pid = None # Reset if ProcessId is not an int
                            elif key == "CommandLine" and pid is not None:
                                # Check if the command line actually contains the script path
                                # This adds an extra check because LIKE might be too broad
                                if self.MCP_SERVER_SCRIPT_PATH in value:
                                    processes.append(pid) # Store PID directly for now
                                pid = None # Reset pid after processing a CommandLine entry
                except FileNotFoundError:
                     FreeCAD.Console.PrintError("Error: WMIC command not found. Is it in the system PATH?\\n")
                except subprocess.CalledProcessError as e:
                     FreeCAD.Console.PrintError(f"Error finding process with WMIC (return code {e.returncode}): {e.stderr or e.stdout}\\n")
                except Exception as e:
                    FreeCAD.Console.PrintError(f"Error finding process with WMIC: {e}\\n")
            else: # Linux/macOS
                try:
                    # Be careful with escaping special characters if script path has them
                    # pgrep -f should be reasonably safe
                    cmd = ['pgrep', '-f', self.MCP_SERVER_SCRIPT_PATH]
                    result = subprocess.run(cmd, capture_output=True, text=True, shell=False) # Use shell=False
                    if result.returncode == 0:
                        pids = [int(pid) for pid in result.stdout.splitlines() if pid.isdigit()]
                        processes.extend(pids) # Store PIDs directly for now
                    # No error print needed if returncode is non-zero (means not found)
                except FileNotFoundError:
                    FreeCAD.Console.PrintError("Error: pgrep command not found. Is it in the system PATH?\\n")
                except Exception as e:
                    FreeCAD.Console.PrintError(f"Error finding process with pgrep: {e}\\n")
        return processes

    def _stop_process(self, process_or_pid):
        """Stop a process given a psutil process object or a PID."""
        pid_to_stop = -1
        try:
            if hasattr(process_or_pid, 'terminate') and callable(process_or_pid.terminate):
                # Assume psutil process object
                pid_to_stop = process_or_pid.pid
                FreeCAD.Console.PrintMessage(f"Terminating MCP Server process (PID: {pid_to_stop})...\n")
                process_or_pid.terminate()
                process_or_pid.wait(timeout=3) # Wait for graceful termination
                if process_or_pid.is_running():
                    FreeCAD.Console.PrintWarning(f"Process {pid_to_stop} did not terminate gracefully, killing...\n")
                    process_or_pid.kill()
                    process_or_pid.wait(timeout=1)
            elif isinstance(process_or_pid, int) and process_or_pid > 0:
                # Assume PID
                pid_to_stop = process_or_pid
                FreeCAD.Console.PrintMessage(f"Terminating MCP Server process (PID: {pid_to_stop})...\n")
                if sys.platform == 'win32':
                    subprocess.run(["taskkill", "/F", "/PID", str(pid_to_stop)], check=True, capture_output=True)
                else:
                    os.kill(pid_to_stop, signal.SIGTERM) # Send TERM signal first
                    time.sleep(1) # Give it a moment
                    try:
                        os.kill(pid_to_stop, 0) # Check if process exists
                        # If it still exists, force kill
                        FreeCAD.Console.PrintWarning(f"Process {pid_to_stop} did not terminate gracefully, killing...\n")
                        os.kill(pid_to_stop, signal.SIGKILL)
                    except OSError:
                        pass # Process already terminated
            else:
                FreeCAD.Console.PrintError(f"Invalid process object or PID for stopping: {process_or_pid}\n")
                return False

            FreeCAD.Console.PrintMessage(f"Process {pid_to_stop} terminated.\n")
            return True

        except Exception as e:
            FreeCAD.Console.PrintError(f"Error stopping process {pid_to_stop}: {str(e)}\n")
            # Attempt force kill if termination failed
            try:
                if pid_to_stop > 0:
                    if hasattr(process_or_pid, 'kill') and callable(process_or_pid.kill):
                        process_or_pid.kill()
                    elif isinstance(process_or_pid, int):
                         if sys.platform == 'win32':
                            subprocess.run(["taskkill", "/F", "/PID", str(pid_to_stop)], check=False, capture_output=True)
                         else:
                             os.kill(pid_to_stop, signal.SIGKILL)
                    FreeCAD.Console.PrintWarning(f"Force killed process {pid_to_stop}.\n")
            except Exception as kill_e:
                 FreeCAD.Console.PrintError(f"Error force killing process {pid_to_stop}: {kill_e}\n")
            return False

    def _handle_log_file_change(self, path):
        """Handle changes detected specifically to the log file."""
        if path == self._mcp_log_file_path:
            FreeCAD.Console.PrintMessage(f"MCP Log Watcher: Detected change in {path}. Reloading content.\\n")
            self._load_mcp_log_content()
        # If the watcher reports the file changed, ensure it's still being watched
        if self._mcp_log_watcher and path not in self._mcp_log_watcher.files() and os.path.exists(path):
             self._mcp_log_watcher.addPath(path)

    def _handle_log_directory_change(self, path):
        """Handle changes detected in the log file's directory."""
        log_dir = os.path.dirname(self._mcp_log_file_path)
        if path == log_dir:
            FreeCAD.Console.PrintMessage(f"MCP Log Watcher: Detected change in directory {path}. Checking log file.\\n")
            # Check if the log file now exists and add it to watcher if it wasn't already
            if os.path.exists(self._mcp_log_file_path) and self._mcp_log_watcher:
                 if self._mcp_log_file_path not in self._mcp_log_watcher.files():
                      self._mcp_log_watcher.addPath(self._mcp_log_file_path)
                      FreeCAD.Console.PrintMessage(f"MCP Log Watcher: Log file created. Added {self._mcp_log_file_path} to watcher.\\n")
            # Reload content regardless, as the file might have appeared or disappeared
            self._load_mcp_log_content()


    def _load_mcp_log_content(self, max_lines=500):
        """Load (tail) content from the MCP log file into the text edit."""
        if not self._mcp_log_text_edit or not self._mcp_log_file_path:
            if self._mcp_log_text_edit:
                 self._mcp_log_text_edit.setPlainText("(Log viewer not configured - missing log file path)")
            return

        log_content = f"--- Log file: {self._mcp_log_file_path} ---\\n"
        log_content += f"--- Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')} ---\\n\\n"
        try:
            if os.path.exists(self._mcp_log_file_path):
                # Try reading the last N lines efficiently if possible (platform dependent?)
                # Simple approach: read all, take last N
                with open(self._mcp_log_file_path, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()
                    log_lines = lines[-max_lines:] # Get the last max_lines
                    if len(lines) > max_lines:
                         log_content += f"(Showing last {max_lines} lines of {len(lines)})\\n\\n"
                    log_content += "".join(log_lines)

                # Ensure watcher is watching the file if it exists now
                if self._mcp_log_watcher and self._mcp_log_file_path not in self._mcp_log_watcher.files():
                     self._mcp_log_watcher.addPath(self._mcp_log_file_path)

            else:
                log_content += "(Log file does not exist)"
                 # Ensure watcher is watching the directory if file doesn't exist
                log_dir = os.path.dirname(self._mcp_log_file_path)
                if self._mcp_log_watcher and os.path.exists(log_dir) and log_dir not in self._mcp_log_watcher.directories():
                    self._mcp_log_watcher.addPath(log_dir)


        except Exception as e:
            error_msg = f"Error reading log file: {type(e).__name__} - {e}"
            log_content += f"\\n\\n{error_msg}"
            FreeCAD.Console.PrintError(f"Error reading MCP log file {self._mcp_log_file_path}: {error_msg}\\n")

        current_text = self._mcp_log_text_edit.toPlainText()
        # Only update if content changed to avoid unnecessary UI updates/scroll jumps
        if current_text != log_content:
            self._mcp_log_text_edit.setPlainText(log_content)
            # Scroll to the bottom after updating
            scrollbar = self._mcp_log_text_edit.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def _toggle_mcp_log_viewer(self, checked):
        """Show or hide the MCP log dock widget."""
        if self._mcp_log_dock_widget:
            self._mcp_log_dock_widget.setVisible(checked)
            if checked:
                 # Ensure content is fresh when shown
                 self._load_mcp_log_content()
                 # Bring dock to front / raise it
                 self._mcp_log_dock_widget.raise_()


    # Add __del__ for potential cleanup (might need refinement)
    def __del__(self):
        try:
            FreeCAD.Console.PrintMessage("MCPIndicatorWorkbench cleaning up...\\n")
            if self._mcp_log_watcher:
                # Disconnect signals safely
                try: self._mcp_log_watcher.fileChanged.disconnect(self._handle_log_file_change)
                except RuntimeError: pass # Signal already disconnected
                try: self._mcp_log_watcher.directoryChanged.disconnect(self._handle_log_directory_change)
                except RuntimeError: pass # Signal already disconnected

                paths_to_remove = self._mcp_log_watcher.files() + self._mcp_log_watcher.directories()
                if paths_to_remove:
                     self._mcp_log_watcher.removePaths(paths_to_remove)
                self._mcp_log_watcher.deleteLater() # Schedule for deletion

            mw = FreeCADGui.getMainWindow()
            if mw and self._mcp_log_dock_widget:
                 mw.removeDockWidget(self._mcp_log_dock_widget)
                 self._mcp_log_dock_widget.deleteLater() # Schedule for deletion

        except Exception as e:
             FreeCAD.Console.PrintError(f"Error during MCPIndicatorWorkbench cleanup: {type(e).__name__} - {e}\\n")

FreeCADGui.addWorkbench(MCPIndicatorWorkbench())
