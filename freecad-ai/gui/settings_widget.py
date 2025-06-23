"""Settings Widget - GUI for addon settings"""

import os
import sys

# Ensure the addon directory is in the Python path
# This block should be as early as possible
addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if addon_dir not in sys.path:
    sys.path.insert(0, addon_dir)

# Standard library imports
import json
import logging
from typing import Dict

# Third-party imports
from PySide2 import QtCore, QtWidgets

# Local application/library specific imports
from config.config_manager import ConfigManager
from utils.cad_context_extractor import get_cad_context_extractor
from utils.dependency_checker import DependencyChecker


class SystemPromptsTableModel(QtCore.QAbstractTableModel):
    """Table model for system prompts management."""

    def __init__(self, prompts_data: Dict[str, str] = None):
        super().__init__()
        self.prompts_data = prompts_data or self._get_default_prompts()
        self.headers = ["Provider/Context", "System Prompt"]

    def _get_default_prompts(self) -> Dict[str, str]:
        """Get default system prompts."""
        return {
            "default": "You are an AI assistant specialized in FreeCAD CAD operations. Help users with 3D modeling, parametric design, and CAD workflows. Be precise and practical in your responses.",
            "anthropic": "You are Claude, an AI assistant specialized in FreeCAD CAD operations. You have expertise in 3D modeling, parametric design, engineering workflows, and manufacturing processes. Provide detailed, accurate guidance for CAD tasks.",
            "openai": "You are a helpful AI assistant with expertise in FreeCAD and computer-aided design. Help users create, modify, and optimize 3D models with clear, step-by-step instructions.",
            "google": "You are an AI assistant specialized in FreeCAD CAD software. Assist users with 3D modeling tasks, workbench navigation, and design optimization. Focus on practical, actionable advice.",
            "cad_context": "When CAD context is provided, analyze the current FreeCAD document state including objects, geometry, and workspace. Use this information to provide contextually relevant suggestions and solutions.",
            "error_handling": "When users encounter errors or issues, provide systematic troubleshooting steps. Consider common FreeCAD pitfalls and suggest alternative approaches when needed.",
            "beginner_mode": "Explain concepts clearly for users new to FreeCAD. Include basic terminology explanations and step-by-step guidance. Suggest learning resources when appropriate.",
            "advanced_mode": "Provide detailed technical information for experienced users. Include advanced techniques, scripting examples, and optimization strategies. Assume familiarity with CAD concepts.",
        }

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.prompts_data)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self.headers)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if row >= len(self.prompts_data):
            return None

        keys = list(self.prompts_data.keys())
        key = keys[row]

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            if col == 0:
                return key
            elif col == 1:
                return self.prompts_data[key]

        return None

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid() or role != QtCore.Qt.EditRole:
            return False

        row = index.row()
        col = index.column()

        if row >= len(self.prompts_data):
            return False

        keys = list(self.prompts_data.keys())
        old_key = keys[row]

        if col == 0:  # Provider/Context name
            if value != old_key and value not in self.prompts_data:
                # Rename key
                self.prompts_data[value] = self.prompts_data.pop(old_key)
                self.dataChanged.emit(index, index)
                return True
        elif col == 1:  # System prompt
            self.prompts_data[old_key] = value
            self.dataChanged.emit(index, index)
            return True

        return False

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        return (
            QtCore.Qt.ItemIsEnabled
            | QtCore.Qt.ItemIsSelectable
            | QtCore.Qt.ItemIsEditable
        )

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.headers[section]
        return None

    def add_prompt(self, name: str, prompt: str):
        """Add a new prompt."""
        if name not in self.prompts_data:
            self.beginInsertRows(
                QtCore.QModelIndex(), len(self.prompts_data), len(self.prompts_data)
            )
            self.prompts_data[name] = prompt
            self.endInsertRows()

    def remove_prompt(self, name: str):
        """Remove a prompt."""
        if name in self.prompts_data:
            keys = list(self.prompts_data.keys())
            row = keys.index(name)
            self.beginRemoveRows(QtCore.QModelIndex(), row, row)
            del self.prompts_data[name]
            self.endRemoveRows()

    def get_prompts_data(self) -> Dict[str, str]:
        """Get the current prompts data."""
        return self.prompts_data.copy()


class CADContextPreviewDialog(QtWidgets.QDialog):
    """Dialog to preview CAD context information."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CAD Context Preview")
        self.setModal(True)
        self.resize(700, 500)
        self._setup_ui()
        self._load_context()

    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QtWidgets.QVBoxLayout(self)

        # Header
        header_label = QtWidgets.QLabel("Current CAD Context Information")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        layout.addWidget(header_label)

        # Tab widget for different context views
        self.tab_widget = QtWidgets.QTabWidget()
        layout.addWidget(self.tab_widget)

        # Compact view tab
        self.compact_text = QtWidgets.QTextEdit()
        self.compact_text.setReadOnly(True)
        self.compact_text.setStyleSheet("font-family: monospace; font-size: 11px;")
        self.tab_widget.addTab(self.compact_text, "Compact View")

        # Detailed view tab
        self.detailed_text = QtWidgets.QTextEdit()
        self.detailed_text.setReadOnly(True)
        self.detailed_text.setStyleSheet("font-family: monospace; font-size: 10px;")
        self.tab_widget.addTab(self.detailed_text, "Detailed View")

        # Control buttons
        button_layout = QtWidgets.QHBoxLayout()

        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._load_context)
        button_layout.addWidget(self.refresh_btn)

        self.copy_compact_btn = QtWidgets.QPushButton("Copy Compact")
        self.copy_compact_btn.clicked.connect(self._copy_compact)
        button_layout.addWidget(self.copy_compact_btn)

        self.copy_detailed_btn = QtWidgets.QPushButton("Copy Detailed")
        self.copy_detailed_btn.clicked.connect(self._copy_detailed)
        button_layout.addWidget(self.copy_detailed_btn)

        button_layout.addStretch()

        self.close_btn = QtWidgets.QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def _load_context(self):
        """Load and display CAD context."""
        try:
            extractor = get_cad_context_extractor()

            # Load compact view
            compact_context = extractor.get_compact_context()
            self.compact_text.setPlainText(compact_context)

            # Load detailed view
            full_context = extractor.get_full_context()
            detailed_text = json.dumps(full_context, indent=2)
            self.detailed_text.setPlainText(detailed_text)

        except Exception as e:
            error_msg = f"Error loading CAD context: {str(e)}"
            self.compact_text.setPlainText(error_msg)
            self.detailed_text.setPlainText(error_msg)

    def _copy_compact(self):
        """Copy compact context to clipboard."""
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(self.compact_text.toPlainText())
        QtWidgets.QMessageBox.information(
            self, "Copied", "Compact context copied to clipboard"
        )

    def _copy_detailed(self):
        """Copy detailed context to clipboard."""
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(self.detailed_text.toPlainText())
        QtWidgets.QMessageBox.information(
            self, "Copied", "Detailed context copied to clipboard"
        )


class SettingsWidget(QtWidgets.QWidget):
    """Widget for addon settings management."""

    settings_changed = QtCore.Signal()
    api_key_validated = QtCore.Signal(str, bool, str)
    api_key_changed = QtCore.Signal(str)  # provider_name

    def __init__(self, parent=None):
        super(SettingsWidget, self).__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.config_manager = None
        self.prompts_model = None
        self._setup_config_manager()
        self._setup_ui()
        self._load_settings()

    def _setup_config_manager(self):
        """Setup configuration manager."""
        try:
            # Debug: Print sys.path and addon directory info
            addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.logger.info(f"Addon directory: {addon_dir}")
            self.logger.info(f"Current working directory: {os.getcwd()}")
            self.logger.info(f"Addon dir in sys.path: {addon_dir in sys.path}")

            # Import ConfigManager
            self.config_manager = ConfigManager()
            self.logger.info("ConfigManager initialized successfully")
        except ImportError as e:
            self.logger.error(f"Failed to import ConfigManager: {e}")
            self.logger.error(f"Import error type: {type(e)}")
            self.logger.error(f"Import error args: {e.args}")
            self.config_manager = None
        except Exception as e:
            self.logger.error(f"Failed to initialize ConfigManager: {e}")
            self.logger.error(f"Error type: {type(e)}")
            self.logger.error(f"Error args: {e.args}")
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
        self._create_system_prompts_tab()
        self._create_tools_tab()
        self._create_dependencies_tab()

        # Control buttons
        self._create_control_buttons(layout)

    def _create_system_prompts_tab(self):
        """Create system prompts management tab."""
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)

        # Header
        header_layout = QtWidgets.QHBoxLayout()
        header_label = QtWidgets.QLabel("System Prompts Configuration")
        header_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(header_label)

        header_layout.addStretch()

        # CAD Context preview button
        self.cad_context_btn = QtWidgets.QPushButton("Preview CAD Context")
        self.cad_context_btn.setToolTip(
            "Preview what CAD context information is sent to AI"
        )
        self.cad_context_btn.clicked.connect(self._preview_cad_context)
        header_layout.addWidget(self.cad_context_btn)

        layout.addLayout(header_layout)

        # Description
        desc_label = QtWidgets.QLabel(
            "Configure system prompts for different AI providers and contexts. "
            "These prompts define how the AI should behave and respond to user queries."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; font-size: 10px; padding: 5px;")
        layout.addWidget(desc_label)

        # Table for prompts
        self.prompts_model = SystemPromptsTableModel()
        self.prompts_table = QtWidgets.QTableView()
        self.prompts_table.setModel(self.prompts_model)

        # Configure table
        self.prompts_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.prompts_table.setAlternatingRowColors(True)
        self.prompts_table.setSortingEnabled(True)

        # Set column widths
        header = self.prompts_table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)

        # Set row height
        self.prompts_table.verticalHeader().setDefaultSectionSize(60)

        layout.addWidget(self.prompts_table)

        # Buttons for prompt management
        button_layout = QtWidgets.QHBoxLayout()

        self.add_prompt_btn = QtWidgets.QPushButton("Add Prompt")
        self.add_prompt_btn.clicked.connect(self._add_prompt)
        button_layout.addWidget(self.add_prompt_btn)

        self.remove_prompt_btn = QtWidgets.QPushButton("Remove Prompt")
        self.remove_prompt_btn.clicked.connect(self._remove_prompt)
        button_layout.addWidget(self.remove_prompt_btn)

        self.reset_prompts_btn = QtWidgets.QPushButton("Reset to Defaults")
        self.reset_prompts_btn.clicked.connect(self._reset_prompts)
        button_layout.addWidget(self.reset_prompts_btn)

        button_layout.addStretch()

        self.import_prompts_btn = QtWidgets.QPushButton("Import")
        self.import_prompts_btn.clicked.connect(self._import_prompts)
        button_layout.addWidget(self.import_prompts_btn)

        self.export_prompts_btn = QtWidgets.QPushButton("Export")
        self.export_prompts_btn.clicked.connect(self._export_prompts)
        button_layout.addWidget(self.export_prompts_btn)

        layout.addLayout(button_layout)

        self.tab_widget.addTab(tab, "System Prompts")

    def _create_general_tab(self):
        """Create general settings tab."""
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)

        # UI Settings
        ui_group = QtWidgets.QGroupBox("User Interface")
        ui_layout = QtWidgets.QFormLayout(ui_group)

        self.theme_combo = QtWidgets.QComboBox()
        self.theme_combo.addItems(["default", "dark", "light"])
        self.theme_combo.currentTextChanged.connect(
            lambda text: self._on_ui_setting_changed("theme", text)
        )
        ui_layout.addRow("Theme:", self.theme_combo)

        self.auto_save_cb = QtWidgets.QCheckBox("Auto-save configuration")
        self.auto_save_cb.stateChanged.connect(
            lambda state: self._on_ui_setting_changed(
                "auto_save", state == QtCore.Qt.Checked
            )
        )
        ui_layout.addRow("", self.auto_save_cb)

        self.tooltips_cb = QtWidgets.QCheckBox("Show tooltips")
        self.tooltips_cb.stateChanged.connect(
            lambda state: self._on_ui_setting_changed(
                "show_tooltips", state == QtCore.Qt.Checked
            )
        )
        ui_layout.addRow("", self.tooltips_cb)

        self.confirm_cb = QtWidgets.QCheckBox("Confirm operations")
        self.confirm_cb.stateChanged.connect(
            lambda state: self._on_ui_setting_changed(
                "confirm_operations", state == QtCore.Qt.Checked
            )
        )
        ui_layout.addRow("", self.confirm_cb)

        layout.addWidget(ui_group)

        # Logging Settings
        log_group = QtWidgets.QGroupBox("Logging")
        log_layout = QtWidgets.QFormLayout(log_group)

        self.log_level_combo = QtWidgets.QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.currentTextChanged.connect(
            lambda text: self._on_ui_setting_changed("log_level", text)
        )
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
        self.default_radius_spin.valueChanged.connect(
            lambda v: self._on_tool_default_changed(
                "advanced_primitives", "default_radius", v
            )
        )
        primitives_layout.addRow("Default Radius:", self.default_radius_spin)

        self.default_height_spin = QtWidgets.QDoubleSpinBox()
        self.default_height_spin.setRange(0.1, 1000.0)
        self.default_height_spin.setValue(10.0)
        self.default_height_spin.setSuffix(" mm")
        self.default_height_spin.valueChanged.connect(
            lambda v: self._on_tool_default_changed(
                "advanced_primitives", "default_height", v
            )
        )
        primitives_layout.addRow("Default Height:", self.default_height_spin)

        layout.addWidget(primitives_group)

        # Surface Modification defaults
        surface_group = QtWidgets.QGroupBox("Surface Modification Defaults")
        surface_layout = QtWidgets.QFormLayout(surface_group)

        self.default_fillet_spin = QtWidgets.QDoubleSpinBox()
        self.default_fillet_spin.setRange(0.1, 100.0)
        self.default_fillet_spin.setValue(1.0)
        self.default_fillet_spin.setSuffix(" mm")
        self.default_fillet_spin.valueChanged.connect(
            lambda v: self._on_tool_default_changed(
                "surface_modification", "default_fillet_radius", v
            )
        )
        surface_layout.addRow("Default Fillet Radius:", self.default_fillet_spin)

        self.default_chamfer_spin = QtWidgets.QDoubleSpinBox()
        self.default_chamfer_spin.setRange(0.1, 100.0)
        self.default_chamfer_spin.setValue(1.0)
        self.default_chamfer_spin.setSuffix(" mm")
        self.default_chamfer_spin.valueChanged.connect(
            lambda v: self._on_tool_default_changed(
                "surface_modification", "default_chamfer_distance", v
            )
        )
        surface_layout.addRow("Default Chamfer Distance:", self.default_chamfer_spin)

        self.default_draft_spin = QtWidgets.QDoubleSpinBox()
        self.default_draft_spin.setRange(0.1, 45.0)
        self.default_draft_spin.setValue(5.0)
        self.default_draft_spin.setSuffix("°")
        self.default_draft_spin.valueChanged.connect(
            lambda v: self._on_tool_default_changed(
                "surface_modification", "default_draft_angle", v
            )
        )
        surface_layout.addRow("Default Draft Angle:", self.default_draft_spin)

        layout.addWidget(surface_group)

        layout.addStretch()
        self.tab_widget.addTab(tab, "Tool Defaults")

    def _create_dependencies_tab(self):
        """Create dependencies management tab."""
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(tab)

        header_label = QtWidgets.QLabel("Manage Missing Dependencies")
        header_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(header_label)

        desc_label = QtWidgets.QLabel(
            "Check for and install any missing Python dependencies required by the addon."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; font-size: 10px; padding: 5px;")
        layout.addWidget(desc_label)

        self.missing_deps_list = QtWidgets.QListWidget()
        self.missing_deps_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        layout.addWidget(self.missing_deps_list)

        button_layout = QtWidgets.QHBoxLayout()
        self.check_deps_btn = QtWidgets.QPushButton("Check for Missing Dependencies")
        self.check_deps_btn.clicked.connect(self._check_dependencies)
        button_layout.addWidget(self.check_deps_btn)

        self.install_deps_btn = QtWidgets.QPushButton("Install Selected Dependencies")
        self.install_deps_btn.clicked.connect(self._install_selected_dependencies)
        button_layout.addWidget(self.install_deps_btn)
        layout.addLayout(button_layout)

        self.deps_status_label = QtWidgets.QLabel("Status: Idle")
        self.deps_status_label.setWordWrap(True)
        layout.addWidget(self.deps_status_label)

        layout.addStretch()
        self.tab_widget.addTab(tab, "Dependencies")

    def _check_dependencies(self):
        """Check for missing dependencies and update the list."""
        self.deps_status_label.setText("Status: Checking dependencies...")
        QtWidgets.QApplication.processEvents()  # Ensure UI updates

        try:
            checker = DependencyChecker()
            missing = checker.get_missing_dependencies()

            self.missing_deps_list.clear()
            if missing:
                for dep in missing:
                    self.missing_deps_list.addItem(dep)
                self.deps_status_label.setText(f"Status: Found {len(missing)} missing dependencies.")
                self.install_deps_btn.setEnabled(True)
            else:
                self.deps_status_label.setText("Status: All dependencies are installed.")
                self.install_deps_btn.setEnabled(False)
        except Exception as e:
            self.logger.error(f"Error checking dependencies: {e}")
            self.deps_status_label.setText(f"Status: Error checking dependencies: {e}")
            QtWidgets.QMessageBox.warning(self, "Dependency Check Error", str(e))

    def _install_selected_dependencies(self):
        """Install selected missing dependencies."""
        selected_items = self.missing_deps_list.selectedItems()
        if not selected_items:
            QtWidgets.QMessageBox.information(self, "No Selection", "Please select dependencies to install.")
            return

        deps_to_install = [item.text() for item in selected_items]
        
        self.deps_status_label.setText(f"Status: Installing {', '.join(deps_to_install)}...")
        QtWidgets.QApplication.processEvents() # Ensure UI updates

        try:
            checker = DependencyChecker()
            successfully_installed, failed_to_install = checker.install_dependencies(deps_to_install)
            
            # Log the results
            if successfully_installed:
                self.logger.info(f"Successfully installed: {', '.join(successfully_installed)}")
            if failed_to_install:
                self.logger.warning(f"Failed to install: {', '.join(failed_to_install)}")

            # Update UI based on results
            if successfully_installed and not failed_to_install:
                QtWidgets.QMessageBox.information(self, "Installation Complete", 
                                                  f"Successfully installed: {', '.join(successfully_installed)}."
                                                  "\\nPlease restart FreeCAD for changes to take full effect.")
            elif failed_to_install:
                error_message = f"Installation Report:\n\nSuccessfully installed: {', '.join(successfully_installed) if successfully_installed else 'None'}\nFailed to install: {', '.join(failed_to_install)}\n\nCheck the FreeCAD Report View or console for more details from pip."
                if not successfully_installed:
                     error_message += "\\nNo packages were installed successfully."
                error_message += "\\nSome packages may require a FreeCAD restart even if partially successful."
                QtWidgets.QMessageBox.warning(self, "Installation Issues", error_message)
            
            # Always re-check dependencies to update the list and status
            self._check_dependencies()

        except Exception as e:
            self.logger.error(f"Error during installation process in UI: {e}")
            self.deps_status_label.setText(f"Status: Error during installation: {e}")
            QtWidgets.QMessageBox.critical(self, "Installation Error", 
                                         f"An unexpected error occurred: {e}"
                                         "\\nCheck the FreeCAD Report View or console for details.")
            # Optionally, re-check dependencies even after an unexpected error
            self._check_dependencies()

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
        self.save_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; }"
        )
        self.save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(self.save_btn)

        layout.addLayout(button_layout)

    def _preview_cad_context(self):
        """Preview CAD context information."""
        dialog = CADContextPreviewDialog(self)
        dialog.exec_()

    def _add_prompt(self):
        """Add a new system prompt."""
        name, ok = QtWidgets.QInputDialog.getText(
            self, "Add System Prompt", "Enter prompt name/context:"
        )

        if ok and name.strip():
            name = name.strip()
            if name in self.prompts_model.prompts_data:
                QtWidgets.QMessageBox.warning(
                    self, "Error", f"Prompt '{name}' already exists"
                )
                return

            prompt, ok = QtWidgets.QInputDialog.getMultiLineText(
                self, "Add System Prompt", f"Enter system prompt for '{name}':"
            )

            if ok:
                self.prompts_model.add_prompt(name, prompt)

    def _remove_prompt(self):
        """Remove selected system prompt."""
        selection = self.prompts_table.selectionModel().selectedRows()
        if not selection:
            QtWidgets.QMessageBox.information(
                self, "Info", "Please select a prompt to remove"
            )
            return

        row = selection[0].row()
        keys = list(self.prompts_model.prompts_data.keys())
        if row < len(keys):
            name = keys[row]

            reply = QtWidgets.QMessageBox.question(
                self,
                "Remove Prompt",
                f"Are you sure you want to remove the prompt '{name}'?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            )

            if reply == QtWidgets.QMessageBox.Yes:
                self.prompts_model.remove_prompt(name)

    def _reset_prompts(self):
        """Reset prompts to defaults."""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Reset Prompts",
            "Are you sure you want to reset all system prompts to defaults?\nThis will remove any custom prompts.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        )

        if reply == QtWidgets.QMessageBox.Yes:
            self.prompts_model = SystemPromptsTableModel()
            self.prompts_table.setModel(self.prompts_model)

    def _import_prompts(self):
        """Import system prompts from file."""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Import System Prompts", "", "JSON Files (*.json)"
        )

        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    prompts_data = json.load(f)

                if isinstance(prompts_data, dict):
                    self.prompts_model = SystemPromptsTableModel(prompts_data)
                    self.prompts_table.setModel(self.prompts_model)
                    QtWidgets.QMessageBox.information(
                        self, "Success", "System prompts imported successfully"
                    )
                else:
                    QtWidgets.QMessageBox.warning(
                        self, "Error", "Invalid prompts file format"
                    )

            except Exception as e:
                QtWidgets.QMessageBox.warning(
                    self, "Error", f"Failed to import prompts: {str(e)}"
                )

    def _export_prompts(self):
        """Export system prompts to file."""
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export System Prompts", "system_prompts.json", "JSON Files (*.json)"
        )

        if file_path:
            try:
                prompts_data = self.prompts_model.get_prompts_data()
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(prompts_data, f, indent=2, ensure_ascii=False)

                QtWidgets.QMessageBox.information(
                    self, "Success", "System prompts exported successfully"
                )

            except Exception as e:
                QtWidgets.QMessageBox.warning(
                    self, "Error", f"Failed to export prompts: {str(e)}"
                )

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
        self.logger.info("Starting to load settings...")

        if not self.config_manager:
            self.logger.error("Cannot load settings: config_manager is None")
            # Show error message to user
            error_label = QtWidgets.QLabel(
                "Error: Configuration manager failed to initialize.\nCheck console for details."
            )
            error_label.setStyleSheet("color: red; font-weight: bold; padding: 20px;")
            error_label.setAlignment(QtCore.Qt.AlignCenter)

            # Add error label to each tab
            for i in range(self.tab_widget.count()):
                tab = self.tab_widget.widget(i)
                if hasattr(tab, "layout") and tab.layout():
                    tab.layout().insertWidget(
                        0, QtWidgets.QLabel("Configuration Error - Check console")
                    )
            return

        self.logger.info("ConfigManager available, loading settings...")

        # Load UI settings
        ui_settings = self.config_manager.get_config("ui_settings", {})
        self.logger.info(f"Loaded UI settings: {ui_settings}")
        self.theme_combo.setCurrentText(ui_settings.get("theme", "default"))
        self.auto_save_cb.setChecked(ui_settings.get("auto_save", True))
        self.tooltips_cb.setChecked(ui_settings.get("show_tooltips", True))
        self.confirm_cb.setChecked(ui_settings.get("confirm_operations", True))
        self.log_level_combo.setCurrentText(ui_settings.get("log_level", "INFO"))

        # Load tool defaults
        tool_defaults = self.config_manager.get_config("tool_defaults", {})
        self.logger.info(f"Loaded tool defaults: {tool_defaults}")
        primitives_defaults = tool_defaults.get("advanced_primitives", {})
        self.default_radius_spin.setValue(
            primitives_defaults.get("default_radius", 5.0)
        )
        self.default_height_spin.setValue(
            primitives_defaults.get("default_height", 10.0)
        )

        surface_defaults = tool_defaults.get("surface_modification", {})
        self.default_fillet_spin.setValue(
            surface_defaults.get("default_fillet_radius", 1.0)
        )
        self.default_chamfer_spin.setValue(
            surface_defaults.get("default_chamfer_distance", 1.0)
        )
        self.default_draft_spin.setValue(
            surface_defaults.get("default_draft_angle", 5.0)
        )

        # Load system prompts
        system_prompts = self.config_manager.get_config("system_prompts", {})
        self.logger.info(f"Loaded system prompts count: {len(system_prompts)}")
        if system_prompts and self.prompts_model:
            self.prompts_model = SystemPromptsTableModel(system_prompts)
            self.prompts_table.setModel(self.prompts_model)

        self.logger.info("Settings loaded successfully")

    def _save_settings(self):
        """Save all settings."""
        if not self.config_manager:
            QtWidgets.QMessageBox.warning(
                self, "Error", "Configuration manager not available"
            )
            return

        # Save system prompts
        if self.prompts_model:
            prompts_data = self.prompts_model.get_prompts_data()
            self.config_manager.set_config("system_prompts", prompts_data)

        success = self.config_manager.save_config()
        if success:
            QtWidgets.QMessageBox.information(
                self, "Success", "Settings saved successfully"
            )
            self.settings_changed.emit()
        else:
            QtWidgets.QMessageBox.warning(self, "Error", "Failed to save settings")

    def _reset_config(self):
        """Reset configuration to defaults."""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Reset Configuration",
            "Are you sure you want to reset all settings to defaults?\nThis will remove all API keys and custom configurations.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )

        if reply == QtWidgets.QMessageBox.Yes and self.config_manager:
            success = self.config_manager.reset_config()
            if success:
                self._load_settings()
                QtWidgets.QMessageBox.information(
                    self, "Success", "Configuration reset to defaults"
                )
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Error", "Failed to reset configuration"
                )

    def _import_config(self):
        """Import configuration from file."""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Import Configuration", "", "JSON Files (*.json)"
        )

        if file_path and self.config_manager:
            success = self.config_manager.import_config(file_path)
            if success:
                self._load_settings()
                QtWidgets.QMessageBox.information(
                    self, "Success", "Configuration imported successfully"
                )
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Error", "Failed to import configuration"
                )

    def _export_config(self):
        """Export configuration to file."""
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export Configuration",
            "mcp_freecad_config.json",
            "JSON Files (*.json)",
        )

        if file_path and self.config_manager:
            # Ask if user wants to include API keys
            reply = QtWidgets.QMessageBox.question(
                self,
                "Export API Keys",
                "Do you want to include API keys in the export?\n(Keys will be encrypted)",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )

            include_keys = reply == QtWidgets.QMessageBox.Yes
            success = self.config_manager.export_config(file_path, include_keys)

            if success:
                QtWidgets.QMessageBox.information(
                    self, "Success", "Configuration exported successfully"
                )
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Error", "Failed to export configuration"
                )

    def get_system_prompt(self, context: str = "default") -> str:
        """Get system prompt for a specific context."""
        if self.prompts_model:
            prompts_data = self.prompts_model.get_prompts_data()
            return prompts_data.get(context, prompts_data.get("default", ""))
        return ""
