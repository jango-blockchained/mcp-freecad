"""Providers Widget - Consolidated AI Provider and API Key Management"""

from PySide2 import QtCore, QtGui, QtWidgets


class ProvidersWidget(QtWidgets.QWidget):
    """Widget for consolidated AI provider and API key management."""

    # Signals
    provider_added = QtCore.Signal(str)
    provider_removed = QtCore.Signal(str)
    provider_configured = QtCore.Signal(str)
    api_key_changed = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(ProvidersWidget, self).__init__(parent)

        # Initialize services
        self.ai_manager = None
        self.config_manager = None
        self.provider_service = None

        self._setup_services()
        self._setup_ui()
        self._create_default_providers()
        self._load_configuration()

    def _setup_services(self):
        """Setup AI manager and config manager."""
        try:
            from ..ai.ai_manager import AIManager
            self.ai_manager = AIManager()
        except ImportError:
            self.ai_manager = None

        try:
            from ..config.config_manager import ConfigManager
            self.config_manager = ConfigManager()
        except ImportError:
            self.config_manager = None

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Create sections
        self._create_api_keys_section(layout)
        self._create_providers_section(layout)
        self._create_provider_config_section(layout)
        self._create_control_buttons(layout)

    def _create_api_keys_section(self, layout):
        """Create API keys management section."""
        api_group = QtWidgets.QGroupBox("API Keys")
        api_layout = QtWidgets.QFormLayout(api_group)

        # OpenAI API Key
        openai_layout = QtWidgets.QHBoxLayout()
        self.openai_key_input = QtWidgets.QLineEdit()
        self.openai_key_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.openai_key_input.setPlaceholderText("sk-...")
        openai_layout.addWidget(self.openai_key_input)

        self.openai_show_btn = QtWidgets.QPushButton("👁")
        self.openai_show_btn.setMaximumWidth(30)
        self.openai_show_btn.setCheckable(True)
        self.openai_show_btn.clicked.connect(lambda: self._toggle_password_visibility(self.openai_key_input, self.openai_show_btn))
        openai_layout.addWidget(self.openai_show_btn)

        self.openai_test_btn = QtWidgets.QPushButton("Test")
        self.openai_test_btn.setMaximumWidth(60)
        self.openai_test_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 4px; }")
        self.openai_test_btn.clicked.connect(lambda: self._test_api_key("openai"))
        openai_layout.addWidget(self.openai_test_btn)

        api_layout.addRow("OpenAI:", openai_layout)

        # Anthropic API Key
        anthropic_layout = QtWidgets.QHBoxLayout()
        self.anthropic_key_input = QtWidgets.QLineEdit()
        self.anthropic_key_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.anthropic_key_input.setPlaceholderText("sk-ant-...")
        anthropic_layout.addWidget(self.anthropic_key_input)

        self.anthropic_show_btn = QtWidgets.QPushButton("👁")
        self.anthropic_show_btn.setMaximumWidth(30)
        self.anthropic_show_btn.setCheckable(True)
        self.anthropic_show_btn.clicked.connect(lambda: self._toggle_password_visibility(self.anthropic_key_input, self.anthropic_show_btn))
        anthropic_layout.addWidget(self.anthropic_show_btn)

        self.anthropic_test_btn = QtWidgets.QPushButton("Test")
        self.anthropic_test_btn.setMaximumWidth(60)
        self.anthropic_test_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 4px; }")
        self.anthropic_test_btn.clicked.connect(lambda: self._test_api_key("anthropic"))
        anthropic_layout.addWidget(self.anthropic_test_btn)

        api_layout.addRow("Anthropic:", anthropic_layout)

        # Google API Key
        google_layout = QtWidgets.QHBoxLayout()
        self.google_key_input = QtWidgets.QLineEdit()
        self.google_key_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.google_key_input.setPlaceholderText("Google API Key...")
        google_layout.addWidget(self.google_key_input)

        self.google_show_btn = QtWidgets.QPushButton("👁")
        self.google_show_btn.setMaximumWidth(30)
        self.google_show_btn.setCheckable(True)
        self.google_show_btn.clicked.connect(lambda: self._toggle_password_visibility(self.google_key_input, self.google_show_btn))
        google_layout.addWidget(self.google_show_btn)

        self.google_test_btn = QtWidgets.QPushButton("Test")
        self.google_test_btn.setMaximumWidth(60)
        self.google_test_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 4px; }")
        self.google_test_btn.clicked.connect(lambda: self._test_api_key("google"))
        google_layout.addWidget(self.google_test_btn)

        api_layout.addRow("Google:", google_layout)

        # OpenRouter API Key
        openrouter_layout = QtWidgets.QHBoxLayout()
        self.openrouter_key_input = QtWidgets.QLineEdit()
        self.openrouter_key_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.openrouter_key_input.setPlaceholderText("OpenRouter API Key...")
        openrouter_layout.addWidget(self.openrouter_key_input)

        self.openrouter_show_btn = QtWidgets.QPushButton("👁")
        self.openrouter_show_btn.setMaximumWidth(30)
        self.openrouter_show_btn.setCheckable(True)
        self.openrouter_show_btn.clicked.connect(lambda: self._toggle_password_visibility(self.openrouter_key_input, self.openrouter_show_btn))
        openrouter_layout.addWidget(self.openrouter_show_btn)

        self.openrouter_test_btn = QtWidgets.QPushButton("Test")
        self.openrouter_test_btn.setMaximumWidth(60)
        self.openrouter_test_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 4px; }")
        self.openrouter_test_btn.clicked.connect(lambda: self._test_api_key("openrouter"))
        openrouter_layout.addWidget(self.openrouter_test_btn)

        api_layout.addRow("OpenRouter:", openrouter_layout)

        layout.addWidget(api_group)

        # Connect auto-save signals
        self.openai_key_input.textChanged.connect(lambda: self._save_api_key("openai", self.openai_key_input.text()))
        self.anthropic_key_input.textChanged.connect(lambda: self._save_api_key("anthropic", self.anthropic_key_input.text()))
        self.google_key_input.textChanged.connect(lambda: self._save_api_key("google", self.google_key_input.text()))
        self.openrouter_key_input.textChanged.connect(lambda: self._save_api_key("openrouter", self.openrouter_key_input.text()))

    def _create_providers_section(self, layout):
        """Create providers list and management section."""
        providers_group = QtWidgets.QGroupBox("AI Providers")
        providers_layout = QtWidgets.QVBoxLayout(providers_group)

        # Provider controls
        controls_layout = QtWidgets.QHBoxLayout()

        controls_layout.addWidget(QtWidgets.QLabel("Active Providers:"))

        self.add_provider_btn = QtWidgets.QPushButton("Add Provider")
        self.add_provider_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 6px; }")
        self.add_provider_btn.clicked.connect(self._add_provider)
        controls_layout.addWidget(self.add_provider_btn)

        self.remove_provider_btn = QtWidgets.QPushButton("Remove")
        self.remove_provider_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; padding: 6px; }")
        self.remove_provider_btn.clicked.connect(self._remove_provider)
        controls_layout.addWidget(self.remove_provider_btn)

        controls_layout.addStretch()
        providers_layout.addLayout(controls_layout)

        # Provider table
        self.providers_table = QtWidgets.QTableWidget(0, 5)
        self.providers_table.setHorizontalHeaderLabels(["Name", "Type", "Model", "Status", "Default"])
        self.providers_table.horizontalHeader().setStretchLastSection(True)
        self.providers_table.setMaximumHeight(150)
        self.providers_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.providers_table.cellClicked.connect(self._on_provider_selected)
        providers_layout.addWidget(self.providers_table)

        layout.addWidget(providers_group)

    def _create_provider_config_section(self, layout):
        """Create provider configuration section."""
        config_group = QtWidgets.QGroupBox("Provider Configuration")
        config_layout = QtWidgets.QFormLayout(config_group)

        # Provider selection
        self.selected_provider_label = QtWidgets.QLabel("None selected")
        self.selected_provider_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        config_layout.addRow("Selected Provider:", self.selected_provider_label)

        # Model selection
        self.model_combo = QtWidgets.QComboBox()
        self.model_combo.setMinimumWidth(200)
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        config_layout.addRow("Model:", self.model_combo)

        # Configuration parameters
        params_layout = QtWidgets.QGridLayout()

        # Temperature
        params_layout.addWidget(QtWidgets.QLabel("Temperature:"), 0, 0)
        self.temperature_spin = QtWidgets.QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setSingleStep(0.1)
        self.temperature_spin.setValue(0.7)
        self.temperature_spin.valueChanged.connect(self._on_config_changed)
        params_layout.addWidget(self.temperature_spin, 0, 1)

        # Max tokens
        params_layout.addWidget(QtWidgets.QLabel("Max Tokens:"), 0, 2)
        self.max_tokens_spin = QtWidgets.QSpinBox()
        self.max_tokens_spin.setRange(100, 8192)
        self.max_tokens_spin.setValue(4096)
        self.max_tokens_spin.valueChanged.connect(self._on_config_changed)
        params_layout.addWidget(self.max_tokens_spin, 0, 3)

        # Timeout
        params_layout.addWidget(QtWidgets.QLabel("Timeout:"), 1, 0)
        self.timeout_spin = QtWidgets.QSpinBox()
        self.timeout_spin.setRange(5, 300)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" sec")
        self.timeout_spin.valueChanged.connect(self._on_config_changed)
        params_layout.addWidget(self.timeout_spin, 1, 1)

        # Thinking mode (for compatible models)
        self.thinking_mode_check = QtWidgets.QCheckBox("Thinking Mode")
        self.thinking_mode_check.setToolTip("Enable extended reasoning for compatible models")
        self.thinking_mode_check.toggled.connect(self._on_config_changed)
        params_layout.addWidget(self.thinking_mode_check, 1, 2)

        # Default provider checkbox
        self.default_provider_check = QtWidgets.QCheckBox("Default Provider")
        self.default_provider_check.setToolTip("Use as default for conversations")
        self.default_provider_check.toggled.connect(self._on_default_changed)
        params_layout.addWidget(self.default_provider_check, 1, 3)

        config_layout.addRow(params_layout)

        # Test connection
        self.test_connection_btn = QtWidgets.QPushButton("Test Connection")
        self.test_connection_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 8px; }")
        self.test_connection_btn.clicked.connect(self._test_connection)
        config_layout.addRow(self.test_connection_btn)

        layout.addWidget(config_group)

    def _create_control_buttons(self, layout):
        """Create control buttons."""
        button_layout = QtWidgets.QHBoxLayout()

        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._refresh_providers)
        button_layout.addWidget(self.refresh_btn)

        button_layout.addStretch()

        self.save_config_btn = QtWidgets.QPushButton("Save Configuration")
        self.save_config_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; }")
        self.save_config_btn.clicked.connect(self._save_configuration)
        button_layout.addWidget(self.save_config_btn)

        layout.addLayout(button_layout)

    def _toggle_password_visibility(self, line_edit, button):
        """Toggle password visibility for API key inputs."""
        if button.isChecked():
            line_edit.setEchoMode(QtWidgets.QLineEdit.Normal)
            button.setText("🙈")
        else:
            line_edit.setEchoMode(QtWidgets.QLineEdit.Password)
            button.setText("👁")

    def _test_api_key(self, provider):
        """Test API key for provider."""
        # Get the key from input
        if provider == "openai":
            key = self.openai_key_input.text()
        elif provider == "anthropic":
            key = self.anthropic_key_input.text()
        elif provider == "google":
            key = self.google_key_input.text()
        elif provider == "openrouter":
            key = self.openrouter_key_input.text()
        else:
            return

        if not key:
            QtWidgets.QMessageBox.warning(self, "Error", f"Please enter {provider} API key first")
            return

        # Validate with config manager if available
        if self.config_manager:
            is_valid = self.config_manager.validate_api_key(provider, key)
            if is_valid:
                QtWidgets.QMessageBox.information(self, "Success", f"{provider} API key format is valid")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", f"{provider} API key format is invalid")
        else:
            # Basic format validation
            if self._basic_key_validation(provider, key):
                QtWidgets.QMessageBox.information(self, "Success", f"{provider} API key format appears valid")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", f"{provider} API key format is invalid")

    def _basic_key_validation(self, provider, key):
        """Basic API key format validation."""
        if provider == "openai":
            return key.startswith("sk-") and len(key) > 20
        elif provider == "anthropic":
            return key.startswith("sk-ant-") and len(key) > 20
        elif provider == "google":
            return len(key) > 20
        elif provider == "openrouter":
            return key.startswith("sk-or-") and len(key) > 20
        return False

    def _save_api_key(self, provider, key):
        """Save API key for provider."""
        if not key or not self.config_manager:
            return

        success = self.config_manager.set_api_key(provider, key)
        if success:
            self.api_key_changed.emit(provider)
            # Refresh providers to update status
            self._refresh_providers()

    def _get_default_provider_by_name(self, provider_name):
        """Get default provider info by name."""
        # Check default providers first
        if hasattr(self, 'default_providers'):
            for provider in self.default_providers:
                if provider['name'] == provider_name:
                    return provider

        # Check custom providers
        if hasattr(self, 'custom_providers'):
            for provider in self.custom_providers:
                if provider['name'] == provider_name:
                    return provider

        return None

    def _create_default_providers(self):
        """Create default providers for common AI services."""
        default_providers = [
            {
                'name': 'OpenAI',
                'type': 'openai',
                'models': ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
                'default_model': 'gpt-4o-mini',
                'status': 'Not configured'
            },
            {
                'name': 'Anthropic',
                'type': 'anthropic',
                'models': ['claude-4-20241120', 'claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022', 'claude-3-opus-20240229'],
                'default_model': 'claude-3-5-sonnet-20241022',
                'status': 'Not configured'
            },
            {
                'name': 'Google',
                'type': 'google',
                'models': ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro'],
                'default_model': 'gemini-1.5-flash',
                'status': 'Not configured'
            },
            {
                'name': 'OpenRouter',
                'type': 'openrouter',
                'models': ['anthropic/claude-3.5-sonnet', 'openai/gpt-4o', 'google/gemini-pro', 'meta-llama/llama-3.1-405b'],
                'default_model': 'anthropic/claude-3.5-sonnet',
                'status': 'Not configured'
            }
        ]

        # Store default providers in a class attribute
        self.default_providers = default_providers

        # Initial refresh to show default providers
        self._refresh_providers()

    def _add_provider(self):
        """Add new provider."""
        dialog = ProviderDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            provider_data = dialog.get_provider_data()

            # Validate provider name
            if not provider_data['name'].strip():
                QtWidgets.QMessageBox.warning(self, "Error", "Please enter a provider name")
                return

            # Check if provider name already exists
            if self._provider_in_table(provider_data['name']):
                QtWidgets.QMessageBox.warning(self, "Error", "Provider name already exists")
                return

            # Create provider info
            new_provider = {
                'name': provider_data['name'],
                'type': provider_data['type'],
                'models': self._get_default_models_for_type(provider_data['type']),
                'default_model': provider_data.get('config', {}).get('model', ''),
                'status': 'Custom provider'
            }

            # If no specific model provided, use first default model
            if not new_provider['default_model'] and new_provider['models']:
                new_provider['default_model'] = new_provider['models'][0]

            # Add to custom providers list
            if not hasattr(self, 'custom_providers'):
                self.custom_providers = []
            self.custom_providers.append(new_provider)

            # Save API key if provided
            if provider_data.get('api_key') and self.config_manager:
                self.config_manager.set_api_key(provider_data['type'], provider_data['api_key'])

            # Refresh display
            self._refresh_providers()
            self.provider_added.emit(provider_data['name'])

            QtWidgets.QMessageBox.information(self, "Success", f"Provider '{provider_data['name']}' added successfully")

    def _get_default_models_for_type(self, provider_type):
        """Get default models for a provider type."""
        model_map = {
            'openai': ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
            'anthropic': ['claude-4-20241120', 'claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022'],
            'google': ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro'],
            'openrouter': ['anthropic/claude-3.5-sonnet', 'openai/gpt-4o', 'google/gemini-pro']
        }
        return model_map.get(provider_type, ['default-model'])

    def _remove_provider(self):
        """Remove selected provider."""
        current_row = self.providers_table.currentRow()
        if current_row >= 0:
            name_item = self.providers_table.item(current_row, 0)
            if name_item:
                provider_name = name_item.text()

                reply = QtWidgets.QMessageBox.question(
                    self, "Remove Provider",
                    f"Are you sure you want to remove provider '{provider_name}'?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                )

                if reply == QtWidgets.QMessageBox.Yes and self.ai_manager:
                    success = self.ai_manager.remove_provider(provider_name)
                    if success:
                        self._refresh_providers()
                        self.provider_removed.emit(provider_name)

    def _on_provider_selected(self, row, column):
        """Handle provider selection in table."""
        name_item = self.providers_table.item(row, 0)
        if name_item:
            provider_name = name_item.text()
            self.selected_provider_label.setText(provider_name)
            self._load_provider_config(provider_name)

    def _load_provider_config(self, provider_name):
        """Load configuration for selected provider."""
        # First check if it's a default provider
        default_provider = self._get_default_provider_by_name(provider_name)
        if default_provider:
            # Update model list with default provider models
            models = default_provider['models']
            self.model_combo.clear()
            self.model_combo.addItems(models)

            # Set default model
            default_model = default_provider['default_model']
            index = self.model_combo.findText(default_model)
            if index >= 0:
                self.model_combo.setCurrentIndex(index)

            # Load default configuration
            self.temperature_spin.setValue(0.7)
            self.max_tokens_spin.setValue(4096)
            self.timeout_spin.setValue(30)
            self.thinking_mode_check.setChecked(False)

            # Enable thinking mode for Claude providers
            if default_provider['type'] == 'anthropic':
                self.thinking_mode_check.setEnabled(True)
            else:
                self.thinking_mode_check.setEnabled(False)

            return

        # If not a default provider, check AI manager
        if self.ai_manager:
            provider = self.ai_manager.providers.get(provider_name)
            if provider:
                # Update model list
                models = provider.get_available_models()
                self.model_combo.clear()
                self.model_combo.addItems(models)

                # Set current model
                current_model = provider.get_current_model()
                if current_model:
                    index = self.model_combo.findText(current_model)
                    if index >= 0:
                        self.model_combo.setCurrentIndex(index)

                # Load other configuration if available
                if hasattr(provider, 'config'):
                    config = provider.config
                    self.temperature_spin.setValue(config.get('temperature', 0.7))
                    self.max_tokens_spin.setValue(config.get('max_tokens', 4096))
                    self.timeout_spin.setValue(config.get('timeout', 30))
                    self.thinking_mode_check.setChecked(config.get('thinking_mode', False))

    def _on_model_changed(self, model_name):
        """Handle model selection change."""
        provider_name = self.selected_provider_label.text()
        if provider_name != "None selected" and self.ai_manager and model_name:
            provider = self.ai_manager.providers.get(provider_name)
            if provider:
                provider.set_model(model_name)
                self._refresh_providers()

    def _on_config_changed(self):
        """Handle configuration parameter changes."""
        provider_name = self.selected_provider_label.text()
        if provider_name != "None selected" and self.ai_manager:
            provider = self.ai_manager.providers.get(provider_name)
            if provider and hasattr(provider, 'config'):
                provider.config.update({
                    'temperature': self.temperature_spin.value(),
                    'max_tokens': self.max_tokens_spin.value(),
                    'timeout': self.timeout_spin.value(),
                    'thinking_mode': self.thinking_mode_check.isChecked()
                })
                self.provider_configured.emit(provider_name)

    def _on_default_changed(self, checked):
        """Handle default provider change."""
        if checked:
            provider_name = self.selected_provider_label.text()
            if provider_name != "None selected" and self.config_manager:
                self.config_manager.set_default_provider(provider_name)
                self._refresh_providers()

    def _test_connection(self):
        """Test connection for selected provider."""
        provider_name = self.selected_provider_label.text()
        if provider_name == "None selected":
            QtWidgets.QMessageBox.warning(self, "Error", "Please select a provider first")
            return

        self.test_connection_btn.setEnabled(False)
        self.test_connection_btn.setText("Testing...")

        # Simulate test (real implementation would test actual connection)
        QtCore.QTimer.singleShot(2000, self._test_connection_finished)

    def _test_connection_finished(self):
        """Handle test connection completion."""
        self.test_connection_btn.setEnabled(True)
        self.test_connection_btn.setText("Test Connection")
        QtWidgets.QMessageBox.information(self, "Success", "Connection test completed")

    def _refresh_providers(self):
        """Refresh providers table."""
        self.providers_table.setRowCount(0)

        # Add default providers first
        if hasattr(self, 'default_providers'):
            for provider_info in self.default_providers:
                self._add_default_provider_to_table(provider_info)

        # Add custom providers
        if hasattr(self, 'custom_providers'):
            for provider_info in self.custom_providers:
                if not self._provider_in_table(provider_info['name']):
                    self._add_default_provider_to_table(provider_info)

        # Add providers from AI manager if available
        if self.ai_manager:
            for provider_name, provider in self.ai_manager.providers.items():
                if not self._provider_in_table(provider_name):
                    self._add_provider_to_table(provider_name, provider)

        # Also update from provider service if available
        if self.provider_service:
            providers = self.provider_service.get_all_providers()
            for provider_name, provider_info in providers.items():
                if not self._provider_in_table(provider_name):
                    self._add_provider_info_to_table(provider_name, provider_info)

    def _add_default_provider_to_table(self, provider_info):
        """Add default provider to table."""
        row = self.providers_table.rowCount()
        self.providers_table.insertRow(row)

        provider_name = provider_info['name']
        provider_type = provider_info['type']
        default_model = provider_info['default_model']

        # Check if API key is configured
        has_api_key = False
        if self.config_manager:
            api_key = self.config_manager.get_api_key(provider_type)
            has_api_key = bool(api_key and len(api_key.strip()) > 10)

        status = "Configured" if has_api_key else "Not configured"

        self.providers_table.setItem(row, 0, QtWidgets.QTableWidgetItem(provider_name))
        self.providers_table.setItem(row, 1, QtWidgets.QTableWidgetItem(provider_type.title()))
        self.providers_table.setItem(row, 2, QtWidgets.QTableWidgetItem(default_model))

        # Color code the status
        status_item = QtWidgets.QTableWidgetItem(status)
        if has_api_key:
            status_item.setForeground(QtGui.QColor("#4CAF50"))
        else:
            status_item.setForeground(QtGui.QColor("#FF9800"))
        self.providers_table.setItem(row, 3, status_item)

        # Check if default provider
        default_provider = self.config_manager.get_default_provider() if self.config_manager else ""
        is_default = provider_name == default_provider
        default_item = QtWidgets.QTableWidgetItem("✓" if is_default else "")
        self.providers_table.setItem(row, 4, default_item)

    def _add_provider_to_table(self, provider_name, provider):
        """Add provider to table."""
        row = self.providers_table.rowCount()
        self.providers_table.insertRow(row)

        self.providers_table.setItem(row, 0, QtWidgets.QTableWidgetItem(provider_name))
        self.providers_table.setItem(row, 1, QtWidgets.QTableWidgetItem(provider.get_provider_name()))
        self.providers_table.setItem(row, 2, QtWidgets.QTableWidgetItem(provider.get_current_model() or "Default"))
        self.providers_table.setItem(row, 3, QtWidgets.QTableWidgetItem("Active"))

        # Check if default provider
        default_provider = self.config_manager.get_default_provider() if self.config_manager else ""
        is_default = provider_name == default_provider
        default_item = QtWidgets.QTableWidgetItem("✓" if is_default else "")
        self.providers_table.setItem(row, 4, default_item)

    def _add_provider_info_to_table(self, provider_name, provider_info):
        """Add provider info from service to table."""
        row = self.providers_table.rowCount()
        self.providers_table.insertRow(row)

        self.providers_table.setItem(row, 0, QtWidgets.QTableWidgetItem(provider_name))
        self.providers_table.setItem(row, 1, QtWidgets.QTableWidgetItem(provider_info.get("type", "Unknown")))
        self.providers_table.setItem(row, 2, QtWidgets.QTableWidgetItem(provider_info.get("config", {}).get("model", "Default")))

        status = provider_info.get("status", "Unknown")
        status_item = QtWidgets.QTableWidgetItem(status)
        if status == "connected":
            status_item.setForeground(QtGui.QColor("#4CAF50"))
        elif status == "error":
            status_item.setForeground(QtGui.QColor("#f44336"))
        else:
            status_item.setForeground(QtGui.QColor("#FF9800"))
        self.providers_table.setItem(row, 3, status_item)

        self.providers_table.setItem(row, 4, QtWidgets.QTableWidgetItem(""))

    def _provider_in_table(self, provider_name):
        """Check if provider is already in table."""
        for row in range(self.providers_table.rowCount()):
            item = self.providers_table.item(row, 0)
            if item and item.text() == provider_name:
                return True
        return False

    def _save_configuration(self):
        """Save all configuration."""
        if self.config_manager:
            success = self.config_manager.save_config()
            if success:
                QtWidgets.QMessageBox.information(self, "Success", "Configuration saved successfully")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Failed to save configuration")

    def _load_configuration(self):
        """Load configuration from config manager."""
        if not self.config_manager:
            return

        # Load API keys
        for provider in ["openai", "anthropic", "google", "openrouter"]:
            key = self.config_manager.get_api_key(provider)
            if key:
                if provider == "openai":
                    self.openai_key_input.setText(key)
                elif provider == "anthropic":
                    self.anthropic_key_input.setText(key)
                elif provider == "google":
                    self.google_key_input.setText(key)
                elif provider == "openrouter":
                    self.openrouter_key_input.setText(key)

        # Refresh providers
        self._refresh_providers()

    def set_provider_service(self, provider_service):
        """Set the provider integration service."""
        self.provider_service = provider_service

        if provider_service:
            provider_service.provider_added.connect(lambda name, type: self._refresh_providers())
            provider_service.provider_removed.connect(lambda name: self._refresh_providers())
            provider_service.provider_status_changed.connect(self._on_provider_status_changed)
            provider_service.providers_updated.connect(self._refresh_providers)

            # Initial refresh
            self._refresh_providers()

    def _on_provider_status_changed(self, provider_name: str, status: str, message: str):
        """Handle provider status change."""
        # Update status in table
        for row in range(self.providers_table.rowCount()):
            name_item = self.providers_table.item(row, 0)
            if name_item and name_item.text() == provider_name:
                status_item = self.providers_table.item(row, 3)
                if status_item:
                    status_item.setText(status)
                    if status == "connected":
                        status_item.setForeground(QtGui.QColor("#4CAF50"))
                    elif status == "error":
                        status_item.setForeground(QtGui.QColor("#f44336"))
                    else:
                        status_item.setForeground(QtGui.QColor("#FF9800"))
                break

    def get_active_providers(self):
        """Get list of active providers."""
        providers = []
        for row in range(self.providers_table.rowCount()):
            name_item = self.providers_table.item(row, 0)
            if name_item:
                providers.append(name_item.text())
        return providers

    def get_default_provider(self):
        """Get the default provider."""
        if self.config_manager:
            return self.config_manager.get_default_provider()
        return None


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
        self.api_key_input.setPlaceholderText("API key (optional - can be set in API Keys section)")
        form_layout.addRow("API Key:", self.api_key_input)

        self.model_input = QtWidgets.QLineEdit()
        self.model_input.setPlaceholderText("e.g., 'claude-3-sonnet-20240229' (optional)")
        form_layout.addRow("Model:", self.model_input)

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
        config = {}
        if self.model_input.text():
            config['model'] = self.model_input.text()

        return {
            'name': self.name_input.text(),
            'type': self.type_combo.currentText(),
            'api_key': self.api_key_input.text(),
            'config': config
        }
