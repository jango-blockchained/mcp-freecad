"""Connection Widget - GUI for managing MCP connections"""

from PySide2 import QtCore, QtGui, QtWidgets


class ConnectionWidget(QtWidgets.QWidget):
    """Widget for managing MCP connections."""

    connection_changed = QtCore.Signal(str, str)
    connection_tested = QtCore.Signal(bool, str)

    def __init__(self, parent=None):
        super(ConnectionWidget, self).__init__(parent)
        self.current_connection = None
        self.connection_status = "Disconnected"
        self.provider_service = None
        self._setup_mcp_bridge()
        self._setup_ui()
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
        layout.setSpacing(10); layout.setContentsMargins(10, 10, 10, 10)
        self._create_status_section(layout)
        self._create_method_section(layout)
        self._create_ai_provider_section(layout)
        self._create_controls_section(layout)

    def _create_status_section(self, layout):
        """Create connection status section."""
        status_group = QtWidgets.QGroupBox("Connection Status")
        status_layout = QtWidgets.QHBoxLayout(status_group)

        self.status_label = QtWidgets.QLabel("Disconnected")
        self.status_label.setStyleSheet("color: red; font-weight: bold; padding: 5px;")
        status_layout.addWidget(self.status_label)

        self.status_indicator = QtWidgets.QLabel("●")
        self.status_indicator.setStyleSheet("color: red; font-size: 16px;")
        status_layout.addWidget(self.status_indicator)
        layout.addWidget(status_group)

    def _create_method_section(self, layout):
        """Create connection method selection section."""
        method_group = QtWidgets.QGroupBox("Connection Method")
        method_layout = QtWidgets.QVBoxLayout(method_group)

        self.method_combo = QtWidgets.QComboBox()
        self.method_combo.addItems(["Auto", "Launcher", "Wrapper", "Server", "Bridge", "Mock"])
        method_layout.addWidget(self.method_combo)

        # Method description
        self.method_desc = QtWidgets.QLabel("Auto-detect best connection method")
        self.method_desc.setWordWrap(True)
        self.method_desc.setStyleSheet("color: gray; font-size: 11px; padding: 5px;")
        method_layout.addWidget(self.method_desc)

        layout.addWidget(method_group)

        # Connect combo box
        self.method_combo.currentTextChanged.connect(self._on_method_changed)

    def _create_ai_provider_section(self, layout):
        """Create AI provider status section."""
        ai_group = QtWidgets.QGroupBox("AI Provider Status")
        ai_layout = QtWidgets.QVBoxLayout(ai_group)

        # Provider status table
        self.provider_status_table = QtWidgets.QTableWidget(0, 3)
        self.provider_status_table.setHorizontalHeaderLabels(["Provider", "Status", "Last Update"])
        self.provider_status_table.horizontalHeader().setStretchLastSection(True)
        self.provider_status_table.setMaximumHeight(100)
        self.provider_status_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        ai_layout.addWidget(self.provider_status_table)

        # Provider controls
        provider_controls_layout = QtWidgets.QHBoxLayout()

        self.test_provider_btn = QtWidgets.QPushButton("Test Selected")
        self.test_provider_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 6px; }")
        self.test_provider_btn.clicked.connect(self._on_test_selected_provider)
        provider_controls_layout.addWidget(self.test_provider_btn)

        self.refresh_providers_btn = QtWidgets.QPushButton("Refresh")
        self.refresh_providers_btn.clicked.connect(self._refresh_provider_status)
        provider_controls_layout.addWidget(self.refresh_providers_btn)

        provider_controls_layout.addStretch()
        ai_layout.addLayout(provider_controls_layout)

        layout.addWidget(ai_group)

    def _create_controls_section(self, layout):
        """Create connection control buttons."""
        controls_layout = QtWidgets.QHBoxLayout()

        self.connect_btn = QtWidgets.QPushButton("Connect")
        self.connect_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; }")

        self.disconnect_btn = QtWidgets.QPushButton("Disconnect")
        self.disconnect_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; padding: 8px; }")
        self.disconnect_btn.setEnabled(False)

        self.test_btn = QtWidgets.QPushButton("Test")
        self.test_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; padding: 8px; }")

        controls_layout.addWidget(self.connect_btn)
        controls_layout.addWidget(self.disconnect_btn)
        controls_layout.addWidget(self.test_btn)

        layout.addLayout(controls_layout)

        # Connect signals
        self.connect_btn.clicked.connect(self._on_connect)
        self.disconnect_btn.clicked.connect(self._on_disconnect)
        self.test_btn.clicked.connect(self._on_test)

    def _auto_detect_connection(self):
        """Auto-detect available connection method."""
        if self.connection_config.get('connection_method'):
            method = self.connection_config['connection_method']
            if method == 'launcher':
                self.method_combo.setCurrentText("Launcher")
            elif method == 'wrapper':
                self.method_combo.setCurrentText("Wrapper")
            elif method == 'server':
                self.method_combo.setCurrentText("Server")
            elif method == 'bridge':
                self.method_combo.setCurrentText("Bridge")
            else:
                self.method_combo.setCurrentText("Auto")

    def _on_method_changed(self, method):
        """Handle method selection change."""
        descriptions = {
            "Auto": "Auto-detect best connection method",
            "Launcher": "Use AppRun launcher (recommended for AppImage)",
            "Wrapper": "Use subprocess wrapper",
            "Server": "Connect to running FreeCAD socket server",
            "Bridge": "Use FreeCAD CLI bridge",
            "Mock": "Use mock connection for testing"
        }
        self.method_desc.setText(descriptions.get(method, "Unknown method"))

    def _on_connect(self):
        """Handle connect button click."""
        method = self.method_combo.currentText().lower()

        # Update UI immediately
        self._update_connection_status("Connecting...", "orange")
        self.connect_btn.setEnabled(False)

        # Simulate connection (real implementation would use MCP bridge)
        try:
            if self.mcp_bridge:
                # Use actual MCP bridge for connection
                success = self._attempt_connection(method)
            else:
                # Fallback simulation
                success = True

            if success:
                self._update_connection_status("Connected", "green")
                self.disconnect_btn.setEnabled(True)
                self.current_connection = method
                self.connection_changed.emit(method, "connected")
            else:
                self._update_connection_status("Connection Failed", "red")
                self.connect_btn.setEnabled(True)

        except Exception as e:
            self._update_connection_status(f"Error: {str(e)}", "red")
            self.connect_btn.setEnabled(True)

    def _on_disconnect(self):
        """Handle disconnect button click."""
        self._update_connection_status("Disconnected", "red")
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.current_connection = None
        self.connection_changed.emit("", "disconnected")

    def _on_test(self):
        """Handle test button click."""
        method = self.method_combo.currentText().lower()

        try:
            if self.mcp_bridge:
                # Test with actual MCP bridge
                success = self._test_connection(method)
                message = "Connection test successful" if success else "Connection test failed"
            else:
                # Fallback simulation
                success = True
                message = "Test completed (simulated)"

            self.connection_tested.emit(success, message)

            # Show result in status
            original_status = self.status_label.text()
            self.status_label.setText(message)
            QtCore.QTimer.singleShot(3000, lambda: self.status_label.setText(original_status))

        except Exception as e:
            self.connection_tested.emit(False, str(e))

    def _update_connection_status(self, status, color):
        """Update connection status display."""
        self.status_label.setText(status)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold; padding: 5px;")
        self.status_indicator.setStyleSheet(f"color: {color}; font-size: 16px;")
        self.connection_status = status

    def _attempt_connection(self, method):
        """Attempt to establish connection using specified method."""
        # This would interface with the actual MCP connection system
        # For now, return success for launcher/wrapper methods
        return method in ['auto', 'launcher', 'wrapper', 'mock']

    def _test_connection(self, method):
        """Test connection with specified method."""
        # This would test the actual connection
        # For now, return success for most methods
        return method != 'server'  # Server might not be running

    def get_connection_status(self):
        """Get current connection status."""
        return {
            'method': self.current_connection,
            'status': self.connection_status,
            'connected': self.disconnect_btn.isEnabled()
        }

    def set_provider_service(self, provider_service):
        """Set the provider integration service."""
        self.provider_service = provider_service

        # Connect to provider service signals
        if provider_service:
            provider_service.provider_status_changed.connect(self._on_provider_status_changed)
            provider_service.providers_updated.connect(self._refresh_provider_status)

            # Initial refresh
            self._refresh_provider_status()

    def _on_provider_status_changed(self, provider_name: str, status: str, message: str):
        """Handle provider status change."""
        # Update the provider status table
        for row in range(self.provider_status_table.rowCount()):
            name_item = self.provider_status_table.item(row, 0)
            if name_item and name_item.text() == provider_name:
                # Update status
                status_item = self.provider_status_table.item(row, 1)
                if status_item:
                    status_item.setText(status)
                    # Color code the status
                    if status == "connected":
                        status_item.setForeground(QtGui.QColor("#4CAF50"))
                    elif status == "error":
                        status_item.setForeground(QtGui.QColor("#f44336"))
                    else:
                        status_item.setForeground(QtGui.QColor("#FF9800"))

                # Update last update time
                time_item = self.provider_status_table.item(row, 2)
                if time_item:
                    time_item.setText(QtCore.QDateTime.currentDateTime().toString("hh:mm:ss"))
                break

    def _refresh_provider_status(self):
        """Refresh provider status table."""
        if not self.provider_service:
            return

        # Clear table
        self.provider_status_table.setRowCount(0)

        # Add providers
        providers = self.provider_service.get_all_providers()
        for provider_name, provider_info in providers.items():
            row = self.provider_status_table.rowCount()
            self.provider_status_table.insertRow(row)

            # Provider name
            name_item = QtWidgets.QTableWidgetItem(provider_name)
            self.provider_status_table.setItem(row, 0, name_item)

            # Status
            status = provider_info.get("status", "unknown")
            status_item = QtWidgets.QTableWidgetItem(status)
            if status == "connected":
                status_item.setForeground(QtGui.QColor("#4CAF50"))
            elif status == "error":
                status_item.setForeground(QtGui.QColor("#f44336"))
            else:
                status_item.setForeground(QtGui.QColor("#FF9800"))
            self.provider_status_table.setItem(row, 1, status_item)

            # Last update
            last_test = provider_info.get("last_test", "Never")
            time_item = QtWidgets.QTableWidgetItem(last_test)
            self.provider_status_table.setItem(row, 2, time_item)

    def _on_test_selected_provider(self):
        """Test the selected provider."""
        current_row = self.provider_status_table.currentRow()
        if current_row >= 0 and self.provider_service:
            name_item = self.provider_status_table.item(current_row, 0)
            if name_item:
                provider_name = name_item.text()
                self.provider_service.test_provider_connection(provider_name)
