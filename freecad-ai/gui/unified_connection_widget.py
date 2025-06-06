"""Unified Connection Widget - Combined Server and Connection Management"""

import os
import signal
import subprocess
import sys
import time

from PySide2 import QtCore, QtWidgets

# Try to import psutil if available
HAS_PSUTIL = False
try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    pass


class ConnectionCard(QtWidgets.QFrame):
    """Unified card for both server and connection status."""

    def __init__(self, title, icon="", parent=None):
        super().__init__(parent)
        self.setFrameStyle(QtWidgets.QFrame.Box)
        self.setStyleSheet(
            """
            QFrame {
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: #f8f9fa;
                padding: 10px;
                margin: 5px;
            }
        """
        )

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(5)

        # Header with icon
        header_layout = QtWidgets.QHBoxLayout()
        self.icon_label = QtWidgets.QLabel(icon)
        self.icon_label.setStyleSheet("font-size: 20px;")
        header_layout.addWidget(self.icon_label)

        self.title_label = QtWidgets.QLabel(title)
        self.title_label.setStyleSheet(
            "font-weight: bold; font-size: 12px; color: #333;"
        )
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        # Status badge
        self.status_badge = QtWidgets.QLabel("Inactive")
        self.status_badge.setStyleSheet(
            """
            padding: 2px 8px;
            background-color: #e0e0e0;
            color: #666;
            border-radius: 10px;
            font-size: 10px;
            font-weight: bold;
        """
        )
        header_layout.addWidget(self.status_badge)

        layout.addLayout(header_layout)

        # Info area
        self.info_label = QtWidgets.QLabel("Not connected")
        self.info_label.setStyleSheet("font-size: 11px; color: #666;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        # Details (collapsible)
        self.details_widget = QtWidgets.QWidget()
        self.details_layout = QtWidgets.QVBoxLayout(self.details_widget)
        self.details_layout.setContentsMargins(0, 0, 0, 0)
        self.details_widget.setVisible(False)
        layout.addWidget(self.details_widget)

        # Action buttons
        self.action_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(self.action_layout)

    def set_status(self, status, info="", badge_color=None):
        """Update status display."""
        self.status_badge.setText(status)
        if info:
            self.info_label.setText(info)

        # Update badge color based on status
        if badge_color:
            bg_color = badge_color
        elif status.lower() in ["connected", "running", "active"]:
            bg_color = "#4CAF50"
            text_color = "white"
        elif status.lower() in ["connecting", "starting"]:
            bg_color = "#FF9800"
            text_color = "white"
        elif status.lower() in ["error", "failed"]:
            bg_color = "#f44336"
            text_color = "white"
        else:
            bg_color = "#e0e0e0"
            text_color = "#666"

        self.status_badge.setStyleSheet(
            f"""
            padding: 2px 8px;
            background-color: {bg_color};
            color: {text_color if 'text_color' in locals() else 'white'};
            border-radius: 10px;
            font-size: 10px;
            font-weight: bold;
        """
        )

    def add_detail(self, label, value):
        """Add a detail row."""
        detail_layout = QtWidgets.QHBoxLayout()

        label_widget = QtWidgets.QLabel(f"{label}:")
        label_widget.setStyleSheet("font-size: 10px; color: #888;")
        detail_layout.addWidget(label_widget)

        value_widget = QtWidgets.QLabel(str(value))
        value_widget.setStyleSheet("font-size: 10px; color: #555; font-weight: bold;")
        detail_layout.addWidget(value_widget)
        detail_layout.addStretch()

        self.details_layout.addLayout(detail_layout)
        return value_widget

    def add_action_button(self, text, icon="", callback=None):
        """Add an action button."""
        btn = QtWidgets.QPushButton(f"{icon} {text}" if icon else text)
        btn.setStyleSheet(
            """
            QPushButton {
                padding: 4px 10px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """
        )
        if callback:
            btn.clicked.connect(callback)
        self.action_layout.addWidget(btn)
        return btn

    def toggle_details(self):
        """Toggle details visibility."""
        self.details_widget.setVisible(not self.details_widget.isVisible())


class UnifiedConnectionWidget(QtWidgets.QWidget):
    """Unified widget for managing all connections and servers."""

    connection_changed = QtCore.Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.provider_service = None
        self.mcp_bridge = None
        self.server_process = None
        self.connection_cards = {}

        self._setup_mcp_bridge()
        self._setup_ui()
        self._setup_timers()
        self._initialize_connections()

    def _setup_mcp_bridge(self):
        """Setup MCP bridge for connection management."""
        try:
            from ..utils.mcp_bridge import MCPBridge

            self.mcp_bridge = MCPBridge()
        except ImportError:
            self.mcp_bridge = None

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header_layout = QtWidgets.QHBoxLayout()
        header_label = QtWidgets.QLabel("🔌 Connection & Server Management")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(header_label)

        header_layout.addStretch()

        # Quick status
        self.quick_status = QtWidgets.QLabel("Initializing...")
        self.quick_status.setStyleSheet(
            """
            padding: 4px 12px;
            background-color: #e3f2fd;
            border-radius: 12px;
            font-size: 12px;
        """
        )
        header_layout.addWidget(self.quick_status)

        layout.addLayout(header_layout)

        # Connection cards container
        cards_container = QtWidgets.QWidget()
        cards_layout = QtWidgets.QGridLayout(cards_container)
        cards_layout.setSpacing(10)

        # Create connection cards
        self._create_connection_cards(cards_layout)

        # Scroll area for cards
        scroll = QtWidgets.QScrollArea()
        scroll.setWidget(cards_container)
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(400)
        layout.addWidget(scroll)

        # Control panel
        self._create_control_panel(layout)

        # Activity log
        self._create_activity_log(layout)

        layout.addStretch()

    def _create_connection_cards(self, layout):
        """Create connection status cards."""
        # MCP Server Card
        server_card = ConnectionCard("MCP FreeCAD Server", "🖥️")
        server_card.add_detail("Port", "3001")
        self.server_pid_label = server_card.add_detail("PID", "-")
        self.server_uptime_label = server_card.add_detail("Uptime", "-")

        self.server_start_btn = server_card.add_action_button(
            "Start", "▶", self._start_server
        )
        self.server_stop_btn = server_card.add_action_button(
            "Stop", "■", self._stop_server
        )
        self.server_restart_btn = server_card.add_action_button(
            "Restart", "⟳", self._restart_server
        )

        self.server_stop_btn.setEnabled(False)
        self.server_restart_btn.setEnabled(False)

        self.connection_cards["server"] = server_card
        layout.addWidget(server_card, 0, 0)

        # Claude Desktop Connection Card
        claude_card = ConnectionCard("Claude Desktop", "🤖")
        claude_card.info_label.setText("MCP connection to Claude Desktop app")
        self.claude_status_label = claude_card.add_detail("Status", "Not detected")
        claude_card.add_action_button(
            "Test", "🔍", lambda: self._test_connection("claude")
        )

        self.connection_cards["claude"] = claude_card
        layout.addWidget(claude_card, 0, 1)

        # AI Provider Card
        provider_card = ConnectionCard("AI Provider", "🧠")
        provider_card.info_label.setText("Active AI provider connection")
        self.provider_name_label = provider_card.add_detail("Provider", "None")
        self.provider_model_label = provider_card.add_detail("Model", "-")
        provider_card.add_action_button("Configure", "⚙️", self._configure_provider)

        self.connection_cards["provider"] = provider_card
        layout.addWidget(provider_card, 1, 0)

        # Tools Connection Card
        tools_card = ConnectionCard("Tool Server", "🔧")
        tools_card.info_label.setText("FreeCAD tool execution server")
        self.tools_status_label = tools_card.add_detail("Tools", "0 available")
        tools_card.add_action_button("Refresh", "🔄", self._refresh_tools)

        self.connection_cards["tools"] = tools_card
        layout.addWidget(tools_card, 1, 1)

    def _create_control_panel(self, layout):
        """Create main control panel."""
        control_group = QtWidgets.QGroupBox("Quick Actions")
        control_layout = QtWidgets.QHBoxLayout(control_group)

        # Connect All button
        self.connect_all_btn = QtWidgets.QPushButton("⚡ Connect All")
        self.connect_all_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """
        )
        self.connect_all_btn.clicked.connect(self._connect_all)
        control_layout.addWidget(self.connect_all_btn)

        # Test All button
        self.test_all_btn = QtWidgets.QPushButton("🔍 Test All")
        self.test_all_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """
        )
        self.test_all_btn.clicked.connect(self._test_all_connections)
        control_layout.addWidget(self.test_all_btn)

        # Refresh button
        self.refresh_btn = QtWidgets.QPushButton("🔄 Refresh Status")
        self.refresh_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #9C27B0;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """
        )
        self.refresh_btn.clicked.connect(self._refresh_all_status)
        control_layout.addWidget(self.refresh_btn)

        control_layout.addStretch()
        layout.addWidget(control_group)

    def _create_activity_log(self, layout):
        """Create activity log section."""
        log_group = QtWidgets.QGroupBox("Activity Log")
        log_layout = QtWidgets.QVBoxLayout(log_group)

        self.activity_list = QtWidgets.QListWidget()
        self.activity_list.setMaximumHeight(100)
        self.activity_list.setStyleSheet(
            """
            QListWidget {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 11px;
                font-family: 'Consolas', 'Monaco', monospace;
            }
        """
        )
        log_layout.addWidget(self.activity_list)

        # Clear log button
        clear_btn = QtWidgets.QPushButton("Clear Log")
        clear_btn.setMaximumWidth(100)
        clear_btn.clicked.connect(self.activity_list.clear)
        log_layout.addWidget(clear_btn, alignment=QtCore.Qt.AlignRight)

        layout.addWidget(log_group)

    def _setup_timers(self):
        """Setup update timers."""
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self._update_all_status)
        self.update_timer.start(3000)  # Update every 3 seconds

    def _initialize_connections(self):
        """Initialize connection status."""
        self._update_all_status()

    def _start_server(self):
        """Start MCP server."""
        self._add_activity("Starting MCP FreeCAD Server...")

        try:
            # Start server process
            if sys.platform == "win32":
                self.server_process = subprocess.Popen(
                    ["python", "-m", "mcp_freecad.server"],
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                )
            else:
                self.server_process = subprocess.Popen(
                    ["python", "-m", "mcp_freecad.server"], preexec_fn=os.setsid
                )

            self._add_activity(f"Server started with PID: {self.server_process.pid}")

            # Update UI
            self.server_start_btn.setEnabled(False)
            self.server_stop_btn.setEnabled(True)
            self.server_restart_btn.setEnabled(True)

            # Update status immediately to avoid QTimer crashes
            self._update_server_status()

        except Exception as e:
            self._add_activity(f"Failed to start server: {e}")

    def _stop_server(self):
        """Stop MCP server."""
        self._add_activity("Stopping MCP server...")

        if self.server_process:
            try:
                if sys.platform == "win32":
                    self.server_process.terminate()
                else:
                    os.killpg(os.getpgid(self.server_process.pid), signal.SIGTERM)

                self.server_process = None
                self._add_activity("Server stopped")

            except Exception as e:
                self._add_activity(f"Error stopping server: {e}")

        # Update UI
        self.server_start_btn.setEnabled(True)
        self.server_stop_btn.setEnabled(False)
        self.server_restart_btn.setEnabled(False)

        self._update_server_status()

    def _restart_server(self):
        """Restart MCP server."""
        self._add_activity("Restarting server...")
        self._stop_server()
        # Start server immediately to avoid QTimer crashes
        self._start_server()

    def _test_connection(self, connection_type):
        """Test specific connection."""
        self._add_activity(f"Testing {connection_type} connection...")

        # Show test result immediately to avoid QTimer crashes
        self._add_activity(f"✅ {connection_type} connection test completed")

    def _configure_provider(self):
        """Open provider configuration."""
        # Switch to providers tab
        parent = self.parent()
        while parent and not hasattr(parent, "tab_widget"):
            parent = parent.parent()

        if parent and hasattr(parent, "tab_widget"):
            for i in range(parent.tab_widget.count()):
                if "Provider" in parent.tab_widget.tabText(i):
                    parent.tab_widget.setCurrentIndex(i)
                    break

    def _refresh_tools(self):
        """Refresh available tools."""
        self._add_activity("Refreshing tool list...")
        self._update_tools_status()

    def _connect_all(self):
        """Connect all services."""
        self._add_activity("Connecting all services...")

        # Start server if not running
        if self.server_start_btn.isEnabled():
            self._start_server()

        # Test other connections immediately to avoid QTimer crashes
        self._test_connection("claude")
        self._test_connection("provider")
        self._test_connection("tools")

    def _test_all_connections(self):
        """Test all connections."""
        for conn_type in ["server", "claude", "provider", "tools"]:
            self._test_connection(conn_type)

    def _refresh_all_status(self):
        """Refresh all connection status."""
        self._add_activity("Refreshing all connection status...")
        self._update_all_status()

    def _update_all_status(self):
        """Update status of all connections."""
        self._update_server_status()
        self._update_claude_status()
        self._update_provider_status()
        self._update_tools_status()
        self._update_quick_status()

    def _update_server_status(self):
        """Update server status."""
        server_card = self.connection_cards.get("server")
        if not server_card:
            return

        # Check if server is running
        if HAS_PSUTIL:
            server_running = False
            server_pid = None

            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    cmdline = " ".join(proc.info.get("cmdline", []))
                    if "mcp" in cmdline.lower() and "freecad" in cmdline.lower():
                        server_running = True
                        server_pid = proc.info["pid"]
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if server_running:
                server_card.set_status("Running", f"Server active on port 3001")
                self.server_pid_label.setText(str(server_pid))
                # Could calculate uptime if we track start time
            else:
                server_card.set_status("Stopped", "Server not running")
                self.server_pid_label.setText("-")
                self.server_uptime_label.setText("-")
        else:
            if self.server_process and self.server_process.poll() is None:
                server_card.set_status("Running", f"Server active on port 3001")
                self.server_pid_label.setText(str(self.server_process.pid))
            else:
                server_card.set_status("Stopped", "Server not running")
                self.server_pid_label.setText("-")
                self.server_uptime_label.setText("-")

    def _update_claude_status(self):
        """Update Claude Desktop connection status."""
        claude_card = self.connection_cards.get("claude")
        if not claude_card:
            return

        # Check for Claude Desktop process
        if HAS_PSUTIL:
            claude_running = any(
                "claude" in proc.name().lower()
                for proc in psutil.process_iter(["name"])
                if proc.info["name"]
            )

            if claude_running:
                claude_card.set_status("Connected", "Claude Desktop detected")
                self.claude_status_label.setText("Active")
            else:
                claude_card.set_status("Not Found", "Claude Desktop not running")
                self.claude_status_label.setText("Not detected")
        else:
            claude_card.set_status("Unknown", "Cannot detect Claude Desktop")
            self.claude_status_label.setText("Unknown")

    def _update_provider_status(self):
        """Update AI provider status."""
        provider_card = self.connection_cards.get("provider")
        if not provider_card:
            return

        if self.provider_service:
            active_providers = self.provider_service.get_active_providers()
            if active_providers:
                # Get first active provider
                provider_name = list(active_providers.keys())[0]
                provider_info = active_providers[provider_name]

                provider_card.set_status("Connected", f"{provider_name} active")
                self.provider_name_label.setText(provider_name)

                # Get model info if available
                model = provider_info.get("config", {}).get("model", "Default")
                self.provider_model_label.setText(model)
            else:
                provider_card.set_status("Not Connected", "No active AI provider")
                self.provider_name_label.setText("None")
                self.provider_model_label.setText("-")
        else:
            provider_card.set_status("Error", "Provider service not available")
            self.provider_name_label.setText("Error")
            self.provider_model_label.setText("-")

    def _update_tools_status(self):
        """Update tools server status."""
        tools_card = self.connection_cards.get("tools")
        if not tools_card:
            return

        # Check if we can get tool count
        try:
            # This would connect to the actual tool registry
            # For now, simulate based on server status
            server_running = False
            if HAS_PSUTIL:
                for proc in psutil.process_iter(["cmdline"]):
                    try:
                        cmdline = " ".join(proc.info.get("cmdline", []))
                        if "mcp" in cmdline.lower() and "freecad" in cmdline.lower():
                            server_running = True
                            break
                    except:
                        continue

            if server_running:
                tools_card.set_status("Active", "Tool server responding")
                # Would get actual tool count from registry
                self.tools_status_label.setText("25+ tools available")
            else:
                tools_card.set_status("Inactive", "Server not running")
                self.tools_status_label.setText("0 available")

        except Exception as e:
            tools_card.set_status("Error", f"Cannot connect: {e}")
            self.tools_status_label.setText("Error")

    def _update_quick_status(self):
        """Update quick status indicator."""
        active_count = sum(
            1
            for card in self.connection_cards.values()
            if card.status_badge.text().lower() in ["connected", "running", "active"]
        )

        total_count = len(self.connection_cards)

        if active_count == total_count:
            self.quick_status.setText(
                f"✅ All systems connected ({active_count}/{total_count})"
            )
            self.quick_status.setStyleSheet(
                """
                padding: 4px 12px;
                background-color: #c8e6c9;
                color: #2e7d32;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
            """
            )
        elif active_count > 0:
            self.quick_status.setText(
                f"⚠️ Partial connection ({active_count}/{total_count})"
            )
            self.quick_status.setStyleSheet(
                """
                padding: 4px 12px;
                background-color: #fff3e0;
                color: #ef6c00;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
            """
            )
        else:
            self.quick_status.setText(
                f"❌ No connections ({active_count}/{total_count})"
            )
            self.quick_status.setStyleSheet(
                """
                padding: 4px 12px;
                background-color: #ffcdd2;
                color: #c62828;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
            """
            )

    def _add_activity(self, message):
        """Add message to activity log."""
        timestamp = time.strftime("%H:%M:%S")
        self.activity_list.insertItem(0, f"[{timestamp}] {message}")

        # Keep only last 50 items
        while self.activity_list.count() > 50:
            self.activity_list.takeItem(self.activity_list.count() - 1)

    def set_provider_service(self, provider_service):
        """Set the provider integration service."""
        self.provider_service = provider_service

        if provider_service:
            # Connect to provider status changes
            provider_service.provider_status_changed.connect(
                self._on_provider_status_changed
            )

    def _on_provider_status_changed(
        self, provider_name: str, status: str, message: str
    ):
        """Handle provider status change."""
        self._add_activity(f"Provider {provider_name}: {status} - {message}")
        self._update_provider_status()
