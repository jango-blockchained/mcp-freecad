from PySide2.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFrame
from PySide2.QtCore import Qt

class ConnectionStatusDialog(QDialog):
    """
    Dialog to display live connection status for FreeCAD RPC and MCP servers.
    Subscribes to status_changed signals from the connection managers.
    """
    def __init__(self, fc_manager, mcp_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connection Status")
        self.setMinimumWidth(400)
        self.fc_manager = fc_manager
        self.mcp_manager = mcp_manager
        self._build_ui()
        # Connect signals
        self.fc_manager.status_changed.connect(self._update_fc_status)
        self.mcp_manager.status_changed.connect(self._update_mcp_status)
        # Initial update
        self._update_fc_status(self.fc_manager.get_status())
        self._update_mcp_status(self.mcp_manager.get_status())

    def _build_ui(self):
        layout = QVBoxLayout()
        # FreeCAD status
        self.fc_label = QLabel()
        self.fc_label.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        layout.addWidget(QLabel("<b>FreeCAD RPC Server</b>"))
        layout.addWidget(self.fc_label)
        # MCP status
        self.mcp_label = QLabel()
        self.mcp_label.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        layout.addWidget(QLabel("<b>MCP Server</b>"))
        layout.addWidget(self.mcp_label)
        # Close button
        btn_layout = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _update_fc_status(self, status):
        text = self._format_status(status)
        self.fc_label.setText(text)

    def _update_mcp_status(self, status):
        text = self._format_status(status)
        self.mcp_label.setText(text)

    def _format_status(self, status):
        if not status:
            return "<i>No status available</i>"
        lines = []
        mode = status.get("type", "unknown")
        running = status.get("running", False)
        pid = status.get("pid")
        error = status.get("error")
        lines.append(f"<b>Mode:</b> {mode}")
        lines.append(f"<b>Running:</b> {'Yes' if running else 'No'}")
        if pid:
            lines.append(f"<b>PID:</b> {pid}")
        if error:
            lines.append(f"<b>Error:</b> <span style='color:red'>{error}</span>")
        return "<br>".join(lines)
