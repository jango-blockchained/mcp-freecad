"""FreeCAD MCP Workbench - Main workbench implementation"""

import os
import sys
import FreeCAD
import FreeCADGui

# Try to import PySide2, fall back gracefully if not available
try:
    from PySide2 import QtWidgets, QtCore, QtGui
    HAS_PYSIDE2 = True
except ImportError:
    try:
        from PySide import QtGui as QtWidgets
        from PySide import QtCore, QtGui
        HAS_PYSIDE2 = False
        FreeCAD.Console.PrintWarning("MCP Integration: Using PySide instead of PySide2\n")
    except ImportError:
        FreeCAD.Console.PrintError("MCP Integration: No Qt bindings available\n")
        HAS_PYSIDE2 = False


class MCPShowInterfaceCommand:
    """Command to show the MCP interface."""

    def GetResources(self):
        return {
            'Pixmap': '',  # Icon path
            'MenuText': 'Show MCP Interface',
            'ToolTip': 'Show the MCP Integration interface'
        }

    def IsActive(self):
        return True

    def Activated(self):
        FreeCAD.Console.PrintMessage("MCP Integration: Interface command activated\n")
        # Show a simple message for now
        if HAS_PYSIDE2:
            QtWidgets.QMessageBox.information(
                FreeCADGui.getMainWindow(),
                "MCP Integration",
                "MCP Integration interface is being developed.\nThis will provide AI-powered CAD assistance."
            )


# Register the command
if hasattr(FreeCADGui, 'addCommand'):
    FreeCADGui.addCommand('MCP_ShowInterface', MCPShowInterfaceCommand())


class MCPMainWidget(QtWidgets.QWidget if HAS_PYSIDE2 else object):
    """Main widget containing the tabbed interface."""

    def __init__(self, parent=None):
        # Initialize all attributes first to prevent AttributeError
        self.status_bar = None
        self.tab_widget = None
        self.log_display = None
        self.chat_display = None
        self.provider_combo = None
        self.model_combo = None
        self.connection_status = None

        if HAS_PYSIDE2:
            super().__init__(parent)
            self.init_ui()
        else:
            # No GUI available, create minimal interface
            FreeCAD.Console.PrintMessage("MCP Integration: GUI not available, minimal mode\n")

    def init_ui(self):
        """Initialize the user interface."""
        try:
            if not HAS_PYSIDE2:
                return

            self.setWindowTitle("MCP Integration")
            self.setMinimumSize(800, 600)

            # Create main layout
            layout = QtWidgets.QVBoxLayout(self)

            # Create tab widget
            self.tab_widget = QtWidgets.QTabWidget()
            layout.addWidget(self.tab_widget)

            # Create tabs
            self._create_ai_models_tab()
            self._create_connections_tab()
            self._create_servers_tab()
            self._create_tools_tab()
            self._create_logs_tab()

            # Status bar
            self.status_bar = QtWidgets.QStatusBar()
            layout.addWidget(self.status_bar)
            self.status_bar.showMessage("MCP Integration Ready")

        except Exception as e:
            FreeCAD.Console.PrintError(f"MCP Integration: Failed to create GUI: {e}\n")

    def _create_ai_models_tab(self):
        """Create the AI Models tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        # Header
        header = QtWidgets.QLabel("🤖 AI Models & Providers")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(header)

        # Provider selection
        provider_group = QtWidgets.QGroupBox("AI Provider")
        provider_layout = QtWidgets.QVBoxLayout(provider_group)

        self.provider_combo = QtWidgets.QComboBox()
        self.provider_combo.addItems(["Claude (Anthropic)", "Gemini (Google)", "OpenRouter"])
        provider_layout.addWidget(self.provider_combo)

        # Model selection
        self.model_combo = QtWidgets.QComboBox()
        self.model_combo.addItems([
            "claude-4-opus-20250522",
            "claude-4-sonnet-20250522",
            "gemini-2.5-pro-latest",
            "gpt-4.1-turbo"
        ])
        provider_layout.addWidget(self.model_combo)

        layout.addWidget(provider_group)

        # Chat interface
        chat_group = QtWidgets.QGroupBox("AI Chat")
        chat_layout = QtWidgets.QVBoxLayout(chat_group)

        self.chat_display = QtWidgets.QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setMaximumHeight(200)
        chat_layout.addWidget(self.chat_display)

        # Chat input
        input_layout = QtWidgets.QHBoxLayout()
        self.chat_input = QtWidgets.QLineEdit()
        self.chat_input.setPlaceholderText("Ask the AI assistant...")
        send_button = QtWidgets.QPushButton("Send")
        send_button.clicked.connect(self._send_chat_message)

        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(send_button)
        chat_layout.addLayout(input_layout)

        layout.addWidget(chat_group)
        layout.addStretch()

        self.tab_widget.addTab(widget, "AI Models")

    def _create_connections_tab(self):
        """Create the Connections tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        # Header
        header = QtWidgets.QLabel("🔗 FreeCAD Connections")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(header)

        # Connection status
        status_group = QtWidgets.QGroupBox("Connection Status")
        status_layout = QtWidgets.QVBoxLayout(status_group)

        self.connection_status = QtWidgets.QLabel("🔴 Disconnected")
        self.connection_status.setStyleSheet("font-size: 14px; padding: 10px;")
        status_layout.addWidget(self.connection_status)

        connect_button = QtWidgets.QPushButton("Connect to FreeCAD")
        connect_button.clicked.connect(self._connect_to_freecad)
        status_layout.addWidget(connect_button)

        layout.addWidget(status_group)
        layout.addStretch()

        self.tab_widget.addTab(widget, "Connections")

    def _create_servers_tab(self):
        """Create the Servers tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        # Header
        header = QtWidgets.QLabel("🖥️ MCP Servers")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(header)

        # Server list
        server_group = QtWidgets.QGroupBox("Active Servers")
        server_layout = QtWidgets.QVBoxLayout(server_group)

        server_list = QtWidgets.QListWidget()
        server_list.addItems(["FreeCAD MCP Server", "AI Provider Bridge", "Tool Manager"])
        server_layout.addWidget(server_list)

        layout.addWidget(server_group)
        layout.addStretch()

        self.tab_widget.addTab(widget, "Servers")

    def _create_tools_tab(self):
        """Create the Tools tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        # Header
        header = QtWidgets.QLabel("🛠️ MCP Tools")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(header)

        # Tool categories
        tools_group = QtWidgets.QGroupBox("Available Tools")
        tools_layout = QtWidgets.QVBoxLayout(tools_group)

        tool_buttons = [
            ("Create Primitive", "Create basic geometric shapes"),
            ("Measure Distance", "Measure distances between objects"),
            ("Export Model", "Export to various formats"),
            ("Generate Code", "Generate FreeCAD Python scripts")
        ]

        for tool_name, tool_desc in tool_buttons:
            button = QtWidgets.QPushButton(f"{tool_name}\n{tool_desc}")
            button.clicked.connect(lambda checked, name=tool_name: self._execute_tool(name))
            tools_layout.addWidget(button)

        layout.addWidget(tools_group)
        layout.addStretch()

        self.tab_widget.addTab(widget, "Tools")

    def _create_logs_tab(self):
        """Create the Logs tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        # Header
        header = QtWidgets.QLabel("📋 Activity Logs")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(header)

        # Log display
        self.log_display = QtWidgets.QTextEdit()
        self.log_display.setReadOnly(True)
        layout.addWidget(self.log_display)

        # Clear button
        clear_button = QtWidgets.QPushButton("Clear Logs")
        clear_button.clicked.connect(lambda: self.log_display.clear())
        layout.addWidget(clear_button)

        self.tab_widget.addTab(widget, "Logs")

    def _send_chat_message(self):
        """Send a chat message to the AI."""
        if not hasattr(self, 'chat_input') or not self.chat_input:
            return

        message = self.chat_input.text().strip()
        if not message:
            return

        self.chat_input.clear()
        self._add_log("AI Chat", f"User: {message}")

        # TODO: Implement actual AI integration
        if hasattr(self, 'chat_display') and self.chat_display:
            self.chat_display.append(f"<div style='margin: 10px; padding: 10px; background-color: #f3e5f5; border-radius: 5px;'><strong>🤖 AI:</strong> AI integration not yet implemented. This will connect to {self.provider_combo.currentText() if self.provider_combo else 'AI Provider'} using {self.model_combo.currentText() if self.model_combo else 'AI Model'}.</div>")

    def _connect_to_freecad(self):
        """Connect to FreeCAD."""
        self._add_log("Connection", "Attempting to connect...")
        # TODO: Implement actual connection
        if hasattr(self, 'connection_status') and self.connection_status:
            self.connection_status.setText("🟡 Connecting...")

        if HAS_PYSIDE2:
            QtWidgets.QMessageBox.information(self, "Connection", "Connection implementation coming soon")

    def _execute_tool(self, tool_name):
        """Execute an MCP tool."""
        self._add_log("Tool", f"Executing: {tool_name}")
        # TODO: Implement actual tool execution
        if HAS_PYSIDE2:
            QtWidgets.QMessageBox.information(self, "Tool Execution", f"Tool '{tool_name}' not yet implemented")

    def _add_log(self, category, message):
        """Add a log entry."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {category}: {message}"

        # Only append to log_display if it exists
        if hasattr(self, 'log_display') and self.log_display:
            self.log_display.append(log_entry)

        # Update status bar only if it exists
        if hasattr(self, 'status_bar') and self.status_bar:
            self.status_bar.showMessage(f"Last: {message}", 3000)


class MCPWorkbench(FreeCADGui.Workbench):
    """MCP Integration Workbench for FreeCAD"""

    MenuText = "MCP Integration"
    ToolTip = "Model Context Protocol Integration for AI-powered CAD operations"
    Icon = os.path.join(os.path.dirname(__file__), "resources", "icons", "mcp_workbench.svg")

    def __init__(self):
        """Initialize the MCP workbench."""
        self.addon_dir = os.path.dirname(__file__)
        self.main_widget = None
        self.dock_widget = None

    def Initialize(self):
        """Initialize the workbench GUI components."""
        FreeCAD.Console.PrintMessage("MCP Integration Workbench: Initializing...\n")

        try:
            # Create the main tabbed interface
            self._create_main_interface()

            # Create toolbar (simplified)
            self._create_toolbar()

            FreeCAD.Console.PrintMessage("MCP Integration Workbench: Initialization complete\n")

        except Exception as e:
            FreeCAD.Console.PrintError(f"MCP Integration Workbench: Initialization failed: {e}\n")
            # Minimal fallback initialization
            FreeCAD.Console.PrintMessage("MCP Integration Workbench: Running in minimal mode\n")

    def Activated(self):
        """Called when the workbench is activated."""
        FreeCAD.Console.PrintMessage("MCP Integration Workbench: Activated\n")

        # Show the dock widget if it exists
        if self.dock_widget:
            self.dock_widget.show()

    def Deactivated(self):
        """Called when the workbench is deactivated."""
        FreeCAD.Console.PrintMessage("MCP Integration Workbench: Deactivated\n")

        # Hide the dock widget
        if self.dock_widget:
            self.dock_widget.hide()

    def GetClassName(self):
        """Return the workbench class name."""
        return "MCPWorkbench"

    def GetIcon(self):
        """Return the workbench icon."""
        icon_path = os.path.join(self.addon_dir, "resources", "icons", "mcp_workbench.svg")
        if os.path.exists(icon_path):
            return icon_path
        else:
            # Return a fallback or empty string if icon doesn't exist
            return ""

    def _create_main_interface(self):
        """Create the main tabbed interface."""
        try:
            # Check if Qt bindings are available
            if not HAS_PYSIDE2:
                FreeCAD.Console.PrintError("MCP Integration: Cannot create GUI without Qt bindings\n")
                return

            # Create main widget
            self.main_widget = MCPMainWidget()

            # Create dock widget to hold the main widget
            if self.main_widget and hasattr(self.main_widget, 'status_bar'):
                self.dock_widget = QtWidgets.QDockWidget("MCP Integration", FreeCADGui.getMainWindow())
                self.dock_widget.setWidget(self.main_widget)
                FreeCADGui.getMainWindow().addDockWidget(QtCore.Qt.RightDockWidgetArea, self.dock_widget)

        except Exception as e:
            FreeCAD.Console.PrintError(f"Failed to create main interface: {e}\n")

    def _create_toolbar(self):
        """Create the MCP toolbar."""
        try:
            # For now, create a simple toolbar without complex commands
            # This avoids the command registration issues
            toolbar_commands = []

            # Register basic commands if needed
            if hasattr(self, 'main_widget') and self.main_widget:
                toolbar_commands = ["MCP_ShowInterface"]

            # Only create toolbar if we have commands
            if toolbar_commands:
                self.appendToolbar("MCP Integration", toolbar_commands)
            else:
                FreeCAD.Console.PrintMessage("MCP Integration: Toolbar creation skipped - no commands available\n")

        except Exception as e:
            FreeCAD.Console.PrintError(f"Failed to create toolbar: {e}\n")

    def _create_dock_widget(self):
        """Create and show the dock widget."""
        try:
            # Create dock widget
            self.dock_widget = FreeCADGui.PySideUic.loadUi(
                os.path.join(self.addon_dir, "gui", "mcp_dock.ui")
            ) if os.path.exists(os.path.join(self.addon_dir, "gui", "mcp_dock.ui")) else self.main_widget

            # Add to FreeCAD main window
            mw = FreeCADGui.getMainWindow()
            mw.addDockWidget(QtCore.Qt.RightDockWidgetArea,
                           QtWidgets.QDockWidget("MCP Integration", self.dock_widget))

        except Exception as e:
            FreeCAD.Console.PrintError(f"Failed to create dock widget: {e}\n")

    def _open_ai_chat(self):
        """Open the AI chat interface."""
        try:
            if self.main_widget and hasattr(self.main_widget, 'tab_widget'):
                # Switch to AI Models tab
                self.main_widget.tab_widget.setCurrentIndex(0)
                if self.dock_widget:
                    self.dock_widget.show()
        except Exception as e:
            FreeCAD.Console.PrintError(f"Failed to open AI chat: {e}\n")

    def _show_server_status(self):
        """Show server status."""
        try:
            if self.main_widget and hasattr(self.main_widget, 'tab_widget'):
                # Switch to Servers tab
                self.main_widget.tab_widget.setCurrentIndex(2)
                if self.dock_widget:
                    self.dock_widget.show()
        except Exception as e:
            FreeCAD.Console.PrintError(f"Failed to show server status: {e}\n")

    def _open_settings(self):
        """Open the settings dialog."""
        try:
            if HAS_PYSIDE2:
                QtWidgets.QMessageBox.information(
                    FreeCADGui.getMainWindow(),
                    "Settings",
                    "Settings dialog coming soon!\nThis will allow configuration of API keys and preferences."
                )
        except Exception as e:
            FreeCAD.Console.PrintError(f"Failed to open settings: {e}\n")
