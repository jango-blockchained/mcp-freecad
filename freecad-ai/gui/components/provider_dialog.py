"""Provider Dialog - Dialog for adding new AI providers"""

from PySide2 import QtWidgets


class ProviderDialog(QtWidgets.QDialog):
    """Dialog for adding new AI providers."""

    def __init__(self, parent=None):
        super(ProviderDialog, self).__init__(parent)
        self.setWindowTitle("Add AI Provider")
        self.setModal(True)
        self.resize(400, 300)
        self._setup_ui()

    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QtWidgets.QVBoxLayout(self)

        # Form layout
        form_layout = QtWidgets.QFormLayout()

        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setPlaceholderText("e.g., 'My Claude Provider'")
        form_layout.addRow("Provider Name:", self.name_input)

        self.type_combo = QtWidgets.QComboBox()
        self.type_combo.addItems(["anthropic", "openai", "google", "openrouter"])
        form_layout.addRow("Provider Type:", self.type_combo)

        self.api_key_input = QtWidgets.QLineEdit()
        self.api_key_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.api_key_input.setPlaceholderText(
            "API key (optional - can be set in API Keys section)"
        )
        form_layout.addRow("API Key:", self.api_key_input)

        self.model_input = QtWidgets.QLineEdit()
        self.model_input.setPlaceholderText(
            "e.g., 'claude-3-sonnet-20240229' (optional)"
        )
        form_layout.addRow("Model:", self.model_input)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()

        self.ok_btn = QtWidgets.QPushButton("Add Provider")
        self.ok_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; }"
        )

        self.cancel_btn = QtWidgets.QPushButton("Cancel")

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.ok_btn)

        layout.addLayout(button_layout)

        # Connect signals
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def get_provider_data(self):
        """Get provider data from dialog."""
        config = {}
        if self.model_input.text():
            config["model"] = self.model_input.text()

        return {
            "name": self.name_input.text(),
            "type": self.type_combo.currentText(),
            "api_key": self.api_key_input.text(),
            "config": config,
        }
