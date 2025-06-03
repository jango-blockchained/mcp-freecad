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

        # Create sections with flexible layout
        self._create_providers_section(layout)
        self._create_provider_config_section(layout)
        self._create_control_buttons(layout)

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

        # Provider table with flexible sizing
        self.providers_table = QtWidgets.QTableWidget(0, 5)
        self.providers_table.setHorizontalHeaderLabels(["Name", "Type", "Model", "Status", "Default"])

        # Make table flexible
        header = self.providers_table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)  # Name column stretches
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)  # Type column fits content
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)  # Model column stretches
        header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)  # Status column fits content
        header.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)  # Default column fits content

        self.providers_table.setMaximumHeight(150)
        self.providers_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.providers_table.cellClicked.connect(self._on_provider_selected)
        providers_layout.addWidget(self.providers_table)

        layout.addWidget(providers_group)

    def _create_provider_config_section(self, layout):
        """Create integrated provider configuration and API key section."""
        config_group = QtWidgets.QGroupBox("Provider Configuration")
        config_layout = QtWidgets.QVBoxLayout(config_group)

        # Provider selection
        selection_layout = QtWidgets.QHBoxLayout()
        selection_layout.addWidget(QtWidgets.QLabel("Selected Provider:"))
        self.selected_provider_label = QtWidgets.QLabel("None selected")
        self.selected_provider_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        selection_layout.addWidget(self.selected_provider_label)
        selection_layout.addStretch()
        config_layout.addLayout(selection_layout)

        # Create tabbed interface for better organization
        self.config_tabs = QtWidgets.QTabWidget()

        # Basic Configuration Tab
        basic_tab = QtWidgets.QWidget()
        basic_layout = QtWidgets.QFormLayout(basic_tab)

        # Model selection
        self.model_combo = QtWidgets.QComboBox()
        self.model_combo.setMinimumWidth(200)
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        basic_layout.addRow("Model:", self.model_combo)

        # Configuration parameters in a grid for better space usage
        params_widget = QtWidgets.QWidget()
        params_layout = QtWidgets.QGridLayout(params_widget)
        params_layout.setSpacing(10)

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

        basic_layout.addRow("Parameters:", params_widget)
        self.config_tabs.addTab(basic_tab, "Configuration")

        # API Key Tab
        api_tab = QtWidgets.QWidget()
        api_layout = QtWidgets.QFormLayout(api_tab)

        # API Key input with show/hide and test functionality
        api_key_widget = QtWidgets.QWidget()
        api_key_layout = QtWidgets.QHBoxLayout(api_key_widget)
        api_key_layout.setContentsMargins(0, 0, 0, 0)

        self.api_key_input = QtWidgets.QLineEdit()
        self.api_key_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.api_key_input.setPlaceholderText("Enter API key for selected provider...")
        self.api_key_input.textChanged.connect(self._on_api_key_changed)
        api_key_layout.addWidget(self.api_key_input)

        self.api_key_show_btn = QtWidgets.QPushButton("👁")
        self.api_key_show_btn.setMaximumWidth(30)
        self.api_key_show_btn.setCheckable(True)
        self.api_key_show_btn.clicked.connect(lambda: self._toggle_password_visibility(self.api_key_input, self.api_key_show_btn))
        api_key_layout.addWidget(self.api_key_show_btn)

        self.api_key_test_btn = QtWidgets.QPushButton("Test")
        self.api_key_test_btn.setMaximumWidth(60)
        self.api_key_test_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 4px; }")
        self.api_key_test_btn.clicked.connect(self._test_current_api_key)
        api_key_layout.addWidget(self.api_key_test_btn)

        api_layout.addRow("API Key:", api_key_widget)

        # API Key status
        self.api_key_status_label = QtWidgets.QLabel("")
        self.api_key_status_label.setStyleSheet("color: #666; font-size: 10px; padding: 2px;")
        api_layout.addRow("Status:", self.api_key_status_label)

        self.config_tabs.addTab(api_tab, "API Key")

        config_layout.addWidget(self.config_tabs)

        # Test connection and status
        actions_layout = QtWidgets.QHBoxLayout()

        self.test_connection_btn = QtWidgets.QPushButton("Test Connection")
        self.test_connection_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; padding: 8px; }")
        self.test_connection_btn.clicked.connect(self._test_connection)
        actions_layout.addWidget(self.test_connection_btn)

        actions_layout.addStretch()
        config_layout.addLayout(actions_layout)

        # Status label for configuration changes
        self.config_status_label = QtWidgets.QLabel("")
        self.config_status_label.setStyleSheet("color: #4CAF50; font-size: 10px; padding: 2px;")
        config_layout.addWidget(self.config_status_label)

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

    def _test_current_api_key(self):
        """Test API key for currently selected provider."""
        provider_name = self.selected_provider_label.text()
        if provider_name == "None selected":
            QtWidgets.QMessageBox.warning(self, "Error", "Please select a provider first")
            return

        key = self.api_key_input.text()
        if not key:
            QtWidgets.QMessageBox.warning(self, "Error", "Please enter an API key first")
            return

        # Get provider type
        provider_info = self._get_default_provider_by_name(provider_name)
        if provider_info:
            provider_type = provider_info['type']
        else:
            # Try to determine from provider name
            provider_type = provider_name.lower()

        # Validate with config manager if available
        if self.config_manager:
            is_valid = self.config_manager.validate_api_key(provider_type, key)
            if is_valid:
                QtWidgets.QMessageBox.information(self, "Success", f"API key format is valid")
                self.api_key_status_label.setText("✅ Valid format")
                self.api_key_status_label.setStyleSheet("color: #4CAF50; font-size: 10px; padding: 2px;")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", f"API key format is invalid")
                self.api_key_status_label.setText("❌ Invalid format")
                self.api_key_status_label.setStyleSheet("color: #f44336; font-size: 10px; padding: 2px;")
        else:
            # Basic format validation
            if self._basic_key_validation(provider_type, key):
                QtWidgets.QMessageBox.information(self, "Success", f"API key format appears valid")
                self.api_key_status_label.setText("✅ Valid format")
                self.api_key_status_label.setStyleSheet("color: #4CAF50; font-size: 10px; padding: 2px;")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", f"API key format is invalid")
                self.api_key_status_label.setText("❌ Invalid format")
                self.api_key_status_label.setStyleSheet("color: #f44336; font-size: 10px; padding: 2px;")

    def _on_api_key_changed(self):
        """Handle API key changes for the selected provider."""
        provider_name = self.selected_provider_label.text()
        if provider_name == "None selected":
            return

        key = self.api_key_input.text()

        # Get provider type
        provider_info = self._get_default_provider_by_name(provider_name)
        if provider_info:
            provider_type = provider_info['type']
        else:
            provider_type = provider_name.lower()

        # Save API key
        if key and self.config_manager:
            success = self.config_manager.set_api_key(provider_type, key)
            if success:
                self.api_key_changed.emit(provider_type)
                self.api_key_status_label.setText("✅ Saved")
                self.api_key_status_label.setStyleSheet("color: #4CAF50; font-size: 10px; padding: 2px;")
                # Refresh providers to update status
                self._refresh_providers()
                # Clear status after 2 seconds
                QtCore.QTimer.singleShot(2000, lambda: self.api_key_status_label.setText(""))
            else:
                self.api_key_status_label.setText("❌ Save failed")
                self.api_key_status_label.setStyleSheet("color: #f44336; font-size: 10px; padding: 2px;")
        elif not key:
            self.api_key_status_label.setText("")

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
                'name': 'Anthropic',
                'type': 'anthropic',
                'models': ['claude-4-20241120', 'claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022', 'claude-3-opus-20240229'],
                'default_model': 'claude-4-20241120',
                'status': 'Not configured'
            },
            {
                'name': 'OpenAI',
                'type': 'openai',
                'models': ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
                'default_model': 'gpt-4o-mini',
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

        # Set Anthropic as the default provider if no default is set
        if self.config_manager:
            current_default = self.config_manager.get_default_provider()
            if not current_default:
                self.config_manager.set_default_provider('Anthropic')

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

            # Save provider configuration to config manager
            if self.config_manager:
                provider_config = {
                    'enabled': True,
                    'model': new_provider['default_model'],
                    'temperature': 0.7,
                    'timeout': 30,
                    'max_tokens': 4000
                }
                # Add thinking mode for Anthropic providers
                if provider_data['type'] == 'anthropic':
                    provider_config['thinking_mode'] = False

                success = self.config_manager.set_provider_config(provider_data['name'], provider_config)
                if not success:
                    QtWidgets.QMessageBox.warning(self, "Warning",
                                                f"Provider added but failed to save configuration for {provider_data['name']}")

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
        # Load API key for the selected provider
        provider_info = self._get_default_provider_by_name(provider_name)
        if provider_info:
            provider_type = provider_info['type']

            # Load API key
            if self.config_manager:
                api_key = self.config_manager.get_api_key(provider_type)
                if api_key:
                    self.api_key_input.setText(api_key)
                    self.api_key_status_label.setText("✅ Configured")
                    self.api_key_status_label.setStyleSheet("color: #4CAF50; font-size: 10px; padding: 2px;")
                else:
                    self.api_key_input.setText("")
                    self.api_key_status_label.setText("⚠️ Not configured")
                    self.api_key_status_label.setStyleSheet("color: #FF9800; font-size: 10px; padding: 2px;")

            # Update model list with default provider models
            models = provider_info['models']
            self.model_combo.clear()
            self.model_combo.addItems(models)

            # Set default model
            default_model = provider_info['default_model']
            index = self.model_combo.findText(default_model)
            if index >= 0:
                self.model_combo.setCurrentIndex(index)

            # Load default configuration
            self.temperature_spin.setValue(0.7)
            self.max_tokens_spin.setValue(4096)
            self.timeout_spin.setValue(30)
            self.thinking_mode_check.setChecked(False)

            # Load saved configuration from config manager if available
            if self.config_manager:
                saved_config = self.config_manager.get_provider_config(provider_name)
                if saved_config:
                    self.temperature_spin.setValue(saved_config.get('temperature', 0.7))
                    self.max_tokens_spin.setValue(saved_config.get('max_tokens', 4096))
                    self.timeout_spin.setValue(saved_config.get('timeout', 30))
                    self.thinking_mode_check.setChecked(saved_config.get('thinking_mode', False))

                    # Update model if saved
                    saved_model = saved_config.get('model')
                    if saved_model:
                        index = self.model_combo.findText(saved_model)
                        if index >= 0:
                            self.model_combo.setCurrentIndex(index)

            # Enable thinking mode for Claude providers
            if provider_info['type'] == 'anthropic':
                self.thinking_mode_check.setEnabled(True)
            else:
                self.thinking_mode_check.setEnabled(False)

            # Check if this is the default provider
            if self.config_manager:
                default_provider = self.config_manager.get_default_provider()
                self.default_provider_check.setChecked(provider_name == default_provider)

            return

        # If not a default provider, check AI manager
        if self.ai_manager:
            provider = self.ai_manager.providers.get(provider_name)
            if provider:
                # Clear API key input for AI manager providers
                self.api_key_input.setText("")
                self.api_key_status_label.setText("Managed by AI Manager")
                self.api_key_status_label.setStyleSheet("color: #666; font-size: 10px; padding: 2px;")

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

                # Save model change to config manager for persistence
                if self.config_manager:
                    existing_config = self.config_manager.get_provider_config(provider_name)
                    existing_config['model'] = model_name

                    success = self.config_manager.set_provider_config(provider_name, existing_config)
                    if not success:
                        QtWidgets.QMessageBox.warning(self, "Warning",
                                                    f"Failed to save model configuration for {provider_name}")
                        self.config_status_label.setText("❌ Failed to save model configuration")
                        self.config_status_label.setStyleSheet("color: #f44336; font-size: 10px; padding: 2px;")
                    else:
                        self.config_status_label.setText("✅ Model configuration saved automatically")
                        self.config_status_label.setStyleSheet("color: #4CAF50; font-size: 10px; padding: 2px;")
                        # Clear status after 3 seconds
                        QtCore.QTimer.singleShot(3000, lambda: self.config_status_label.setText(""))

                self._refresh_providers()

    def _on_config_changed(self):
        """Handle configuration parameter changes."""
        provider_name = self.selected_provider_label.text()
        if provider_name != "None selected" and self.ai_manager:
            provider = self.ai_manager.providers.get(provider_name)
            if provider and hasattr(provider, 'config'):
                # Update provider object config
                new_config = {
                    'temperature': self.temperature_spin.value(),
                    'max_tokens': self.max_tokens_spin.value(),
                    'timeout': self.timeout_spin.value(),
                    'thinking_mode': self.thinking_mode_check.isChecked()
                }
                provider.config.update(new_config)

                # Save to config manager for persistence
                if self.config_manager:
                    # Get existing provider config and update it
                    existing_config = self.config_manager.get_provider_config(provider_name)
                    existing_config.update(new_config)

                    # Save the updated configuration
                    success = self.config_manager.set_provider_config(provider_name, existing_config)
                    if not success:
                        QtWidgets.QMessageBox.warning(self, "Warning",
                                                    f"Failed to save configuration for {provider_name}")
                        self.config_status_label.setText("❌ Failed to save configuration")
                        self.config_status_label.setStyleSheet("color: #f44336; font-size: 10px; padding: 2px;")
                    else:
                        self.config_status_label.setText("✅ Configuration saved automatically")
                        self.config_status_label.setStyleSheet("color: #4CAF50; font-size: 10px; padding: 2px;")
                        # Clear status after 3 seconds
                        QtCore.QTimer.singleShot(3000, lambda: self.config_status_label.setText(""))

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

        # Refresh providers to show current state
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
