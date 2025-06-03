"""Settings Widget - GUI for addon settings"""

import os
import sys

# Ensure the addon directory is in the Python path
addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if addon_dir not in sys.path:
    sys.path.insert(0, addon_dir)

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
            # Import ConfigManager using absolute path after sys.path setup
            from config.config_manager import ConfigManager
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
        self._create_general_tab()
        self._create_tools_tab()

        # Control buttons
        self._create_control_buttons(layout)



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
