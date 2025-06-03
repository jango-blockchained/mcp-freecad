"""Settings Widget - GUI for addon settings"""

from PySide2 import QtCore, QtGui, QtWidgets
import logging
from typing import Dict, Any, Optional


class SettingsWidget(QtWidgets.QWidget):
    """Widget for addon settings management."""

    settings_changed = QtCore.Signal()
    api_key_validated = QtCore.Signal(str, bool, str)
    api_key_changed = QtCore.Signal(str)  # provider_name

    def __init__(self, parent=None):
        super(SettingsWidget, self).__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.config_manager = None
        self._setup_config_manager()
        self._setup_ui()
        self._load_settings()

    def _setup_config_manager(self):
        """Setup configuration manager."""
        try:
            from ..config.config_manager import ConfigManager
            self.config_manager = ConfigManager()
        except ImportError as e:
            self.logger.error(f"Failed to import ConfigManager: {e}")
            self.config_manager = None

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Create tab widget
        self.tab_widget = QtWidgets.QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create tabs
        self._create_api_keys_tab()
        self._create_providers_tab()
        self._create_general_tab()
        self._create_tools_tab()

        # Control buttons
        self._create_control_buttons(layout)

    def _create_api_keys_tab(self):
        """Create API keys management tab."""
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)

        # API Keys section
        api_group = QtWidgets.QGroupBox("API Keys")
        api_layout = QtWidgets.QFormLayout(api_group)

        # OpenAI API Key
        self.openai_key_input = QtWidgets.QLineEdit()
        self.openai_key_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.openai_key_input.setPlaceholderText("sk-...")
        openai_layout = QtWidgets.QHBoxLayout()
        openai_layout.addWidget(self.openai_key_input)

        self.openai_test_btn = QtWidgets.QPushButton("Test")
        self.openai_test_btn.setMaximumWidth(60)
        self.openai_test_btn.clicked.connect(lambda: self._test_api_key("openai"))
        openai_layout.addWidget(self.openai_test_btn)

        self.openai_show_btn = QtWidgets.QPushButton("👁")
        self.openai_show_btn.setMaximumWidth(30)
        self.openai_show_btn.setCheckable(True)
        self.openai_show_btn.clicked.connect(lambda: self._toggle_password_visibility(self.openai_key_input, self.openai_show_btn))
        openai_layout.addWidget(self.openai_show_btn)

        api_layout.addRow("OpenAI API Key:", openai_layout)

        # Anthropic API Key
        self.anthropic_key_input = QtWidgets.QLineEdit()
        self.anthropic_key_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.anthropic_key_input.setPlaceholderText("sk-ant-...")
        anthropic_layout = QtWidgets.QHBoxLayout()
        anthropic_layout.addWidget(self.anthropic_key_input)

        self.anthropic_test_btn = QtWidgets.QPushButton("Test")
        self.anthropic_test_btn.setMaximumWidth(60)
        self.anthropic_test_btn.clicked.connect(lambda: self._test_api_key("anthropic"))
        anthropic_layout.addWidget(self.anthropic_test_btn)

        self.anthropic_show_btn = QtWidgets.QPushButton("👁")
        self.anthropic_show_btn.setMaximumWidth(30)
        self.anthropic_show_btn.setCheckable(True)
        self.anthropic_show_btn.clicked.connect(lambda: self._toggle_password_visibility(self.anthropic_key_input, self.anthropic_show_btn))
        anthropic_layout.addWidget(self.anthropic_show_btn)

        api_layout.addRow("Anthropic API Key:", anthropic_layout)

        # Google API Key
        self.google_key_input = QtWidgets.QLineEdit()
        self.google_key_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.google_key_input.setPlaceholderText("Google API Key...")
        google_layout = QtWidgets.QHBoxLayout()
        google_layout.addWidget(self.google_key_input)

        self.google_test_btn = QtWidgets.QPushButton("Test")
        self.google_test_btn.setMaximumWidth(60)
        self.google_test_btn.clicked.connect(lambda: self._test_api_key("google"))
        google_layout.addWidget(self.google_test_btn)

        self.google_show_btn = QtWidgets.QPushButton("👁")
        self.google_show_btn.setMaximumWidth(30)
        self.google_show_btn.setCheckable(True)
        self.google_show_btn.clicked.connect(lambda: self._toggle_password_visibility(self.google_key_input, self.google_show_btn))
        google_layout.addWidget(self.google_show_btn)

        api_layout.addRow("Google API Key:", google_layout)

        layout.addWidget(api_group)

        # Status section
        status_group = QtWidgets.QGroupBox("API Key Status")
        status_layout = QtWidgets.QVBoxLayout(status_group)

        self.api_status_label = QtWidgets.QLabel("No API keys configured")
        self.api_status_label.setWordWrap(True)
        status_layout.addWidget(self.api_status_label)

        layout.addWidget(status_group)

        # Connect signals for auto-save
        self.openai_key_input.textChanged.connect(lambda: self._save_api_key("openai", self.openai_key_input.text()))
        self.anthropic_key_input.textChanged.connect(lambda: self._save_api_key("anthropic", self.anthropic_key_input.text()))
        self.google_key_input.textChanged.connect(lambda: self._save_api_key("google", self.google_key_input.text()))

        layout.addStretch()
        self.tab_widget.addTab(tab, "API Keys")

    def _create_providers_tab(self):
        """Create providers configuration tab."""
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)

        # Default provider
        default_group = QtWidgets.QGroupBox("Default Provider")
        default_layout = QtWidgets.QFormLayout(default_group)

        self.default_provider_combo = QtWidgets.QComboBox()
        self.default_provider_combo.addItems(["openai", "anthropic", "google"])
        self.default_provider_combo.currentTextChanged.connect(self._on_default_provider_changed)
        default_layout.addRow("Default Provider:", self.default_provider_combo)

        layout.addWidget(default_group)

        # Provider configurations
        self.provider_configs = {}
        for provider in ["openai", "anthropic", "google"]:
            group = QtWidgets.QGroupBox(f"{provider.title()} Configuration")
            group_layout = QtWidgets.QFormLayout(group)

            # Enabled checkbox
            enabled_cb = QtWidgets.QCheckBox("Enabled")
            enabled_cb.stateChanged.connect(lambda state, p=provider: self._on_provider_enabled_changed(p, state))
            group_layout.addRow("", enabled_cb)

            # Model selection
            model_combo = QtWidgets.QComboBox()
            model_combo.setEditable(True)
            if provider == "openai":
                model_combo.addItems(["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"])
            elif provider == "anthropic":
                model_combo.addItems(["claude-3-sonnet-20240229", "claude-3-haiku-20240307", "claude-3-opus-20240229"])
            elif provider == "google":
                model_combo.addItems(["gemini-pro", "gemini-pro-vision"])
            model_combo.currentTextChanged.connect(lambda text, p=provider: self._on_provider_config_changed(p, "model", text))
            group_layout.addRow("Model:", model_combo)

            # Temperature
            temp_spin = QtWidgets.QDoubleSpinBox()
            temp_spin.setRange(0.0, 2.0)
            temp_spin.setSingleStep(0.1)
            temp_spin.setDecimals(1)
            temp_spin.setValue(0.7)
            temp_spin.valueChanged.connect(lambda value, p=provider: self._on_provider_config_changed(p, "temperature", value))
            group_layout.addRow("Temperature:", temp_spin)

            # Timeout
            timeout_spin = QtWidgets.QSpinBox()
            timeout_spin.setRange(5, 300)
            timeout_spin.setValue(30)
            timeout_spin.setSuffix(" seconds")
            timeout_spin.valueChanged.connect(lambda value, p=provider: self._on_provider_config_changed(p, "timeout", value))
            group_layout.addRow("Timeout:", timeout_spin)

            # Max tokens
            tokens_spin = QtWidgets.QSpinBox()
            tokens_spin.setRange(100, 8000)
            tokens_spin.setValue(4000)
            tokens_spin.valueChanged.connect(lambda value, p=provider: self._on_provider_config_changed(p, "max_tokens", value))
            group_layout.addRow("Max Tokens:", tokens_spin)

            self.provider_configs[provider] = {
                "enabled": enabled_cb,
                "model": model_combo,
                "temperature": temp_spin,
                "timeout": timeout_spin,
                "max_tokens": tokens_spin
            }

            layout.addWidget(group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "Providers")

    def _create_general_tab(self):
        """Create general settings tab."""
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)

        # UI Settings
        ui_group = QtWidgets.QGroupBox("User Interface")
        ui_layout = QtWidgets.QFormLayout(ui_group)

        self.theme_combo = QtWidgets.QComboBox()
        self.theme_combo.addItems(["default", "dark", "light"])
        self.theme_combo.currentTextChanged.connect(lambda text: self._on_ui_setting_changed("theme", text))
        ui_layout.addRow("Theme:", self.theme_combo)

        self.auto_save_cb = QtWidgets.QCheckBox("Auto-save configuration")
        self.auto_save_cb.stateChanged.connect(lambda state: self._on_ui_setting_changed("auto_save", state == QtCore.Qt.Checked))
        ui_layout.addRow("", self.auto_save_cb)

        self.tooltips_cb = QtWidgets.QCheckBox("Show tooltips")
        self.tooltips_cb.stateChanged.connect(lambda state: self._on_ui_setting_changed("show_tooltips", state == QtCore.Qt.Checked))
        ui_layout.addRow("", self.tooltips_cb)

        self.confirm_cb = QtWidgets.QCheckBox("Confirm operations")
        self.confirm_cb.stateChanged.connect(lambda state: self._on_ui_setting_changed("confirm_operations", state == QtCore.Qt.Checked))
        ui_layout.addRow("", self.confirm_cb)

        layout.addWidget(ui_group)

        # Logging Settings
        log_group = QtWidgets.QGroupBox("Logging")
        log_layout = QtWidgets.QFormLayout(log_group)

        self.log_level_combo = QtWidgets.QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.currentTextChanged.connect(lambda text: self._on_ui_setting_changed("log_level", text))
        log_layout.addRow("Log Level:", self.log_level_combo)

        layout.addWidget(log_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "General")

    def _create_tools_tab(self):
        """Create tools default settings tab."""
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)

        # Advanced Primitives defaults
        primitives_group = QtWidgets.QGroupBox("Advanced Primitives Defaults")
        primitives_layout = QtWidgets.QFormLayout(primitives_group)

        self.default_radius_spin = QtWidgets.QDoubleSpinBox()
        self.default_radius_spin.setRange(0.1, 1000.0)
        self.default_radius_spin.setValue(5.0)
        self.default_radius_spin.setSuffix(" mm")
        self.default_radius_spin.valueChanged.connect(lambda v: self._on_tool_default_changed("advanced_primitives", "default_radius", v))
        primitives_layout.addRow("Default Radius:", self.default_radius_spin)

        self.default_height_spin = QtWidgets.QDoubleSpinBox()
        self.default_height_spin.setRange(0.1, 1000.0)
        self.default_height_spin.setValue(10.0)
        self.default_height_spin.setSuffix(" mm")
        self.default_height_spin.valueChanged.connect(lambda v: self._on_tool_default_changed("advanced_primitives", "default_height", v))
        primitives_layout.addRow("Default Height:", self.default_height_spin)

        layout.addWidget(primitives_group)

        # Surface Modification defaults
        surface_group = QtWidgets.QGroupBox("Surface Modification Defaults")
        surface_layout = QtWidgets.QFormLayout(surface_group)

        self.default_fillet_spin = QtWidgets.QDoubleSpinBox()
        self.default_fillet_spin.setRange(0.1, 100.0)
        self.default_fillet_spin.setValue(1.0)
        self.default_fillet_spin.setSuffix(" mm")
        self.default_fillet_spin.valueChanged.connect(lambda v: self._on_tool_default_changed("surface_modification", "default_fillet_radius", v))
        surface_layout.addRow("Default Fillet Radius:", self.default_fillet_spin)

        self.default_chamfer_spin = QtWidgets.QDoubleSpinBox()
        self.default_chamfer_spin.setRange(0.1, 100.0)
        self.default_chamfer_spin.setValue(1.0)
        self.default_chamfer_spin.setSuffix(" mm")
        self.default_chamfer_spin.valueChanged.connect(lambda v: self._on_tool_default_changed("surface_modification", "default_chamfer_distance", v))
        surface_layout.addRow("Default Chamfer Distance:", self.default_chamfer_spin)

        self.default_draft_spin = QtWidgets.QDoubleSpinBox()
        self.default_draft_spin.setRange(0.1, 45.0)
        self.default_draft_spin.setValue(5.0)
        self.default_draft_spin.setSuffix("°")
        self.default_draft_spin.valueChanged.connect(lambda v: self._on_tool_default_changed("surface_modification", "default_draft_angle", v))
        surface_layout.addRow("Default Draft Angle:", self.default_draft_spin)

        layout.addWidget(surface_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "Tool Defaults")

    def _create_control_buttons(self, layout):
        """Create control buttons."""
        button_layout = QtWidgets.QHBoxLayout()

        # Import/Export buttons
        self.import_btn = QtWidgets.QPushButton("Import Config")
        self.import_btn.clicked.connect(self._import_config)
        button_layout.addWidget(self.import_btn)

        self.export_btn = QtWidgets.QPushButton("Export Config")
        self.export_btn.clicked.connect(self._export_config)
        button_layout.addWidget(self.export_btn)

        button_layout.addStretch()

        # Reset button
        self.reset_btn = QtWidgets.QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self._reset_config)
        button_layout.addWidget(self.reset_btn)

        # Save button
        self.save_btn = QtWidgets.QPushButton("Save Settings")
        self.save_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; }")
        self.save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(self.save_btn)

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
        if not self.config_manager:
            QtWidgets.QMessageBox.warning(self, "Error", "Configuration manager not available")
            return

        # Get the key from input
        if provider == "openai":
            key = self.openai_key_input.text()
        elif provider == "anthropic":
            key = self.anthropic_key_input.text()
        elif provider == "google":
            key = self.google_key_input.text()
        else:
            return

        if not key:
            QtWidgets.QMessageBox.warning(self, "Error", f"Please enter {provider} API key first")
            return

        # Validate key format
        is_valid = self.config_manager.validate_api_key(provider, key)

        if is_valid:
            QtWidgets.QMessageBox.information(self, "Success", f"{provider} API key format is valid")
            self.api_key_validated.emit(provider, True, "Key format valid")
        else:
            QtWidgets.QMessageBox.warning(self, "Error", f"{provider} API key format is invalid")
            self.api_key_validated.emit(provider, False, "Invalid key format")

    def _save_api_key(self, provider, key):
        """Save API key for provider."""
        if not self.config_manager or not key:
            return

        success = self.config_manager.set_api_key(provider, key)
        if success:
            self._update_api_status()
            # Emit signal for provider integration service
            self.api_key_changed.emit(provider)

    def _update_api_status(self):
        """Update API key status display."""
        if not self.config_manager:
            return

        configured_keys = self.config_manager.list_api_keys()
        if configured_keys:
            status = f"Configured providers: {', '.join(configured_keys)}"
        else:
            status = "No API keys configured"

        self.api_status_label.setText(status)

    def _on_default_provider_changed(self, provider):
        """Handle default provider change."""
        if self.config_manager:
            self.config_manager.set_default_provider(provider)

    def _on_provider_enabled_changed(self, provider, state):
        """Handle provider enabled state change."""
        enabled = state == QtCore.Qt.Checked
        self._on_provider_config_changed(provider, "enabled", enabled)

    def _on_provider_config_changed(self, provider, key, value):
        """Handle provider configuration change."""
        if not self.config_manager:
            return

        config = self.config_manager.get_provider_config(provider)
        config[key] = value
        self.config_manager.set_provider_config(provider, config)

    def _on_ui_setting_changed(self, key, value):
        """Handle UI setting change."""
        if self.config_manager:
            self.config_manager.set_config(f"ui_settings.{key}", value)

    def _on_tool_default_changed(self, tool, key, value):
        """Handle tool default change."""
        if self.config_manager:
            self.config_manager.set_config(f"tool_defaults.{tool}.{key}", value)

    def _load_settings(self):
        """Load settings from configuration."""
        if not self.config_manager:
            return

        # Load API keys
        for provider in ["openai", "anthropic", "google"]:
            key = self.config_manager.get_api_key(provider)
            if key:
                if provider == "openai":
                    self.openai_key_input.setText(key)
                elif provider == "anthropic":
                    self.anthropic_key_input.setText(key)
                elif provider == "google":
                    self.google_key_input.setText(key)

        # Load provider configurations
        for provider in ["openai", "anthropic", "google"]:
            config = self.config_manager.get_provider_config(provider)
            if config and provider in self.provider_configs:
                controls = self.provider_configs[provider]
                controls["enabled"].setChecked(config.get("enabled", False))
                controls["model"].setCurrentText(config.get("model", ""))
                controls["temperature"].setValue(config.get("temperature", 0.7))
                controls["timeout"].setValue(config.get("timeout", 30))
                controls["max_tokens"].setValue(config.get("max_tokens", 4000))

        # Load default provider
        default_provider = self.config_manager.get_default_provider()
        self.default_provider_combo.setCurrentText(default_provider)

        # Load UI settings
        ui_settings = self.config_manager.get_config("ui_settings", {})
        self.theme_combo.setCurrentText(ui_settings.get("theme", "default"))
        self.auto_save_cb.setChecked(ui_settings.get("auto_save", True))
        self.tooltips_cb.setChecked(ui_settings.get("show_tooltips", True))
        self.confirm_cb.setChecked(ui_settings.get("confirm_operations", True))
        self.log_level_combo.setCurrentText(ui_settings.get("log_level", "INFO"))

        # Load tool defaults
        tool_defaults = self.config_manager.get_config("tool_defaults", {})
        primitives_defaults = tool_defaults.get("advanced_primitives", {})
        self.default_radius_spin.setValue(primitives_defaults.get("default_radius", 5.0))
        self.default_height_spin.setValue(primitives_defaults.get("default_height", 10.0))

        surface_defaults = tool_defaults.get("surface_modification", {})
        self.default_fillet_spin.setValue(surface_defaults.get("default_fillet_radius", 1.0))
        self.default_chamfer_spin.setValue(surface_defaults.get("default_chamfer_distance", 1.0))
        self.default_draft_spin.setValue(surface_defaults.get("default_draft_angle", 5.0))

        self._update_api_status()

    def _save_settings(self):
        """Save all settings."""
        if not self.config_manager:
            QtWidgets.QMessageBox.warning(self, "Error", "Configuration manager not available")
            return

        success = self.config_manager.save_config()
        if success:
            QtWidgets.QMessageBox.information(self, "Success", "Settings saved successfully")
            self.settings_changed.emit()
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Failed to save settings")

    def _reset_config(self):
        """Reset configuration to defaults."""
        reply = QtWidgets.QMessageBox.question(
            self, "Reset Configuration",
            "Are you sure you want to reset all settings to defaults?\nThis will remove all API keys and custom configurations.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes and self.config_manager:
            success = self.config_manager.reset_config()
            if success:
                self._load_settings()
                QtWidgets.QMessageBox.information(self, "Success", "Configuration reset to defaults")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Failed to reset configuration")

    def _import_config(self):
        """Import configuration from file."""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Import Configuration", "", "JSON Files (*.json)"
        )

        if file_path and self.config_manager:
            success = self.config_manager.import_config(file_path)
            if success:
                self._load_settings()
                QtWidgets.QMessageBox.information(self, "Success", "Configuration imported successfully")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Failed to import configuration")

    def _export_config(self):
        """Export configuration to file."""
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export Configuration", "mcp_freecad_config.json", "JSON Files (*.json)"
        )

        if file_path and self.config_manager:
            # Ask if user wants to include API keys
            reply = QtWidgets.QMessageBox.question(
                self, "Export API Keys",
                "Do you want to include API keys in the export?\n(Keys will be encrypted)",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No
            )

            include_keys = reply == QtWidgets.QMessageBox.Yes
            success = self.config_manager.export_config(file_path, include_keys)

            if success:
                QtWidgets.QMessageBox.information(self, "Success", "Configuration exported successfully")
            else:
                QtWidgets.QMessageBox.warning(self, "Error", "Failed to export configuration")
