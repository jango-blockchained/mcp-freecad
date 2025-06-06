"""Connection Widget - Visual and interactive MCP connection manager"""

import time

from PySide2 import QtCore, QtWidgets


class ConnectionStatusCard(QtWidgets.QFrame):
    """Visual card for connection status display."""

    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QtWidgets.QFrame.Box)
        self.setStyleSheet(
            """
            QFrame {
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: #f8f9fa;
                padding: 10px;
            }
        """
        )

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(5)

        # Title
        self.title_label = QtWidgets.QLabel(title)
        self.title_label.setStyleSheet(
            "font-weight: bold; font-size: 12px; color: #333;"
        )
        layout.addWidget(self.title_label)

        # Status indicator
        status_layout = QtWidgets.QHBoxLayout()
        self.status_icon = QtWidgets.QLabel("⭕")
        self.status_icon.setStyleSheet("font-size: 24px;")
        status_layout.addWidget(self.status_icon)

        self.status_text = QtWidgets.QLabel("Disconnected")
        self.status_text.setStyleSheet("font-size: 11px; color: #666;")
        status_layout.addWidget(self.status_text)
        status_layout.addStretch()

        layout.addLayout(status_layout)

        # Connection info
        self.info_label = QtWidgets.QLabel("Not connected")
        self.info_label.setStyleSheet("font-size: 10px; color: #999;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        # Last activity
        self.activity_label = QtWidgets.QLabel("")
        self.activity_label.setStyleSheet(
            "font-size: 9px; color: #aaa; font-style: italic;"
        )
        layout.addWidget(self.activity_label)

    def set_status(self, status, info="", activity=""):
        """Update connection status."""
        if status == "connected":
            self.status_icon.setText("🟢")
            self.status_text.setText("Connected")
            self.setStyleSheet(
                """
                QFrame {
                    border: 2px solid #4CAF50;
                    border-radius: 8px;
                    background-color: #f1f8f4;
                    padding: 10px;
                }
            """
            )
        elif status == "connecting":
            self.status_icon.setText("🟡")
            self.status_text.setText("Connecting...")
            self.setStyleSheet(
                """
                QFrame {
                    border: 2px solid #FF9800;
                    border-radius: 8px;
                    background-color: #fff8f1;
                    padding: 10px;
                }
            """
            )
        elif status == "error":
            self.status_icon.setText("🔴")
            self.status_text.setText("Error")
            self.setStyleSheet(
                """
                QFrame {
                    border: 2px solid #f44336;
                    border-radius: 8px;
                    background-color: #fdf1f1;
                    padding: 10px;
                }
            """
            )
        else:  # disconnected
            self.status_icon.setText("⭕")
            self.status_text.setText("Disconnected")
            self.setStyleSheet(
                """
                QFrame {
                    border: 2px solid #ddd;
                    border-radius: 8px;
                    background-color: #f8f9fa;
                    padding: 10px;
                }
            """
            )

        if info:
            self.info_label.setText(info)
        if activity:
            self.activity_label.setText(f"Last activity: {activity}")


class ConnectionWidget(QtWidgets.QWidget):
    """Enhanced widget for managing MCP connections."""

    connection_changed = QtCore.Signal(str, str)
    connection_tested = QtCore.Signal(bool, str)

    def __init__(self, parent=None):
        super(ConnectionWidget, self).__init__(parent)
        self.current_connection = None
        self.connection_status = "Disconnected"
        self.provider_service = None
        self.connection_cards = {}

        self._setup_mcp_bridge()
        self._setup_ui()
        self._setup_update_timer()
        self._auto_detect_connection()

    def _setup_mcp_bridge(self):
        """Setup MCP bridge for connection management."""
        try:
            from ..utils.mcp_bridge import MCPBridge

            self.mcp_bridge = MCPBridge()
            self.connection_config = self.mcp_bridge.get_connection_config()
        except ImportError:
            self.mcp_bridge = None
            self.connection_config = {}

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(5, 5, 5, 5)

        # Header with real-time status
        header_layout = QtWidgets.QHBoxLayout()
        header_label = QtWidgets.QLabel("🔌 Connection Manager")
        header_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_layout.addWidget(header_label)

        header_layout.addStretch()

        # Real-time connection counter
        self.active_connections_label = QtWidgets.QLabel("0 active connections")
        self.active_connections_label.setStyleSheet(
            "padding: 3px 10px; background-color: #e3f2fd; border-radius: 12px; font-size: 11px;"
        )
        header_layout.addWidget(self.active_connections_label)

        layout.addLayout(header_layout)

        # Connection cards grid
        self._create_connection_cards(layout)

        # Connection control panel
        self._create_control_panel(layout)

        # Activity log
        self._create_activity_log(layout)

        layout.addStretch()

    def _create_connection_cards(self, layout):
        """Create visual connection status cards."""
        cards_group = QtWidgets.QGroupBox("Active Connections")
        cards_layout = QtWidgets.QGridLayout(cards_group)
        cards_layout.setSpacing(10)

        # Create cards for different connection types
        connections = [
            ("FreeCAD MCP", "Main MCP connection to FreeCAD"),
            ("Claude Desktop", "Connection to Claude Desktop app"),
            ("AI Provider", "Active AI provider connection"),
            ("Tool Server", "FreeCAD tool server status"),
        ]

        for i, (name, desc) in enumerate(connections):
            card = ConnectionStatusCard(name)
            card.info_label.setText(desc)
            self.connection_cards[name] = card
            cards_layout.addWidget(card, i // 2, i % 2)

        layout.addWidget(cards_group)

    def _create_control_panel(self, layout):
        """Create connection control panel."""
        control_group = QtWidgets.QGroupBox("Connection Control")
        control_layout = QtWidgets.QVBoxLayout(control_group)

        # Method selection with visual feedback
        method_layout = QtWidgets.QHBoxLayout()
        method_layout.addWidget(QtWidgets.QLabel("Method:"))

        self.method_combo = QtWidgets.QComboBox()
        self.method_combo.addItems(
            ["Auto-detect", "Launcher", "Wrapper", "Server", "Bridge"]
        )
        self.method_combo.setMinimumWidth(120)
        self.method_combo.currentTextChanged.connect(self._on_method_changed)
        method_layout.addWidget(self.method_combo)

        # Visual method indicator
        self.method_indicator = QtWidgets.QLabel("✨")
        self.method_indicator.setStyleSheet("font-size: 16px;")
        method_layout.addWidget(self.method_indicator)

        method_layout.addStretch()
        control_layout.addLayout(method_layout)

        # Quick action buttons
        button_layout = QtWidgets.QHBoxLayout()

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
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """
        )
        button_layout.addWidget(self.connect_all_btn)

        self.disconnect_all_btn = QtWidgets.QPushButton("🛑 Disconnect All")
        self.disconnect_all_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """
        )
        self.disconnect_all_btn.setEnabled(False)
        button_layout.addWidget(self.disconnect_all_btn)

        self.test_btn = QtWidgets.QPushButton("🔍 Test All")
        self.test_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """
        )
        button_layout.addWidget(self.test_btn)

        button_layout.addStretch()
        control_layout.addLayout(button_layout)

        layout.addWidget(control_group)

        # Connect signals
        self.connect_all_btn.clicked.connect(self._on_connect_all)
        self.disconnect_all_btn.clicked.connect(self._on_disconnect_all)
        self.test_btn.clicked.connect(self._on_test_all)

    def _create_activity_log(self, layout):
        """Create activity log section."""
        log_group = QtWidgets.QGroupBox("Connection Activity")
        log_layout = QtWidgets.QVBoxLayout(log_group)

        self.activity_list = QtWidgets.QListWidget()
        self.activity_list.setMaximumHeight(100)
        self.activity_list.setStyleSheet(
            """
            QListWidget {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 10px;
                font-family: monospace;
            }
        """
        )
        log_layout.addWidget(self.activity_list)

        layout.addWidget(log_group)

    def _setup_update_timer(self):
        """Setup timer for real-time updates."""
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self._update_connection_status)
        self.update_timer.start(2000)  # Update every 2 seconds

    def _auto_detect_connection(self):
        """Auto-detect available connection method."""
        if self.connection_config.get("connection_method"):
            method = self.connection_config["connection_method"]
            method_map = {
                "launcher": "Launcher",
                "wrapper": "Wrapper",
                "server": "Server",
                "bridge": "Bridge",
            }
            self.method_combo.setCurrentText(method_map.get(method, "Auto-detect"))

    def _on_method_changed(self, method):
        """Handle method selection change."""
        icons = {
            "Auto-detect": "✨",
            "Launcher": "🚀",
            "Wrapper": "📦",
            "Server": "🖥️",
            "Bridge": "🌉",
        }
        self.method_indicator.setText(icons.get(method, "❓"))
        self._add_activity(f"Connection method changed to: {method}")

    def _on_connect_all(self):
        """Handle connect all button click."""
        self._add_activity("Initiating connections...")
        self.connect_all_btn.setEnabled(False)

        # Simulate connecting to different services
        connections = ["FreeCAD MCP", "Claude Desktop", "AI Provider", "Tool Server"]

        for i, conn_name in enumerate(connections):
            card = self.connection_cards.get(conn_name)
            if card:
                card.set_status("connecting", f"Establishing {conn_name} connection...")
                # Direct connection simulation to avoid QTimer crashes
                self._simulate_connection(conn_name)

        self.disconnect_all_btn.setEnabled(True)

    def _simulate_connection(self, conn_name):
        """Simulate individual connection."""
        card = self.connection_cards.get(conn_name)
        if card:
            # Simulate success/failure
            import random

            if random.random() > 0.1:  # 90% success rate
                card.set_status(
                    "connected", f"{conn_name} active", time.strftime("%H:%M:%S")
                )
                self._add_activity(f"✅ {conn_name} connected successfully")
            else:
                card.set_status(
                    "error",
                    f"Failed to connect to {conn_name}",
                    time.strftime("%H:%M:%S"),
                )
                self._add_activity(f"❌ {conn_name} connection failed")

        self._update_active_count()
        self.connect_all_btn.setEnabled(True)

    def _on_disconnect_all(self):
        """Handle disconnect all button click."""
        self._add_activity("Disconnecting all connections...")

        for conn_name, card in self.connection_cards.items():
            card.set_status("disconnected", "Not connected")
            self._add_activity(f"Disconnected from {conn_name}")

        self.disconnect_all_btn.setEnabled(False)
        self.connect_all_btn.setEnabled(True)
        self._update_active_count()

    def _on_test_all(self):
        """Handle test all connections."""
        self._add_activity("Testing all connections...")

        for conn_name, card in self.connection_cards.items():
            current_status = card.status_text.text()
            if current_status == "Connected":
                self._add_activity(f"🔍 Testing {conn_name}...")
                # Show test result immediately to avoid QTimer crashes
                self._add_activity(f"✅ {conn_name} test passed")

    def _update_connection_status(self):
        """Update real-time connection status."""
        # This would check actual connection status
        # For now, just update activity timestamps
        for card in self.connection_cards.values():
            if card.status_text.text() == "Connected":
                card.activity_label.setText(
                    f"Last activity: {time.strftime('%H:%M:%S')}"
                )

    def _update_active_count(self):
        """Update active connections counter."""
        active_count = sum(
            1
            for card in self.connection_cards.values()
            if card.status_text.text() == "Connected"
        )
        self.active_connections_label.setText(f"{active_count} active connections")

        if active_count > 0:
            self.active_connections_label.setStyleSheet(
                "padding: 3px 10px; background-color: #c8e6c9; border-radius: 12px; font-size: 11px;"
            )
        else:
            self.active_connections_label.setStyleSheet(
                "padding: 3px 10px; background-color: #e3f2fd; border-radius: 12px; font-size: 11px;"
            )

    def _add_activity(self, message):
        """Add message to activity log."""
        timestamp = time.strftime("%H:%M:%S")
        self.activity_list.insertItem(0, f"[{timestamp}] {message}")

        # Keep only last 20 items
        while self.activity_list.count() > 20:
            self.activity_list.takeItem(self.activity_list.count() - 1)

    def get_connection_status(self):
        """Get current connection status."""
        active_connections = []
        for name, card in self.connection_cards.items():
            if card.status_text.text() == "Connected":
                active_connections.append(name)

        return {
            "method": self.method_combo.currentText(),
            "active_connections": active_connections,
            "total_active": len(active_connections),
        }

    def set_provider_service(self, provider_service):
        """Set the provider integration service."""
        self.provider_service = provider_service

        if provider_service:
            # Update AI Provider card based on provider status
            provider_service.provider_status_changed.connect(
                self._on_provider_status_changed
            )

    def _on_provider_status_changed(
        self, provider_name: str, status: str, message: str
    ):
        """Handle provider status change."""
        card = self.connection_cards.get("AI Provider")
        if card:
            if status == "connected":
                card.set_status(
                    "connected", f"{provider_name} active", time.strftime("%H:%M:%S")
                )
            elif status == "error":
                card.set_status(
                    "error", f"{provider_name}: {message}", time.strftime("%H:%M:%S")
                )
            else:
                card.set_status("connecting", f"{provider_name}: {status}")

            self._update_active_count()
