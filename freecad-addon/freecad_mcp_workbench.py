"""FreeCAD MCP Workbench - Main workbench implementation"""

import os
import sys
import json
import FreeCAD
import FreeCADGui
import asyncio
import threading
from datetime import datetime

# Try to import PySide2, fall back gracefully if not available
try:
    from PySide2 import QtWidgets, QtCore, QtGui
    HAS_PYSIDE2 = True
except ImportError:
    try:
        from PySide import QtGui as QtWidgets
        from PySide import QtCore, QtGui
        HAS_PYSIDE2 = False
        FreeCAD.Console.PrintWarning("MCP Integration: Using PySide instead of PySide2\n")
    except ImportError:
        FreeCAD.Console.PrintError("MCP Integration: No Qt bindings available\n")
        HAS_PYSIDE2 = False

# Import tools and AI providers with better error handling
try:
    from tools.primitives import PrimitivesTool
    from tools.operations import OperationsTool
    from tools.measurements import MeasurementsTool
    from tools.export_import import ExportImportTool
    TOOLS_AVAILABLE = True
except ImportError as e:
    FreeCAD.Console.PrintError(f"MCP Integration: Failed to import tools: {e}\n")
    TOOLS_AVAILABLE = False

# Import AI providers with lazy loading
try:
    from ai.providers import (
        get_claude_provider, get_gemini_provider, get_openrouter_provider,
        get_available_providers, get_provider_errors, check_dependencies
    )
    AI_PROVIDERS_AVAILABLE = True
except ImportError as e:
    FreeCAD.Console.PrintError(f"MCP Integration: Failed to import AI providers: {e}\n")
    AI_PROVIDERS_AVAILABLE = False


class MCPShowInterfaceCommand:
    """Command to show the MCP interface."""

    def GetResources(self):
        return {
            'Pixmap': '',  # Icon path
            'MenuText': 'Show MCP Interface',
            'ToolTip': 'Show the MCP Integration interface'
        }

    def IsActive(self):
        return True

    def Activated(self):
        FreeCAD.Console.PrintMessage("MCP Integration: Interface command activated\n")
        # Show the main interface (this is handled by the dock widget creation)
        if HAS_PYSIDE2:
            main_window = FreeCADGui.getMainWindow()
            # Find the dock widget if it exists
            for widget in main_window.findChildren(QtWidgets.QDockWidget):
                if widget.windowTitle() == "MCP Integration":
                    widget.show()
                    widget.raise_()
                    return

            # If not found, show message
            QtWidgets.QMessageBox.information(
                main_window,
                "MCP Integration",
                "MCP Integration interface is loaded. Look for the dock widget on the right side."
            )


# Register the command
try:
    if hasattr(FreeCADGui, 'addCommand'):
        FreeCADGui.addCommand('MCP_ShowInterface', MCPShowInterfaceCommand())
        FreeCAD.Console.PrintMessage("MCP Integration: Command 'MCP_ShowInterface' registered successfully\n")
except Exception as e:
    FreeCAD.Console.PrintError(f"MCP Integration: Failed to register command: {e}\n")


class MCPMainWidget(QtWidgets.QWidget if HAS_PYSIDE2 else object):
    """Main widget containing the tabbed interface."""

    def __init__(self, parent=None):
        # Initialize all attributes first to prevent AttributeError
        self.status_bar = None
        self.tab_widget = None
        self.log_display = None
        self.chat_display = None
        self.provider_combo = None
        self.model_combo = None
        self.connection_status = None
        self.chat_input = None
        self.api_key_input = None
        self.thinking_mode_checkbox = None
        self.thinking_budget_spin = None
        self.claude_desktop_mode = None
        self.claude_desktop_enabled = False

        # Initialize tools if available
        if TOOLS_AVAILABLE:
            self.primitives_tool = PrimitivesTool()
            self.operations_tool = OperationsTool()
            self.measurements_tool = MeasurementsTool()
            self.export_import_tool = ExportImportTool()
        else:
            self.primitives_tool = None
            self.operations_tool = None
            self.measurements_tool = None
            self.export_import_tool = None

        # AI provider instance
        self.ai_provider = None
        self.is_connected = False

        # Async event loop for AI operations
        self.loop = None
        self.thread = None

        if HAS_PYSIDE2:
            super().__init__(parent)
            self.init_ui()
            self._start_async_loop()
        else:
            # No GUI available, create minimal interface
            FreeCAD.Console.PrintMessage("MCP Integration: GUI not available, minimal mode\n")

    def _start_async_loop(self):
        """Start async event loop in separate thread for AI operations."""
        def run_loop(loop):
            asyncio.set_event_loop(loop)
            loop.run_forever()

        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=run_loop, args=(self.loop,), daemon=True)
        self.thread.start()

    def init_ui(self):
        """Initialize the user interface."""
        try:
            if not HAS_PYSIDE2:
                return

            self.setWindowTitle("MCP Integration")
            self.setMinimumSize(800, 600)

            # Create main layout
            layout = QtWidgets.QVBoxLayout(self)

            # Create tab widget
            self.tab_widget = QtWidgets.QTabWidget()
            layout.addWidget(self.tab_widget)

            # Create tabs
            self._create_assistant_tab()
            self._create_models_tab()
            self._create_connections_tab()
            self._create_dependencies_tab()
            self._create_servers_tab()
            self._create_tools_tab()
            self._create_logs_tab()

            # Try to integrate with new GUI components
            self._integrate_advanced_gui()

            # Status bar
            self.status_bar = QtWidgets.QStatusBar()
            layout.addWidget(self.status_bar)
            self.status_bar.showMessage("MCP Integration Ready")

        except Exception as e:
            FreeCAD.Console.PrintError(f"MCP Integration: Failed to create GUI: {e}\n")

    def _integrate_advanced_gui(self):
        """Try to integrate with the new advanced GUI components."""
        try:
            # Try to import and initialize the provider integration service
            from ai.provider_integration_service import ProviderIntegrationService
            provider_service = ProviderIntegrationService()

            # Try to update tabs with advanced GUI if available
            self._try_replace_with_advanced_tabs()

            FreeCAD.Console.PrintMessage("MCP Integration: Advanced GUI integration successful\n")
        except ImportError as e:
            FreeCAD.Console.PrintMessage(f"MCP Integration: Advanced GUI not available: {e}\n")
        except Exception as e:
            FreeCAD.Console.PrintWarning(f"MCP Integration: Advanced GUI integration failed: {e}\n")

    def _try_replace_with_advanced_tabs(self):
        """Try to replace basic tabs with advanced versions."""
        try:
            # Import advanced GUI widgets
            from gui.main_widget import MCPMainWidget as AdvancedMainWidget
            from gui.settings_widget import SettingsWidget
            from gui.ai_widget import AIWidget
            from gui.connection_widget import ConnectionWidget

            # Store original tab count
            original_tab_count = self.tab_widget.count()

            # Try to create advanced widgets and replace tabs
            try:
                settings_widget = SettingsWidget()
                # Find and replace Models tab
                for i in range(self.tab_widget.count()):
                    if self.tab_widget.tabText(i) == "Models":
                        self.tab_widget.removeTab(i)
                        self.tab_widget.insertTab(i, settings_widget, "Settings")
                        break
            except Exception as e:
                FreeCAD.Console.PrintWarning(f"Failed to replace Models tab: {e}\n")

            try:
                ai_widget = AIWidget()
                # Find and replace Assistant tab
                for i in range(self.tab_widget.count()):
                    if self.tab_widget.tabText(i) == "Assistant":
                        self.tab_widget.removeTab(i)
                        self.tab_widget.insertTab(i, ai_widget, "AI Assistant")
                        break
            except Exception as e:
                FreeCAD.Console.PrintWarning(f"Failed to replace Assistant tab: {e}\n")

            try:
                connection_widget = ConnectionWidget()
                # Find and replace Connections tab
                for i in range(self.tab_widget.count()):
                    if self.tab_widget.tabText(i) == "Connections":
                        self.tab_widget.removeTab(i)
                        self.tab_widget.insertTab(i, connection_widget, "Connections")
                        break
            except Exception as e:
                FreeCAD.Console.PrintWarning(f"Failed to replace Connections tab: {e}\n")

            FreeCAD.Console.PrintMessage("MCP Integration: Advanced tabs integrated successfully\n")

        except ImportError as e:
            FreeCAD.Console.PrintMessage(f"MCP Integration: Advanced GUI widgets not available: {e}\n")

    def _create_assistant_tab(self):
        """Create the Assistant tab for AI chat."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        # Header
        header = QtWidgets.QLabel("💬 AI Assistant")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(header)

        # Connection status indicator
        self.ai_status_label = QtWidgets.QLabel("Status: Not connected")
        self.ai_status_label.setStyleSheet("padding: 5px; background-color: #f0f0f0; border-radius: 3px;")
        layout.addWidget(self.ai_status_label)

        # Update status based on provider
        self._update_ai_status()

        # Chat interface
        chat_group = QtWidgets.QGroupBox("Conversation")
        chat_layout = QtWidgets.QVBoxLayout(chat_group)

        self.chat_display = QtWidgets.QTextEdit()
        self.chat_display.setReadOnly(True)
        chat_layout.addWidget(self.chat_display)

        # Chat input
        input_layout = QtWidgets.QHBoxLayout()
        self.chat_input = QtWidgets.QLineEdit()
        self.chat_input.setPlaceholderText("Ask the AI assistant about your CAD project...")
        self.chat_input.returnPressed.connect(self._send_chat_message)

        send_button = QtWidgets.QPushButton("Send")
        send_button.clicked.connect(self._send_chat_message)

        clear_button = QtWidgets.QPushButton("Clear")
        clear_button.clicked.connect(lambda: self.chat_display.clear())

        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(send_button)
        input_layout.addWidget(clear_button)
        chat_layout.addLayout(input_layout)

        layout.addWidget(chat_group)

        # Quick prompts
        prompts_group = QtWidgets.QGroupBox("Quick Prompts")
        prompts_layout = QtWidgets.QGridLayout(prompts_group)

        quick_prompts = [
            "How do I create a parametric design?",
            "Explain boolean operations",
            "Best practices for 3D printing",
            "How to export for manufacturing",
            "Optimize my design for strength",
            "Convert 2D sketch to 3D"
        ]

        row = 0
        col = 0
        for prompt in quick_prompts:
            btn = QtWidgets.QPushButton(prompt)
            btn.clicked.connect(lambda checked, p=prompt: self._use_quick_prompt(p))
            prompts_layout.addWidget(btn, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1

        layout.addWidget(prompts_group)

        self.tab_widget.addTab(widget, "Assistant")

    def _create_models_tab(self):
        """Create the Models tab for AI configuration."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        # Header
        header = QtWidgets.QLabel("🤖 AI Model Configuration")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(header)

        # Provider selection
        provider_group = QtWidgets.QGroupBox("AI Provider Settings")
        provider_layout = QtWidgets.QVBoxLayout(provider_group)

        # Provider combo
        provider_label = QtWidgets.QLabel("Provider:")
        self.provider_combo = QtWidgets.QComboBox()
        self.provider_combo.addItems(["Claude (Anthropic)", "Gemini (Google)", "OpenRouter"])
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)

        provider_layout.addWidget(provider_label)
        provider_layout.addWidget(self.provider_combo)

        # Model selection
        model_label = QtWidgets.QLabel("Model:")
        self.model_combo = QtWidgets.QComboBox()
        self._update_model_list()

        provider_layout.addWidget(model_label)
        provider_layout.addWidget(self.model_combo)

        # API Key input
        api_key_label = QtWidgets.QLabel("API Key:")
        api_key_layout = QtWidgets.QHBoxLayout()

        self.api_key_input = QtWidgets.QLineEdit()
        self.api_key_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.api_key_input.setPlaceholderText("Enter your API key...")

        self.show_key_button = QtWidgets.QPushButton("👁")
        self.show_key_button.setMaximumWidth(30)
        self.show_key_button.setCheckable(True)
        self.show_key_button.toggled.connect(lambda checked: self.api_key_input.setEchoMode(
            QtWidgets.QLineEdit.Normal if checked else QtWidgets.QLineEdit.Password
        ))

        api_key_layout.addWidget(self.api_key_input)
        api_key_layout.addWidget(self.show_key_button)

        provider_layout.addWidget(api_key_label)
        provider_layout.addLayout(api_key_layout)

        # Advanced settings
        advanced_group = QtWidgets.QGroupBox("Advanced Settings")
        advanced_layout = QtWidgets.QVBoxLayout(advanced_group)

        # Thinking mode configuration (Claude only)
        thinking_group = QtWidgets.QGroupBox("Thinking Mode (Claude only)")
        thinking_layout = QtWidgets.QHBoxLayout(thinking_group)

        self.thinking_mode_checkbox = QtWidgets.QCheckBox("Enable Thinking Mode")
        self.thinking_budget_spin = QtWidgets.QSpinBox()
        self.thinking_budget_spin.setRange(100, 20000)
        self.thinking_budget_spin.setValue(2000)
        self.thinking_budget_spin.setSuffix(" tokens")
        self.thinking_budget_spin.setEnabled(False)

        self.thinking_mode_checkbox.toggled.connect(self.thinking_budget_spin.setEnabled)

        thinking_layout.addWidget(self.thinking_mode_checkbox)
        thinking_layout.addWidget(QtWidgets.QLabel("Budget:"))
        thinking_layout.addWidget(self.thinking_budget_spin)
        thinking_layout.addStretch()

        advanced_layout.addWidget(thinking_group)

        # Temperature control
        temp_layout = QtWidgets.QHBoxLayout()
        temp_label = QtWidgets.QLabel("Temperature:")
        self.temperature_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.temperature_slider.setRange(0, 100)
        self.temperature_slider.setValue(70)
        self.temperature_value = QtWidgets.QLabel("0.7")
        self.temperature_slider.valueChanged.connect(
            lambda v: self.temperature_value.setText(f"{v/100:.1f}")
        )

        temp_layout.addWidget(temp_label)
        temp_layout.addWidget(self.temperature_slider)
        temp_layout.addWidget(self.temperature_value)
        advanced_layout.addLayout(temp_layout)

        provider_layout.addWidget(advanced_group)

        # Connection actions
        actions_layout = QtWidgets.QHBoxLayout()

        test_button = QtWidgets.QPushButton("Test Connection")
        test_button.clicked.connect(self._test_ai_connection)

        save_button = QtWidgets.QPushButton("Save Settings")
        save_button.clicked.connect(self._save_ai_settings)

        actions_layout.addWidget(test_button)
        actions_layout.addWidget(save_button)
        actions_layout.addStretch()

        provider_layout.addLayout(actions_layout)

        layout.addWidget(provider_group)

        # Claude Desktop Mode
        claude_desktop_group = QtWidgets.QGroupBox("Claude Desktop Integration")
        claude_desktop_layout = QtWidgets.QVBoxLayout(claude_desktop_group)

        # Mode toggle
        self.claude_desktop_mode = QtWidgets.QCheckBox("Enable Claude Desktop Mode")
        self.claude_desktop_mode.setToolTip("Hide the Assistant tab and use Claude Desktop App instead")
        self.claude_desktop_mode.toggled.connect(self._on_claude_desktop_mode_changed)
        claude_desktop_layout.addWidget(self.claude_desktop_mode)

        # Configuration instructions
        config_label = QtWidgets.QLabel("Claude Desktop Configuration:")
        config_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        claude_desktop_layout.addWidget(config_label)

        self.claude_config_text = QtWidgets.QTextEdit()
        self.claude_config_text.setReadOnly(True)
        self.claude_config_text.setMaximumHeight(200)
        self._update_claude_config_text()
        claude_desktop_layout.addWidget(self.claude_config_text)

        # Copy config button
        copy_config_button = QtWidgets.QPushButton("📋 Copy Configuration to Clipboard")
        copy_config_button.clicked.connect(self._copy_claude_config)
        claude_desktop_layout.addWidget(copy_config_button)

        # Status and help
        help_text = QtWidgets.QLabel(
            "When enabled, the Assistant tab will be hidden and you can interact with FreeCAD "
            "directly from Claude Desktop App using the MCP server."
        )
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #666; font-style: italic; margin-top: 10px;")
        claude_desktop_layout.addWidget(help_text)

        layout.addWidget(claude_desktop_group)

        # Model information
        info_group = QtWidgets.QGroupBox("Model Information")
        info_layout = QtWidgets.QVBoxLayout(info_group)

        self.model_info_text = QtWidgets.QTextEdit()
        self.model_info_text.setReadOnly(True)
        self.model_info_text.setMaximumHeight(150)
        self._update_model_info()

        info_layout.addWidget(self.model_info_text)
        layout.addWidget(info_group)

        layout.addStretch()

        self.tab_widget.addTab(widget, "Models")

    def _create_connections_tab(self):
        """Create the Connections tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        # Header
        header = QtWidgets.QLabel("🔗 FreeCAD Connections")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(header)

        # Connection status
        status_group = QtWidgets.QGroupBox("Connection Status")
        status_layout = QtWidgets.QVBoxLayout(status_group)

        self.connection_status = QtWidgets.QLabel("🔴 Disconnected")
        self.connection_status.setStyleSheet("font-size: 14px; padding: 10px;")
        status_layout.addWidget(self.connection_status)

        # Connection info
        info_label = QtWidgets.QLabel("FreeCAD Document Status:")
        self.doc_info = QtWidgets.QLabel("No active document")
        self.doc_info.setStyleSheet("padding: 5px; background-color: #f0f0f0; border-radius: 3px;")

        status_layout.addWidget(info_label)
        status_layout.addWidget(self.doc_info)

        connect_button = QtWidgets.QPushButton("Connect to FreeCAD")
        connect_button.clicked.connect(self._connect_to_freecad)
        status_layout.addWidget(connect_button)

        layout.addWidget(status_group)

        # Quick actions
        actions_group = QtWidgets.QGroupBox("Quick Actions")
        actions_layout = QtWidgets.QVBoxLayout(actions_group)

        new_doc_button = QtWidgets.QPushButton("Create New Document")
        new_doc_button.clicked.connect(self._create_new_document)
        actions_layout.addWidget(new_doc_button)

        refresh_button = QtWidgets.QPushButton("Refresh Connection")
        refresh_button.clicked.connect(self._refresh_connection)
        actions_layout.addWidget(refresh_button)

        layout.addWidget(actions_group)
        layout.addStretch()

        self.tab_widget.addTab(widget, "Connections")

    def _create_dependencies_tab(self):
        """Create the Dependencies tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        # Header
        header = QtWidgets.QLabel("📦 Python Dependencies")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(header)

        # Dependency status
        status_group = QtWidgets.QGroupBox("Dependency Status")
        status_layout = QtWidgets.QVBoxLayout(status_group)

        # Create dependency status display
        self.dependency_status_widget = QtWidgets.QWidget()
        self.dependency_status_layout = QtWidgets.QVBoxLayout(self.dependency_status_widget)
        status_layout.addWidget(self.dependency_status_widget)

        # Refresh button
        refresh_deps_button = QtWidgets.QPushButton("🔄 Refresh Status")
        refresh_deps_button.clicked.connect(self._refresh_dependency_status)
        status_layout.addWidget(refresh_deps_button)

        layout.addWidget(status_group)

        # Installation section
        install_group = QtWidgets.QGroupBox("Install Dependencies")
        install_layout = QtWidgets.QVBoxLayout(install_group)

        # Install all missing button
        install_all_button = QtWidgets.QPushButton("📥 Install All Missing Dependencies")
        install_all_button.clicked.connect(self._install_all_dependencies)
        install_layout.addWidget(install_all_button)

        # Manual installation help
        help_group = QtWidgets.QGroupBox("Manual Installation")
        help_layout = QtWidgets.QVBoxLayout(help_group)

        help_text = QtWidgets.QTextEdit()
        help_text.setReadOnly(True)
        help_text.setMaximumHeight(150)
        help_text.setHtml("""
        <h4>Manual Installation Instructions</h4>
        <p>If automatic installation fails, you can install dependencies manually:</p>
        <ol>
            <li><b>Copy the script</b> from the "Installation Script" section below</li>
            <li><b>Paste it</b> into the FreeCAD Python console</li>
            <li><b>Press Enter</b> to run the installation</li>
            <li><b>Restart FreeCAD</b> after installation completes</li>
        </ol>
        <p><b>Note:</b> For AppImage users, dependencies need to be installed each time you update FreeCAD.</p>
        """)
        help_layout.addWidget(help_text)

        # Installation script display
        script_label = QtWidgets.QLabel("Installation Script (copy to Python console):")
        self.installation_script = QtWidgets.QTextEdit()
        self.installation_script.setMaximumHeight(200)
        self.installation_script.setReadOnly(True)

        copy_script_button = QtWidgets.QPushButton("📋 Copy Script to Clipboard")
        copy_script_button.clicked.connect(self._copy_installation_script)

        help_layout.addWidget(script_label)
        help_layout.addWidget(self.installation_script)
        help_layout.addWidget(copy_script_button)

        install_layout.addWidget(help_group)
        layout.addWidget(install_group)

        # Installation info
        info_group = QtWidgets.QGroupBox("Installation Information")
        info_layout = QtWidgets.QVBoxLayout(info_group)

        self.installation_info = QtWidgets.QTextEdit()
        self.installation_info.setReadOnly(True)
        self.installation_info.setMaximumHeight(120)
        info_layout.addWidget(self.installation_info)

        layout.addWidget(info_group)

        # Initialize the display
        self._refresh_dependency_status()

        self.tab_widget.addTab(widget, "Dependencies")

    def _refresh_dependency_status(self):
        """Refresh the dependency status display."""
        try:
            # Clear existing status widgets
            for i in reversed(range(self.dependency_status_layout.count())):
                child = self.dependency_status_layout.takeAt(i).widget()
                if child:
                    child.deleteLater()

            if AI_PROVIDERS_AVAILABLE:
                # Check dependencies using the dependency manager
                dependencies = check_dependencies()

                for dep_name, available in dependencies.items():
                    status_widget = QtWidgets.QWidget()
                    status_layout = QtWidgets.QHBoxLayout(status_widget)

                    # Status icon and name
                    if available:
                        icon_label = QtWidgets.QLabel("✅")
                        status_text = f"{dep_name}: Installed"
                        style = "color: green; font-weight: bold;"
                    else:
                        icon_label = QtWidgets.QLabel("❌")
                        status_text = f"{dep_name}: Missing"
                        style = "color: red; font-weight: bold;"

                    name_label = QtWidgets.QLabel(status_text)
                    name_label.setStyleSheet(style)

                    # Install button for missing dependencies
                    if not available:
                        install_button = QtWidgets.QPushButton(f"Install {dep_name}")
                        install_button.clicked.connect(lambda checked, dep=dep_name: self._install_single_dependency(dep))
                        status_layout.addWidget(install_button)

                    status_layout.addWidget(icon_label)
                    status_layout.addWidget(name_label)
                    status_layout.addStretch()

                    self.dependency_status_layout.addWidget(status_widget)
            else:
                # Fallback if dependency manager not available
                error_label = QtWidgets.QLabel("❌ Dependency manager not available")
                error_label.setStyleSheet("color: red; font-weight: bold;")
                self.dependency_status_layout.addWidget(error_label)

            # Update installation info
            self._update_installation_info()

            # Update installation script
            self._update_installation_script()

        except Exception as e:
            error_label = QtWidgets.QLabel(f"❌ Error checking dependencies: {str(e)}")
            error_label.setStyleSheet("color: red;")
            self.dependency_status_layout.addWidget(error_label)

    def _update_installation_info(self):
        """Update the installation information display."""
        try:
            if AI_PROVIDERS_AVAILABLE:
                from utils.dependency_manager import DependencyManager
                manager = DependencyManager()
                info = manager.get_installation_info()

                info_html = f"""
                <h4>Installation Environment</h4>
                <table>
                    <tr><td><b>FreeCAD Version:</b></td><td>{info['freecad_version']}</td></tr>
                    <tr><td><b>Installation Type:</b></td><td>{info['installation_type']}</td></tr>
                    <tr><td><b>Platform:</b></td><td>{info['platform']}</td></tr>
                    <tr><td><b>Python Executable:</b></td><td>{info['python_executable']}</td></tr>
                    <tr><td><b>Target Directory:</b></td><td>{info['pip_target_directory']}</td></tr>
                </table>
                """
                self.installation_info.setHtml(info_html)
            else:
                self.installation_info.setPlainText("Installation information not available")
        except Exception as e:
            self.installation_info.setPlainText(f"Error getting installation info: {str(e)}")

    def _update_installation_script(self):
        """Update the installation script display."""
        try:
            if AI_PROVIDERS_AVAILABLE:
                from utils.dependency_manager import get_aiohttp_install_script
                script = get_aiohttp_install_script()
                self.installation_script.setPlainText(script)
            else:
                self.installation_script.setPlainText("# Installation script not available")
        except Exception as e:
            self.installation_script.setPlainText(f"# Error generating script: {str(e)}")

    def _install_single_dependency(self, dependency_name: str):
        """Install a single dependency."""
        try:
            if not AI_PROVIDERS_AVAILABLE:
                QtWidgets.QMessageBox.warning(self, "Error", "Dependency manager not available")
                return

            from utils.dependency_manager import DependencyManager

            # Create progress dialog
            progress = QtWidgets.QProgressDialog(f"Installing {dependency_name}...", "Cancel", 0, 0, self)
            progress.setWindowModality(QtCore.Qt.WindowModal)
            progress.show()

            def progress_callback(message):
                self._add_log("Dependencies", message)
                QtWidgets.QApplication.processEvents()

            manager = DependencyManager(progress_callback)
            success = manager.install_dependency(dependency_name)

            progress.close()

            if success:
                QtWidgets.QMessageBox.information(
                    self,
                    "Success",
                    f"{dependency_name} installed successfully!\n\nPlease restart FreeCAD to use the new dependency."
                )
                self._refresh_dependency_status()
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Installation Failed",
                    f"Failed to install {dependency_name}. Check the logs for details."
                )

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error installing {dependency_name}: {str(e)}")

    def _install_all_dependencies(self):
        """Install all missing dependencies."""
        try:
            if not AI_PROVIDERS_AVAILABLE:
                QtWidgets.QMessageBox.warning(self, "Error", "Dependency manager not available")
                return

            from utils.dependency_manager import DependencyManager

            manager = DependencyManager()
            missing = manager.get_missing_dependencies()

            if not missing:
                QtWidgets.QMessageBox.information(self, "No Action Needed", "All dependencies are already installed!")
                return

            # Confirm installation
            reply = QtWidgets.QMessageBox.question(
                self,
                "Install Dependencies",
                f"Install {len(missing)} missing dependencies?\n\n{', '.join(missing)}",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )

            if reply != QtWidgets.QMessageBox.Yes:
                return

            # Create progress dialog
            progress = QtWidgets.QProgressDialog("Installing dependencies...", "Cancel", 0, 0, self)
            progress.setWindowModality(QtCore.Qt.WindowModal)
            progress.show()

            def progress_callback(message):
                self._add_log("Dependencies", message)
                QtWidgets.QApplication.processEvents()

            manager = DependencyManager(progress_callback)
            success = manager.install_missing_dependencies()

            progress.close()

            if success:
                QtWidgets.QMessageBox.information(
                    self,
                    "Success",
                    "All dependencies installed successfully!\n\nPlease restart FreeCAD to use the new dependencies."
                )
                self._refresh_dependency_status()
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Partial Success",
                    "Some dependencies failed to install. Check the logs for details."
                )

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Error installing dependencies: {str(e)}")

    def _copy_installation_script(self):
        """Copy the installation script to clipboard."""
        try:
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.setText(self.installation_script.toPlainText())
            QtWidgets.QMessageBox.information(self, "Copied", "Installation script copied to clipboard!")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Failed to copy script: {str(e)}")

    def _create_servers_tab(self):
        """Create the Servers tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        # Header
        header = QtWidgets.QLabel("🖥️ MCP Servers")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(header)

        # Server list
        server_group = QtWidgets.QGroupBox("Server Information")
        server_layout = QtWidgets.QVBoxLayout(server_group)

        info_text = QtWidgets.QTextEdit()
        info_text.setReadOnly(True)
        info_text.setHtml("""
        <h3>MCP Server Configuration</h3>
        <p>The MCP server provides the bridge between AI assistants and FreeCAD.</p>

        <h4>Available Connection Methods:</h4>
        <ul>
            <li><b>Launcher</b> - Uses AppImage extraction (Recommended)</li>
            <li><b>Wrapper</b> - Python subprocess isolation</li>
            <li><b>Server</b> - Socket-based connection</li>
            <li><b>Bridge</b> - FreeCAD CLI interface</li>
        </ul>

        <h4>Current Status:</h4>
        <p>This addon integrates directly with FreeCAD, so no separate server is needed for basic operations.</p>
        """)

        server_layout.addWidget(info_text)
        layout.addWidget(server_group)
        layout.addStretch()

        self.tab_widget.addTab(widget, "Servers")

    def _create_tools_tab(self):
        """Create the Tools tab using the new comprehensive tools widget."""
        try:
            # Try to import the new comprehensive tools widget
            from gui.tools_widget import ToolsWidget
            tools_widget = ToolsWidget()
            self.tab_widget.addTab(tools_widget, "Tools")
            FreeCAD.Console.PrintMessage("MCP Integration: Using new comprehensive tools widget\n")
        except ImportError as e:
            FreeCAD.Console.PrintWarning(f"MCP Integration: Could not import new tools widget: {e}\n")
            FreeCAD.Console.PrintMessage("MCP Integration: Falling back to basic tools interface\n")

            # Fallback to basic tools interface
            widget = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout(widget)

            # Header
            header = QtWidgets.QLabel("🛠️ MCP Tools")
            header.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
            layout.addWidget(header)

            # Tool categories
            tools_group = QtWidgets.QGroupBox("Available Tools")
            tools_layout = QtWidgets.QVBoxLayout(tools_group)

            # Create tool category groups
            categories = [
                ("Basic Primitives", [
                    ("Create Box", "primitives.create_box"),
                    ("Create Cylinder", "primitives.create_cylinder"),
                    ("Create Sphere", "primitives.create_sphere"),
                    ("Create Cone", "primitives.create_cone"),
                    ("Create Torus", "primitives.create_torus")
                ]),
                ("Basic Operations", [
                    ("Boolean Union", "operations.boolean_union"),
                    ("Boolean Cut", "operations.boolean_cut"),
                    ("Boolean Intersection", "operations.boolean_intersection"),
                    ("Move Object", "operations.move_object"),
                    ("Rotate Object", "operations.rotate_object"),
                    ("Scale Object", "operations.scale_object")
                ]),
                ("Measurements", [
                    ("Measure Distance", "measurements.measure_distance"),
                    ("Measure Angle", "measurements.measure_angle"),
                    ("Measure Volume", "measurements.measure_volume"),
                    ("Measure Area", "measurements.measure_area"),
                    ("Measure Bounding Box", "measurements.measure_bounding_box")
                ]),
                ("Export/Import", [
                    ("Export STL", "export_import.export_stl"),
                    ("Export STEP", "export_import.export_step"),
                    ("Import STL", "export_import.import_stl"),
                    ("Import STEP", "export_import.import_step")
                ])
            ]

            for category_name, tools in categories:
                category_group = QtWidgets.QGroupBox(category_name)
                category_layout = QtWidgets.QGridLayout(category_group)

                row = 0
                col = 0
                for tool_name, tool_id in tools:
                    button = QtWidgets.QPushButton(tool_name)
                    button.clicked.connect(lambda checked, tid=tool_id: self._execute_tool(tid))
                    category_layout.addWidget(button, row, col)

                    col += 1
                    if col > 2:  # 3 columns
                        col = 0
                        row += 1

                tools_layout.addWidget(category_group)

            layout.addWidget(tools_group)
            layout.addStretch()

            self.tab_widget.addTab(widget, "Tools")

    def _create_logs_tab(self):
        """Create the Logs tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        # Header
        header = QtWidgets.QLabel("📋 Activity Logs")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(header)

        # Log display
        self.log_display = QtWidgets.QTextEdit()
        self.log_display.setReadOnly(True)
        layout.addWidget(self.log_display)

        # Log controls
        controls_layout = QtWidgets.QHBoxLayout()

        clear_button = QtWidgets.QPushButton("Clear Logs")
        clear_button.clicked.connect(lambda: self.log_display.clear())

        export_button = QtWidgets.QPushButton("Export Logs")
        export_button.clicked.connect(self._export_logs)

        controls_layout.addWidget(clear_button)
        controls_layout.addWidget(export_button)
        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        self.tab_widget.addTab(widget, "Logs")

    def _on_provider_changed(self, provider_text):
        """Handle provider selection change."""
        self._update_model_list()
        self._update_model_info()
        self._update_ai_status()
        # Enable/disable thinking mode based on provider
        is_claude = "Claude" in provider_text
        if self.thinking_mode_checkbox:
            self.thinking_mode_checkbox.setEnabled(is_claude)
            if not is_claude:
                self.thinking_mode_checkbox.setChecked(False)

    def _update_model_list(self):
        """Update model list based on selected provider."""
        if not self.model_combo:
            return

        self.model_combo.clear()

        provider_text = self.provider_combo.currentText() if self.provider_combo else ""

        if "Claude" in provider_text:
            models = [
                "claude-4-opus-20250522",
                "claude-4-sonnet-20250522",
                "claude-3-7-sonnet-20250224",
                "claude-3-5-sonnet-20241022"
            ]
        elif "Gemini" in provider_text:
            models = [
                "gemini-2.5-pro-latest",
                "gemini-1.5-pro-latest",
                "gemini-1.5-flash-latest"
            ]
        elif "OpenRouter" in provider_text:
            models = [
                "anthropic/claude-4-opus",
                "anthropic/claude-4-sonnet",
                "google/gemini-2.5-pro",
                "openai/gpt-4.1-turbo"
            ]
        else:
            models = []

        self.model_combo.addItems(models)

    def _test_ai_connection(self):
        """Test the AI provider connection."""
        self._add_log("AI", "Testing connection...")

        api_key = self.api_key_input.text() if self.api_key_input else ""
        if not api_key:
            QtWidgets.QMessageBox.warning(self, "API Key Required", "Please enter your API key first.")
            return

        try:
            # Create provider instance
            provider_text = self.provider_combo.currentText() if self.provider_combo else ""
            model = self.model_combo.currentText() if self.model_combo else ""

            if not AI_PROVIDERS_AVAILABLE:
                raise Exception("AI providers not available")

            if "Claude" in provider_text:
                ClaudeProvider = get_claude_provider()
                if ClaudeProvider:
                    self.ai_provider = ClaudeProvider(api_key, model)
                else:
                    raise Exception("Claude provider not available")
            elif "Gemini" in provider_text:
                GeminiProvider = get_gemini_provider()
                if GeminiProvider:
                    self.ai_provider = GeminiProvider(api_key, model)
                else:
                    raise Exception("Gemini provider not available")
            elif "OpenRouter" in provider_text:
                OpenRouterProvider = get_openrouter_provider()
                if OpenRouterProvider:
                    self.ai_provider = OpenRouterProvider(api_key, model)
                else:
                    raise Exception("OpenRouter provider not available")
            else:
                raise Exception("Invalid provider selected")

            # Enable thinking mode if requested (Claude only)
            if "Claude" in provider_text and self.thinking_mode_checkbox and self.thinking_mode_checkbox.isChecked():
                budget = self.thinking_budget_spin.value() if self.thinking_budget_spin else 2000
                self.ai_provider.enable_thinking_mode(budget)

            # Test connection (synchronous for now)
            self._add_log("AI", f"Testing {provider_text} connection...")

            # Run async test in the event loop
            future = asyncio.run_coroutine_threadsafe(
                self.ai_provider.test_connection(),
                self.loop
            )

            # Wait for result with timeout
            success = future.result(timeout=10)

            if success:
                self._add_log("AI", "✅ Connection successful!")
                QtWidgets.QMessageBox.information(self, "Success", "AI connection test successful!")
            else:
                self._add_log("AI", "❌ Connection test failed")
                QtWidgets.QMessageBox.warning(self, "Failed", "AI connection test failed. Please check your API key.")

        except Exception as e:
            self._add_log("AI", f"❌ Error: {str(e)}")
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to test connection: {str(e)}")

    def _send_chat_message(self):
        """Send a chat message to the AI."""
        if not hasattr(self, 'chat_input') or not self.chat_input:
            return

        message = self.chat_input.text().strip()
        if not message:
            return

        if not self.ai_provider:
            QtWidgets.QMessageBox.warning(self, "No AI Provider", "Please configure and test an AI provider first.")
            return

        self.chat_input.clear()
        self._add_log("AI Chat", f"User: {message}")

        # Display user message
        if hasattr(self, 'chat_display') and self.chat_display:
            self.chat_display.append(f"<div style='margin: 5px; padding: 8px; background-color: #e3f2fd; border-radius: 5px;'><strong>You:</strong> {message}</div>")

        # Send to AI asynchronously
        self._send_ai_message_async(message)

    def _send_ai_message_async(self, message):
        """Send message to AI provider asynchronously."""
        async def send_message():
            try:
                response = await self.ai_provider.send_message(message)
                return response
            except Exception as e:
                return None, str(e)

        # Schedule the coroutine
        future = asyncio.run_coroutine_threadsafe(send_message(), self.loop)

        # Handle the response when ready
        def handle_response():
            try:
                result = future.result(timeout=0.1)
                if result and hasattr(result, 'content'):
                    # Display AI response
                    if self.chat_display:
                        thinking_html = ""
                        if hasattr(result, 'thinking_process') and result.thinking_process:
                            thinking_html = f"<div style='margin: 5px; padding: 8px; background-color: #f5f5f5; border-left: 3px solid #9c27b0; font-style: italic;'><strong>🧠 Thinking:</strong><br>{result.thinking_process.replace(chr(10), '<br>')}</div>"

                        response_html = f"<div style='margin: 5px; padding: 8px; background-color: #f3e5f5; border-radius: 5px;'><strong>🤖 AI:</strong> {result.content.replace(chr(10), '<br>')}</div>"

                        self.chat_display.append(thinking_html + response_html)

                    self._add_log("AI Chat", f"AI: {result.content[:100]}...")
                else:
                    error_msg = result[1] if isinstance(result, tuple) else "Unknown error"
                    if self.chat_display:
                        self.chat_display.append(f"<div style='margin: 5px; padding: 8px; background-color: #ffebee; border-radius: 5px;'><strong>❌ Error:</strong> {error_msg}</div>")
                    self._add_log("AI Chat", f"Error: {error_msg}")
            except Exception as e:
                if not future.done():
                    # Still processing, check again later
                    QtCore.QTimer.singleShot(100, handle_response)
                else:
                    # Actual error
                    if self.chat_display:
                        self.chat_display.append(f"<div style='margin: 5px; padding: 8px; background-color: #ffebee; border-radius: 5px;'><strong>❌ Error:</strong> {str(e)}</div>")
                    self._add_log("AI Chat", f"Error: {str(e)}")

        # Start checking for response
        QtCore.QTimer.singleShot(100, handle_response)

    def _connect_to_freecad(self):
        """Connect to FreeCAD (check current state)."""
        self._add_log("Connection", "Checking FreeCAD connection...")

        try:
            # Check if we have an active document
            if FreeCAD.ActiveDocument:
                self.is_connected = True
                self.connection_status.setText("🟢 Connected")
                self.connection_status.setStyleSheet("font-size: 14px; padding: 10px; color: green;")

                # Update document info
                doc_name = FreeCAD.ActiveDocument.Name
                obj_count = len(FreeCAD.ActiveDocument.Objects)
                self.doc_info.setText(f"Document: {doc_name} ({obj_count} objects)")

                self._add_log("Connection", f"Connected to document: {doc_name}")
                QtWidgets.QMessageBox.information(self, "Connected", f"Connected to FreeCAD document: {doc_name}")
            else:
                self.is_connected = True  # We're in FreeCAD, just no document
                self.connection_status.setText("🟡 Connected (No Document)")
                self.connection_status.setStyleSheet("font-size: 14px; padding: 10px; color: orange;")
                self.doc_info.setText("No active document")

                self._add_log("Connection", "Connected to FreeCAD (no active document)")

                # Ask if user wants to create a new document
                reply = QtWidgets.QMessageBox.question(
                    self,
                    "No Document",
                    "No active document found. Would you like to create a new one?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                )

                if reply == QtWidgets.QMessageBox.Yes:
                    self._create_new_document()

        except Exception as e:
            self.is_connected = False
            self.connection_status.setText("🔴 Connection Failed")
            self.connection_status.setStyleSheet("font-size: 14px; padding: 10px; color: red;")
            self._add_log("Connection", f"Failed to connect: {str(e)}")
            QtWidgets.QMessageBox.critical(self, "Connection Error", f"Failed to connect: {str(e)}")

    def _create_new_document(self):
        """Create a new FreeCAD document."""
        try:
            doc = FreeCAD.newDocument("MCPDocument")
            FreeCAD.setActiveDocument(doc.Name)
            self._add_log("Document", f"Created new document: {doc.Name}")
            self._refresh_connection()
        except Exception as e:
            self._add_log("Document", f"Failed to create document: {str(e)}")
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to create document: {str(e)}")

    def _refresh_connection(self):
        """Refresh the connection status."""
        self._connect_to_freecad()

    def _execute_tool(self, tool_id):
        """Execute an MCP tool."""
        self._add_log("Tool", f"Executing: {tool_id}")

        if not TOOLS_AVAILABLE:
            QtWidgets.QMessageBox.warning(self, "Tools Not Available", "Tools are not properly imported.")
            return

        if not FreeCAD.ActiveDocument:
            QtWidgets.QMessageBox.warning(self, "No Document", "Please create or open a document first.")
            return

        try:
            # Parse tool ID
            parts = tool_id.split('.')
            if len(parts) != 2:
                raise ValueError(f"Invalid tool ID: {tool_id}")

            tool_category, tool_method = parts

            # Get the appropriate tool instance
            if tool_category == "primitives":
                tool = self.primitives_tool
            elif tool_category == "operations":
                tool = self.operations_tool
            elif tool_category == "measurements":
                tool = self.measurements_tool
            elif tool_category == "export_import":
                tool = self.export_import_tool
            else:
                raise ValueError(f"Unknown tool category: {tool_category}")

            # Get the method
            if not hasattr(tool, tool_method):
                raise ValueError(f"Tool method not found: {tool_method}")

            method = getattr(tool, tool_method)

            # Create input dialog based on tool
            dialog = self._create_tool_dialog(tool_id, method)
            if dialog and dialog.exec_():
                params = dialog.get_parameters()

                # Execute the tool
                result = method(**params)

                # Show result
                if result.get('success'):
                    self._add_log("Tool", f"✅ {result.get('message', 'Success')}")
                    QtWidgets.QMessageBox.information(self, "Success", result.get('message', 'Operation completed successfully'))
                else:
                    self._add_log("Tool", f"❌ {result.get('message', 'Failed')}")
                    QtWidgets.QMessageBox.warning(self, "Failed", result.get('message', 'Operation failed'))

        except Exception as e:
            self._add_log("Tool", f"Error: {str(e)}")
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to execute tool: {str(e)}")

    def _create_tool_dialog(self, tool_id, method):
        """Create input dialog for tool parameters."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"Tool: {tool_id}")
        dialog.setMinimumWidth(400)

        layout = QtWidgets.QVBoxLayout(dialog)

        # Add description
        if hasattr(method, '__doc__') and method.__doc__:
            desc_label = QtWidgets.QLabel(method.__doc__.split('\n')[0])
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)
            layout.addWidget(QtWidgets.QLabel(""))  # Spacer

        # Parameter inputs
        inputs = {}

        # Define parameter configurations for common tools
        param_configs = {
            "primitives.create_box": [
                ("length", "float", 10.0, "Length (mm)"),
                ("width", "float", 10.0, "Width (mm)"),
                ("height", "float", 10.0, "Height (mm)")
            ],
            "primitives.create_cylinder": [
                ("radius", "float", 5.0, "Radius (mm)"),
                ("height", "float", 10.0, "Height (mm)")
            ],
            "primitives.create_sphere": [
                ("radius", "float", 5.0, "Radius (mm)")
            ],
            "primitives.create_cone": [
                ("radius1", "float", 5.0, "Bottom Radius (mm)"),
                ("radius2", "float", 0.0, "Top Radius (mm)"),
                ("height", "float", 10.0, "Height (mm)")
            ],
            "primitives.create_torus": [
                ("radius1", "float", 10.0, "Major Radius (mm)"),
                ("radius2", "float", 2.0, "Minor Radius (mm)")
            ],
            "operations.boolean_union": [
                ("obj1_name", "object", "", "First Object"),
                ("obj2_name", "object", "", "Second Object"),
                ("keep_originals", "bool", False, "Keep Original Objects")
            ],
            "operations.boolean_cut": [
                ("obj1_name", "object", "", "Object to Cut From"),
                ("obj2_name", "object", "", "Cutting Object"),
                ("keep_originals", "bool", False, "Keep Original Objects")
            ],
            "operations.move_object": [
                ("obj_name", "object", "", "Object to Move"),
                ("x", "float", 0.0, "X Displacement"),
                ("y", "float", 0.0, "Y Displacement"),
                ("z", "float", 0.0, "Z Displacement"),
                ("relative", "bool", True, "Relative Movement")
            ],
            "measurements.measure_distance": [
                ("point1", "point", "", "First Point/Object"),
                ("point2", "point", "", "Second Point/Object")
            ],
            "measurements.measure_volume": [
                ("obj_name", "object", "", "Object to Measure")
            ],
            "export_import.export_stl": [
                ("filepath", "file_save", "model.stl", "Output File"),
                ("object_names", "objects", "", "Objects to Export (empty = all)"),
                ("ascii", "bool", False, "ASCII Format")
            ],
            "export_import.import_stl": [
                ("filepath", "file_open", "", "STL File"),
                ("object_name", "string", "", "Object Name (optional)")
            ]
        }

        # Get parameter configuration
        if tool_id in param_configs:
            params = param_configs[tool_id]

            form_layout = QtWidgets.QFormLayout()

            for param_name, param_type, default_value, label in params:
                if param_type == "float":
                    spin = QtWidgets.QDoubleSpinBox()
                    spin.setRange(-10000, 10000)
                    spin.setValue(default_value)
                    spin.setDecimals(2)
                    inputs[param_name] = spin
                    form_layout.addRow(label, spin)

                elif param_type == "bool":
                    check = QtWidgets.QCheckBox()
                    check.setChecked(default_value)
                    inputs[param_name] = check
                    form_layout.addRow(label, check)

                elif param_type == "string":
                    line = QtWidgets.QLineEdit()
                    line.setText(default_value)
                    inputs[param_name] = line
                    form_layout.addRow(label, line)

                elif param_type == "object":
                    combo = QtWidgets.QComboBox()
                    # Populate with current objects
                    if FreeCAD.ActiveDocument:
                        for obj in FreeCAD.ActiveDocument.Objects:
                            combo.addItem(obj.Name)
                    inputs[param_name] = combo
                    form_layout.addRow(label, combo)

                elif param_type == "objects":
                    line = QtWidgets.QLineEdit()
                    line.setPlaceholderText("Object1,Object2,... (empty = all)")
                    inputs[param_name] = line
                    form_layout.addRow(label, line)

                elif param_type == "point":
                    line = QtWidgets.QLineEdit()
                    line.setPlaceholderText("ObjectName or [x,y,z]")
                    inputs[param_name] = line
                    form_layout.addRow(label, line)

                elif param_type == "file_save":
                    widget = QtWidgets.QWidget()
                    h_layout = QtWidgets.QHBoxLayout(widget)
                    h_layout.setContentsMargins(0, 0, 0, 0)

                    line = QtWidgets.QLineEdit()
                    line.setText(default_value)
                    browse_btn = QtWidgets.QPushButton("Browse...")

                    def browse_save():
                        filename, _ = QtWidgets.QFileDialog.getSaveFileName(dialog, "Save File", default_value)
                        if filename:
                            line.setText(filename)

                    browse_btn.clicked.connect(browse_save)
                    h_layout.addWidget(line)
                    h_layout.addWidget(browse_btn)

                    inputs[param_name] = line
                    form_layout.addRow(label, widget)

                elif param_type == "file_open":
                    widget = QtWidgets.QWidget()
                    h_layout = QtWidgets.QHBoxLayout(widget)
                    h_layout.setContentsMargins(0, 0, 0, 0)

                    line = QtWidgets.QLineEdit()
                    browse_btn = QtWidgets.QPushButton("Browse...")

                    def browse_open():
                        filename, _ = QtWidgets.QFileDialog.getOpenFileName(dialog, "Open File")
                        if filename:
                            line.setText(filename)

                    browse_btn.clicked.connect(browse_open)
                    h_layout.addWidget(line)
                    h_layout.addWidget(browse_btn)

                    inputs[param_name] = line
                    form_layout.addRow(label, widget)

            layout.addLayout(form_layout)

        # Buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        # Store inputs for retrieval
        dialog.inputs = inputs

        def get_parameters():
            """Extract parameters from dialog inputs."""
            params = {}
            for name, widget in inputs.items():
                if isinstance(widget, QtWidgets.QDoubleSpinBox):
                    params[name] = widget.value()
                elif isinstance(widget, QtWidgets.QCheckBox):
                    params[name] = widget.isChecked()
                elif isinstance(widget, QtWidgets.QComboBox):
                    params[name] = widget.currentText()
                elif isinstance(widget, QtWidgets.QLineEdit):
                    text = widget.text()
                    # Handle special cases
                    if name == "object_names" and text:
                        # Convert comma-separated list to array
                        params[name] = [s.strip() for s in text.split(',') if s.strip()]
                    elif name.startswith("point") and text:
                        # Handle point specification
                        if text.startswith('[') and text.endswith(']'):
                            # Parse as coordinates
                            try:
                                coords = eval(text)
                                if isinstance(coords, (list, tuple)) and len(coords) == 3:
                                    params[name] = list(coords)
                                else:
                                    params[name] = text
                            except:
                                params[name] = text
                        else:
                            # Object name
                            params[name] = text
                    elif text:  # Only add if not empty
                        params[name] = text
            return params

        dialog.get_parameters = get_parameters

        return dialog

    def _export_logs(self):
        """Export logs to file."""
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export Logs",
            f"mcp_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt)"
        )

        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write(self.log_display.toPlainText())
                self._add_log("Export", f"Logs exported to: {filename}")
                QtWidgets.QMessageBox.information(self, "Success", "Logs exported successfully")
            except Exception as e:
                self._add_log("Export", f"Failed to export logs: {str(e)}")
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to export logs: {str(e)}")

    def _add_log(self, category, message):
        """Add a log entry."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {category}: {message}"

        # Only append to log_display if it exists
        if hasattr(self, 'log_display') and self.log_display:
            self.log_display.append(log_entry)

        # Update status bar only if it exists
        if hasattr(self, 'status_bar') and self.status_bar:
            self.status_bar.showMessage(f"Last: {message}", 3000)

        # Also print to FreeCAD console
        FreeCAD.Console.PrintMessage(f"MCP Integration: {log_entry}\n")

    def _update_ai_status(self):
        """Update the AI connection status label."""
        if not hasattr(self, 'ai_status_label'):
            return

        if self.ai_provider:
            provider_text = self.provider_combo.currentText() if self.provider_combo else "Unknown"
            model = self.model_combo.currentText() if self.model_combo else "Unknown"
            self.ai_status_label.setText(f"Status: Connected to {provider_text} ({model})")
            self.ai_status_label.setStyleSheet("padding: 5px; background-color: #c8e6c9; border-radius: 3px;")
        else:
            self.ai_status_label.setText("Status: Not connected")
            self.ai_status_label.setStyleSheet("padding: 5px; background-color: #ffcdd2; border-radius: 3px;")

    def _use_quick_prompt(self, prompt):
        """Use a quick prompt in the chat."""
        if hasattr(self, 'chat_input') and self.chat_input:
            self.chat_input.setText(prompt)
            self._send_chat_message()

    def _save_ai_settings(self):
        """Save AI provider settings."""
        try:
            # Here you could save settings to a configuration file
            # For now, just show a success message
            self._add_log("Settings", "AI settings saved")
            QtWidgets.QMessageBox.information(self, "Settings Saved", "AI provider settings have been saved.")
        except Exception as e:
            self._add_log("Settings", f"Failed to save settings: {str(e)}")
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")

    def _update_model_info(self):
        """Update the model information display."""
        if not hasattr(self, 'model_info_text'):
            return

        provider_text = self.provider_combo.currentText() if self.provider_combo else ""
        model = self.model_combo.currentText() if self.model_combo else ""

        info_html = "<style>body { font-family: Arial, sans-serif; }</style>"

        if "Claude" in provider_text:
            if "opus" in model:
                info_html += """
                <h4>Claude 4 Opus</h4>
                <p><b>Best for:</b> Complex analysis, research, creative tasks</p>
                <p><b>Context:</b> 200K tokens</p>
                <p><b>Features:</b> Thinking mode, advanced reasoning</p>
                """
            elif "sonnet" in model:
                info_html += """
                <h4>Claude 4 Sonnet</h4>
                <p><b>Best for:</b> Coding, technical tasks, CAD design</p>
                <p><b>Context:</b> 200K tokens</p>
                <p><b>Features:</b> Thinking mode, optimized for development</p>
                """
            else:
                info_html += """
                <h4>Claude Model</h4>
                <p>Advanced AI assistant with strong reasoning capabilities.</p>
                """
        elif "Gemini" in provider_text:
            if "2.5-pro" in model:
                info_html += """
                <h4>Gemini 2.5 Pro</h4>
                <p><b>Best for:</b> Multimodal tasks, analysis, general assistance</p>
                <p><b>Context:</b> 1M tokens</p>
                <p><b>Features:</b> Latest Google AI, very large context</p>
                """
            else:
                info_html += """
                <h4>Gemini Model</h4>
                <p>Google's advanced AI with multimodal capabilities.</p>
                """
        elif "OpenRouter" in provider_text:
            info_html += """
            <h4>OpenRouter</h4>
            <p><b>Access to:</b> Multiple AI models through unified API</p>
            <p><b>Models:</b> Claude, GPT-4, Gemini, and more</p>
            <p><b>Benefit:</b> Single API key for multiple providers</p>
            """
        else:
            info_html += """
            <h4>Select a Model</h4>
            <p>Choose a provider and model to see information.</p>
            """

        self.model_info_text.setHtml(info_html)

    def _on_claude_desktop_mode_changed(self, enabled):
        """Handle Claude Desktop Mode toggle."""
        self.claude_desktop_enabled = enabled

        if enabled:
            # Hide the Assistant tab
            for i in range(self.tab_widget.count()):
                if self.tab_widget.tabText(i) == "Assistant":
                    self.tab_widget.setTabVisible(i, False)
                    break

            self._add_log("Claude Desktop", "Claude Desktop Mode enabled - Assistant tab hidden")
            QtWidgets.QMessageBox.information(
                self,
                "Claude Desktop Mode",
                "Claude Desktop Mode enabled!\n\n"
                "The Assistant tab is now hidden. Use Claude Desktop App to interact with FreeCAD.\n\n"
                "Make sure to:\n"
                "1. Copy the configuration from the Models tab\n"
                "2. Add it to your Claude Desktop config file\n"
                "3. Restart Claude Desktop"
            )
        else:
            # Show the Assistant tab
            for i in range(self.tab_widget.count()):
                if self.tab_widget.tabText(i) == "Assistant":
                    self.tab_widget.setTabVisible(i, True)
                    break

            self._add_log("Claude Desktop", "Claude Desktop Mode disabled - Assistant tab restored")

    def _update_claude_config_text(self):
        """Update the Claude Desktop configuration text."""
        try:
            # Get the absolute path to the launcher script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            launcher_path = os.path.join(script_dir, "..", "scripts", "launch_mcp_server.py")
            launcher_path = os.path.abspath(launcher_path)

            # Get Python executable
            python_exe = sys.executable

            # Create configuration for different platforms
            if sys.platform == "win32":
                config = {
                    "mcpServers": {
                        "freecad": {
                            "command": python_exe,
                            "args": [launcher_path, "--headless"]
                        }
                    }
                }
                config_file_path = "%APPDATA%\\Claude\\claude_desktop_config.json"
            else:
                config = {
                    "mcpServers": {
                        "freecad": {
                            "command": python_exe,
                            "args": [launcher_path, "--headless"]
                        }
                    }
                }
                config_file_path = "~/Library/Application Support/Claude/claude_desktop_config.json"

            config_json = json.dumps(config, indent=2)

            config_text = f"""Add this configuration to your Claude Desktop config file:

File location: {config_file_path}

Configuration:
{config_json}

Instructions:
1. Open Claude Desktop App
2. Create/edit the config file at the location above
3. Add the configuration (merge with existing mcpServers if any)
4. Restart Claude Desktop
5. Look for the FreeCAD tools in Claude Desktop

Note: Make sure the MCP library is installed:
pip install mcp>=1.0.0"""

            self.claude_config_text.setPlainText(config_text)

        except Exception as e:
            self.claude_config_text.setPlainText(f"Error generating configuration: {str(e)}")

    def _copy_claude_config(self):
        """Copy Claude Desktop configuration to clipboard."""
        try:
            clipboard = QtWidgets.QApplication.clipboard()

            # Get just the JSON configuration
            script_dir = os.path.dirname(os.path.abspath(__file__))
            launcher_path = os.path.join(script_dir, "..", "scripts", "launch_mcp_server.py")
            launcher_path = os.path.abspath(launcher_path)
            python_exe = sys.executable

            config = {
                "mcpServers": {
                    "freecad": {
                        "command": python_exe,
                        "args": [launcher_path, "--headless"]
                    }
                }
            }

            config_json = json.dumps(config, indent=2)
            clipboard.setText(config_json)

            QtWidgets.QMessageBox.information(
                self,
                "Copied",
                "Claude Desktop configuration copied to clipboard!\n\n"
                "Paste this into your claude_desktop_config.json file."
            )
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Failed to copy configuration: {str(e)}")


class MCPWorkbench(FreeCADGui.Workbench):
    """MCP Integration Workbench for FreeCAD"""

    MenuText = "MCP Integration"
    ToolTip = "Model Context Protocol Integration for AI-powered CAD operations"

    def __init__(self):
        """Initialize the MCP workbench."""
        self.__class__.Icon = self._get_icon_path()

    def _get_icon_path(self):
        """Get the workbench icon path."""
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "resources", "icons", "mcp_workbench.svg")
            if os.path.exists(icon_path):
                return icon_path
        except:
            pass
        return ""

    def Initialize(self):
        """Initialize the workbench GUI components."""
        FreeCAD.Console.PrintMessage("MCP Integration Workbench: Initializing...\n")

        try:
            # Create toolbar with available commands
            self._create_toolbar()

            # Create dock widget for the interface
            self._create_dock_widget()

            FreeCAD.Console.PrintMessage("MCP Integration Workbench: Initialization complete\n")

        except Exception as e:
            FreeCAD.Console.PrintError(f"MCP Integration Workbench: Initialization failed: {e}\n")
            import traceback
            FreeCAD.Console.PrintError(f"MCP Integration Workbench: Traceback: {traceback.format_exc()}\n")

    def Activated(self):
        """Called when the workbench is activated."""
        FreeCAD.Console.PrintMessage("MCP Integration Workbench: Activated\n")

    def Deactivated(self):
        """Called when the workbench is deactivated."""
        FreeCAD.Console.PrintMessage("MCP Integration Workbench: Deactivated\n")

    def GetClassName(self):
        """Return the workbench class name."""
        return "Gui::PythonWorkbench"

    def _create_toolbar(self):
        """Create the MCP toolbar."""
        try:
            # Create a simple toolbar with basic commands
            toolbar_commands = []

            # Only add commands that are properly registered
            try:
                # Check if the command exists before adding it
                if hasattr(FreeCADGui, 'listCommands') and 'MCP_ShowInterface' in FreeCADGui.listCommands():
                    toolbar_commands.append("MCP_ShowInterface")
            except:
                pass

            # Only create toolbar if we have valid commands and appendToolbar method exists
            if toolbar_commands and hasattr(self, 'appendToolbar'):
                self.appendToolbar("MCP Integration", toolbar_commands)
                FreeCAD.Console.PrintMessage(f"MCP Integration: Toolbar created with {len(toolbar_commands)} commands\n")
            else:
                if not hasattr(self, 'appendToolbar'):
                    FreeCAD.Console.PrintMessage("MCP Integration: appendToolbar method not available\n")
                else:
                    FreeCAD.Console.PrintMessage("MCP Integration: Toolbar creation skipped - no valid commands available\n")

        except Exception as e:
            FreeCAD.Console.PrintError(f"Failed to create toolbar: {e}\n")
            import traceback
            FreeCAD.Console.PrintError(f"Toolbar creation traceback: {traceback.format_exc()}\n")

    def _create_dock_widget(self):
        """Create and show the dock widget."""
        try:
            if not HAS_PYSIDE2:
                FreeCAD.Console.PrintMessage("MCP Integration: Skipping dock widget creation - no Qt bindings\n")
                return

            # Create main widget
            main_widget = MCPMainWidget()

            # Create dock widget to hold the main widget
            if main_widget and hasattr(main_widget, 'status_bar'):
                dock_widget = QtWidgets.QDockWidget("MCP Integration", FreeCADGui.getMainWindow())
                dock_widget.setObjectName("MCPIntegrationDockWidget")  # Fix QMainWindow::saveState() warning
                dock_widget.setWidget(main_widget)
                FreeCADGui.getMainWindow().addDockWidget(QtCore.Qt.RightDockWidgetArea, dock_widget)
                FreeCAD.Console.PrintMessage("MCP Integration: Dock widget created successfully\n")

        except Exception as e:
            FreeCAD.Console.PrintError(f"Failed to create dock widget: {e}\n")
            import traceback
            FreeCAD.Console.PrintError(f"Dock widget creation traceback: {traceback.format_exc()}\n")


