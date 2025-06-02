from PySide2.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QFileDialog, QMessageBox, QLabel, QHBoxLayout
from PySide2.QtCore import Qt

class SettingsDialog(QDialog):
    """
    Dialog for configuring FreeCAD RPC and MCP server settings.
    On save, calls the provided on_save callback with the new settings dict.
    """
    def __init__(self, current_settings: dict, on_save, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MCP Indicator Settings")
        self.setModal(True)
        self.on_save = on_save
        self.current_settings = current_settings
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        # FreeCAD RPC
        self.fc_host_edit = QLineEdit(self.current_settings.get("fc_host", "localhost"))
        self.fc_port_edit = QLineEdit(str(self.current_settings.get("fc_port", 9875)))
        form.addRow("FreeCAD RPC Host:", self.fc_host_edit)
        form.addRow("FreeCAD RPC Port:", self.fc_port_edit)

        # MCP
        self.mcp_host_edit = QLineEdit(self.current_settings.get("mcp_host", "localhost"))
        self.mcp_port_edit = QLineEdit(str(self.current_settings.get("mcp_port", 8000)))
        self.mcp_script_edit = QLineEdit(self.current_settings.get("mcp_script", ""))
        mcp_script_btn = QPushButton("Browse...")
        mcp_script_btn.clicked.connect(self._browse_mcp_script)
        mcp_script_layout = QHBoxLayout()
        mcp_script_layout.addWidget(self.mcp_script_edit)
        mcp_script_layout.addWidget(mcp_script_btn)
        form.addRow("MCP Server Host:", self.mcp_host_edit)
        form.addRow("MCP Server Port:", self.mcp_port_edit)
        form.addRow("MCP Server Script:", mcp_script_layout)

        layout.addLayout(form)

        # Save/Cancel
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        save_btn.clicked.connect(self._on_save)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def _browse_mcp_script(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select MCP Server Script", "", "Python Scripts (*.py);;All Files (*)")
        if path:
            self.mcp_script_edit.setText(path)

    def _on_save(self):
        # Validate
        try:
            fc_port = int(self.fc_port_edit.text())
            mcp_port = int(self.mcp_port_edit.text())
        except ValueError:
            QMessageBox.critical(self, "Invalid Input", "Ports must be integers.")
            return
        mcp_script = self.mcp_script_edit.text().strip()
        if not mcp_script:
            QMessageBox.critical(self, "Invalid Input", "MCP server script path is required.")
            return
        # Gather settings
        settings = {
            "fc_host": self.fc_host_edit.text().strip(),
            "fc_port": fc_port,
            "mcp_host": self.mcp_host_edit.text().strip(),
            "mcp_port": mcp_port,
            "mcp_script": mcp_script
        }
        # Call callback
        self.on_save(settings)
        self.accept()
