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

        # Create the main tabbed interface
        self._create_main_interface()

        # Create toolbar
        self._create_toolbar()

        FreeCAD.Console.PrintMessage("MCP Integration Workbench: Initialization complete\n")

    def Activated(self):
        """Called when the workbench is activated."""
        FreeCAD.Console.PrintMessage("MCP Integration Workbench: Activated\n")

        # Show the main widget if it exists
        if self.main_widget:
            self.main_widget.show()

        # Create dock widget if it doesn't exist
        if not self.dock_widget:
            self._create_dock_widget()

    def Deactivated(self):
        """Called when the workbench is deactivated."""
        FreeCAD.Console.PrintMessage("MCP Integration Workbench: Deactivated\n")

        # Hide the dock widget
        if self.dock_widget:
            self.dock_widget.hide()

    def GetClassName(self):
        """Return the workbench class name."""
        return "MCPWorkbench"

        def _create_main_interface(self):
        """Create the main tabbed interface."""
        try:
            # Check if Qt bindings are available
            if not HAS_PYSIDE2:
                FreeCAD.Console.PrintError("MCP Integration: Cannot create GUI without Qt bindings\n")
                return

            # Import GUI modules
            gui_dir = os.path.join(self.addon_dir, "gui")
            if gui_dir not in sys.path:
                sys.path.append(gui_dir)

            # Create main widget
            self.main_widget = MCPMainWidget()

        except Exception as e:
            FreeCAD.Console.PrintError(f"Failed to create main interface: {e}\n")

    def _create_toolbar(self):
        """Create the MCP toolbar."""
        try:
            # Define toolbar actions
            toolbar_actions = [
                {
                    "name": "MCP_AI_Chat",
                    "text": "AI Chat",
                    "tooltip": "Open AI conversation interface",
                    "icon": "ai_chat.svg",
                    "callback": self._open_ai_chat
                },
                {
                    "name": "MCP_Server_Status",
                    "text": "Server Status",
                    "tooltip": "View MCP server connection status",
                    "icon": "server_status.svg",
                    "callback": self._show_server_status
                },
                {
                    "name": "MCP_Settings",
                    "text": "Settings",
                    "tooltip": "Configure MCP settings and API keys",
                    "icon": "settings.svg",
                    "callback": self._open_settings
                }
            ]

            # Add toolbar to FreeCAD
            self.appendToolbar("MCP Integration", [action["name"] for action in toolbar_actions])

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
            if self.main_widget:
                self.main_widget.show_ai_tab()
        except Exception as e:
            FreeCAD.Console.PrintError(f"Failed to open AI chat: {e}\n")

    def _show_server_status(self):
        """Show server status dialog."""
        try:
            if self.main_widget:
                self.main_widget.show_servers_tab()
        except Exception as e:
            FreeCAD.Console.PrintError(f"Failed to show server status: {e}\n")

    def _open_settings(self):
        """Open settings dialog."""
        try:
            # Import settings dialog
            from gui.settings_dialog import SettingsDialog
            dialog = SettingsDialog()
            dialog.exec_()
        except Exception as e:
            FreeCAD.Console.PrintError(f"Failed to open settings: {e}\n")


class MCPMainWidget(QtWidgets.QWidget if HAS_PYSIDE2 else object):
    """Main widget containing the tabbed interface."""

    def __init__(self, parent=None):
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
            "claude-3-7-sonnet-20250224"
        ])
        provider_layout.addWidget(QtWidgets.QLabel("Model:"))
        provider_layout.addWidget(self.model_combo)

        # Thinking mode
        self.thinking_mode_cb = QtWidgets.QCheckBox("✨ Thinking Mode")
        provider_layout.addWidget(self.thinking_mode_cb)

        # Thinking budget
        budget_layout = QtWidgets.QHBoxLayout()
        budget_layout.addWidget(QtWidgets.QLabel("Thinking Budget:"))
        self.thinking_budget = QtWidgets.QSpinBox()
        self.thinking_budget.setRange(100, 20000)
        self.thinking_budget.setValue(2000)
        self.thinking_budget.setSuffix(" tokens")
        budget_layout.addWidget(self.thinking_budget)
        provider_layout.addLayout(budget_layout)

        layout.addWidget(provider_group)

        # API Key configuration
        api_group = QtWidgets.QGroupBox("API Configuration")
        api_layout = QtWidgets.QVBoxLayout(api_group)

        self.api_key_input = QtWidgets.QLineEdit()
        self.api_key_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.api_key_input.setPlaceholderText("Enter your API key...")
        api_layout.addWidget(QtWidgets.QLabel("API Key:"))
        api_layout.addWidget(self.api_key_input)

        # Test connection button
        self.test_connection_btn = QtWidgets.QPushButton("🔍 Test Connection")
        self.test_connection_btn.clicked.connect(self._test_api_connection)
        api_layout.addWidget(self.test_connection_btn)

        layout.addWidget(api_group)

        # Chat interface
        chat_group = QtWidgets.QGroupBox("AI Conversation")
        chat_layout = QtWidgets.QVBoxLayout(chat_group)

        # Chat display
        self.chat_display = QtWidgets.QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setHtml("""
        <div style='padding: 10px;'>
        <h3>🚀 Welcome to MCP Integration!</h3>
        <p>Configure your AI provider above, then start chatting for AI-powered CAD assistance.</p>
        <p><strong>Example:</strong> "Create a 50mm cube and export it as STL"</p>
        </div>
        """)
        chat_layout.addWidget(self.chat_display)

        # Chat input
        input_layout = QtWidgets.QHBoxLayout()
        self.chat_input = QtWidgets.QLineEdit()
        self.chat_input.setPlaceholderText("Ask me anything about CAD design...")
        self.chat_input.returnPressed.connect(self._send_message)

        self.send_btn = QtWidgets.QPushButton("Send")
        self.send_btn.clicked.connect(self._send_message)

        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(self.send_btn)
        chat_layout.addLayout(input_layout)

        layout.addWidget(chat_group)

        layout.addStretch()
        self.tab_widget.addTab(widget, "🤖 AI Models")

    def _create_connections_tab(self):
        """Create the Connections tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        header = QtWidgets.QLabel("🔗 MCP Connections")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(header)

        # Connection method selection
        method_group = QtWidgets.QGroupBox("Connection Method")
        method_layout = QtWidgets.QVBoxLayout(method_group)

        self.connection_methods = QtWidgets.QButtonGroup()
        methods = [
            ("Launcher (Recommended)", "launcher"),
            ("Wrapper", "wrapper"),
            ("Server", "server"),
            ("Bridge", "bridge"),
            ("Mock (Testing)", "mock")
        ]

        for name, value in methods:
            radio = QtWidgets.QRadioButton(name)
            radio.setProperty("method", value)
            self.connection_methods.addButton(radio)
            method_layout.addWidget(radio)
            if value == "launcher":
                radio.setChecked(True)

        layout.addWidget(method_group)

        # Connection status
        status_group = QtWidgets.QGroupBox("Connection Status")
        status_layout = QtWidgets.QVBoxLayout(status_group)

        self.connection_status = QtWidgets.QLabel("🔴 Disconnected")
        self.connection_status.setStyleSheet("font-size: 14px; padding: 5px;")
        status_layout.addWidget(self.connection_status)

        # Connect button
        self.connect_btn = QtWidgets.QPushButton("🔗 Connect to FreeCAD")
        self.connect_btn.clicked.connect(self._connect_to_freecad)
        status_layout.addWidget(self.connect_btn)

        layout.addWidget(status_group)
        layout.addStretch()

        self.tab_widget.addTab(widget, "🔗 Connections")

    def _create_servers_tab(self):
        """Create the Servers tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        header = QtWidgets.QLabel("🖥️ Server Management")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(header)

        # MCP Server
        mcp_group = QtWidgets.QGroupBox("MCP Server")
        mcp_layout = QtWidgets.QVBoxLayout(mcp_group)

        self.mcp_status = QtWidgets.QLabel("🔴 Stopped")
        mcp_layout.addWidget(self.mcp_status)

        mcp_buttons = QtWidgets.QHBoxLayout()
        self.start_mcp_btn = QtWidgets.QPushButton("▶️ Start")
        self.stop_mcp_btn = QtWidgets.QPushButton("⏹️ Stop")
        self.restart_mcp_btn = QtWidgets.QPushButton("🔄 Restart")

        mcp_buttons.addWidget(self.start_mcp_btn)
        mcp_buttons.addWidget(self.stop_mcp_btn)
        mcp_buttons.addWidget(self.restart_mcp_btn)
        mcp_layout.addLayout(mcp_buttons)

        layout.addWidget(mcp_group)

        # FreeCAD Server
        fc_group = QtWidgets.QGroupBox("FreeCAD Server")
        fc_layout = QtWidgets.QVBoxLayout(fc_group)

        self.fc_status = QtWidgets.QLabel("🔴 Stopped")
        fc_layout.addWidget(self.fc_status)

        fc_buttons = QtWidgets.QHBoxLayout()
        self.start_fc_btn = QtWidgets.QPushButton("▶️ Start")
        self.stop_fc_btn = QtWidgets.QPushButton("⏹️ Stop")
        self.restart_fc_btn = QtWidgets.QPushButton("🔄 Restart")

        fc_buttons.addWidget(self.start_fc_btn)
        fc_buttons.addWidget(self.stop_fc_btn)
        fc_buttons.addWidget(self.restart_fc_btn)
        fc_layout.addLayout(fc_buttons)

        layout.addWidget(fc_group)
        layout.addStretch()

        self.tab_widget.addTab(widget, "🖥️ Servers")

    def _create_tools_tab(self):
        """Create the Tools tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        header = QtWidgets.QLabel("🛠️ MCP Tools")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(header)

        # Tool categories
        scroll = QtWidgets.QScrollArea()
        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_widget)

        tool_categories = [
            ("🔧 Primitives", ["Create Box", "Create Cylinder", "Create Sphere", "Create Cone"]),
            ("⚙️ Operations", ["Boolean Union", "Boolean Cut", "Boolean Intersection"]),
            ("📐 Measurements", ["Measure Distance", "Measure Angle", "Calculate Volume"]),
            ("💾 Export/Import", ["Export STL", "Export STEP", "Import STEP"])
        ]

        for category_name, tools in tool_categories:
            group = QtWidgets.QGroupBox(category_name)
            group_layout = QtWidgets.QVBoxLayout(group)

            for tool in tools:
                btn = QtWidgets.QPushButton(tool)
                btn.clicked.connect(lambda checked, t=tool: self._execute_tool(t))
                group_layout.addWidget(btn)

            scroll_layout.addWidget(group)

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        self.tab_widget.addTab(widget, "🛠️ Tools")

    def _create_logs_tab(self):
        """Create the Logs tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        header = QtWidgets.QLabel("📋 Activity Logs")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(header)

        # Log display
        self.log_display = QtWidgets.QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("font-family: monospace; background-color: #1e1e1e; color: #ffffff;")
        layout.addWidget(self.log_display)

        # Log controls
        controls = QtWidgets.QHBoxLayout()
        self.clear_logs_btn = QtWidgets.QPushButton("🗑️ Clear Logs")
        self.save_logs_btn = QtWidgets.QPushButton("💾 Save Logs")

        controls.addWidget(self.clear_logs_btn)
        controls.addWidget(self.save_logs_btn)
        controls.addStretch()
        layout.addLayout(controls)

        self.tab_widget.addTab(widget, "📋 Logs")

        # Add initial log entry
        self._add_log("System", "MCP Integration initialized successfully")

    def show_ai_tab(self):
        """Show the AI Models tab."""
        self.tab_widget.setCurrentIndex(0)
        self.show()

    def show_servers_tab(self):
        """Show the Servers tab."""
        self.tab_widget.setCurrentIndex(2)
        self.show()

    def _test_api_connection(self):
        """Test API connection."""
        self._add_log("API", "Testing connection...")
        # TODO: Implement actual API test
        QtWidgets.QMessageBox.information(self, "API Test", "Connection test not yet implemented")

    def _send_message(self):
        """Send message to AI."""
        message = self.chat_input.text().strip()
        if not message:
            return

        # Add user message to chat
        self.chat_display.append(f"<div style='margin: 10px; padding: 10px; background-color: #e3f2fd; border-radius: 5px;'><strong>You:</strong> {message}</div>")

        # Clear input
        self.chat_input.clear()

        # Log the message
        self._add_log("AI Chat", f"User: {message}")

        # TODO: Implement actual AI integration
        self.chat_display.append(f"<div style='margin: 10px; padding: 10px; background-color: #f3e5f5; border-radius: 5px;'><strong>🤖 AI:</strong> AI integration not yet implemented. This will connect to {self.provider_combo.currentText()} using {self.model_combo.currentText()}.</div>")

    def _connect_to_freecad(self):
        """Connect to FreeCAD."""
        self._add_log("Connection", "Attempting to connect...")
        # TODO: Implement actual connection
        self.connection_status.setText("🟡 Connecting...")
        QtWidgets.QMessageBox.information(self, "Connection", "Connection implementation coming soon")

    def _execute_tool(self, tool_name):
        """Execute an MCP tool."""
        self._add_log("Tool", f"Executing: {tool_name}")
        # TODO: Implement actual tool execution
        QtWidgets.QMessageBox.information(self, "Tool Execution", f"Tool '{tool_name}' not yet implemented")

    def _add_log(self, category, message):
        """Add a log entry."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {category}: {message}"
        self.log_display.append(log_entry)

        # Update status bar
        self.status_bar.showMessage(f"Last: {message}", 3000)
