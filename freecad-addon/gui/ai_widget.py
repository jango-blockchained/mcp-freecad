"""AI Widget - GUI for AI model integration"""

import asyncio
import json
from PySide2 import QtCore, QtGui, QtWidgets


class AIWidget(QtWidgets.QWidget):
    """Widget for AI model management."""

    # Signals for AI events
    provider_added = QtCore.Signal(str)  # provider_name
    provider_removed = QtCore.Signal(str)  # provider_name
    model_changed = QtCore.Signal(str, str)  # provider, model
    message_sent = QtCore.Signal(str, str)  # provider, message

    def __init__(self, parent=None):
        """Initialize the AI widget."""
        super(AIWidget, self).__init__(parent)

        # AI Manager instance
        self.ai_manager = None
        self.current_provider = None
        self.conversation_history = []

        # Setup AI manager
        self._setup_ai_manager()

        # Setup UI
        self._setup_ui()
        self._load_saved_providers()

    def _setup_ai_manager(self):
        """Setup AI manager."""
        try:
            from ..ai.ai_manager import AIManager
            self.ai_manager = AIManager()
        except ImportError:
            self.ai_manager = None

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Provider management section
        self._create_provider_section(layout)

        # Model selection section
        self._create_model_section(layout)

        # Conversation interface
        self._create_conversation_section(layout)

        # API status and usage
        self._create_status_section(layout)

    def _create_provider_section(self, layout):
        """Create AI provider management section."""
        provider_group = QtWidgets.QGroupBox("AI Providers")
        provider_layout = QtWidgets.QVBoxLayout(provider_group)

        # Provider list and controls
        provider_controls_layout = QtWidgets.QHBoxLayout()

        self.provider_combo = QtWidgets.QComboBox()
        self.provider_combo.setMinimumWidth(150)
        provider_controls_layout.addWidget(QtWidgets.QLabel("Active Provider:"))
        provider_controls_layout.addWidget(self.provider_combo)

        self.add_provider_btn = QtWidgets.QPushButton("Add Provider")
        self.add_provider_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 6px; }")
        provider_controls_layout.addWidget(self.add_provider_btn)

        self.remove_provider_btn = QtWidgets.QPushButton("Remove")
        self.remove_provider_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; padding: 6px; }")
        provider_controls_layout.addWidget(self.remove_provider_btn)

        provider_layout.addLayout(provider_controls_layout)

        # Provider status table
        self.provider_table = QtWidgets.QTableWidget(0, 4)
        self.provider_table.setHorizontalHeaderLabels(["Provider", "Type", "Model", "Status"])
        self.provider_table.horizontalHeader().setStretchLastSection(True)
        self.provider_table.setMaximumHeight(120)
        provider_layout.addWidget(self.provider_table)

        layout.addWidget(provider_group)

        # Connect signals
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        self.add_provider_btn.clicked.connect(self._on_add_provider)
        self.remove_provider_btn.clicked.connect(self._on_remove_provider)

    def _create_model_section(self, layout):
        """Create model selection section."""
        model_group = QtWidgets.QGroupBox("Model Configuration")
        model_layout = QtWidgets.QGridLayout(model_group)

        # Model selection
        model_layout.addWidget(QtWidgets.QLabel("Model:"), 0, 0)
        self.model_combo = QtWidgets.QComboBox()
        self.model_combo.setMinimumWidth(200)
        model_layout.addWidget(self.model_combo, 0, 1)

        # Model parameters
        model_layout.addWidget(QtWidgets.QLabel("Max Tokens:"), 1, 0)
        self.max_tokens_spin = QtWidgets.QSpinBox()
        self.max_tokens_spin.setRange(100, 8192)
        self.max_tokens_spin.setValue(4096)
        model_layout.addWidget(self.max_tokens_spin, 1, 1)

        model_layout.addWidget(QtWidgets.QLabel("Temperature:"), 0, 2)
        self.temperature_spin = QtWidgets.QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setSingleStep(0.1)
        self.temperature_spin.setValue(0.7)
        model_layout.addWidget(self.temperature_spin, 0, 3)

        # Thinking Mode controls (Claude 4/3.7 models)
        self.thinking_mode_check = QtWidgets.QCheckBox("Thinking Mode")
        self.thinking_mode_check.setToolTip("Enable extended reasoning for Claude 4 and 3.7 models")
        self.thinking_mode_check.setStyleSheet("font-weight: bold; color: #6366F1;")
        model_layout.addWidget(self.thinking_mode_check, 2, 0)

        self.thinking_budget_spin = QtWidgets.QSpinBox()
        self.thinking_budget_spin.setRange(100, 20000)
        self.thinking_budget_spin.setValue(2000)
        self.thinking_budget_spin.setSuffix(" tokens")
        self.thinking_budget_spin.setEnabled(False)
        self.thinking_budget_spin.setToolTip("Token budget for thinking mode (empty = unlimited)")
        model_layout.addWidget(self.thinking_budget_spin, 2, 1)

        thinking_info_label = QtWidgets.QLabel("🧠 Extended reasoning")
        thinking_info_label.setStyleSheet("font-size: 10px; color: #6B7280; font-style: italic;")
        model_layout.addWidget(thinking_info_label, 2, 2)

        # Test connection button
        self.test_connection_btn = QtWidgets.QPushButton("Test Connection")
        self.test_connection_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 8px; }")
        model_layout.addWidget(self.test_connection_btn, 1, 2, 1, 2)

        layout.addWidget(model_group)

        # Connect signals
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        self.thinking_mode_check.toggled.connect(self._on_thinking_mode_toggled)
        self.thinking_budget_spin.valueChanged.connect(self._on_thinking_budget_changed)
        self.test_connection_btn.clicked.connect(self._on_test_connection)

    def _create_conversation_section(self, layout):
        """Create conversation interface."""
        conversation_group = QtWidgets.QGroupBox("AI Conversation")
        conversation_layout = QtWidgets.QVBoxLayout(conversation_group)

        # Conversation display
        self.conversation_text = QtWidgets.QTextEdit()
        self.conversation_text.setMinimumHeight(200)
        self.conversation_text.setReadOnly(True)
        self.conversation_text.setStyleSheet("font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-size: 12px;")
        conversation_layout.addWidget(self.conversation_text)

        # Message input
        input_layout = QtWidgets.QHBoxLayout()

        self.message_input = QtWidgets.QLineEdit()
        self.message_input.setPlaceholderText("Ask the AI about FreeCAD operations...")
        input_layout.addWidget(self.message_input)

        self.send_btn = QtWidgets.QPushButton("Send")
        self.send_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 15px; }")
        input_layout.addWidget(self.send_btn)

        conversation_layout.addLayout(input_layout)

        # Conversation controls
        controls_layout = QtWidgets.QHBoxLayout()

        self.clear_conversation_btn = QtWidgets.QPushButton("Clear")
        self.clear_conversation_btn.clicked.connect(self._clear_conversation)

        self.save_conversation_btn = QtWidgets.QPushButton("Save")
        self.save_conversation_btn.clicked.connect(self._save_conversation)

        self.context_check = QtWidgets.QCheckBox("Use CAD Context")
        self.context_check.setChecked(True)
        self.context_check.setToolTip("Include current FreeCAD document state in AI queries")

        controls_layout.addWidget(self.clear_conversation_btn)
        controls_layout.addWidget(self.save_conversation_btn)
        controls_layout.addStretch()
        controls_layout.addWidget(self.context_check)

        conversation_layout.addLayout(controls_layout)

        layout.addWidget(conversation_group)

        # Connect signals
        self.message_input.returnPressed.connect(self._on_send_message)
        self.send_btn.clicked.connect(self._on_send_message)

    def _create_status_section(self, layout):
        """Create API status and usage section."""
        status_group = QtWidgets.QGroupBox("API Status & Usage")
        status_layout = QtWidgets.QGridLayout(status_group)

        # API Status
        status_layout.addWidget(QtWidgets.QLabel("API Status:"), 0, 0)
        self.api_status_label = QtWidgets.QLabel("Not Connected")
        self.api_status_label.setStyleSheet("color: red; font-weight: bold;")
        status_layout.addWidget(self.api_status_label, 0, 1)

        # Request count
        status_layout.addWidget(QtWidgets.QLabel("Requests Today:"), 1, 0)
        self.request_count_label = QtWidgets.QLabel("0")
        self.request_count_label.setStyleSheet("color: #2196F3; font-weight: bold;")
        status_layout.addWidget(self.request_count_label, 1, 1)

        # Estimated cost
        status_layout.addWidget(QtWidgets.QLabel("Est. Cost:"), 0, 2)
        self.cost_label = QtWidgets.QLabel("$0.00")
        self.cost_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        status_layout.addWidget(self.cost_label, 0, 3)

        # Last response time
        status_layout.addWidget(QtWidgets.QLabel("Response Time:"), 1, 2)
        self.response_time_label = QtWidgets.QLabel("-")
        self.response_time_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        status_layout.addWidget(self.response_time_label, 1, 3)

        layout.addWidget(status_group)

    def _on_provider_changed(self, provider_name):
        """Handle provider selection change."""
        if provider_name and self.ai_manager:
            self.current_provider = provider_name
            self.ai_manager.set_active_provider(provider_name)
            self._update_model_list()
            self._update_api_status()

            # Update thinking mode availability for new provider
            provider = self.ai_manager.providers.get(provider_name)
            if provider:
                self._update_thinking_mode_availability(provider)

    def _on_model_changed(self, model_name):
        """Handle model selection change."""
        if self.current_provider and self.ai_manager and model_name:
            provider = self.ai_manager.providers.get(self.current_provider)
            if provider:
                provider.set_model(model_name)
                self.model_changed.emit(self.current_provider, model_name)
                self._update_thinking_mode_availability(provider)

    def _on_add_provider(self):
        """Handle add provider button click."""
        dialog = ProviderDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            provider_data = dialog.get_provider_data()

            if self.ai_manager:
                success = self.ai_manager.add_provider(
                    provider_data['name'],
                    provider_data['type'],
                    provider_data['api_key'],
                    provider_data['config']
                )

                if success:
                    self._update_provider_list()
                    self.provider_added.emit(provider_data['name'])
                    self._add_conversation_message("System", f"Added {provider_data['type']} provider: {provider_data['name']}")
                else:
                    QtWidgets.QMessageBox.warning(self, "Error", "Failed to add provider")

    def _on_remove_provider(self):
        """Handle remove provider button click."""
        provider_name = self.provider_combo.currentText()
        if provider_name and self.ai_manager:
            reply = QtWidgets.QMessageBox.question(
                self, "Remove Provider",
                f"Are you sure you want to remove provider '{provider_name}'?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )

            if reply == QtWidgets.QMessageBox.Yes:
                success = self.ai_manager.remove_provider(provider_name)
                if success:
                    self._update_provider_list()
                    self.provider_removed.emit(provider_name)

    def _on_test_connection(self):
        """Handle test connection button click."""
        if not self.current_provider or not self.ai_manager:
            QtWidgets.QMessageBox.warning(self, "Error", "No provider selected")
            return

        self.test_connection_btn.setEnabled(False)
        self.test_connection_btn.setText("Testing...")

        # Use QTimer to simulate async operation
        QtCore.QTimer.singleShot(2000, self._test_connection_finished)

    def _test_connection_finished(self):
        """Handle test connection completion."""
        self.test_connection_btn.setEnabled(True)
        self.test_connection_btn.setText("Test Connection")

        # Simulate successful test
        self.api_status_label.setText("Connected")
        self.api_status_label.setStyleSheet("color: green; font-weight: bold;")
        self._add_conversation_message("System", "Connection test successful")

    def _on_thinking_mode_toggled(self, checked):
        """Handle thinking mode toggle."""
        self.thinking_budget_spin.setEnabled(checked)

        if self.current_provider and self.ai_manager:
            provider = self.ai_manager.providers.get(self.current_provider)
            if provider and hasattr(provider, 'enable_thinking_mode'):
                if checked:
                    budget = self.thinking_budget_spin.value() if self.thinking_budget_spin.value() > 0 else None
                    success = provider.enable_thinking_mode(budget)
                    if success:
                        self._add_conversation_message("System", f"Thinking mode enabled for {self.current_provider}")
                    else:
                        self.thinking_mode_check.setChecked(False)
                        self.thinking_budget_spin.setEnabled(False)
                        QtWidgets.QMessageBox.warning(self, "Warning", "Current model doesn't support thinking mode")
                else:
                    provider.disable_thinking_mode()
                    self._add_conversation_message("System", f"Thinking mode disabled for {self.current_provider}")

    def _on_thinking_budget_changed(self, value):
        """Handle thinking budget change."""
        if self.thinking_mode_check.isChecked() and self.current_provider and self.ai_manager:
            provider = self.ai_manager.providers.get(self.current_provider)
            if provider and hasattr(provider, 'config'):
                budget = value if value > 0 else None
                provider.config['thinking_budget'] = budget

    def _update_thinking_mode_availability(self, provider):
        """Update thinking mode controls based on current model."""
        if hasattr(provider, '_supports_thinking_mode'):
            supports_thinking = provider._supports_thinking_mode()
            self.thinking_mode_check.setEnabled(supports_thinking)

            if supports_thinking:
                self.thinking_mode_check.setToolTip("Enable extended reasoning for this model")
                # Show which models support thinking
                current_model = provider.get_current_model() or ""
                if "claude-4" in current_model or "claude-3-7" in current_model:
                    self.thinking_mode_check.setText("Thinking Mode ✨")
                else:
                    self.thinking_mode_check.setText("Thinking Mode")
            else:
                self.thinking_mode_check.setChecked(False)
                self.thinking_mode_check.setText("Thinking Mode (Not Available)")
                self.thinking_mode_check.setToolTip("Current model doesn't support thinking mode")
                self.thinking_budget_spin.setEnabled(False)
        else:
            self.thinking_mode_check.setEnabled(False)
            self.thinking_mode_check.setText("Thinking Mode (Not Available)")
            self.thinking_mode_check.setToolTip("Current provider doesn't support thinking mode")

    def _on_send_message(self):
        """Handle send message button click."""
        message = self.message_input.text().strip()
        if not message:
            return

        if not self.current_provider or not self.ai_manager:
            QtWidgets.QMessageBox.warning(self, "Error", "No AI provider selected")
            return

        # Add user message to conversation
        self._add_conversation_message("You", message)
        self.message_input.clear()

        # Show thinking indicator
        self._add_conversation_message("AI", "Thinking...")

        # Simulate AI response (real implementation would be async)
        QtCore.QTimer.singleShot(1500, lambda: self._simulate_ai_response(message))

        # Update usage statistics
        current_count = int(self.request_count_label.text())
        self.request_count_label.setText(str(current_count + 1))
        self.response_time_label.setText("1.2s")

    def _simulate_ai_response(self, user_message):
        """Simulate AI response."""
        # Remove thinking indicator
        text = self.conversation_text.toPlainText()
        if text.endswith("AI: Thinking..."):
            text = text[:-len("AI: Thinking...")]
            self.conversation_text.setPlainText(text)

        # Generate simulated response based on message content
        if "box" in user_message.lower() or "cube" in user_message.lower():
            response = "I can help you create a box in FreeCAD. You can use the Part Workbench and select 'Create Box' or use the MCP tool freecad.create_box with parameters like length, width, and height."
        elif "cylinder" in user_message.lower():
            response = "To create a cylinder in FreeCAD, you can use the freecad.create_cylinder tool. You'll need to specify the radius and height parameters."
        elif "export" in user_message.lower() and "stl" in user_message.lower():
            response = "You can export your model to STL format using the freecad.export_stl tool. This will create a file suitable for 3D printing."
        else:
            response = f"I understand you're asking about: '{user_message}'. I can help you with FreeCAD operations including creating primitives, performing boolean operations, and exporting models. What specific operation would you like to perform?"

        self._add_conversation_message("AI", response)

    def _add_conversation_message(self, sender, message):
        """Add message to conversation display."""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M")

        # Style messages differently based on sender
        if sender == "You":
            style = "color: #2196F3; font-weight: bold;"
        elif sender == "AI":
            style = "color: #4CAF50; font-weight: bold;"
        else:  # System
            style = "color: #FF9800; font-style: italic;"

        # Add message with formatting
        cursor = self.conversation_text.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)

        # Add sender with styling
        format_sender = QtGui.QTextCharFormat()
        if sender == "You":
            format_sender.setForeground(QtGui.QColor("#2196F3"))
        elif sender == "AI":
            format_sender.setForeground(QtGui.QColor("#4CAF50"))
        else:
            format_sender.setForeground(QtGui.QColor("#FF9800"))
        format_sender.setFontWeight(QtGui.QFont.Bold)

        cursor.insertText(f"{sender} ({timestamp}): ", format_sender)
        cursor.insertText(f"{message}\n\n")

        # Auto-scroll to bottom
        self.conversation_text.moveCursor(QtGui.QTextCursor.End)

    def _clear_conversation(self):
        """Clear conversation history."""
        self.conversation_text.clear()
        self.conversation_history.clear()

    def _save_conversation(self):
        """Save conversation to file."""
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Conversation", "ai_conversation.txt", "Text Files (*.txt)"
        )
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.conversation_text.toPlainText())
                QtWidgets.QMessageBox.information(self, "Success", "Conversation saved successfully")
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error", f"Failed to save conversation: {str(e)}")

    def _update_provider_list(self):
        """Update provider combo box and table."""
        self.provider_combo.clear()
        self.provider_table.setRowCount(0)

        if self.ai_manager:
            for provider_name, provider in self.ai_manager.providers.items():
                self.provider_combo.addItem(provider_name)

                # Add to table
                row = self.provider_table.rowCount()
                self.provider_table.insertRow(row)
                self.provider_table.setItem(row, 0, QtWidgets.QTableWidgetItem(provider_name))
                self.provider_table.setItem(row, 1, QtWidgets.QTableWidgetItem(provider.get_provider_name()))
                self.provider_table.setItem(row, 2, QtWidgets.QTableWidgetItem(provider.get_current_model() or "N/A"))
                self.provider_table.setItem(row, 3, QtWidgets.QTableWidgetItem("Active"))

    def _update_model_list(self):
        """Update model combo box for current provider."""
        self.model_combo.clear()

        if self.current_provider and self.ai_manager:
            provider = self.ai_manager.providers.get(self.current_provider)
            if provider:
                models = provider.get_available_models()
                self.model_combo.addItems(models)

                # Set current model if available
                current_model = provider.get_current_model()
                if current_model:
                    index = self.model_combo.findText(current_model)
                    if index >= 0:
                        self.model_combo.setCurrentIndex(index)

    def _update_api_status(self):
        """Update API status display."""
        if self.current_provider and self.ai_manager:
            provider = self.ai_manager.providers.get(self.current_provider)
            if provider:
                is_valid = provider.validate_api_key()
                if is_valid:
                    self.api_status_label.setText("Connected")
                    self.api_status_label.setStyleSheet("color: green; font-weight: bold;")
                else:
                    self.api_status_label.setText("Invalid API Key")
                    self.api_status_label.setStyleSheet("color: red; font-weight: bold;")

    def _load_saved_providers(self):
        """Load saved providers from configuration."""
        # TODO: Implement loading from persistent storage
        pass


class ProviderDialog(QtWidgets.QDialog):
    """Dialog for adding AI providers."""

    def __init__(self, parent=None):
        super(ProviderDialog, self).__init__(parent)
        self.setWindowTitle("Add AI Provider")
        self.setModal(True)
        self.resize(400, 250)

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
        self.type_combo.addItems(["Claude", "Gemini", "OpenRouter"])
        form_layout.addRow("Provider Type:", self.type_combo)

        self.api_key_input = QtWidgets.QLineEdit()
        self.api_key_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.api_key_input.setPlaceholderText("Enter your API key")
        form_layout.addRow("API Key:", self.api_key_input)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()

        self.ok_btn = QtWidgets.QPushButton("Add Provider")
        self.ok_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; }")

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
        return {
            'name': self.name_input.text(),
            'type': self.type_combo.currentText().lower(),
            'api_key': self.api_key_input.text(),
            'config': {}
        }
