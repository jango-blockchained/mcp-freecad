import os
import time
import FreeCAD
import FreeCADGui
from PySide2 import QtCore, QtGui, QtWidgets
from PySide2.QtWidgets import QDockWidget, QTextEdit, QVBoxLayout, QPushButton, QWidget, QMenu, QAction
from PySide2.QtCore import QFileSystemWatcher, QTimer, QStandardPaths, Qt

class UIManager:
    """Manages UI elements for the MCP Indicator Workbench."""

    def __init__(self, config_manager, process_manager, status_checker, path_finder):
        """Initialize with the necessary manager instances."""
        self.config = config_manager
        self.process_manager = process_manager
        self.status_checker = status_checker
        self.path_finder = path_finder

        # UI elements
        self.control_button = None
        self.freecad_server_status_button = None
        self.mcp_server_status_button = None
        self.connection_info_dialog = None
        self.flow_visualization_action = None

        # Log viewer elements
        self.mcp_log_dock_widget = None
        self.mcp_log_text_edit = None
        self.mcp_log_watcher = None
        self.mcp_log_file_path = None
        self.show_mcp_log_action = None

        # Initialize log file path
        self._init_log_file_path()

    def _init_log_file_path(self):
        """Initialize the path to the MCP server log file."""
        mcp_script_path = self.config.get_mcp_server_script_path()
        if mcp_script_path and os.path.exists(os.path.dirname(mcp_script_path)):
            script_dir = os.path.dirname(mcp_script_path)
            # The log file is expected in a 'logs' subdirectory relative to the script's dir
            self.mcp_log_file_path = os.path.normpath(os.path.join(script_dir, "logs", "freecad_mcp_server.log"))
            FreeCAD.Console.PrintMessage(f"MCP Log Viewer: Target log file path: {self.mcp_log_file_path}\n")
        else:
            FreeCAD.Console.PrintWarning("MCP Log Viewer: MCP_SERVER_SCRIPT_PATH not set or invalid, log viewer will be disabled.\n")

    def setup_ui(self, workbench):
        """Set up all UI elements for the workbench."""
        self._create_status_buttons(workbench)
        self._create_menu_actions(workbench)
        self._setup_log_watcher()

    def _create_status_buttons(self, workbench):
        """Create status indicator buttons in the status bar."""
        mw = FreeCADGui.getMainWindow()
        if not mw:
            return

        statusbar = mw.statusBar()

        # Create MCP server status button
        self.mcp_server_status_button = QtWidgets.QToolButton()
        self.mcp_server_status_button.setAutoRaise(True)
        self.mcp_server_status_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.mcp_server_status_button.clicked.connect(lambda: self._show_mcp_server_info())
        statusbar.addPermanentWidget(self.mcp_server_status_button)

        # Create FreeCAD server status button
        self.freecad_server_status_button = QtWidgets.QToolButton()
        self.freecad_server_status_button.setAutoRaise(True)
        self.freecad_server_status_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.freecad_server_status_button.clicked.connect(lambda: self._show_freecad_server_info())
        statusbar.addPermanentWidget(self.freecad_server_status_button)

        # Create main indicator/control button
        self.control_button = QtWidgets.QToolButton()
        self.control_button.setAutoRaise(True)
        self.control_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.control_button.clicked.connect(lambda: self._show_connection_info())

        # Create control menu
        control_menu = QMenu(self.control_button)

        # MCP Server Controls
        mcp_menu = control_menu.addMenu("MCP Server")
        mcp_start_action = mcp_menu.addAction("Start")
        mcp_start_action.triggered.connect(lambda: self.process_manager.start_mcp_server())
        mcp_stop_action = mcp_menu.addAction("Stop")
        mcp_stop_action.triggered.connect(lambda: self.process_manager.stop_mcp_server())
        mcp_restart_action = mcp_menu.addAction("Restart")
        mcp_restart_action.triggered.connect(lambda: self.process_manager.restart_mcp_server())

        # FreeCAD Server Controls
        freecad_menu = control_menu.addMenu("Legacy Socket Server")
        freecad_start_action = freecad_menu.addAction("Start")
        freecad_start_action.triggered.connect(lambda: self.process_manager.start_freecad_server())
        freecad_stop_action = freecad_menu.addAction("Stop")
        freecad_stop_action.triggered.connect(lambda: self.process_manager.stop_freecad_server())
        freecad_restart_action = freecad_menu.addAction("Restart")
        freecad_restart_action.triggered.connect(lambda: self.process_manager.restart_freecad_server())

        # Settings and tools
        control_menu.addSeparator()
        settings_action = control_menu.addAction("Settings")
        settings_action.triggered.connect(self._show_settings)

        # Log viewer
        self.show_mcp_log_action = control_menu.addAction("Show MCP Log")
        self.show_mcp_log_action.setCheckable(True)
        self.show_mcp_log_action.triggered.connect(self._toggle_mcp_log_viewer)

        # Dependencies
        install_deps_action = control_menu.addAction("Install MCP Dependencies")
        # This will be connected to dependency_manager.install_dependencies

        # Set menu
        self.control_button.setMenu(control_menu)
        statusbar.addPermanentWidget(self.control_button)

        # Initialize button icons
        self._update_indicator_icon()
        self._update_freecad_server_icon()
        self._update_mcp_server_icon()

    def _create_menu_actions(self, workbench):
        """Create menu entries for the workbench."""
        # Create a list to store actions
        self.action_list = []

        # Connection Info
        connection_action = FreeCADGui.Action("Connection Info")
        connection_action.setStatusTip("Show MCP connection information")
        connection_action.triggered.connect(lambda: self._show_connection_info())
        self.action_list.append(connection_action)

        # MCP Server Info
        mcp_info_action = FreeCADGui.Action("MCP Server Info")
        mcp_info_action.setStatusTip("Show MCP server information")
        mcp_info_action.triggered.connect(lambda: self._show_mcp_server_info())
        self.action_list.append(mcp_info_action)

        # Socket Server Info
        socket_info_action = FreeCADGui.Action("Socket Server Info")
        socket_info_action.setStatusTip("Show legacy socket server information")
        socket_info_action.triggered.connect(lambda: self._show_freecad_server_info())
        self.action_list.append(socket_info_action)

        # Separator
        self.action_list.append("Separator")

        # MCP Server controls
        mcp_start_action = FreeCADGui.Action("Start MCP Server")
        mcp_start_action.setStatusTip("Start the MCP server")
        mcp_start_action.triggered.connect(lambda: self.process_manager.start_mcp_server())
        self.action_list.append(mcp_start_action)

        mcp_stop_action = FreeCADGui.Action("Stop MCP Server")
        mcp_stop_action.setStatusTip("Stop the MCP server")
        mcp_stop_action.triggered.connect(lambda: self.process_manager.stop_mcp_server())
        self.action_list.append(mcp_stop_action)

        mcp_restart_action = FreeCADGui.Action("Restart MCP Server")
        mcp_restart_action.setStatusTip("Restart the MCP server")
        mcp_restart_action.triggered.connect(lambda: self.process_manager.restart_mcp_server())
        self.action_list.append(mcp_restart_action)

        # Separator
        self.action_list.append("Separator")

        # Socket Server controls
        socket_start_action = FreeCADGui.Action("Start Socket Server")
        socket_start_action.setStatusTip("Start the legacy socket server")
        socket_start_action.triggered.connect(lambda: self.process_manager.start_freecad_server())
        self.action_list.append(socket_start_action)

        socket_stop_action = FreeCADGui.Action("Stop Socket Server")
        socket_stop_action.setStatusTip("Stop the legacy socket server")
        socket_stop_action.triggered.connect(lambda: self.process_manager.stop_freecad_server())
        self.action_list.append(socket_stop_action)

        socket_restart_action = FreeCADGui.Action("Restart Socket Server")
        socket_restart_action.setStatusTip("Restart the legacy socket server")
        socket_restart_action.triggered.connect(lambda: self.process_manager.restart_freecad_server())
        self.action_list.append(socket_restart_action)

        # Separator
        self.action_list.append("Separator")

        # Flow visualization
        self.flow_visualization_action = FreeCADGui.Action("Show Flow Visualization")
        self.flow_visualization_action.setStatusTip("Show MCP message flow visualization")
        self.flow_visualization_action.triggered.connect(lambda: self._show_flow_visualization())
        self.action_list.append(self.flow_visualization_action)

        # Settings
        settings_action = FreeCADGui.Action("Settings")
        settings_action.setStatusTip("Configure MCP indicator settings")
        settings_action.triggered.connect(self._show_settings)
        self.action_list.append(settings_action)

        # Install dependencies
        install_deps_action = FreeCADGui.Action("Install MCP Dependencies")
        install_deps_action.setStatusTip("Install Python dependencies for MCP server")
        # This will be connected to dependency_manager.install_dependencies
        self.action_list.append(install_deps_action)

        # Set the action list on the workbench
        workbench.appendToolbar("MCP Controls", self.action_list)
        workbench.appendMenu("MCP Indicator", self.action_list)

    def _setup_log_watcher(self):
        """Set up the file system watcher for the MCP log file."""
        if not self.mcp_log_file_path:
            return

        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(self.mcp_log_file_path)
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
                FreeCAD.Console.PrintMessage(f"Created log directory: {log_dir}\n")
            except Exception as e:
                FreeCAD.Console.PrintError(f"Failed to create log directory: {str(e)}\n")
                return

        # Create an empty log file if it doesn't exist
        if not os.path.exists(self.mcp_log_file_path):
            try:
                with open(self.mcp_log_file_path, 'w') as f:
                    f.write("# MCP Server Log\n")
                FreeCAD.Console.PrintMessage(f"Created empty log file: {self.mcp_log_file_path}\n")
            except Exception as e:
                FreeCAD.Console.PrintError(f"Failed to create log file: {str(e)}\n")
                return

        # Set up the file watcher
        self.mcp_log_watcher = QFileSystemWatcher()

        # Watch both the directory and the file
        self.mcp_log_watcher.addPath(log_dir)
        self.mcp_log_watcher.addPath(self.mcp_log_file_path)

        # Connect signals
        self.mcp_log_watcher.fileChanged.connect(self._handle_log_file_change)
        self.mcp_log_watcher.directoryChanged.connect(lambda path: self._handle_log_directory_change(path))

    def _handle_log_file_change(self, path):
        """Handle changes to the log file."""
        # If the log dock widget is visible, update its content
        if self.mcp_log_dock_widget and self.mcp_log_dock_widget.isVisible() and self.mcp_log_text_edit:
            self._load_mcp_log_content()

        # The file might have been deleted and recreated, re-add it to the watcher
        if not self.mcp_log_watcher.files().contains(path) and os.path.exists(path):
            self.mcp_log_watcher.addPath(path)

    def _handle_log_directory_change(self, path):
        """Handle changes to the log directory."""
        # Check if our log file has been created/deleted
        if os.path.exists(self.mcp_log_file_path) and not self.mcp_log_watcher.files().contains(self.mcp_log_file_path):
            self.mcp_log_watcher.addPath(self.mcp_log_file_path)

    def _load_mcp_log_content(self, max_lines=500):
        """Load the content from the MCP log file into the text edit."""
        if not self.mcp_log_text_edit or not self.mcp_log_file_path or not os.path.exists(self.mcp_log_file_path):
            return

        try:
            with open(self.mcp_log_file_path, 'r', encoding='utf-8', errors='replace') as f:
                # Read all lines and take the last max_lines
                lines = f.readlines()
                if len(lines) > max_lines:
                    lines = lines[-max_lines:]

                # Update the text edit
                self.mcp_log_text_edit.clear()
                self.mcp_log_text_edit.append("".join(lines))

                # Scroll to bottom
                cursor = self.mcp_log_text_edit.textCursor()
                cursor.movePosition(QtWidgets.QTextCursor.End)
                self.mcp_log_text_edit.setTextCursor(cursor)

        except Exception as e:
            FreeCAD.Console.PrintError(f"Error loading MCP log file: {str(e)}\n")
            self.mcp_log_text_edit.clear()
            self.mcp_log_text_edit.append(f"Error loading log file: {str(e)}")

    def _toggle_mcp_log_viewer(self, checked):
        """Toggle the visibility of the MCP log viewer dock widget."""
        # Create the dock widget if it doesn't exist
        if not self.mcp_log_dock_widget:
            mw = FreeCADGui.getMainWindow()
            if not mw:
                return

            self.mcp_log_dock_widget = QDockWidget("MCP Server Log", mw)
            self.mcp_log_dock_widget.setObjectName("MCPLogDockWidget")

            # Create a widget to hold the text edit and controls
            log_widget = QWidget()
            log_layout = QVBoxLayout(log_widget)

            # Create text edit for log content
            self.mcp_log_text_edit = QTextEdit()
            self.mcp_log_text_edit.setReadOnly(True)

            # Use a monospace font
            font = self.mcp_log_text_edit.font()
            font.setFamily("Courier")
            self.mcp_log_text_edit.setFont(font)
            log_layout.addWidget(self.mcp_log_text_edit)

            # Add a refresh button
            refresh_btn = QPushButton("Refresh")
            refresh_btn.clicked.connect(lambda: self._load_mcp_log_content())
            log_layout.addWidget(refresh_btn)

            # Set the widget as the dock widget's content
            self.mcp_log_dock_widget.setWidget(log_widget)

            # Add the dock widget to the main window
            mw.addDockWidget(Qt.RightDockWidgetArea, self.mcp_log_dock_widget)

            # Load initial content
            self._load_mcp_log_content()

        # Toggle visibility based on checked state
        if self.mcp_log_dock_widget.isVisible() != checked:
            self.mcp_log_dock_widget.setVisible(checked)

        # Update the action's checked state to match
        self.show_mcp_log_action.setChecked(checked)

    def _update_indicator_icon(self):
        """Update the main indicator icon based on connection status."""
        if not self.control_button:
            return

        # Create icons for different states
        icon_connected = QtGui.QIcon(":icons/mcp_connected.svg")
        icon_disconnected = QtGui.QIcon(":icons/mcp_disconnected.svg")

        if not icon_connected.isNull():
            # SVG icons loaded successfully
            pass
        else:
            # Fall back to simple colored icons
            pixmap_connected = QtGui.QPixmap(16, 16)
            pixmap_connected.fill(QtGui.QColor(0, 200, 0))  # Green
            icon_connected = QtGui.QIcon(pixmap_connected)

            pixmap_disconnected = QtGui.QPixmap(16, 16)
            pixmap_disconnected.fill(QtGui.QColor(200, 0, 0))  # Red
            icon_disconnected = QtGui.QIcon(pixmap_disconnected)

        # Set the icon based on connection status
        if self.status_checker.connected:
            self.control_button.setIcon(icon_connected)
        else:
            self.control_button.setIcon(icon_disconnected)

        # Update tooltip
        self._update_tooltip()

    def _update_freecad_server_icon(self):
        """Update the FreeCAD server status icon."""
        if not self.freecad_server_status_button:
            return

        # Create icons for different states
        icon_running = QtGui.QIcon(":icons/server_running.svg")
        icon_stopped = QtGui.QIcon(":icons/server_stopped.svg")

        if not icon_running.isNull():
            # SVG icons loaded successfully
            pass
        else:
            # Fall back to simple colored icons
            pixmap_running = QtGui.QPixmap(16, 16)
            pixmap_running.fill(QtGui.QColor(0, 100, 200))  # Blue
            icon_running = QtGui.QIcon(pixmap_running)

            pixmap_stopped = QtGui.QPixmap(16, 16)
            pixmap_stopped.fill(QtGui.QColor(150, 150, 150))  # Gray
            icon_stopped = QtGui.QIcon(pixmap_stopped)

        # Set the icon based on server status
        if self.process_manager.is_freecad_server_running():
            self.freecad_server_status_button.setIcon(icon_running)
            self.freecad_server_status_button.setToolTip("FreeCAD Socket Server: Running")
        else:
            self.freecad_server_status_button.setIcon(icon_stopped)
            self.freecad_server_status_button.setToolTip("FreeCAD Socket Server: Stopped")

    def _update_mcp_server_icon(self):
        """Update the MCP server status icon."""
        if not self.mcp_server_status_button:
            return

        # Create icons for different states
        icon_running = QtGui.QIcon(":icons/mcp_server_running.svg")
        icon_stopped = QtGui.QIcon(":icons/mcp_server_stopped.svg")

        if not icon_running.isNull():
            # SVG icons loaded successfully
            pass
        else:
            # Fall back to simple colored icons
            pixmap_running = QtGui.QPixmap(16, 16)
            pixmap_running.fill(QtGui.QColor(0, 150, 50))  # Green
            icon_running = QtGui.QIcon(pixmap_running)

            pixmap_stopped = QtGui.QPixmap(16, 16)
            pixmap_stopped.fill(QtGui.QColor(150, 150, 150))  # Gray
            icon_stopped = QtGui.QIcon(pixmap_stopped)

        # Set the icon based on server status
        if self.process_manager.is_mcp_server_running():
            self.mcp_server_status_button.setIcon(icon_running)
            self.mcp_server_status_button.setToolTip("MCP Server: Running")
        else:
            self.mcp_server_status_button.setIcon(icon_stopped)
            self.mcp_server_status_button.setToolTip("MCP Server: Stopped")

    def _update_tooltip(self):
        """Update the tooltip for the main control button."""
        if not self.control_button:
            return

        if self.status_checker.connected:
            connected_time = ""
            if self.status_checker.connection_timestamp:
                duration = time.time() - self.status_checker.connection_timestamp
                hours, remainder = divmod(duration, 3600)
                minutes, seconds = divmod(remainder, 60)

                if hours > 0:
                    connected_time = f"Connected for {int(hours)}h {int(minutes)}m"
                elif minutes > 0:
                    connected_time = f"Connected for {int(minutes)}m {int(seconds)}s"
                else:
                    connected_time = f"Connected for {int(seconds)}s"

            tooltip = f"MCP: Connected to {self.config.get_mcp_server_host()}:{self.config.get_mcp_server_port()}\n{connected_time}"
        else:
            tooltip = f"MCP: Not connected to {self.config.get_mcp_server_host()}:{self.config.get_mcp_server_port()}"

        if self.status_checker.connection_error:
            tooltip += f"\nError: {self.status_checker.connection_error}"

        self.control_button.setToolTip(tooltip)

    def update_ui(self):
        """Update all UI elements with current status."""
        self._update_indicator_icon()
        self._update_freecad_server_icon()
        self._update_mcp_server_icon()
        self._update_action_states()

    def _update_action_states(self):
        """Update the enabled/disabled state of actions based on current status."""
        if not hasattr(self, 'action_list'):
            return

        # Get current status
        mcp_script_path_valid = bool(self.config.get_mcp_server_script_path() and
                                    os.path.exists(self.config.get_mcp_server_script_path()))
        server_script_path_valid = bool(self.config.get_server_script_path() and
                                        os.path.exists(self.config.get_server_script_path()))
        mcp_server_running = self.process_manager.is_mcp_server_running()
        freecad_server_running = self.process_manager.is_freecad_server_running()

        # Update each action in the list
        for action in self.action_list:
            if isinstance(action, str):
                continue  # Skip separators

            # MCP Server actions
            if action.text() == "Start MCP Server":
                action.setEnabled(mcp_script_path_valid and not mcp_server_running)
            elif action.text() == "Stop MCP Server":
                action.setEnabled(mcp_server_running)
            elif action.text() == "Restart MCP Server":
                action.setEnabled(mcp_script_path_valid and mcp_server_running)

            # Socket Server actions
            elif action.text() == "Start Socket Server":
                action.setEnabled(server_script_path_valid and not freecad_server_running)
            elif action.text() == "Stop Socket Server":
                action.setEnabled(freecad_server_running)
            elif action.text() == "Restart Socket Server":
                action.setEnabled(server_script_path_valid and freecad_server_running)

    # Dialog methods
    def _show_connection_info(self):
        """Show dialog with connection information."""
        info = self.status_checker.get_detailed_connection_info()
        html = self._get_client_info_html(info)
        self._show_info_dialog("MCP Connection Information", html)

    def _show_freecad_server_info(self):
        """Show dialog with FreeCAD server information."""
        html = self._get_freecad_server_info_html()
        self._show_info_dialog("FreeCAD Socket Server Information", html)

    def _show_mcp_server_info(self):
        """Show dialog with MCP server information."""
        html = self._get_mcp_server_info_html()
        self._show_info_dialog("MCP Server Information", html)

    def _show_flow_visualization(self):
        """Show the flow visualization dialog."""
        try:
            from mcp_indicator import flow_visualization
            flow_dialog = flow_visualization.MCPFlowDialog()
            flow_dialog.show()
        except Exception as e:
            FreeCAD.Console.PrintError(f"Error showing flow visualization: {str(e)}\n")
            self._show_info_dialog("Error", f"<p>Failed to load flow visualization: {str(e)}</p>")

    def _show_info_dialog(self, title, html_content):
        """Show a modal dialog with formatted HTML content."""
        # Reuse existing dialog if possible
        if self.connection_info_dialog:
            try:
                self.connection_info_dialog.setWindowTitle(title)
                self.connection_info_dialog.findChild(QtWidgets.QTextBrowser).setHtml(html_content)
                self.connection_info_dialog.show()
                self.connection_info_dialog.raise_()
                return
            except:
                # Dialog was destroyed, need to recreate
                self.connection_info_dialog = None

        # Create a new dialog
        mw = FreeCADGui.getMainWindow()
        self.connection_info_dialog = QtWidgets.QDialog(mw)
        self.connection_info_dialog.setWindowTitle(title)
        self.connection_info_dialog.setModal(False)
        self.connection_info_dialog.setMinimumWidth(600)
        self.connection_info_dialog.setMinimumHeight(400)

        layout = QtWidgets.QVBoxLayout(self.connection_info_dialog)

        text_browser = QtWidgets.QTextBrowser()
        text_browser.setHtml(html_content)
        text_browser.setOpenExternalLinks(True)
        layout.addWidget(text_browser)

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        button_box.rejected.connect(self.connection_info_dialog.close)
        layout.addWidget(button_box)

        self.connection_info_dialog.show()

    def _get_client_info_html(self, info=None):
        """Generate HTML content for connection info dialog."""
        if info is None:
            info = self.status_checker.get_detailed_connection_info()

        host = info.get("mcp_server_host", "unknown")
        port = info.get("mcp_server_port", "unknown")
        connected = info.get("connected", False)
        connection_time = info.get("connection_time")
        connection_duration = info.get("connection_duration", "N/A")
        connection_error = info.get("connection_error")
        details = info.get("details", {})

        # Create HTML content
        html = f"""
        <h2>MCP Connection Status</h2>
        <table>
          <tr>
            <td><b>MCP Server Host:</b></td>
            <td>{host}</td>
          </tr>
          <tr>
            <td><b>MCP Server Port:</b></td>
            <td>{port}</td>
          </tr>
          <tr>
            <td><b>Connected:</b></td>
            <td>{'Yes' if connected else 'No'}</td>
          </tr>
        """

        if connected and connection_time:
            time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(connection_time))
            html += f"""
            <tr>
              <td><b>Connected Since:</b></td>
              <td>{time_str}</td>
            </tr>
            <tr>
              <td><b>Connection Duration:</b></td>
              <td>{connection_duration}</td>
            </tr>
            """

        if not connected and connection_error:
            html += f"""
            <tr>
              <td><b>Connection Error:</b></td>
              <td style="color: red;">{connection_error}</td>
            </tr>
            """

        html += "</table>"

        # Add MCP server details if connected
        if connected and details:
            html += "<h2>MCP Server Details</h2><table>"
            for key, value in details.items():
                if key != "connections" and value:
                    html += f"<tr><td><b>{key.replace('_', ' ').title()}:</b></td><td>{value}</td></tr>"
            html += "</table>"

            # Add active connections if available
            connections = details.get("connections", {})
            if connections and not isinstance(connections, str):
                html += "<h2>Active Connections</h2><table>"
                for conn_id, conn_details in connections.items():
                    if isinstance(conn_details, dict):
                        html += f"<tr><td colspan='2'><b>Connection {conn_id}</b></td></tr>"
                        for k, v in conn_details.items():
                            html += f"<tr><td style='padding-left: 20px;'><b>{k.replace('_', ' ').title()}:</b></td><td>{v}</td></tr>"
                html += "</table>"

        return html

    def _get_freecad_server_info_html(self):
        """Generate HTML content for FreeCAD server info dialog."""
        running = self.process_manager.is_freecad_server_running()
        server_path = self.config.get_server_script_path()

        html = f"""
        <h2>FreeCAD Socket Server Status</h2>
        <table>
          <tr>
            <td><b>Server Status:</b></td>
            <td>{'Running' if running else 'Stopped'}</td>
          </tr>
          <tr>
            <td><b>Server Script Path:</b></td>
            <td>{server_path or 'Not configured'}</td>
          </tr>
        """

        if server_path:
            script_exists = os.path.exists(server_path)
            html += f"""
            <tr>
              <td><b>Script Exists:</b></td>
              <td>{'Yes' if script_exists else 'No - Script not found!'}</td>
            </tr>
            """

        html += "</table>"

        if not server_path:
            html += """
            <p style="color: red;">FreeCAD Socket Server script path is not configured.
            Use the Settings dialog to set the path to freecad_socket_server.py.</p>
            """

        return html

    def _get_mcp_server_info_html(self):
        """Generate HTML content for MCP server info dialog."""
        running = self.process_manager.is_mcp_server_running()
        server_path = self.config.get_mcp_server_script_path()
        config_path = self.config.get_mcp_server_config()
        host = self.config.get_mcp_server_host()
        port = self.config.get_mcp_server_port()

        html = f"""
        <h2>MCP Server Status</h2>
        <table>
          <tr>
            <td><b>Server Status:</b></td>
            <td>{'Running' if running else 'Stopped'}</td>
          </tr>
          <tr>
            <td><b>Server Host:</b></td>
            <td>{host}</td>
          </tr>
          <tr>
            <td><b>Server Port:</b></td>
            <td>{port}</td>
          </tr>
          <tr>
            <td><b>Server Script Path:</b></td>
            <td>{server_path or 'Not configured'}</td>
          </tr>
        """

        if server_path:
            script_exists = os.path.exists(server_path)
            html += f"""
            <tr>
              <td><b>Script Exists:</b></td>
              <td>{'Yes' if script_exists else 'No - Script not found!'}</td>
            </tr>
            """

        if config_path:
            config_exists = os.path.exists(config_path)
            html += f"""
            <tr>
              <td><b>Config Path:</b></td>
              <td>{config_path}</td>
            </tr>
            <tr>
              <td><b>Config Exists:</b></td>
              <td>{'Yes' if config_exists else 'No - Config file not found!'}</td>
            </tr>
            """
        else:
            html += """
            <tr>
              <td><b>Config Path:</b></td>
              <td>Not configured (will use defaults)</td>
            </tr>
            """

        html += "</table>"

        if not server_path:
            html += """
            <p style="color: red;">MCP Server script path is not configured.
            Use the Settings dialog to set the path to freecad_mcp_server.py.</p>
            """

        return html

    def _show_settings(self):
        """Show settings dialog for the MCP Indicator."""
        # Create the dialog
        dialog = QtWidgets.QDialog(FreeCADGui.getMainWindow())
        dialog.setWindowTitle("MCP Indicator Settings")
        dialog.setMinimumWidth(600)

        layout = QtWidgets.QVBoxLayout(dialog)

        # Create form layout for settings
        form_layout = QtWidgets.QFormLayout()

        # Repository path
        repo_layout = QtWidgets.QHBoxLayout()
        repo_edit = QtWidgets.QLineEdit()
        repo_edit.setText(self.config.get_repo_path())
        repo_edit.setMinimumWidth(300)
        repo_browse = QtWidgets.QPushButton("Browse...")
        repo_browse.clicked.connect(lambda: self._browse_repo_path(repo_edit))
        repo_layout.addWidget(repo_edit)
        repo_layout.addWidget(repo_browse)
        form_layout.addRow("MCP Repository Path:", repo_layout)

        # FreeCAD Server path
        server_layout = QtWidgets.QHBoxLayout()
        server_edit = QtWidgets.QLineEdit()
        server_edit.setText(self.config.get_server_script_path())
        server_edit.setMinimumWidth(300)
        server_browse = QtWidgets.QPushButton("Browse...")
        server_browse.clicked.connect(lambda: self._browse_server_path(server_edit))
        server_layout.addWidget(server_edit)
        server_layout.addWidget(server_browse)
        form_layout.addRow("FreeCAD Server Script:", server_layout)

        # MCP Server path
        mcp_layout = QtWidgets.QHBoxLayout()
        mcp_edit = QtWidgets.QLineEdit()
        mcp_edit.setText(self.config.get_mcp_server_script_path())
        mcp_edit.setMinimumWidth(300)
        mcp_browse = QtWidgets.QPushButton("Browse...")
        mcp_browse.clicked.connect(lambda: self._browse_mcp_server_path(mcp_edit))
        mcp_layout.addWidget(mcp_edit)
        mcp_layout.addWidget(mcp_browse)
        form_layout.addRow("MCP Server Script:", mcp_layout)

        # Configuration file path
        config_layout = QtWidgets.QHBoxLayout()
        config_edit = QtWidgets.QLineEdit()
        config_edit.setText(self.config.get_mcp_server_config())
        config_edit.setMinimumWidth(300)
        config_browse = QtWidgets.QPushButton("Browse...")
        config_browse.clicked.connect(lambda: self._browse_config_path(config_edit))
        config_layout.addWidget(config_edit)
        config_layout.addWidget(config_browse)
        form_layout.addRow("MCP Server Config:", config_layout)

        # Host and Port
        host_edit = QtWidgets.QLineEdit()
        host_edit.setText(self.config.get_mcp_server_host())
        form_layout.addRow("MCP Server Host:", host_edit)

        port_edit = QtWidgets.QSpinBox()
        port_edit.setRange(1, 65535)
        port_edit.setValue(self.config.get_mcp_server_port())
        form_layout.addRow("MCP Server Port:", port_edit)

        layout.addLayout(form_layout)

        # Auto-config from repo path
        auto_config_btn = QtWidgets.QPushButton("Auto-Configure from Repository Path")
        auto_config_btn.clicked.connect(lambda: self._apply_repo_path(repo_edit.text(), server_edit, mcp_edit))
        layout.addWidget(auto_config_btn)

        # Buttons
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        # Show the dialog and handle result
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            # Save settings
            self.config.set_repo_path(repo_edit.text())
            self.config.set_server_script_path(server_edit.text())
            self.config.set_mcp_server_script_path(mcp_edit.text())
            self.config.set_mcp_server_config(config_edit.text())
            self.config.set_mcp_server_host(host_edit.text())
            self.config.set_mcp_server_port(port_edit.value())
            self.config.save_settings()

            # Reinitialize log file path
            self._init_log_file_path()

            # Update UI states with new settings
            self.update_ui()

    def _browse_repo_path(self, line_edit):
        """Browse for a directory to use as the repository path."""
        current_path = line_edit.text()
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            FreeCADGui.getMainWindow(),
            "Select MCP Repository Directory",
            current_path or os.path.expanduser("~"),
        )

        if directory:
            line_edit.setText(directory)

    def _apply_repo_path(self, repo_path, server_edit, mcp_edit):
        """Apply the repository path and auto-configure script paths."""
        if not repo_path or not os.path.isdir(repo_path):
            QtWidgets.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Invalid Repository Path",
                "Please select a valid repository directory.",
            )
            return

        # Temporarily set the repo path
        self.config.set_repo_path(repo_path)

        # Update paths
        if self.path_finder.update_paths_from_repo():
            # Update UI if successful
            server_edit.setText(self.config.get_server_script_path())
            mcp_edit.setText(self.config.get_mcp_server_script_path())
            QtWidgets.QMessageBox.information(
                FreeCADGui.getMainWindow(),
                "Paths Updated",
                "Script paths have been updated based on the repository path.",
            )
        else:
            QtWidgets.QMessageBox.warning(
                FreeCADGui.getMainWindow(),
                "Update Failed",
                "Could not update script paths from repository path.\n"
                "Please check that the repository structure is correct.",
            )

    def _browse_server_path(self, line_edit):
        """Browse for the FreeCAD server script."""
        current_path = line_edit.text()
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            FreeCADGui.getMainWindow(),
            "Select FreeCAD Server Script",
            os.path.dirname(current_path) if current_path else os.path.expanduser("~"),
            "Python Files (*.py);;All Files (*.*)",
        )

        if file_path:
            line_edit.setText(file_path)

    def _browse_mcp_server_path(self, line_edit):
        """Browse for the MCP server script."""
        current_path = line_edit.text()
        filter_str = "Python/Shell Files (*.py *.sh);;Python Files (*.py);;Shell Scripts (*.sh);;All Files (*.*)"

        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            FreeCADGui.getMainWindow(),
            "Select MCP Server Script",
            os.path.dirname(current_path) if current_path else os.path.expanduser("~"),
            filter_str,
        )

        if file_path:
            line_edit.setText(file_path)

    def _browse_config_path(self, line_edit):
        """Browse for the MCP server config file."""
        current_path = line_edit.text()
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            FreeCADGui.getMainWindow(),
            "Select MCP Server Config File",
            os.path.dirname(current_path) if current_path else os.path.expanduser("~"),
            "JSON Files (*.json);;All Files (*.*)",
        )

        if file_path:
            line_edit.setText(file_path)
