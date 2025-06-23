"""Providers Widget - Consolidated AI Provider and API Key Management"""

from PySide2 import QtCore, QtGui, QtWidgets

# Import extracted components
from .config.fallback_config_manager import FallbackConfigManager
from .components.provider_dialog import ProviderDialog
from .utils.import_strategies import try_import_ai_manager, try_import_config_manager


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

        # Flag to prevent excessive config saving during loading
        self._loading_config = False

        self._setup_services()
        self._setup_ui()
        self._create_default_providers()
        self._load_configuration()

    def _setup_services(self):
        """Setup AI manager and config manager."""
        print("DEBUG: Setting up services for ProvidersWidget...")
        self.ai_manager = try_import_ai_manager()
        self.config_manager = try_import_config_manager()

        if self.ai_manager:
            print(f"DEBUG: AIManager loaded with {len(self.ai_manager.providers)} providers")
        else:
            print("DEBUG: AIManager not available")

        if self.config_manager is None:
            print(
                "Warning: Could not import ConfigManager - configuration features will be disabled"
            )
            print("Tried the following import strategies:")
            print("1. from ..config.config_manager import ConfigManager")
            print("2. from config.config_manager import ConfigManager")
            print("3. Direct path import with sys.path modification")
            print("4. importlib.util dynamic import")

            # Show current working directory and paths for debugging
            import os

            print(f"Current working directory: {os.getcwd()}")
            print(f"Current file location: {os.path.abspath(__file__)}")
            addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_file = os.path.join(addon_dir, "config", "config_manager.py")
            print(f"Expected config file location: {config_file}")
            print(f"Config file exists: {os.path.exists(config_file)}")

            import sys

            print(f"Python path: {sys.path[:3]}...")  # Show first 3 entries

            # Use fallback config manager
            print("Using fallback config manager for basic functionality")
            try:
                self.config_manager = FallbackConfigManager()
                print("✅ Fallback config manager loaded successfully")
            except Exception as e:
                print(f"❌ Even fallback config manager failed: {e}")
                self.config_manager = None
        else:
            print("DEBUG: ConfigManager loaded successfully")

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Create sections with flexible layout
        self._create_providers_section(layout)
        self._create_provider_config_section(layout)
        self._create_control_buttons(layout)

        # Add stretch at the bottom to prevent content from stretching
        layout.addStretch()

    def _create_providers_section(self, layout):
        """Create providers list and management section."""
        providers_group = QtWidgets.QGroupBox("AI Providers")
        providers_group.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )
        providers_layout = QtWidgets.QVBoxLayout(providers_group)

        # Provider controls
        controls_layout = QtWidgets.QHBoxLayout()

        controls_layout.addWidget(QtWidgets.QLabel("Active Providers:"))

        self.add_provider_btn = QtWidgets.QPushButton("Add Provider")
        self.add_provider_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; padding: 6px; }"
        )
        self.add_provider_btn.clicked.connect(self._add_provider)
        controls_layout.addWidget(self.add_provider_btn)

        self.remove_provider_btn = QtWidgets.QPushButton("Remove")
        self.remove_provider_btn.setStyleSheet(
            "QPushButton { background-color: #f44336; color: white; padding: 6px; }"
        )
        self.remove_provider_btn.clicked.connect(self._remove_provider)
        controls_layout.addWidget(self.remove_provider_btn)

        controls_layout.addStretch()
        providers_layout.addLayout(controls_layout)

        # Provider table with flexible sizing
        self.providers_table = QtWidgets.QTableWidget(0, 5)
        self.providers_table.setHorizontalHeaderLabels(
            ["Name", "Type", "Model", "Status", "Default"]
        )

        # Make table flexible
        header = self.providers_table.horizontalHeader()
        header.setSectionResizeMode(
            0, QtWidgets.QHeaderView.Stretch
        )  # Name column stretches
        header.setSectionResizeMode(
            1, QtWidgets.QHeaderView.ResizeToContents
        )  # Type column fits content
        header.setSectionResizeMode(
            2, QtWidgets.QHeaderView.Stretch
        )  # Model column stretches
        header.setSectionResizeMode(
            3, QtWidgets.QHeaderView.ResizeToContents
        )  # Status column fits content
        header.setSectionResizeMode(
            4, QtWidgets.QHeaderView.ResizeToContents
        )  # Default column fits content

        self.providers_table.setMaximumHeight(150)
        self.providers_table.setMinimumHeight(100)
        self.providers_table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows
        )
        self.providers_table.cellClicked.connect(self._on_provider_selected)
        self.providers_table.setVisible(True)  # Ensure table is visible
        providers_layout.addWidget(self.providers_table)

        layout.addWidget(providers_group)

    def _create_provider_config_section(self, layout):
        """Create integrated provider configuration and API key section."""
        config_group = QtWidgets.QGroupBox("Provider Configuration")
        config_group.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )
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
        self.thinking_mode_check.setToolTip(
            "Enable extended reasoning for compatible models"
        )
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
        self.api_key_show_btn.clicked.connect(
            lambda: self._toggle_password_visibility(
                self.api_key_input, self.api_key_show_btn
            )
        )
        api_key_layout.addWidget(self.api_key_show_btn)

        self.api_key_test_btn = QtWidgets.QPushButton("Test")
        self.api_key_test_btn.setMaximumWidth(60)
        self.api_key_test_btn.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; padding: 4px; }"
        )
        self.api_key_test_btn.clicked.connect(self._test_current_api_key)
        api_key_layout.addWidget(self.api_key_test_btn)

        api_layout.addRow("API Key:", api_key_widget)

        # API Key status
        self.api_key_status_label = QtWidgets.QLabel("")
        self.api_key_status_label.setStyleSheet(
            "color: #666; font-size: 10px; padding: 2px;"
        )
        api_layout.addRow("Status:", self.api_key_status_label)

        self.config_tabs.addTab(api_tab, "API Key")

        config_layout.addWidget(self.config_tabs)

        # Test connection and status
        actions_layout = QtWidgets.QHBoxLayout()

        self.test_connection_btn = QtWidgets.QPushButton("Test Connection")
        self.test_connection_btn.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; padding: 8px; }"
        )
        self.test_connection_btn.clicked.connect(self._test_connection)
        actions_layout.addWidget(self.test_connection_btn)

        # Retry service connection button for debugging
        self.retry_service_btn = QtWidgets.QPushButton("Retry Service")
        self.retry_service_btn.setStyleSheet(
            "QPushButton { background-color: #FF9800; color: white; padding: 8px; }"
        )
        self.retry_service_btn.setToolTip("Try to reconnect to provider service")
        self.retry_service_btn.clicked.connect(self._retry_provider_service)
        actions_layout.addWidget(self.retry_service_btn)

        actions_layout.addStretch()
        config_layout.addLayout(actions_layout)

        # Status label for configuration changes
        self.config_status_label = QtWidgets.QLabel("")
        self.config_status_label.setStyleSheet(
            "color: #4CAF50; font-size: 10px; padding: 2px;"
        )
        config_layout.addWidget(self.config_status_label)

        # Config manager status
        self.config_manager_status = QtWidgets.QLabel("")
        self.config_manager_status.setStyleSheet(
            "color: #666; font-size: 9px; padding: 2px;"
        )
        config_layout.addWidget(self.config_manager_status)

        # Update config manager status
        self._update_config_manager_status()

        layout.addWidget(config_group)

    def _create_control_buttons(self, layout):
        """Create control buttons."""
        button_layout = QtWidgets.QHBoxLayout()

        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._refresh_providers)
        button_layout.addWidget(self.refresh_btn)

        button_layout.addStretch()

        self.save_config_btn = QtWidgets.QPushButton("Save Configuration")
        self.save_config_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; }"
        )
        self.save_config_btn.clicked.connect(self._save_configuration)
        button_layout.addWidget(self.save_config_btn)

        # Add debug button for troubleshooting
        self.debug_config_btn = QtWidgets.QPushButton("Debug Config")
        self.debug_config_btn.setStyleSheet(
            "QPushButton { background-color: #FF9800; color: white; padding: 6px; }"
        )
        self.debug_config_btn.clicked.connect(self._debug_configuration)
        button_layout.addWidget(self.debug_config_btn)

        # Add retry config manager button
        self.retry_config_btn = QtWidgets.QPushButton("Retry Config")
        self.retry_config_btn.setStyleSheet(
            "QPushButton { background-color: #9C27B0; color: white; padding: 6px; }"
        )
        self.retry_config_btn.clicked.connect(self._retry_config_manager)
        button_layout.addWidget(self.retry_config_btn)

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
            QtWidgets.QMessageBox.warning(
                self, "Error", f"Please enter {provider} API key first"
            )
            return

        # Validate with config manager if available
        if self.config_manager:
            is_valid = self.config_manager.validate_api_key(provider, key)
            if is_valid:
                QtWidgets.QMessageBox.information(
                    self, "Success", f"{provider} API key format is valid"
                )
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Error", f"{provider} API key format is invalid"
                )
        else:
            # Basic format validation
            if self._basic_key_validation(provider, key):
                QtWidgets.QMessageBox.information(
                    self, "Success", f"{provider} API key format appears valid"
                )
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Error", f"{provider} API key format is invalid"
                )

    def _test_current_api_key(self):
        """Test API key for currently selected provider."""
        provider_name = self.selected_provider_label.text()
        if provider_name == "None selected":
            QtWidgets.QMessageBox.warning(
                self, "Error", "Please select a provider first"
            )
            return

        key = self.api_key_input.text()
        if not key:
            QtWidgets.QMessageBox.warning(
                self, "Error", "Please enter an API key first"
            )
            return

        # Get provider type
        provider_info = self._get_default_provider_by_name(provider_name)
        if provider_info:
            provider_type = provider_info["type"]
        else:
            # Try to determine from provider name
            provider_type = provider_name.lower()

        # Validate with config manager if available
        if self.config_manager:
            is_valid = self.config_manager.validate_api_key(provider_type, key)
            if is_valid:
                QtWidgets.QMessageBox.information(
                    self, "Success", "API key format is valid"
                )
                self.api_key_status_label.setText("✅ Valid format")
                self.api_key_status_label.setStyleSheet(
                    "color: #4CAF50; font-size: 10px; padding: 2px;"
                )
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Error", "API key format is invalid"
                )
                self.api_key_status_label.setText("❌ Invalid format")
                self.api_key_status_label.setStyleSheet(
                    "color: #f44336; font-size: 10px; padding: 2px;"
                )
        else:
            # Basic format validation
            if self._basic_key_validation(provider_type, key):
                QtWidgets.QMessageBox.information(
                    self, "Success", "API key format appears valid"
                )
                self.api_key_status_label.setText("✅ Valid format")
                self.api_key_status_label.setStyleSheet(
                    "color: #4CAF50; font-size: 10px; padding: 2px;"
                )
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Error", "API key format is invalid"
                )
                self.api_key_status_label.setText("❌ Invalid format")
                self.api_key_status_label.setStyleSheet(
                    "color: #f44336; font-size: 10px; padding: 2px;"
                )

    def _on_api_key_changed(self):
        """Handle API key changes for the selected provider."""
        provider_name = self.selected_provider_label.text()
        if provider_name == "None selected":
            return

        key = self.api_key_input.text()

        # Get provider type
        provider_info = self._get_default_provider_by_name(provider_name)
        if provider_info:
            provider_type = provider_info["type"]
        else:
            provider_type = provider_name.lower()

        # Save API key
        if key and self.config_manager:
            success = self.config_manager.set_api_key(provider_type, key)
            if success:
                # Also ensure provider is enabled when API key is set
                existing_config = self.config_manager.get_provider_config(provider_name)
                if not existing_config:
                    existing_config = {
                        "enabled": True,
                        "model": self._get_default_model_for_provider(provider_type),
                        "temperature": 0.7,
                        "timeout": 30,
                        "max_tokens": 4000,
                    }
                else:
                    existing_config["enabled"] = True
                self.config_manager.set_provider_config(provider_name, existing_config)

                self.api_key_changed.emit(provider_type)
                self.api_key_status_label.setText("✅ Saved")
                self.api_key_status_label.setStyleSheet(
                    "color: #4CAF50; font-size: 10px; padding: 2px;"
                )
                # Refresh providers to update status
                self._refresh_providers()
                # Don't clear status - keep it visible for user reference
            else:
                self.api_key_status_label.setText("❌ Save failed")
                self.api_key_status_label.setStyleSheet(
                    "color: #f44336; font-size: 10px; padding: 2px;"
                )
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
        if hasattr(self, "default_providers"):
            for provider in self.default_providers:
                if provider["name"] == provider_name:
                    return provider

        # Check custom providers
        if hasattr(self, "custom_providers"):
            for provider in self.custom_providers:
                if provider["name"] == provider_name:
                    return provider

        return None

    def _get_default_model_for_provider(self, provider_type):
        """Get default model for a provider type."""
        model_map = {
            "anthropic": "claude-4-20241120",
            "openai": "gpt-4o-mini",
            "google": "gemini-1.5-flash",
            "openrouter": "anthropic/claude-3.5-sonnet",
        }
        return model_map.get(provider_type, "default-model")

    def _create_default_providers(self):
        """Create default providers for common AI services."""
        default_providers = [
            {
                "name": "Anthropic",
                "type": "anthropic",
                "models": [
                    "claude-4-20241120",
                    "claude-3-5-sonnet-20241022",
                    "claude-3-5-haiku-20241022",
                    "claude-3-opus-20240229",
                ],
                "default_model": "claude-4-20241120",
                "status": "Not configured",
            },
            {
                "name": "OpenAI",
                "type": "openai",
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
                "default_model": "gpt-4o-mini",
                "status": "Not configured",
            },
            {
                "name": "Google",
                "type": "google",
                "models": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"],
                "default_model": "gemini-1.5-flash",
                "status": "Not configured",
            },
            {
                "name": "OpenRouter",
                "type": "openrouter",
                "models": [
                    "anthropic/claude-3.5-sonnet",
                    "openai/gpt-4o",
                    "google/gemini-pro",
                    "meta-llama/llama-3.1-405b",
                ],
                "default_model": "anthropic/claude-3.5-sonnet",
                "status": "Not configured",
            },
        ]

        # Store default providers in a class attribute
        self.default_providers = default_providers
        print(f"DEBUG: Created {len(self.default_providers)} default providers")

        # Set Anthropic as the default provider if no default is set
        if self.config_manager:
            current_default = self.config_manager.get_default_provider()
            if not current_default:
                self.config_manager.set_default_provider("Anthropic")

        # Initial refresh to show default providers
        self._refresh_providers()

    def _add_provider(self):
        """Add new provider."""
        dialog = ProviderDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            provider_data = dialog.get_provider_data()

            # Validate provider name
            if not provider_data["name"].strip():
                QtWidgets.QMessageBox.warning(
                    self, "Error", "Please enter a provider name"
                )
                return

            # Check if provider name already exists
            if self._provider_in_table(provider_data["name"]):
                QtWidgets.QMessageBox.warning(
                    self, "Error", "Provider name already exists"
                )
                return

            # Create provider info
            new_provider = {
                "name": provider_data["name"],
                "type": provider_data["type"],
                "models": self._get_default_models_for_type(provider_data["type"]),
                "default_model": provider_data.get("config", {}).get("model", ""),
                "status": "Custom provider",
            }

            # If no specific model provided, use first default model
            if not new_provider["default_model"] and new_provider["models"]:
                new_provider["default_model"] = new_provider["models"][0]

            # Add to custom providers list
            if not hasattr(self, "custom_providers"):
                self.custom_providers = []
            self.custom_providers.append(new_provider)

            # Save API key if provided
            if provider_data.get("api_key") and self.config_manager:
                self.config_manager.set_api_key(
                    provider_data["type"], provider_data["api_key"]
                )

            # Save provider configuration to config manager
            if self.config_manager:
                provider_config = {
                    "enabled": True,
                    "model": new_provider["default_model"],
                    "temperature": 0.7,
                    "timeout": 30,
                    "max_tokens": 4000,
                }
                # Add thinking mode for Anthropic providers
                if provider_data["type"] == "anthropic":
                    provider_config["thinking_mode"] = False

                success = self.config_manager.set_provider_config(
                    provider_data["name"], provider_config
                )
                if not success:
                    QtWidgets.QMessageBox.warning(
                        self,
                        "Warning",
                        f"Provider added but failed to save configuration for {provider_data['name']}",
                    )

            # Refresh display
            self._refresh_providers()
            self.provider_added.emit(provider_data["name"])

            QtWidgets.QMessageBox.information(
                self,
                "Success",
                f"Provider '{provider_data['name']}' added successfully",
            )

    def _get_default_models_for_type(self, provider_type):
        """Get default models for a provider type."""
        model_map = {
            "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
            "anthropic": [
                "claude-4-20241120",
                "claude-3-5-sonnet-20241022",
                "claude-3-5-haiku-20241022",
            ],
            "google": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"],
            "openrouter": [
                "anthropic/claude-3.5-sonnet",
                "openai/gpt-4o",
                "google/gemini-pro",
            ],
        }
        return model_map.get(provider_type, ["default-model"])

    def _remove_provider(self):
        """Remove selected provider."""
        current_row = self.providers_table.currentRow()
        if current_row >= 0:
            name_item = self.providers_table.item(current_row, 0)
            if name_item:
                provider_name = name_item.text()

                reply = QtWidgets.QMessageBox.question(
                    self,
                    "Remove Provider",
                    f"Are you sure you want to remove provider '{provider_name}'?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
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
        # Set loading flag to prevent excessive config saves
        self._loading_config = True

        try:
            # Load API key for the selected provider
            provider_info = self._get_default_provider_by_name(provider_name)
            if provider_info:
                provider_type = provider_info["type"]

                # Load API key
                if self.config_manager:
                    api_key = self.config_manager.get_api_key(provider_type)
                    if api_key:
                        self.api_key_input.setText(api_key)
                        self.api_key_status_label.setText("✅ Configured")
                        self.api_key_status_label.setStyleSheet(
                            "color: #4CAF50; font-size: 10px; padding: 2px;"
                        )
                    else:
                        self.api_key_input.setText("")
                        self.api_key_status_label.setText("⚠️ Not configured")
                        self.api_key_status_label.setStyleSheet(
                            "color: #FF9800; font-size: 10px; padding: 2px;"
                        )

                # Update model list with default provider models
                models = provider_info["models"]
                self.model_combo.clear()
                self.model_combo.addItems(models)

                # Set default model
                default_model = provider_info["default_model"]
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
                    saved_config = self.config_manager.get_provider_config(
                        provider_name
                    )
                    if saved_config:
                        self.temperature_spin.setValue(
                            saved_config.get("temperature", 0.7)
                        )
                        self.max_tokens_spin.setValue(
                            saved_config.get("max_tokens", 4096)
                        )
                        self.timeout_spin.setValue(saved_config.get("timeout", 30))
                        self.thinking_mode_check.setChecked(
                            saved_config.get("thinking_mode", False)
                        )

                        # Update model if saved
                        saved_model = saved_config.get("model")
                        if saved_model:
                            index = self.model_combo.findText(saved_model)
                            if index >= 0:
                                self.model_combo.setCurrentIndex(index)

                # Enable thinking mode for Claude providers
                if provider_info["type"] == "anthropic":
                    self.thinking_mode_check.setEnabled(True)
                else:
                    self.thinking_mode_check.setEnabled(False)

                # Check if this is the default provider
                if self.config_manager:
                    default_provider = self.config_manager.get_default_provider()
                    self.default_provider_check.setChecked(
                        provider_name == default_provider
                    )

                return

            # If not a default provider, check AI manager
            if self.ai_manager:
                provider = self.ai_manager.providers.get(provider_name)
                if provider:
                    # Clear API key input for AI manager providers
                    self.api_key_input.setText("")
                    self.api_key_status_label.setText("Managed by AI Manager")
                    self.api_key_status_label.setStyleSheet(
                        "color: #666; font-size: 10px; padding: 2px;"
                    )

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
                    if hasattr(provider, "config"):
                        config = provider.config
                        self.temperature_spin.setValue(config.get("temperature", 0.7))
                        self.max_tokens_spin.setValue(config.get("max_tokens", 4096))
                        self.timeout_spin.setValue(config.get("timeout", 30))
                        self.thinking_mode_check.setChecked(
                            config.get("thinking_mode", False)
                        )
        finally:
            # Always reset loading flag
            self._loading_config = False

    def _on_model_changed(self, model_name):
        """Handle model selection change."""
        # Skip saving during config loading to prevent excessive saves
        if self._loading_config:
            return

        provider_name = self.selected_provider_label.text()
        if provider_name == "None selected" or not model_name:
            return

        # Update AI manager provider if it exists
        if self.ai_manager:
            provider = self.ai_manager.providers.get(provider_name)
            if provider:
                provider.set_model(model_name)

        # Save model change to config manager for persistence (this is the important part)
        if self.config_manager:
            try:
                existing_config = self.config_manager.get_provider_config(provider_name)
                if not existing_config:
                    existing_config = {}
                existing_config["model"] = model_name
                # Ensure provider is marked as enabled when model is changed
                existing_config["enabled"] = True

                success = self.config_manager.set_provider_config(
                    provider_name, existing_config
                )
                if not success:
                    self.config_status_label.setText(
                        "❌ Failed to save model configuration"
                    )
                    self.config_status_label.setStyleSheet(
                        "color: #f44336; font-size: 10px; padding: 2px;"
                    )
                else:
                    self.config_status_label.setText(
                        "✅ Model configuration saved automatically"
                    )
                    self.config_status_label.setStyleSheet(
                        "color: #4CAF50; font-size: 10px; padding: 2px;"
                    )
                    # Don't clear status - keep it visible for user reference
            except Exception as e:
                self.config_status_label.setText(f"❌ Error: {str(e)[:30]}...")
                self.config_status_label.setStyleSheet(
                    "color: #f44336; font-size: 10px; padding: 2px;"
                )
        else:
            self.config_status_label.setText("❌ Config manager not available")
            self.config_status_label.setStyleSheet(
                "color: #f44336; font-size: 10px; padding: 2px;"
            )

        self._refresh_providers()

    def _on_config_changed(self):
        """Handle configuration parameter changes."""
        # Skip saving during config loading to prevent excessive saves
        if self._loading_config:
            return

        provider_name = self.selected_provider_label.text()
        if provider_name == "None selected":
            return

        # Create new configuration from UI values
        new_config = {
            "temperature": self.temperature_spin.value(),
            "max_tokens": self.max_tokens_spin.value(),
            "timeout": self.timeout_spin.value(),
            "thinking_mode": self.thinking_mode_check.isChecked(),
            "enabled": True,
        }

        # Add current model if available
        current_model = self.model_combo.currentText()
        if current_model:
            new_config["model"] = current_model

        # Update AI manager provider if it exists
        if self.ai_manager:
            provider = self.ai_manager.providers.get(provider_name)
            if provider and hasattr(provider, "config"):
                provider.config.update(new_config)

        # Save to config manager for persistence (this is the important part)
        if self.config_manager:
            try:
                # Get existing provider config and update it
                existing_config = self.config_manager.get_provider_config(provider_name)
                if not existing_config:
                    existing_config = {}
                existing_config.update(new_config)

                # Ensure provider is marked as enabled when configured
                existing_config["enabled"] = True

                # Save the updated configuration
                success = self.config_manager.set_provider_config(
                    provider_name, existing_config
                )
                if not success:
                    self.config_status_label.setText("❌ Failed to save configuration")
                    self.config_status_label.setStyleSheet(
                        "color: #f44336; font-size: 10px; padding: 2px;"
                    )
                else:
                    self.config_status_label.setText(
                        "✅ Configuration saved automatically"
                    )
                    self.config_status_label.setStyleSheet(
                        "color: #4CAF50; font-size: 10px; padding: 2px;"
                    )
                    # Don't clear status - keep it visible for user reference
            except Exception as e:
                self.config_status_label.setText(f"❌ Error: {str(e)[:30]}...")
                self.config_status_label.setStyleSheet(
                    "color: #f44336; font-size: 10px; padding: 2px;"
                )
        else:
            self.config_status_label.setText("❌ Config manager not available")
            self.config_status_label.setStyleSheet(
                "color: #f44336; font-size: 10px; padding: 2px;"
            )

        self.provider_configured.emit(provider_name)

    def _on_default_changed(self, checked):
        """Handle default provider change."""
        if checked:
            provider_name = self.selected_provider_label.text()
            if provider_name != "None selected" and self.config_manager:
                self.config_manager.set_default_provider(provider_name)
                self._refresh_providers()

    def _test_connection(self):
        """Test connection for selected provider with detailed console output."""
        provider_name = self.selected_provider_label.text()
        if provider_name == "None selected":
            QtWidgets.QMessageBox.warning(
                self, "Error", "Please select a provider first"
            )
            return

        # Check if we have API key
        api_key = self.api_key_input.text().strip()
        if not api_key:
            QtWidgets.QMessageBox.warning(
                self, "Error", "Please enter an API key first"
            )
            return

        self.test_connection_btn.setEnabled(False)
        self.test_connection_btn.setText("Testing...")

        # Show console dialog
        self._show_connection_test_console(provider_name, api_key)

    def _show_connection_test_console(self, provider_name, api_key):
        """Show a console-like dialog with real-time test output."""
        # Create console dialog
        console_dialog = QtWidgets.QDialog(self)
        console_dialog.setWindowTitle(f"Connection Test - {provider_name}")
        console_dialog.setModal(True)
        console_dialog.resize(600, 400)

        layout = QtWidgets.QVBoxLayout(console_dialog)

        # Console output area
        console_output = QtWidgets.QTextEdit()
        console_output.setReadOnly(True)
        console_output.setStyleSheet(
            """
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid #555;
                padding: 10px;
            }
        """
        )
        layout.addWidget(console_output)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(console_dialog.accept)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

        # Start the test
        self._perform_real_connection_test(
            provider_name, api_key, console_output, console_dialog
        )

        console_dialog.exec_()

    def _perform_real_connection_test(
        self, provider_name, api_key, console_output, dialog
    ):
        """Perform the actual connection test with real-time console output."""
        import time
        from datetime import datetime

        def log_message(msg, level="INFO"):
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            color = {
                "INFO": "#ffffff",
                "SUCCESS": "#4caf50",
                "ERROR": "#f44336",
                "WARNING": "#ff9800",
                "DEBUG": "#2196f3",
            }.get(level, "#ffffff")

            console_output.append(
                f"<span style='color: #888'>[{timestamp}]</span> "
                f"<span style='color: {color}'>{level}:</span> {msg}"
            )
            console_output.ensureCursorVisible()
            QtWidgets.QApplication.processEvents()

        try:
            log_message("=" * 60)
            log_message(f"CONNECTION TEST STARTED: {provider_name}")
            log_message("=" * 60)

            # Step 1: Validate API key format
            log_message("Step 1/5: Validating API key format...")
            if len(api_key) < 10:
                log_message("API key appears too short", "ERROR")
                self._test_connection_finished(False, "API key too short")
                return
            elif api_key.startswith("sk-") and len(api_key) < 48:
                log_message("OpenAI-style API key detected but seems short", "WARNING")
            elif api_key.startswith("sk-ant-") and len(api_key) < 100:
                log_message("Anthropic API key detected but seems short", "WARNING")
            else:
                log_message("API key format looks valid", "SUCCESS")

            # Step 2: Check provider service availability
            log_message("Step 2/5: Checking provider service...")
            if self.provider_service:
                log_message("Provider service is available", "SUCCESS")
            else:
                log_message("Provider service not available", "ERROR")
                log_message(
                    "This means set_provider_service() was never called", "DEBUG"
                )
                log_message("or the provider service failed to initialize", "DEBUG")
                log_message(
                    "Check FreeCAD console for 'Setting up provider service' messages",
                    "DEBUG",
                )
                self._test_connection_finished(
                    False, "No provider service - check console for details"
                )
                return

            # Step 3: Initialize provider
            log_message("Step 3/5: Initializing provider...")
            try:
                # Get provider type
                provider_info = self._get_default_provider_by_name(provider_name)
                if provider_info:
                    provider_type = provider_info["type"]
                    log_message(f"Provider type: {provider_type}", "DEBUG")
                else:
                    provider_type = provider_name.lower()
                    log_message(f"Assuming provider type: {provider_type}", "WARNING")

                # Try to initialize with provider service
                config = {
                    "model": getattr(self, "model_combo", None)
                    and self.model_combo.currentText()
                    or "default"
                }

                log_message(
                    f"Adding provider to service with config: {config}", "DEBUG"
                )
                success = self.provider_service._initialize_provider(
                    provider_name, api_key, config
                )

                if success:
                    log_message("Provider initialized successfully", "SUCCESS")
                else:
                    log_message("Provider initialization failed", "ERROR")
                    self._test_connection_finished(
                        False, "Provider initialization failed"
                    )
                    return

            except Exception as e:
                log_message(f"Provider initialization error: {str(e)}", "ERROR")
                self._test_connection_finished(False, f"Init error: {str(e)}")
                return

            # Step 4: Test actual connection
            log_message("Step 4/5: Testing API connection...")
            try:
                # Use provider service's test method
                test_success = False
                test_message = "Unknown result"

                # Wait a moment for initialization to complete
                time.sleep(0.5)
                QtWidgets.QApplication.processEvents()

                # Check if provider was added and test it
                providers = self.provider_service.get_all_providers()
                if provider_name in providers:
                    provider_status = providers[provider_name]
                    log_message(f"Provider status: {provider_status}", "DEBUG")

                    # Trigger connection test
                    self.provider_service.test_provider_connection(provider_name)

                    # Wait for test to complete (check status updates)
                    max_wait = 50  # 5 seconds max
                    wait_count = 0
                    while wait_count < max_wait:
                        time.sleep(0.1)
                        QtWidgets.QApplication.processEvents()

                        current_status = self.provider_service.get_provider_status(
                            provider_name
                        )
                        status_text = current_status.get("status", "unknown")

                        if status_text == "testing":
                            log_message("Test in progress...", "DEBUG")
                        elif status_text == "connected":
                            test_success = True
                            test_message = current_status.get(
                                "message", "Connected successfully"
                            )
                            break
                        elif status_text == "error":
                            test_success = False
                            test_message = current_status.get(
                                "message", "Connection failed"
                            )
                            break

                        wait_count += 1

                    if wait_count >= max_wait:
                        log_message("Connection test timed out", "ERROR")
                        test_success = False
                        test_message = "Test timed out"
                else:
                    log_message("Provider not found in provider service", "ERROR")
                    test_success = False
                    test_message = "Provider not registered"

                if test_success:
                    log_message(f"API connection successful: {test_message}", "SUCCESS")
                else:
                    log_message(f"API connection failed: {test_message}", "ERROR")
                    self._test_connection_finished(False, test_message)
                    return

            except Exception as e:
                log_message(f"Connection test error: {str(e)}", "ERROR")
                import traceback

                log_message(f"Traceback: {traceback.format_exc()}", "DEBUG")
                self._test_connection_finished(False, f"Test error: {str(e)}")
                return

            # Step 5: Final validation
            log_message("Step 5/5: Final validation...")
            if test_success:
                log_message("=" * 60, "SUCCESS")
                log_message("CONNECTION TEST COMPLETED SUCCESSFULLY!", "SUCCESS")
                log_message("=" * 60, "SUCCESS")
                self._test_connection_finished(True, "Connection successful")
            else:
                log_message("=" * 60, "ERROR")
                log_message("CONNECTION TEST FAILED!", "ERROR")
                log_message("=" * 60, "ERROR")
                self._test_connection_finished(False, "Test failed")

        except Exception as e:
            log_message(f"Unexpected error during test: {str(e)}", "ERROR")
            import traceback

            log_message(f"Full traceback: {traceback.format_exc()}", "DEBUG")
            self._test_connection_finished(False, f"Unexpected error: {str(e)}")

    def _test_connection_finished(self, success=True, message=""):
        """Handle test connection completion."""
        self.test_connection_btn.setEnabled(True)
        self.test_connection_btn.setText("Test Connection")

        if success:
            QtWidgets.QMessageBox.information(
                self,
                "Connection Test Successful",
                f"Connection test completed successfully!\n\n{message}",
            )
        else:
            QtWidgets.QMessageBox.warning(
                self,
                "Connection Test Failed",
                f"Connection test failed:\n\n{message}\n\nCheck the console output for more details.",
            )

    def _refresh_providers(self):
        """Refresh providers table."""
        print("DEBUG: Refreshing providers table...")
        self.providers_table.setRowCount(0)

        # Add default providers first
        if hasattr(self, "default_providers"):
            print(f"DEBUG: Adding {len(self.default_providers)} default providers")
            for provider_info in self.default_providers:
                self._add_default_provider_to_table(provider_info)
        else:
            print("DEBUG: No default_providers attribute found")

        # Add custom providers
        if hasattr(self, "custom_providers"):
            print(f"DEBUG: Adding {len(self.custom_providers)} custom providers")
            for provider_info in self.custom_providers:
                if not self._provider_in_table(provider_info["name"]):
                    self._add_default_provider_to_table(provider_info)
        else:
            print("DEBUG: No custom_providers attribute found")

        # Add providers from AI manager if available
        if self.ai_manager:
            print(f"DEBUG: AI manager has {len(self.ai_manager.providers)} providers: {list(self.ai_manager.providers.keys())}")
            for provider_name, provider in self.ai_manager.providers.items():
                if not self._provider_in_table(provider_name):
                    self._add_provider_to_table(provider_name, provider)
        else:
            print("DEBUG: No AI manager available")

        # Also update from provider service if available
        if self.provider_service:
            providers = self.provider_service.get_all_providers()
            print(f"DEBUG: Provider service has {len(providers)} providers: {list(providers.keys())}")
            for provider_name, provider_info in providers.items():
                if not self._provider_in_table(provider_name):
                    self._add_provider_info_to_table(provider_name, provider_info)
        else:
            print("DEBUG: No provider service available")
            
        final_row_count = self.providers_table.rowCount()
        print(f"DEBUG: Final provider table has {final_row_count} rows")
        
        # Fallback: if no providers are shown, add at least the default ones manually
        if final_row_count == 0:
            print("DEBUG: No providers in table, adding fallback default providers...")
            fallback_providers = [
                {
                    "name": "Anthropic",
                    "type": "anthropic", 
                    "default_model": "claude-3-5-sonnet-20241022",
                    "status": "Not configured"
                },
                {
                    "name": "OpenAI",
                    "type": "openai",
                    "default_model": "gpt-4o-mini", 
                    "status": "Not configured"
                }
            ]
            
            for provider_info in fallback_providers:
                self._add_default_provider_to_table(provider_info)
                
            print(f"DEBUG: Added {len(fallback_providers)} fallback providers")
            print(f"DEBUG: Table now has {self.providers_table.rowCount()} rows")

    def _add_default_provider_to_table(self, provider_info):
        """Add default provider to table."""
        row = self.providers_table.rowCount()
        self.providers_table.insertRow(row)

        provider_name = provider_info["name"]
        provider_type = provider_info["type"]
        default_model = provider_info["default_model"]

        # Check if API key is configured
        has_api_key = False
        if self.config_manager:
            api_key = self.config_manager.get_api_key(provider_type)
            has_api_key = bool(api_key and len(api_key.strip()) > 10)

        status = "Configured" if has_api_key else "Not configured"

        self.providers_table.setItem(row, 0, QtWidgets.QTableWidgetItem(provider_name))
        self.providers_table.setItem(
            row, 1, QtWidgets.QTableWidgetItem(provider_type.title())
        )
        self.providers_table.setItem(row, 2, QtWidgets.QTableWidgetItem(default_model))

        # Color code the status
        status_item = QtWidgets.QTableWidgetItem(status)
        if has_api_key:
            status_item.setForeground(QtGui.QColor("#4CAF50"))
        else:
            status_item.setForeground(QtGui.QColor("#FF9800"))
        self.providers_table.setItem(row, 3, status_item)

        # Check if default provider
        default_provider = (
            self.config_manager.get_default_provider() if self.config_manager else ""
        )
        is_default = provider_name == default_provider
        default_item = QtWidgets.QTableWidgetItem("✓" if is_default else "")
        self.providers_table.setItem(row, 4, default_item)

    def _add_provider_to_table(self, provider_name, provider):
        """Add provider to table."""
        row = self.providers_table.rowCount()
        self.providers_table.insertRow(row)

        self.providers_table.setItem(row, 0, QtWidgets.QTableWidgetItem(provider_name))
        self.providers_table.setItem(
            row, 1, QtWidgets.QTableWidgetItem(provider.get_provider_name())
        )
        self.providers_table.setItem(
            row,
            2,
            QtWidgets.QTableWidgetItem(provider.get_current_model() or "Default"),
        )
        self.providers_table.setItem(row, 3, QtWidgets.QTableWidgetItem("Active"))

        # Check if default provider
        default_provider = (
            self.config_manager.get_default_provider() if self.config_manager else ""
        )
        is_default = provider_name == default_provider
        default_item = QtWidgets.QTableWidgetItem("✓" if is_default else "")
        self.providers_table.setItem(row, 4, default_item)

    def _add_provider_info_to_table(self, provider_name, provider_info):
        """Add provider info from service to table."""
        row = self.providers_table.rowCount()
        self.providers_table.insertRow(row)

        self.providers_table.setItem(row, 0, QtWidgets.QTableWidgetItem(provider_name))
        self.providers_table.setItem(
            row, 1, QtWidgets.QTableWidgetItem(provider_info.get("type", "Unknown"))
        )
        self.providers_table.setItem(
            row,
            2,
            QtWidgets.QTableWidgetItem(
                provider_info.get("config", {}).get("model", "Default")
            ),
        )

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
            try:
                success = self.config_manager.save_config()
                if success:
                    QtWidgets.QMessageBox.information(
                        self, "Success", "Configuration saved successfully"
                    )
                    self.config_status_label.setText("✅ All configuration saved")
                    self.config_status_label.setStyleSheet(
                        "color: #4CAF50; font-size: 10px; padding: 2px;"
                    )
                    # Don't clear status - keep it visible for user reference
                else:
                    QtWidgets.QMessageBox.warning(
                        self, "Error", "Failed to save configuration"
                    )
                    self.config_status_label.setText(
                        "❌ Failed to save all configuration"
                    )
                    self.config_status_label.setStyleSheet(
                        "color: #f44336; font-size: 10px; padding: 2px;"
                    )
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self, "Error", f"Error saving configuration: {str(e)}"
                )
                self.config_status_label.setText(f"❌ Error: {str(e)}")
                self.config_status_label.setStyleSheet(
                    "color: #f44336; font-size: 10px; padding: 2px;"
                )
        else:
            QtWidgets.QMessageBox.warning(
                self, "Error", "Configuration manager not available"
            )

    def _load_configuration(self):
        """Load configuration from config manager."""
        print("DEBUG: Loading configuration...")
        if not self.config_manager:
            print("DEBUG: No config manager available")
            
        # Ensure default providers are created if not already done
        if not hasattr(self, "default_providers"):
            print("DEBUG: Default providers not found, creating them...")
            self._create_default_providers()

        # Refresh providers to show current state
        print("DEBUG: Refreshing providers from _load_configuration...")
        self._refresh_providers()

    def showEvent(self, event):
        """Handle show event to refresh providers when widget becomes visible."""
        super().showEvent(event)
        print("DEBUG: ProvidersWidget shown, refreshing providers...")
        # Refresh providers when the widget becomes visible
        self._refresh_providers()
        
    def set_provider_service(self, provider_service):
        """Set the provider integration service."""
        print(f"DEBUG: Setting provider service: {provider_service}")
        self.provider_service = provider_service

        if provider_service:
            provider_service.provider_added.connect(
                lambda name, type: self._refresh_providers()
            )
            provider_service.provider_removed.connect(
                lambda name: self._refresh_providers()
            )
            provider_service.provider_status_changed.connect(
                self._on_provider_status_changed
            )
            provider_service.providers_updated.connect(self._refresh_providers)

            # Initial refresh
            print("DEBUG: Provider service set, doing initial refresh...")
            self._refresh_providers()

    def _on_provider_status_changed(
        self, provider_name: str, status: str, message: str
    ):
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

    def _retry_provider_service(self):
        """Try to reconnect to the provider service."""
        try:
            # Try to get provider service from parent widget
            parent_widget = self.parent()
            while parent_widget and not hasattr(parent_widget, "get_provider_service"):
                parent_widget = parent_widget.parent()

            if parent_widget and hasattr(parent_widget, "get_provider_service"):
                provider_service = parent_widget.get_provider_service()
                if provider_service:
                    self.set_provider_service(provider_service)
                    QtWidgets.QMessageBox.information(
                        self, "Success", "Provider service reconnected successfully!"
                    )
                    return

            QtWidgets.QMessageBox.warning(
                self,
                "Error",
                "Could not find provider service in parent widgets.\n\n"
                "The provider service may have failed to initialize.\n"
                "Check the FreeCAD console for error messages.",
            )

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Error",
                f"Error trying to reconnect provider service:\n\n{str(e)}",
            )

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

    def _debug_configuration(self):
        """Debug method to show the current configuration."""
        if not self.config_manager:
            QtWidgets.QMessageBox.warning(
                self, "Debug", "Configuration manager not available"
            )
            return

        try:
            # Get current configuration
            config = self.config_manager.config
            providers_config = config.get("providers", {})

            # Get selected provider info
            provider_name = self.selected_provider_label.text()

            debug_info = []
            debug_info.append(f"Selected Provider: {provider_name}")
            debug_info.append(
                f"Config Manager Available: {self.config_manager is not None}"
            )
            debug_info.append(f"Config File: {self.config_manager.config_file}")
            debug_info.append(f"Keys File: {self.config_manager.keys_file}")
            debug_info.append("")
            debug_info.append("All Providers Configuration:")

            for prov_name, prov_config in providers_config.items():
                debug_info.append(f"  {prov_name}: {prov_config}")

            debug_info.append("")
            debug_info.append("API Keys:")
            api_keys = self.config_manager.list_api_keys()
            for key_provider in api_keys:
                debug_info.append(f"  {key_provider}: configured")

            debug_info.append("")
            debug_info.append(
                f"Default Provider: {self.config_manager.get_default_provider()}"
            )

            # Show debug dialog
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle("Configuration Debug")
            dialog.resize(600, 400)

            layout = QtWidgets.QVBoxLayout(dialog)

            text_edit = QtWidgets.QTextEdit()
            text_edit.setPlainText("\n".join(debug_info))
            text_edit.setReadOnly(True)
            layout.addWidget(text_edit)

            close_btn = QtWidgets.QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)

            dialog.exec_()

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Debug Error", f"Error getting debug info: {str(e)}"
            )

    def _update_config_manager_status(self):
        """Update the config manager status."""
        if self.config_manager:
            self.config_manager_status.setText(
                "✅ Config manager is available and working"
            )
            self.config_manager_status.setStyleSheet(
                "color: #4CAF50; font-size: 9px; padding: 2px;"
            )
        else:
            self.config_manager_status.setText("❌ Config manager is not available")
            self.config_manager_status.setStyleSheet(
                "color: #f44336; font-size: 9px; padding: 2px;"
            )

    def _retry_config_manager(self):
        """Retry to load the config manager."""
        # Try to reload the config manager
        self._setup_services()
        self._update_config_manager_status()

        if self.config_manager:
            self._refresh_providers()
            self.config_status_label.setText("✅ Config manager loaded successfully")
            self.config_status_label.setStyleSheet(
                "color: #4CAF50; font-size: 10px; padding: 2px;"
            )
            QtWidgets.QMessageBox.information(
                self, "Success", "Config manager loaded successfully!"
            )
        else:
            QtWidgets.QMessageBox.warning(
                self,
                "Error",
                "Failed to load config manager. Check console for details.",
            )

