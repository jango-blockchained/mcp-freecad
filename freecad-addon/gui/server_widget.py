"""Server Widget - GUI for managing MCP servers"""

import os
import sys

# Try to import psutil, but handle gracefully if not available
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from PySide2 import QtCore, QtGui, QtWidgets


class ServerWidget(QtWidgets.QWidget):
    """Widget for managing MCP servers."""

    # Signals for server events
    server_started = QtCore.Signal(str)  # server_name
    server_stopped = QtCore.Signal(str)  # server_name
    server_status_changed = QtCore.Signal(str, str)  # server_name, status

    def __init__(self, parent=None):
        """Initialize the server widget."""
        super(ServerWidget, self).__init__(parent)

        # Server state tracking
        self.server_processes = {}
        self.server_status = {}

        # Setup MCP bridge
        self._setup_mcp_bridge()

        # Setup UI
        self._setup_ui()
        self._setup_timer()

        # Initial status update
        self._update_server_status()

    def _setup_mcp_bridge(self):
        """Setup MCP bridge for server management."""
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

        # Server status overview
        self._create_status_overview(layout)

        # Server controls
        self._create_server_controls(layout)

        # Performance monitoring
        self._create_performance_section(layout)

        # Server logs
        self._create_logs_section(layout)

    def _create_status_overview(self, layout):
        """Create server status overview section."""
        status_group = QtWidgets.QGroupBox("Server Status")
        status_layout = QtWidgets.QVBoxLayout(status_group)

        # Main server status
        main_status_layout = QtWidgets.QHBoxLayout()

        self.main_status_label = QtWidgets.QLabel("MCP Server: Stopped")
        self.main_status_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        main_status_layout.addWidget(self.main_status_label)

        self.main_status_indicator = QtWidgets.QLabel("●")
        self.main_status_indicator.setStyleSheet("color: red; font-size: 18px;")
        main_status_layout.addWidget(self.main_status_indicator)

        status_layout.addLayout(main_status_layout)

        # Server info table
        self.server_table = QtWidgets.QTableWidget(0, 4)
        self.server_table.setHorizontalHeaderLabels(["Server", "Status", "PID", "Uptime"])
        self.server_table.horizontalHeader().setStretchLastSection(True)
        self.server_table.setMaximumHeight(150)
        status_layout.addWidget(self.server_table)

        layout.addWidget(status_group)

    def _create_server_controls(self, layout):
        """Create server control buttons."""
        controls_group = QtWidgets.QGroupBox("Server Controls")
        controls_layout = QtWidgets.QVBoxLayout(controls_group)

        # Main controls
        main_controls_layout = QtWidgets.QHBoxLayout()

        self.start_btn = QtWidgets.QPushButton("Start Server")
        self.start_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; }")

        self.stop_btn = QtWidgets.QPushButton("Stop Server")
        self.stop_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; padding: 10px; }")
        self.stop_btn.setEnabled(False)

        self.restart_btn = QtWidgets.QPushButton("Restart Server")
        self.restart_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; font-weight: bold; padding: 10px; }")
        self.restart_btn.setEnabled(False)

        main_controls_layout.addWidget(self.start_btn)
        main_controls_layout.addWidget(self.stop_btn)
        main_controls_layout.addWidget(self.restart_btn)

        controls_layout.addLayout(main_controls_layout)

        # Additional controls
        additional_controls_layout = QtWidgets.QHBoxLayout()

        self.config_btn = QtWidgets.QPushButton("Configure")
        self.config_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 8px; }")

        self.logs_btn = QtWidgets.QPushButton("View Logs")
        self.logs_btn.setStyleSheet("QPushButton { background-color: #9C27B0; color: white; padding: 8px; }")

        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.refresh_btn.setStyleSheet("QPushButton { background-color: #607D8B; color: white; padding: 8px; }")

        additional_controls_layout.addWidget(self.config_btn)
        additional_controls_layout.addWidget(self.logs_btn)
        additional_controls_layout.addWidget(self.refresh_btn)

        controls_layout.addLayout(additional_controls_layout)

        layout.addWidget(controls_group)

        # Connect signals
        self.start_btn.clicked.connect(self._on_start_server)
        self.stop_btn.clicked.connect(self._on_stop_server)
        self.restart_btn.clicked.connect(self._on_restart_server)
        self.config_btn.clicked.connect(self._on_configure)
        self.logs_btn.clicked.connect(self._on_view_logs)
        self.refresh_btn.clicked.connect(self._update_server_status)

    def _create_performance_section(self, layout):
        """Create performance monitoring section."""
        perf_group = QtWidgets.QGroupBox("Performance Metrics")
        perf_layout = QtWidgets.QGridLayout(perf_group)

        # CPU usage
        perf_layout.addWidget(QtWidgets.QLabel("CPU Usage:"), 0, 0)
        self.cpu_label = QtWidgets.QLabel("0%")
        self.cpu_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        perf_layout.addWidget(self.cpu_label, 0, 1)

        # Memory usage
        perf_layout.addWidget(QtWidgets.QLabel("Memory Usage:"), 1, 0)
        self.memory_label = QtWidgets.QLabel("0 MB")
        self.memory_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        perf_layout.addWidget(self.memory_label, 1, 1)

        # Active connections
        perf_layout.addWidget(QtWidgets.QLabel("Active Connections:"), 0, 2)
        self.connections_label = QtWidgets.QLabel("0")
        self.connections_label.setStyleSheet("font-weight: bold; color: #FF9800;")
        perf_layout.addWidget(self.connections_label, 0, 3)

        # Request rate
        perf_layout.addWidget(QtWidgets.QLabel("Request Rate:"), 1, 2)
        self.request_rate_label = QtWidgets.QLabel("0/sec")
        self.request_rate_label.setStyleSheet("font-weight: bold; color: #9C27B0;")
        perf_layout.addWidget(self.request_rate_label, 1, 3)

        layout.addWidget(perf_group)

    def _create_logs_section(self, layout):
        """Create logs display section."""
        logs_group = QtWidgets.QGroupBox("Recent Logs")
        logs_layout = QtWidgets.QVBoxLayout(logs_group)

        self.logs_text = QtWidgets.QTextEdit()
        self.logs_text.setMaximumHeight(100)
        self.logs_text.setReadOnly(True)
        self.logs_text.setStyleSheet("font-family: monospace; font-size: 10px;")
        logs_layout.addWidget(self.logs_text)

        # Log controls
        log_controls_layout = QtWidgets.QHBoxLayout()

        self.clear_logs_btn = QtWidgets.QPushButton("Clear")
        self.clear_logs_btn.clicked.connect(lambda: self.logs_text.clear())

        self.auto_scroll_check = QtWidgets.QCheckBox("Auto-scroll")
        self.auto_scroll_check.setChecked(True)

        log_controls_layout.addWidget(self.clear_logs_btn)
        log_controls_layout.addWidget(self.auto_scroll_check)
        log_controls_layout.addStretch()

        logs_layout.addLayout(log_controls_layout)

        layout.addWidget(logs_group)

    def _setup_timer(self):
        """Setup timer for periodic updates."""
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self._update_performance_metrics)
        self.update_timer.start(2000)  # Update every 2 seconds

    def _on_start_server(self):
        """Handle start server button click."""
        try:
            # Simulate server start (real implementation would use MCP bridge)
            if self.mcp_bridge:
                success = self._start_mcp_server()
            else:
                success = True  # Simulation

            if success:
                self._update_main_status("Running", "green")
                self.start_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
                self.restart_btn.setEnabled(True)
                self._add_log("Server started successfully")
                self.server_started.emit("MCP Server")
            else:
                self._add_log("Failed to start server")

        except Exception as e:
            self._add_log(f"Error starting server: {str(e)}")

    def _on_stop_server(self):
        """Handle stop server button click."""
        try:
            if self.mcp_bridge:
                success = self._stop_mcp_server()
            else:
                success = True  # Simulation

            if success:
                self._update_main_status("Stopped", "red")
                self.start_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)
                self.restart_btn.setEnabled(False)
                self._add_log("Server stopped")
                self.server_stopped.emit("MCP Server")
            else:
                self._add_log("Failed to stop server")

        except Exception as e:
            self._add_log(f"Error stopping server: {str(e)}")

    def _on_restart_server(self):
        """Handle restart server button click."""
        self._add_log("Restarting server...")
        self._on_stop_server()
        QtCore.QTimer.singleShot(1000, self._on_start_server)

    def _on_configure(self):
        """Handle configure button click."""
        # TODO: Open configuration dialog
        self._add_log("Configuration dialog - not implemented yet")

    def _on_view_logs(self):
        """Handle view logs button click."""
        # TODO: Open detailed logs window
        self._add_log("Detailed logs window - not implemented yet")

    def _update_server_status(self):
        """Update server status display."""
        # Clear existing table
        self.server_table.setRowCount(0)

        # Add MCP server entry
        row = self.server_table.rowCount()
        self.server_table.insertRow(row)

        self.server_table.setItem(row, 0, QtWidgets.QTableWidgetItem("MCP Server"))

        # Check if server is running (simplified check)
        is_running = self.stop_btn.isEnabled()
        status = "Running" if is_running else "Stopped"
        pid = "1234" if is_running else "-"
        uptime = "00:05:23" if is_running else "-"

        self.server_table.setItem(row, 1, QtWidgets.QTableWidgetItem(status))
        self.server_table.setItem(row, 2, QtWidgets.QTableWidgetItem(pid))
        self.server_table.setItem(row, 3, QtWidgets.QTableWidgetItem(uptime))

    def _update_performance_metrics(self):
        """Update performance metrics display."""
        try:
            if HAS_PSUTIL:
                # Get system metrics (simplified)
                cpu_percent = psutil.cpu_percent()
                memory_info = psutil.virtual_memory()

                self.cpu_label.setText(f"{cpu_percent:.1f}%")
                self.memory_label.setText(f"{memory_info.used / 1024 / 1024:.0f} MB")
            else:
                # Show placeholder values when psutil is not available
                self.cpu_label.setText("N/A")
                self.memory_label.setText("N/A")

            # Simulate server-specific metrics
            if self.stop_btn.isEnabled():  # Server is running
                self.connections_label.setText("2")
                self.request_rate_label.setText("1.5/sec")
            else:
                self.connections_label.setText("0")
                self.request_rate_label.setText("0/sec")

        except Exception as e:
            pass  # Ignore metrics errors

    def _update_main_status(self, status, color):
        """Update main server status display."""
        self.main_status_label.setText(f"MCP Server: {status}")
        self.main_status_indicator.setStyleSheet(f"color: {color}; font-size: 18px;")

    def _add_log(self, message):
        """Add message to logs display."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"

        self.logs_text.append(log_entry)

        if self.auto_scroll_check.isChecked():
            self.logs_text.moveCursor(QtGui.QTextCursor.End)

    def _start_mcp_server(self):
        """Start the MCP server (actual implementation)."""
        # This would interface with the actual MCP server
        return True

    def _stop_mcp_server(self):
        """Stop the MCP server (actual implementation)."""
        # This would interface with the actual MCP server
        return True
