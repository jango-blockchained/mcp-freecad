import inspect
import os
import socket
import subprocess
import sys
import time
import json
import shutil

import FreeCAD
import FreeCADGui
from PySide2 import QtCore, QtGui, QtWidgets

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
                    os.path.join(project_root, "freecad_mcp_server.py"),
                    os.path.join(
                        os.path.expanduser("~"),
                        "Git",
                        "mcp-freecad",
                        "freecad_mcp_server.py",
                    ),
                    "/usr/local/bin/freecad_mcp_server.py",
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
        mcp_shell_path = os.path.join(self.REPO_PATH, "start_mcp_server.sh")
        mcp_py_path = os.path.join(self.REPO_PATH, "freecad_mcp_server.py")

        if os.path.exists(mcp_shell_path):
            self.MCP_SERVER_SCRIPT_PATH = mcp_shell_path
            self.params.SetString("MCPServerScriptPath", mcp_shell_path)
        elif os.path.exists(mcp_py_path):
            self.MCP_SERVER_SCRIPT_PATH = mcp_py_path
            self.params.SetString("MCPServerScriptPath", mcp_py_path)

        # Create start_mcp_server.sh script if it doesn't exist
        if os.path.exists(mcp_py_path) and not os.path.exists(mcp_shell_path):
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
                        f.write('python "$SCRIPT_DIR/freecad_mcp_server.py" --debug "$@"\n')

                    # Make the script executable
                    os.chmod(mcp_shell_path, 0o755)

                    # Update the MCP server path to use the shell script
                    self.MCP_SERVER_SCRIPT_PATH = mcp_shell_path
                    self.params.SetString("MCPServerScriptPath", mcp_shell_path)
                    FreeCAD.Console.PrintMessage(f"Created start_mcp_server.sh script to use {venv_name} virtual environment\n")
                else:
                    # Check for squashfs-root Python
                    squashfs_python = os.path.join(self.REPO_PATH, "squashfs-root", "usr", "bin", "python")
                    if os.path.exists(squashfs_python):
                        # Create a script that uses squashfs-root Python directly
                        with open(mcp_shell_path, 'w') as f:
                            f.write('#!/bin/bash\n\n')
                            f.write('# Get the directory where this script is located\n')
                            f.write('SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"\n\n')
                            f.write('# Use FreeCAD AppImage Python directly\n')
                            f.write('"$SCRIPT_DIR/squashfs-root/usr/bin/python" "$SCRIPT_DIR/freecad_mcp_server.py" --debug "$@"\n')

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
        from PySide2 import QtCore, QtWidgets  # Add QtCore here

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
        """Generate HTML content for MCP server details"""
        server_status = "Running" if self._mcp_server_running else "Stopped"
        status_color = "green" if self._mcp_server_running else "red"

        html = f"""
        <h2>MCP Server Status</h2>
        <p>Status: <span style='color:{status_color};font-weight:bold;'>{server_status}</span></p>
        <p>Server Path: {self.MCP_SERVER_SCRIPT_PATH}</p>
        <p><strong>Server Type:</strong> MCP Protocol Server (freecad_mcp_server.py)</p>
        <p><strong>Purpose:</strong> Implements Model Context Protocol for AI assistants</p>
        """

        if self._mcp_server_running:
            html += f"""
            <p>Server Port: {self.MCP_SERVER_PORT}</p>
            <p>Connected Clients: {self._connection_details['connected_clients']}</p>
            <p>Uptime: {self._connection_details['server_uptime']} seconds</p>
            """

            if self.MCP_SERVER_CONFIG:
                html += f"<p>Config File: {self.MCP_SERVER_CONFIG}</p>"

            html += """
            <h3>Status</h3>
            <p>This server provides MCP functionality to AI assistants.</p>
            <p>It exposes tools and resources through the Model Context Protocol.</p>
            """

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
            "  • The FreeCAD AppImage Python (squashfs-root/usr/bin/python) if available"
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
                # Record uptime if not already tracked
                if not hasattr(self, '_freecad_server_start_time'):
                    self._freecad_server_start_time = time.time()

                # Calculate uptime
                freecad_uptime = int(time.time() - self._freecad_server_start_time)

                # Add to connection details
                self._connection_details['freecad_server_uptime'] = freecad_uptime

            # If the MCP server is running, update its details
            if self._mcp_server_running:
                # Record uptime if not already tracked
                if not hasattr(self, '_mcp_server_start_time'):
                    self._mcp_server_start_time = time.time()

                # Calculate uptime
                mcp_uptime = int(time.time() - self._mcp_server_start_time)

                # Set connection details
                self._connection_details.update({
                    "type": "WebSocket" if self._connection_status else "None",
                    "client_port": 9000 if self._connection_status else 0,
                    "server_port": self.MCP_SERVER_PORT,
                    "connected_clients": 1 if self._connection_status else 0,
                    "server_uptime": mcp_uptime,
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
        except Exception as e:
            FreeCAD.Console.PrintError(f"Error updating connection details: {str(e)}\n")

    def _is_freecad_server_running(self):
        """Check if the FreeCAD server process is running."""
        try:
            return bool(
                self._freecad_server_process is not None and self._freecad_server_process.poll() is None
            )
        except Exception:
            return False

    def _is_mcp_server_running(self):
        """Check if the MCP server process is running."""
        try:
            return bool(
                self._mcp_server_process is not None and self._mcp_server_process.poll() is None
            )
        except Exception:
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
        wrapper_script = os.path.join(server_dir, "run_freecad_server.sh")
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
        # Local imports to ensure modules are available in this scope
        import os
        import socket
        import subprocess
        import sys
        import time

        from PySide2 import QtCore, QtWidgets

        if self._is_mcp_server_running():
            FreeCAD.Console.PrintMessage("MCP Server is already running.\n")
            return

        if not self.MCP_SERVER_SCRIPT_PATH or not os.path.exists(self.MCP_SERVER_SCRIPT_PATH):
            FreeCAD.Console.PrintError(
                f"MCP Server script not found: {self.MCP_SERVER_SCRIPT_PATH}\n"
            )
            return

        # Check if we can create a shell script for better venv handling
        if self.REPO_PATH and self.MCP_SERVER_SCRIPT_PATH.endswith('.py'):
            script_dir = os.path.dirname(self.MCP_SERVER_SCRIPT_PATH)
            shell_script_path = os.path.join(script_dir, "start_mcp_server.sh")

            # Only create the shell script if it's within the repo directory
            if script_dir == self.REPO_PATH and not os.path.exists(shell_script_path):
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
                    if os.path.exists(squashfs_python):
                        try:
                            FreeCAD.Console.PrintMessage(f"Creating shell script to use squashfs-root Python...\n")
                            with open(shell_script_path, 'w') as f:
                                f.write('#!/bin/bash\n\n')
                                f.write('# Get the directory where this script is located\n')
                                f.write('SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"\n\n')
                                f.write('# Use FreeCAD AppImage Python directly\n')
                                f.write('"$SCRIPT_DIR/squashfs-root/usr/bin/python" "$SCRIPT_DIR/freecad_mcp_server.py" --debug "$@"\n')

                            # Make the script executable
                            os.chmod(shell_script_path, 0o755)

                            # Update the path
                            self.MCP_SERVER_SCRIPT_PATH = shell_script_path
                            self.params.SetString("MCPServerScriptPath", shell_script_path)
                            FreeCAD.Console.PrintMessage(f"Created and will use {shell_script_path} with squashfs-root Python\n")
                        except Exception as e:
                            FreeCAD.Console.PrintError(f"Error creating shell script: {str(e)}\n")

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
        # Local import to ensure module is available in this scope
        import subprocess

        if not self._is_mcp_server_running():
            FreeCAD.Console.PrintMessage("MCP Server is not running.\n")
            return

        try:
            FreeCAD.Console.PrintMessage(
                f"Stopping MCP server (PID: {self._mcp_server_process.pid})...\n"
            )
            self._mcp_server_process.terminate()
            try:
                self._mcp_server_process.wait(timeout=2)
                FreeCAD.Console.PrintMessage("MCP server stopped.\n")
            except subprocess.TimeoutExpired:
                FreeCAD.Console.PrintWarning(
                    "MCP server did not terminate gracefully, killing...\n"
                )
                self._mcp_server_process.kill()
                self._mcp_server_process.wait()
                FreeCAD.Console.PrintMessage("MCP server killed.\n")
        except Exception as e:
            FreeCAD.Console.PrintError(f"Failed to stop MCP server: {str(e)}\n")

        self._mcp_server_process = None
        # Reset server start time
        if hasattr(self, '_mcp_server_start_time'):
            delattr(self, '_mcp_server_start_time')
        self._update_action_states()

    def _restart_mcp_server(self):
        """Restart the freecad_mcp_server.py script."""
        # Local import to ensure Qt module is available in this scope
        from PySide2 import QtCore

        FreeCAD.Console.PrintMessage("Restarting MCP server...\n")
        if self._is_mcp_server_running():
            self._stop_mcp_server()
            QtCore.QTimer.singleShot(500, self._start_mcp_server)
        else:
            self._start_mcp_server()

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


FreeCADGui.addWorkbench(MCPIndicatorWorkbench())
