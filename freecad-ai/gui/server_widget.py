"""Server Widget - Functional GUI for managing MCP servers"""

import os
import sys
import subprocess
import json
from datetime import datetime

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
        self.server_pid = None

        # Setup MCP bridge
        self._setup_mcp_bridge()

        # Setup UI
        self._setup_ui()
        self._setup_timer()

        # Initial status update
        self._check_server_status()

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
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)

        # Compact header
        header_layout = QtWidgets.QHBoxLayout()
        header_label = QtWidgets.QLabel("🖥️ Server Management")
        header_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_layout.addWidget(header_label)

        header_layout.addStretch()

        # Live status indicator
        self.live_status = QtWidgets.QLabel("● Checking...")
        self.live_status.setStyleSheet("font-size: 12px; color: orange;")
        header_layout.addWidget(self.live_status)

        layout.addLayout(header_layout)

        # Server status card
        self._create_status_card(layout)

        # Server controls
        self._create_server_controls(layout)

        # Performance monitoring
        self._create_performance_section(layout)

        # Compact logs
        self._create_logs_section(layout)

        layout.addStretch()

    def _create_status_card(self, layout):
        """Create server status card."""
        status_card = QtWidgets.QFrame()
        status_card.setFrameStyle(QtWidgets.QFrame.Box)
        status_card.setStyleSheet("""
            QFrame {
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: #f8f9fa;
                padding: 10px;
            }
        """)

        card_layout = QtWidgets.QVBoxLayout(status_card)

        # Server name and status
        status_layout = QtWidgets.QHBoxLayout()

        self.server_name_label = QtWidgets.QLabel("MCP FreeCAD Server")
        self.server_name_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        status_layout.addWidget(self.server_name_label)

        status_layout.addStretch()

        self.status_label = QtWidgets.QLabel("Stopped")
        self.status_label.setStyleSheet(
            "padding: 3px 10px; background-color: #ffcdd2; color: #c62828; "
            "border-radius: 12px; font-size: 11px; font-weight: bold;"
        )
        status_layout.addWidget(self.status_label)

        card_layout.addLayout(status_layout)

        # Server details
        details_layout = QtWidgets.QGridLayout()
        details_layout.setSpacing(5)

        self.pid_label = QtWidgets.QLabel("PID: -")
        self.pid_label.setStyleSheet("font-size: 11px; color: #666;")
        details_layout.addWidget(self.pid_label, 0, 0)

        self.port_label = QtWidgets.QLabel("Port: 3001")
        self.port_label.setStyleSheet("font-size: 11px; color: #666;")
        details_layout.addWidget(self.port_label, 0, 1)

        self.uptime_label = QtWidgets.QLabel("Uptime: -")
        self.uptime_label.setStyleSheet("font-size: 11px; color: #666;")
        details_layout.addWidget(self.uptime_label, 1, 0)

        self.connections_label = QtWidgets.QLabel("Connections: 0")
        self.connections_label.setStyleSheet("font-size: 11px; color: #666;")
        details_layout.addWidget(self.connections_label, 1, 1)

        card_layout.addLayout(details_layout)

        layout.addWidget(status_card)

    def _create_server_controls(self, layout):
        """Create server control buttons."""
        controls_layout = QtWidgets.QHBoxLayout()

        self.start_btn = QtWidgets.QPushButton("▶ Start")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)

        self.stop_btn = QtWidgets.QPushButton("■ Stop")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        self.stop_btn.setEnabled(False)

        self.restart_btn = QtWidgets.QPushButton("⟳ Restart")
        self.restart_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """)
        self.restart_btn.setEnabled(False)

        controls_layout.addWidget(self.start_btn)
        controls_layout.addWidget(self.stop_btn)
        controls_layout.addWidget(self.restart_btn)
        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # Connect signals
        self.start_btn.clicked.connect(self._on_start_server)
        self.stop_btn.clicked.connect(self._on_stop_server)
        self.restart_btn.clicked.connect(self._on_restart_server)

    def _create_performance_section(self, layout):
        """Create performance monitoring section."""
        perf_frame = QtWidgets.QFrame()
        perf_frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border-radius: 4px;
                padding: 8px;
            }
        """)

        perf_layout = QtWidgets.QHBoxLayout(perf_frame)
        perf_layout.setSpacing(15)

        # CPU usage
        cpu_widget = QtWidgets.QWidget()
        cpu_layout = QtWidgets.QVBoxLayout(cpu_widget)
        cpu_layout.setSpacing(2)
        cpu_layout.setContentsMargins(0, 0, 0, 0)

        cpu_title = QtWidgets.QLabel("CPU")
        cpu_title.setStyleSheet("font-size: 10px; color: #666;")
        cpu_layout.addWidget(cpu_title, alignment=QtCore.Qt.AlignCenter)

        self.cpu_label = QtWidgets.QLabel("0%")
        self.cpu_label.setStyleSheet("font-weight: bold; color: #2196F3; font-size: 14px;")
        cpu_layout.addWidget(self.cpu_label, alignment=QtCore.Qt.AlignCenter)

        perf_layout.addWidget(cpu_widget)

        # Memory usage
        mem_widget = QtWidgets.QWidget()
        mem_layout = QtWidgets.QVBoxLayout(mem_widget)
        mem_layout.setSpacing(2)
        mem_layout.setContentsMargins(0, 0, 0, 0)

        mem_title = QtWidgets.QLabel("Memory")
        mem_title.setStyleSheet("font-size: 10px; color: #666;")
        mem_layout.addWidget(mem_title, alignment=QtCore.Qt.AlignCenter)

        self.memory_label = QtWidgets.QLabel("0 MB")
        self.memory_label.setStyleSheet("font-weight: bold; color: #4CAF50; font-size: 14px;")
        mem_layout.addWidget(self.memory_label, alignment=QtCore.Qt.AlignCenter)

        perf_layout.addWidget(mem_widget)

        # Request rate
        req_widget = QtWidgets.QWidget()
        req_layout = QtWidgets.QVBoxLayout(req_widget)
        req_layout.setSpacing(2)
        req_layout.setContentsMargins(0, 0, 0, 0)

        req_title = QtWidgets.QLabel("Requests/s")
        req_title.setStyleSheet("font-size: 10px; color: #666;")
        req_layout.addWidget(req_title, alignment=QtCore.Qt.AlignCenter)

        self.request_rate_label = QtWidgets.QLabel("0")
        self.request_rate_label.setStyleSheet("font-weight: bold; color: #FF9800; font-size: 14px;")
        req_layout.addWidget(self.request_rate_label, alignment=QtCore.Qt.AlignCenter)

        perf_layout.addWidget(req_widget)

        perf_layout.addStretch()

        layout.addWidget(perf_frame)

    def _create_logs_section(self, layout):
        """Create compact logs display section."""
        logs_frame = QtWidgets.QFrame()
        logs_frame.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border-radius: 4px;
                padding: 5px;
            }
        """)

        logs_layout = QtWidgets.QVBoxLayout(logs_frame)
        logs_layout.setSpacing(2)
        logs_layout.setContentsMargins(5, 5, 5, 5)

        # Logs header
        logs_header = QtWidgets.QHBoxLayout()
        logs_label = QtWidgets.QLabel("📋 Server Logs")
        logs_label.setStyleSheet("color: #ccc; font-size: 11px; font-weight: bold;")
        logs_header.addWidget(logs_label)

        logs_header.addStretch()

        self.clear_logs_btn = QtWidgets.QPushButton("Clear")
        self.clear_logs_btn.setMaximumHeight(20)
        self.clear_logs_btn.setStyleSheet("""
            QPushButton {
                color: #ccc;
                background-color: #333;
                border: 1px solid #555;
                padding: 2px 8px;
                font-size: 10px;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: #444;
            }
        """)
        self.clear_logs_btn.clicked.connect(lambda: self.logs_text.clear())
        logs_header.addWidget(self.clear_logs_btn)

        logs_layout.addLayout(logs_header)

        self.logs_text = QtWidgets.QTextEdit()
        self.logs_text.setMaximumHeight(80)
        self.logs_text.setReadOnly(True)
        self.logs_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ccc;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10px;
                border: none;
            }
        """)
        logs_layout.addWidget(self.logs_text)

        layout.addWidget(logs_frame)

    def _setup_timer(self):
        """Setup timer for periodic updates."""
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(2000)  # Update every 2 seconds

    def _check_server_status(self):
        """Check if MCP server is running."""
        if HAS_PSUTIL:
            # Check for running MCP server process
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info.get('cmdline', []))
                    if 'mcp' in cmdline.lower() and 'freecad' in cmdline.lower():
                        self.server_pid = proc.info['pid']
                        self._update_status("Running", True)
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        self.server_pid = None
        self._update_status("Stopped", False)
        return False

    def _on_start_server(self):
        """Handle start server button click."""
        self._add_log("Starting MCP FreeCAD server...")

        try:
            # Get the workspace root
            workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            start_script = os.path.join(workspace_root, "start_mcp.py")

            if os.path.exists(start_script):
                # Start the server
                process = subprocess.Popen(
                    [sys.executable, start_script],
                    cwd=workspace_root,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                self.server_pid = process.pid
                self._add_log(f"Server started with PID: {self.server_pid}")
                self._update_status("Running", True)
                self.server_started.emit("MCP Server")
            else:
                self._add_log(f"Error: start_mcp.py not found at {start_script}")

        except Exception as e:
            self._add_log(f"Error starting server: {str(e)}")

    def _on_stop_server(self):
        """Handle stop server button click."""
        self._add_log("Stopping MCP FreeCAD server...")

        if self.server_pid and HAS_PSUTIL:
            try:
                proc = psutil.Process(self.server_pid)
                proc.terminate()
                self._add_log(f"Server process {self.server_pid} terminated")
                self.server_pid = None
                self._update_status("Stopped", False)
                self.server_stopped.emit("MCP Server")
            except Exception as e:
                self._add_log(f"Error stopping server: {str(e)}")
        else:
            self._add_log("No server process found to stop")

    def _on_restart_server(self):
        """Handle restart server button click."""
        self._add_log("Restarting server...")
        self._on_stop_server()
        QtCore.QTimer.singleShot(1000, self._on_start_server)

    def _update_status(self, status, is_running):
        """Update server status display."""
        self.live_status.setText(f"● {status}")
        self.status_label.setText(status)

        if is_running:
            self.live_status.setStyleSheet("font-size: 12px; color: #4CAF50;")
            self.status_label.setStyleSheet(
                "padding: 3px 10px; background-color: #c8e6c9; color: #2e7d32; "
                "border-radius: 12px; font-size: 11px; font-weight: bold;"
            )
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.restart_btn.setEnabled(True)

            if self.server_pid:
                self.pid_label.setText(f"PID: {self.server_pid}")
        else:
            self.live_status.setStyleSheet("font-size: 12px; color: #f44336;")
            self.status_label.setStyleSheet(
                "padding: 3px 10px; background-color: #ffcdd2; color: #c62828; "
                "border-radius: 12px; font-size: 11px; font-weight: bold;"
            )
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.restart_btn.setEnabled(False)
            self.pid_label.setText("PID: -")
            self.uptime_label.setText("Uptime: -")

    def _update_display(self):
        """Update performance metrics and status."""
        # Check server status
        self._check_server_status()

        # Update performance metrics if server is running
        if self.server_pid and HAS_PSUTIL:
            try:
                proc = psutil.Process(self.server_pid)

                # CPU usage
                cpu_percent = proc.cpu_percent()
                self.cpu_label.setText(f"{cpu_percent:.1f}%")

                # Memory usage
                memory_info = proc.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                self.memory_label.setText(f"{memory_mb:.0f} MB")

                # Uptime
                create_time = datetime.fromtimestamp(proc.create_time())
                uptime = datetime.now() - create_time
                hours, remainder = divmod(int(uptime.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                self.uptime_label.setText(f"Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}")

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.server_pid = None
                self._update_status("Stopped", False)
        else:
            self.cpu_label.setText("0%")
            self.memory_label.setText("0 MB")
            self.request_rate_label.setText("0")

    def _add_log(self, message):
        """Add message to logs display."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"

        # Add colored log entry
        cursor = self.logs_text.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)

        # Color based on message type
        if "error" in message.lower():
            cursor.insertHtml(f'<span style="color: #ff5252;">{log_entry}</span><br>')
        elif "started" in message.lower() or "success" in message.lower():
            cursor.insertHtml(f'<span style="color: #69f0ae;">{log_entry}</span><br>')
        elif "warning" in message.lower():
            cursor.insertHtml(f'<span style="color: #ffd740;">{log_entry}</span><br>')
        else:
            cursor.insertHtml(f'<span style="color: #ccc;">{log_entry}</span><br>')

        # Auto-scroll to bottom
        self.logs_text.moveCursor(QtGui.QTextCursor.End)
