"""Enhanced Agent Control Widget with Advanced Diagnostics and Management"""

from datetime import datetime
import json
import traceback

from PySide2 import QtWidgets, QtGui, QtCore

from .provider_selector_widget import ProviderSelectorWidget
from .theme_system import apply_theme_to_widget


class AgentDiagnosticDialog(QtWidgets.QDialog):
    """Advanced diagnostic dialog for agent manager."""
    
    def __init__(self, agent_manager=None, provider_service=None, parent=None):
        super(AgentDiagnosticDialog, self).__init__(parent)
        self.agent_manager = agent_manager
        self.provider_service = provider_service
        self.setWindowTitle("Agent Manager Diagnostics")
        self.resize(700, 500)
        self._setup_ui()
        self._update_diagnostics()
        
    def _setup_ui(self):
        """Setup diagnostic dialog UI."""
        layout = QtWidgets.QVBoxLayout(self)
        
        # Create tab widget for different diagnostic categories
        tab_widget = QtWidgets.QTabWidget()
        
        # Agent Status Tab
        self.agent_status_tab = self._create_agent_status_tab()
        tab_widget.addTab(self.agent_status_tab, "Agent Status")
        
        # Provider Status Tab
        self.provider_status_tab = self._create_provider_status_tab()
        tab_widget.addTab(self.provider_status_tab, "Provider Status")
        
        # Tools Status Tab
        self.tools_status_tab = self._create_tools_status_tab()
        tab_widget.addTab(self.tools_status_tab, "Tools Status")
        
        # System Info Tab
        self.system_info_tab = self._create_system_info_tab()
        tab_widget.addTab(self.system_info_tab, "System Info")
        
        layout.addWidget(tab_widget)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        refresh_btn = QtWidgets.QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._update_diagnostics)
        button_layout.addWidget(refresh_btn)
        
        export_btn = QtWidgets.QPushButton("📄 Export Report")
        export_btn.clicked.connect(self._export_diagnostic_report)
        button_layout.addWidget(export_btn)
        
        button_layout.addStretch()
        
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
    def _create_agent_status_tab(self):
        """Create agent status tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        self.agent_status_text = QtWidgets.QTextEdit()
        self.agent_status_text.setReadOnly(True)
        self.agent_status_text.setFont(QtGui.QFont("Courier", 10))
        layout.addWidget(self.agent_status_text)
        
        return widget
        
    def _create_provider_status_tab(self):
        """Create provider status tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        self.provider_status_text = QtWidgets.QTextEdit()
        self.provider_status_text.setReadOnly(True) 
        self.provider_status_text.setFont(QtGui.QFont("Courier", 10))
        layout.addWidget(self.provider_status_text)
        
        return widget
        
    def _create_tools_status_tab(self):
        """Create tools status tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        self.tools_status_text = QtWidgets.QTextEdit()
        self.tools_status_text.setReadOnly(True)
        self.tools_status_text.setFont(QtGui.QFont("Courier", 10))
        layout.addWidget(self.tools_status_text)
        
        return widget
        
    def _create_system_info_tab(self):
        """Create system info tab."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        self.system_info_text = QtWidgets.QTextEdit()
        self.system_info_text.setReadOnly(True)
        self.system_info_text.setFont(QtGui.QFont("Courier", 10))
        layout.addWidget(self.system_info_text)
        
        return widget
        
    def _update_diagnostics(self):
        """Update all diagnostic information."""
        self._update_agent_status()
        self._update_provider_status()
        self._update_tools_status()
        self._update_system_info()
        
    def _update_agent_status(self):
        """Update agent manager status."""
        status_lines = []
        status_lines.append("=== AGENT MANAGER DIAGNOSTICS ===\n")
        
        if self.agent_manager is None:
            status_lines.append("❌ Agent Manager: NOT AVAILABLE")
            status_lines.append("   └─ Agent manager instance is None")
            status_lines.append("   └─ This usually indicates import failure")
            status_lines.append("   └─ Check FreeCAD console for import errors")
        else:
            status_lines.append("✅ Agent Manager: AVAILABLE")
            
            try:
                # Get agent manager state
                current_mode = self.agent_manager.get_mode()
                status_lines.append(f"   ├─ Current Mode: {current_mode.value}")
                
                current_state = self.agent_manager.execution_state
                status_lines.append(f"   ├─ Execution State: {current_state.value}")
                
                # Get configuration
                config = self.agent_manager.config
                status_lines.append(f"   ├─ Config Loaded: {config is not None}")
                if config:
                    status_lines.append(f"   │  ├─ Require Approval: {config.get('require_approval', 'N/A')}")
                    status_lines.append(f"   │  ├─ Auto Rollback: {config.get('auto_rollback', 'N/A')}")
                    status_lines.append(f"   │  ├─ Safety Checks: {config.get('safety_checks', 'N/A')}")
                    status_lines.append(f"   │  ├─ Execution Timeout: {config.get('execution_timeout', 'N/A')}s")
                    status_lines.append(f"   │  └─ Max Retries: {config.get('max_retries', 'N/A')}")
                
                # Check tool registry
                if hasattr(self.agent_manager, 'tool_registry'):
                    available_tools = self.agent_manager.get_available_tools()
                    total_tools = sum(len(methods) for methods in available_tools.values())
                    status_lines.append("   ├─ Tool Registry: Available")
                    status_lines.append(f"   │  ├─ Total Tools: {total_tools}")
                    status_lines.append(f"   │  └─ Categories: {len(available_tools)}")
                else:
                    status_lines.append("   ├─ Tool Registry: ❌ Not Available")
                
                # Check execution history
                if hasattr(self.agent_manager, 'get_execution_history'):
                    history = self.agent_manager.get_execution_history()
                    status_lines.append(f"   └─ Execution History: {len(history)} entries")
                
            except Exception as e:
                status_lines.append(f"   └─ ❌ Error getting agent status: {str(e)}")
                status_lines.append(f"      └─ {traceback.format_exc()}")
        
        self.agent_status_text.setText("\n".join(status_lines))
        
    def _update_provider_status(self):
        """Update provider service status."""
        status_lines = []
        status_lines.append("=== PROVIDER SERVICE DIAGNOSTICS ===\n")
        
        if self.provider_service is None:
            status_lines.append("❌ Provider Service: NOT AVAILABLE")
            status_lines.append("   └─ Provider service instance is None")
        else:
            status_lines.append("✅ Provider Service: AVAILABLE")
            
            try:
                # Get all providers
                all_providers = self.provider_service.get_all_providers()
                active_providers = self.provider_service.get_active_providers()
                
                status_lines.append(f"   ├─ Total Providers: {len(all_providers)}")
                status_lines.append(f"   ├─ Active Providers: {len(active_providers)}")
                
                if all_providers:
                    status_lines.append("   ├─ Provider Details:")
                    for name, info in all_providers.items():
                        is_active = name in active_providers
                        status_icon = "✅" if is_active else "⚠️"
                        status_lines.append(f"   │  ├─ {status_icon} {name}")
                        status_lines.append(f"   │  │  ├─ Type: {info.get('type', 'Unknown')}")
                        status_lines.append(f"   │  │  ├─ Status: {info.get('status', 'Unknown')}")
                        status_lines.append(f"   │  │  └─ Model: {info.get('model', 'Unknown')}")
                        
                # Get current selection
                current_selection = self.provider_service.get_current_provider_selection()
                status_lines.append(f"   ├─ Current Provider: {current_selection.get('provider', 'None')}")
                status_lines.append(f"   └─ Current Model: {current_selection.get('model', 'None')}")
                
            except Exception as e:
                status_lines.append(f"   └─ ❌ Error getting provider status: {str(e)}")
        
        self.provider_status_text.setText("\n".join(status_lines))
        
    def _update_tools_status(self):
        """Update tools status."""
        status_lines = []
        status_lines.append("=== TOOLS REGISTRY DIAGNOSTICS ===\n")
        
        if self.agent_manager is None:
            status_lines.append("❌ Tools Registry: Agent Manager Not Available")
        else:
            try:
                available_tools = self.agent_manager.get_available_tools()
                status_lines.append(f"✅ Tools Registry: {len(available_tools)} categories available")
                
                for category, tools in available_tools.items():
                    status_lines.append(f"   ├─ {category.title()} ({len(tools)} tools)")
                    for tool in tools[:5]:  # Show first 5 tools per category
                        status_lines.append(f"   │  ├─ {tool}")
                    if len(tools) > 5:
                        status_lines.append(f"   │  └─ ... and {len(tools) - 5} more")
                        
            except Exception as e:
                status_lines.append(f"❌ Error getting tools status: {str(e)}")
        
        self.tools_status_text.setText("\n".join(status_lines))
        
    def _update_system_info(self):
        """Update system information."""
        status_lines = []
        status_lines.append("=== SYSTEM INFORMATION ===\n")
        
        # Python environment
        import sys
        status_lines.append(f"Python Version: {sys.version}")
        status_lines.append(f"Platform: {sys.platform}")
        
        # FreeCAD information
        try:
            import FreeCAD
            status_lines.append(f"FreeCAD Version: {'.'.join(str(v) for v in FreeCAD.Version()[:3])}")
            status_lines.append(f"FreeCAD Build: {FreeCAD.Version()[3] if len(FreeCAD.Version()) > 3 else 'Unknown'}")
        except Exception as e:
            status_lines.append(f"FreeCAD: Error getting version - {str(e)}")
            
        # Qt information
        try:
            from PySide2 import QtCore
            status_lines.append(f"Qt Version: {QtCore.QT_VERSION_STR}")
            status_lines.append(f"PySide2 Version: {QtCore.__version__}")
        except Exception as e:
            status_lines.append(f"Qt: Error getting version - {str(e)}")
            
        # Memory usage
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            status_lines.append(f"Memory Usage: {memory_info.rss / 1024 / 1024:.1f} MB")
        except ImportError:
            status_lines.append("Memory Usage: psutil not available")
        except Exception as e:
            status_lines.append(f"Memory Usage: Error - {str(e)}")
            
        # Current working directory
        import os
        status_lines.append(f"Working Directory: {os.getcwd()}")
        
        # Environment variables related to FreeCAD
        freecad_env_vars = ['FREECAD_USER_HOME', 'FREECAD_USER_DATA', 'FREECADPATH']
        for var in freecad_env_vars:
            value = os.environ.get(var, 'Not set')
            status_lines.append(f"{var}: {value}")
            
        self.system_info_text.setText("\n".join(status_lines))
        
    def _export_diagnostic_report(self):
        """Export diagnostic report to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export Diagnostic Report",
            f"freecad_ai_diagnostic_report_{timestamp}.txt",
            "Text Files (*.txt);;JSON Files (*.json);;All Files (*.*)"
        )
        
        if not filename:
            return
            
        try:
            if filename.endswith('.json'):
                # Export as JSON
                report_data = {
                    "timestamp": datetime.now().isoformat(),
                    "agent_status": self.agent_status_text.toPlainText(),
                    "provider_status": self.provider_status_text.toPlainText(),
                    "tools_status": self.tools_status_text.toPlainText(),
                    "system_info": self.system_info_text.toPlainText()
                }
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(report_data, f, indent=2)
            else:
                # Export as plain text
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("FreeCAD AI Diagnostic Report\n")
                    f.write(f"Generated: {datetime.now().isoformat()}\n")
                    f.write("=" * 50 + "\n\n")
                    
                    f.write(self.agent_status_text.toPlainText())
                    f.write("\n\n" + "=" * 50 + "\n\n")
                    
                    f.write(self.provider_status_text.toPlainText())
                    f.write("\n\n" + "=" * 50 + "\n\n")
                    
                    f.write(self.tools_status_text.toPlainText())
                    f.write("\n\n" + "=" * 50 + "\n\n")
                    
                    f.write(self.system_info_text.toPlainText())
                    
            QtWidgets.QMessageBox.information(
                self, "Export Complete", f"Diagnostic report exported to:\n{filename}"
            )
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Export Error", f"Failed to export diagnostic report:\n{str(e)}"
            )


class EnhancedAgentControlWidget(QtWidgets.QWidget):
    """Enhanced agent control widget with advanced features."""

    def __init__(self, parent=None):
        super(EnhancedAgentControlWidget, self).__init__(parent)

        self.agent_manager = None
        self.provider_service = None
        self.config_manager = None
        self.current_plan = None
        self.execution_queue = []

        # Apply theme
        apply_theme_to_widget(self)

        self._setup_ui()

    def _setup_ui(self):
        """Setup the enhanced user interface."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Provider Selection Section
        self._create_provider_selector(layout)

        # Command Input Section
        self._create_command_section(layout)

        # Execution Status
        self._create_status_section(layout)

        # Enhanced Execution Controls
        self._create_enhanced_control_section(layout)

        # Execution Queue with priorities
        self._create_enhanced_queue_section(layout)

        # Enhanced Safety Settings
        self._create_enhanced_safety_section(layout)

        # Execution History with filtering
        self._create_enhanced_history_section(layout)

        layout.addStretch()



    def _create_provider_selector(self, layout):
        """Create provider selection section using shared widget."""
        provider_group = QtWidgets.QGroupBox("AI Provider Selection")
        provider_layout = QtWidgets.QHBoxLayout(provider_group)

        # Create the shared provider selector widget
        self.provider_selector = ProviderSelectorWidget()
        self.provider_selector.provider_changed.connect(self._on_provider_changed)
        self.provider_selector.refresh_requested.connect(self._on_provider_refresh)
        provider_layout.addWidget(self.provider_selector)

        layout.addWidget(provider_group)

    def _create_enhanced_control_section(self, layout):
        """Create enhanced execution control section."""
        control_group = QtWidgets.QGroupBox("Execution Controls")
        control_layout = QtWidgets.QVBoxLayout(control_group)

        # Primary controls
        primary_layout = QtWidgets.QHBoxLayout()
        
        # Play/Pause button
        self.play_pause_btn = QtWidgets.QPushButton("▶ Start")
        self.play_pause_btn.setEnabled(False)
        self.play_pause_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """
        )
        self.play_pause_btn.clicked.connect(self._toggle_execution)
        primary_layout.addWidget(self.play_pause_btn)

        # Stop button
        self.stop_btn = QtWidgets.QPushButton("⏹ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """
        )
        self.stop_btn.clicked.connect(self._stop_execution)
        primary_layout.addWidget(self.stop_btn)

        # Step button
        self.step_btn = QtWidgets.QPushButton("⏭ Step")
        self.step_btn.setEnabled(False)
        self.step_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #ccc;
            }
        """
        )
        self.step_btn.setToolTip("Execute one step at a time")
        self.step_btn.clicked.connect(self._step_execution)
        primary_layout.addWidget(self.step_btn)

        primary_layout.addStretch()
        control_layout.addLayout(primary_layout)

        # Secondary controls
        secondary_layout = QtWidgets.QHBoxLayout()
        
        # Enhanced diagnostic button
        self.diagnostic_btn = QtWidgets.QPushButton("🔍 Advanced Diagnostics")
        self.diagnostic_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 12px;
                border: none;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """
        )
        self.diagnostic_btn.setToolTip("Open comprehensive diagnostic dialog")
        self.diagnostic_btn.clicked.connect(self._show_advanced_diagnostics)
        secondary_layout.addWidget(self.diagnostic_btn)

        # Quick status button
        self.quick_status_btn = QtWidgets.QPushButton("⚡ Quick Status")
        self.quick_status_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 8px 12px;
                border: none;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
        """
        )
        self.quick_status_btn.setToolTip("Show quick status overview")
        self.quick_status_btn.clicked.connect(self._show_quick_status)
        secondary_layout.addWidget(self.quick_status_btn)

        # Clear queue button
        self.clear_queue_btn = QtWidgets.QPushButton("🗑️ Clear Queue")
        self.clear_queue_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 8px 12px;
                border: none;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
        """
        )
        self.clear_queue_btn.clicked.connect(self._clear_queue)
        secondary_layout.addWidget(self.clear_queue_btn)

        # Export settings button
        self.export_settings_btn = QtWidgets.QPushButton("📤 Export Settings")
        self.export_settings_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #9C27B0;
                color: white;
                padding: 8px 12px;
                border: none;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """
        )
        self.export_settings_btn.setToolTip("Export current agent settings")
        self.export_settings_btn.clicked.connect(self._export_settings)
        secondary_layout.addWidget(self.export_settings_btn)

        secondary_layout.addStretch()
        control_layout.addLayout(secondary_layout)

        layout.addWidget(control_group)

    def _create_enhanced_queue_section(self, layout):
        """Create enhanced execution queue section with priorities."""
        queue_group = QtWidgets.QGroupBox("Execution Queue")
        queue_layout = QtWidgets.QVBoxLayout(queue_group)

        # Queue controls header
        queue_header = QtWidgets.QHBoxLayout()
        
        queue_header.addWidget(QtWidgets.QLabel("Queued Tasks:"))
        
        # Priority filter
        self.priority_filter = QtWidgets.QComboBox()
        self.priority_filter.addItems(["All", "High", "Medium", "Low"])
        self.priority_filter.currentTextChanged.connect(self._filter_queue_by_priority)
        queue_header.addWidget(self.priority_filter)
        
        queue_header.addStretch()
        
        # Queue stats
        self.queue_stats_label = QtWidgets.QLabel("0 tasks")
        queue_header.addWidget(self.queue_stats_label)
        
        queue_layout.addLayout(queue_header)

        # Queue list with enhanced display
        self.queue_list = QtWidgets.QTreeWidget()
        self.queue_list.setHeaderLabels(["Task", "Priority", "Steps", "Est. Time", "Risk"])
        self.queue_list.setMaximumHeight(150)
        self.queue_list.setAlternatingRowColors(True)
        self.queue_list.itemDoubleClicked.connect(self._edit_queue_item)
        queue_layout.addWidget(self.queue_list)

        # Enhanced queue controls
        queue_controls = QtWidgets.QHBoxLayout()

        self.move_up_btn = QtWidgets.QPushButton("↑")
        self.move_up_btn.setToolTip("Move selected item up")
        self.move_up_btn.clicked.connect(self._move_queue_item_up)
        queue_controls.addWidget(self.move_up_btn)

        self.move_down_btn = QtWidgets.QPushButton("↓")
        self.move_down_btn.setToolTip("Move selected item down")
        self.move_down_btn.clicked.connect(self._move_queue_item_down)
        queue_controls.addWidget(self.move_down_btn)

        self.set_priority_btn = QtWidgets.QPushButton("⚡ Priority")
        self.set_priority_btn.setToolTip("Set task priority")
        self.set_priority_btn.clicked.connect(self._set_task_priority)
        queue_controls.addWidget(self.set_priority_btn)

        self.edit_task_btn = QtWidgets.QPushButton("✏️ Edit")
        self.edit_task_btn.setToolTip("Edit selected task")
        self.edit_task_btn.clicked.connect(self._edit_queue_item)
        queue_controls.addWidget(self.edit_task_btn)

        self.remove_item_btn = QtWidgets.QPushButton("×")
        self.remove_item_btn.setToolTip("Remove selected item")
        self.remove_item_btn.clicked.connect(self._remove_queue_item)
        queue_controls.addWidget(self.remove_item_btn)

        queue_controls.addStretch()
        queue_layout.addLayout(queue_controls)

        layout.addWidget(queue_group)



    def _show_advanced_diagnostics(self):
        """Show advanced diagnostic dialog."""
        dialog = AgentDiagnosticDialog(
            self.agent_manager, 
            self.provider_service, 
            self
        )
        dialog.exec_()

    def _show_quick_status(self):
        """Show quick status overview."""
        status_lines = []
        
        # Agent status
        if self.agent_manager:
            mode = self.agent_manager.get_mode().value
            state = self.agent_manager.execution_state.value
            status_lines.append(f"Agent: {mode.title()} mode, {state} state")
        else:
            status_lines.append("Agent: Not available")
            
        # Provider status
        if self.provider_service:
            active_providers = self.provider_service.get_active_providers()
            total_providers = self.provider_service.get_all_providers()
            status_lines.append(f"Providers: {len(active_providers)}/{len(total_providers)} active")
        else:
            status_lines.append("Providers: Service not available")
            
        # Queue status
        status_lines.append(f"Queue: {len(self.execution_queue)} tasks pending")
        
        # Tools status
        if self.agent_manager and hasattr(self.agent_manager, 'get_available_tools'):
            tools = self.agent_manager.get_available_tools()
            total_tools = sum(len(methods) for methods in tools.values())
            status_lines.append(f"Tools: {total_tools} available")
        else:
            status_lines.append("Tools: Status unknown")
            
        QtWidgets.QMessageBox.information(
            self, "Quick Status", "\n".join(status_lines)
        )

    def _on_provider_changed(self, provider_name, model_name):
        """Handle provider selection change from provider selector."""
        print(
            f"EnhancedAgentControlWidget: Provider changed to {provider_name} with model {model_name}"
        )
        # Update agent manager if available
        if self.agent_manager and hasattr(self.agent_manager, "set_provider"):
            try:
                self.agent_manager.set_provider(provider_name, model_name)
            except Exception as e:
                print(
                    f"EnhancedAgentControlWidget: Error setting provider in agent manager: {e}"
                )

    def _on_provider_refresh(self):
        """Handle provider refresh request."""
        print("EnhancedAgentControlWidget: Provider refresh requested")
        if self.provider_service:
            try:
                if hasattr(self.provider_service, "refresh_providers"):
                    self.provider_service.refresh_providers()
                elif hasattr(self.provider_service, "initialize_providers_from_config"):
                    self.provider_service.initialize_providers_from_config()
            except Exception as e:
                print(f"EnhancedAgentControlWidget: Error refreshing providers: {e}")

    def _toggle_execution(self):
        """Toggle execution play/pause."""
        if hasattr(self, 'execution_running') and self.execution_running:
            # Stop execution
            self.execution_running = False
            self.toggle_execution_btn.setText("Start Execution")
            self.toggle_execution_btn.setStyleSheet("background-color: green;")
            
            # Update status
            self._update_execution_status("Stopped")
            print("Execution stopped")
            
        else:
            # Start execution
            self.execution_running = True
            self.toggle_execution_btn.setText("Stop Execution")
            self.toggle_execution_btn.setStyleSheet("background-color: red;")
            
            # Update status
            self._update_execution_status("Running")
            print("Execution started")
    
    def _update_execution_status(self, status):
        """Update execution status display."""
        if hasattr(self, 'status_label'):
            self.status_label.setText(f"Status: {status}")
        
        # Emit signal if available
        if hasattr(self, 'execution_status_changed'):
            self.execution_status_changed.emit(status)

    def _stop_execution(self):
        """Stop current execution."""
        # Force stop execution regardless of current state
        self.execution_running = False
        
        # Reset button states
        if hasattr(self, 'toggle_execution_btn'):
            self.toggle_execution_btn.setText("Start Execution")
            self.toggle_execution_btn.setStyleSheet("background-color: green;")
        
        # Clear any running tasks
        if hasattr(self, 'current_task_id'):
            self.current_task_id = None
            
        # Update status
        self._update_execution_status("Stopped")
        
        # Clear progress if available
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setValue(0)
        
        print("Execution force stopped")

    def _step_execution(self):
        """Execute one step."""
        if not hasattr(self, 'execution_running'):
            self.execution_running = False
            
        # Check if there are tasks to execute
        if self.queue_list.count() == 0:
            QtWidgets.QMessageBox.information(
                self, "No Tasks", "No tasks in queue to execute."
            )
            return
        
        # Get the first task from queue
        first_item = self.queue_list.item(0)
        if first_item:
            task_text = first_item.text()
            
            # Simulate executing one step
            self._update_execution_status("Executing Step")
            
            # Create a simple step execution dialog
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle("Step Execution")
            dialog.setMinimumSize(400, 200)
            
            layout = QtWidgets.QVBoxLayout(dialog)
            layout.addWidget(QtWidgets.QLabel(f"Executing: {task_text}"))
            
            progress = QtWidgets.QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(50)  # Simulate partial completion
            layout.addWidget(progress)
            
            # Add buttons
            button_layout = QtWidgets.QHBoxLayout()
            complete_btn = QtWidgets.QPushButton("Mark Complete")
            cancel_btn = QtWidgets.QPushButton("Cancel")
            
            complete_btn.clicked.connect(lambda: self._complete_step(dialog, first_item))
            cancel_btn.clicked.connect(dialog.reject)
            
            button_layout.addWidget(complete_btn)
            button_layout.addWidget(cancel_btn)
            layout.addLayout(button_layout)
            
            dialog.exec_()
            
        self._update_execution_status("Step Complete")
        print("Step execution completed")
    
    def _complete_step(self, dialog, task_item):
        """Complete the current step."""
        # Remove completed task from queue
        row = self.queue_list.row(task_item)
        self.queue_list.takeItem(row)
        
        # Update queue info
        self._update_queue_info()
        
        dialog.accept()
        print("Step marked as complete")

    # Additional methods for enhanced functionality

    def _create_command_section(self, layout):
        """Create enhanced command input section."""
        command_group = QtWidgets.QGroupBox("Agent Commands")
        command_layout = QtWidgets.QVBoxLayout(command_group)

        # Command input
        input_layout = QtWidgets.QHBoxLayout()

        self.command_input = QtWidgets.QLineEdit()
        self.command_input.setPlaceholderText(
            "Type a command for the agent (e.g., 'Create a 20x20x10mm box')"
        )
        self.command_input.returnPressed.connect(self._send_command)
        self.command_input.setStyleSheet(
            """
            QLineEdit {
                padding: 8px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 6px;
            }
            QLineEdit:focus {
                border-color: #007acc;
            }
        """
        )
        input_layout.addWidget(self.command_input)

        # Send button
        self.send_btn = QtWidgets.QPushButton("Send")
        self.send_btn.clicked.connect(self._send_command)
        self.send_btn.setStyleSheet(
            """
            QPushButton {
                padding: 8px 15px;
                font-size: 14px;
                font-weight: bold;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """
        )
        input_layout.addWidget(self.send_btn)

        command_layout.addLayout(input_layout)

        # Command examples
        examples_label = QtWidgets.QLabel(
            "Examples: 'Create a cylinder 20mm radius, 40mm height' • 'Make a gear with 24 teeth' • 'Design a house foundation 12x8x1.5m'"
        )
        examples_label.setStyleSheet(
            "color: #666; font-size: 11px; font-style: italic; margin-top: 5px;"
        )
        examples_label.setWordWrap(True)
        command_layout.addWidget(examples_label)

        layout.addWidget(command_group)
        
    def _create_status_section(self, layout):
        """Create enhanced status section."""
        status_group = QtWidgets.QGroupBox("Execution Status")
        status_layout = QtWidgets.QVBoxLayout(status_group)

        # Current state
        state_layout = QtWidgets.QHBoxLayout()
        state_layout.addWidget(QtWidgets.QLabel("State:"))
        self.state_label = QtWidgets.QLabel("Idle")
        self.state_label.setStyleSheet(
            """
            QLabel {
                font-weight: bold;
                padding: 5px 10px;
                background-color: #f0f0f0;
                border-radius: 4px;
            }
        """
        )
        state_layout.addWidget(self.state_label)
        state_layout.addStretch()
        status_layout.addLayout(state_layout)

        # Current operation
        op_layout = QtWidgets.QHBoxLayout()
        op_layout.addWidget(QtWidgets.QLabel("Current Operation:"))
        self.operation_label = QtWidgets.QLabel("None")
        self.operation_label.setStyleSheet("color: #666;")
        op_layout.addWidget(self.operation_label)
        op_layout.addStretch()
        status_layout.addLayout(op_layout)

        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)

        layout.addWidget(status_group)
        
    def _create_enhanced_safety_section(self, layout):
        """Create enhanced safety settings."""
        safety_group = QtWidgets.QGroupBox("Safety Settings")
        safety_layout = QtWidgets.QVBoxLayout(safety_group)

        # Safety options
        options_layout = QtWidgets.QGridLayout()

        self.require_approval_cb = QtWidgets.QCheckBox("Require approval for destructive operations")
        self.require_approval_cb.setChecked(True)
        options_layout.addWidget(self.require_approval_cb, 0, 0)

        self.auto_rollback_cb = QtWidgets.QCheckBox("Enable automatic rollback on errors")
        self.auto_rollback_cb.setChecked(True)
        options_layout.addWidget(self.auto_rollback_cb, 0, 1)

        self.safety_checks_cb = QtWidgets.QCheckBox("Enable geometry safety checks")
        self.safety_checks_cb.setChecked(True)
        options_layout.addWidget(self.safety_checks_cb, 1, 0)

        self.backup_before_cb = QtWidgets.QCheckBox("Backup before major operations")
        self.backup_before_cb.setChecked(True)
        options_layout.addWidget(self.backup_before_cb, 1, 1)

        safety_layout.addLayout(options_layout)

        # Timeout settings
        timeout_layout = QtWidgets.QHBoxLayout()
        timeout_layout.addWidget(QtWidgets.QLabel("Execution Timeout:"))
        
        self.timeout_spin = QtWidgets.QSpinBox()
        self.timeout_spin.setRange(5, 300)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" seconds")
        timeout_layout.addWidget(self.timeout_spin)
        
        timeout_layout.addStretch()
        safety_layout.addLayout(timeout_layout)

        layout.addWidget(safety_group)
        
    def _create_enhanced_history_section(self, layout):
        """Create enhanced history section with filtering."""
        history_group = QtWidgets.QGroupBox("Execution History")
        history_layout = QtWidgets.QVBoxLayout(history_group)

        # History controls
        controls_layout = QtWidgets.QHBoxLayout()
        
        controls_layout.addWidget(QtWidgets.QLabel("Filter:"))
        
        self.history_filter = QtWidgets.QComboBox()
        self.history_filter.addItems(["All", "Successful", "Failed", "Today"])
        controls_layout.addWidget(self.history_filter)
        
        controls_layout.addStretch()
        
        # Clear history button
        self.clear_history_btn = QtWidgets.QPushButton("Clear History")
        self.clear_history_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
        """
        )
        self.clear_history_btn.clicked.connect(self._clear_history)
        controls_layout.addWidget(self.clear_history_btn)
        
        history_layout.addLayout(controls_layout)

        # History list
        self.history_list = QtWidgets.QListWidget()
        self.history_list.setMaximumHeight(120)
        self.history_list.setAlternatingRowColors(True)
        history_layout.addWidget(self.history_list)

        layout.addWidget(history_group)

    # Additional methods for enhanced functionality
    def _filter_queue_by_priority(self, priority):
        """Filter queue display by priority."""
        print(f"Filter queue by priority: {priority}")
        
        # Show/hide items based on priority filter
        for i in range(self.queue_list.topLevelItemCount()):
            item = self.queue_list.topLevelItem(i)
            if not item:
                continue
                
            # Extract priority from item text
            item_text = item.text(0)  # First column contains task text
            item_priority = "Medium"  # Default priority
            
            # Check if priority is indicated in brackets
            if " [" in item_text and item_text.endswith("]"):
                priority_start = item_text.rfind(" [")
                item_priority = item_text[priority_start + 2:-1]
            
            # Show/hide based on filter
            if priority == "All":
                item.setHidden(False)
            else:
                item.setHidden(item_priority != priority)
        
        # Update queue statistics after filtering
        self._update_queue_info()
        
    def _edit_queue_item(self):
        """Edit selected queue item."""
        print("Edit queue item called")
        
        # Get current selection
        current_item = self.queue_list.currentItem()
        if not current_item:
            QtWidgets.QMessageBox.information(
                self, "No Selection", "Please select a task to edit."
            )
            return
        
        # Extract current task information
        current_text = current_item.text(0) if hasattr(current_item, 'text') else str(current_item.text())
        current_priority = "Medium"  # Default
        current_steps = current_item.text(2) if hasattr(current_item, 'text') and current_item.columnCount() > 2 else "1"
        current_time = current_item.text(3) if hasattr(current_item, 'text') and current_item.columnCount() > 3 else "5 min"
        
        # Extract priority if present
        if " [" in current_text and current_text.endswith("]"):
            priority_start = current_text.rfind(" [")
            current_priority = current_text[priority_start + 2:-1]
            current_text = current_text[:priority_start]
        
        # Create edit dialog
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Edit Queue Item")
        dialog.setMinimumSize(500, 300)
        
        layout = QtWidgets.QFormLayout(dialog)
        
        # Task description
        task_edit = QtWidgets.QTextEdit()
        task_edit.setPlainText(current_text)
        task_edit.setMaximumHeight(100)
        layout.addRow("Task Description:", task_edit)
        
        # Priority
        priority_combo = QtWidgets.QComboBox()
        priority_combo.addItems(["High", "Medium", "Low"])
        priority_combo.setCurrentText(current_priority)
        layout.addRow("Priority:", priority_combo)
        
        # Estimated steps
        steps_spin = QtWidgets.QSpinBox()
        steps_spin.setRange(1, 100)
        steps_spin.setValue(int(current_steps.split()[0]) if current_steps.split()[0].isdigit() else 1)
        layout.addRow("Estimated Steps:", steps_spin)
        
        # Estimated time
        time_edit = QtWidgets.QLineEdit(current_time)
        layout.addRow("Estimated Time:", time_edit)
        
        # Risk level
        risk_combo = QtWidgets.QComboBox()
        risk_combo.addItems(["Low", "Medium", "High"])
        risk_combo.setCurrentText("Medium")  # Default
        layout.addRow("Risk Level:", risk_combo)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        save_btn = QtWidgets.QPushButton("Save")
        cancel_btn = QtWidgets.QPushButton("Cancel")
        
        save_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        button_widget = QtWidgets.QWidget()
        button_widget.setLayout(button_layout)
        layout.addRow(button_widget)
        
        # Execute dialog
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            # Update the queue item with new information
            new_text = task_edit.toPlainText().strip()
            new_priority = priority_combo.currentText()
            new_steps = str(steps_spin.value())
            new_time = time_edit.text().strip()
            new_risk = risk_combo.currentText()
            
            # Update item text with priority
            display_text = f"{new_text} [{new_priority}]"
            
            # Update tree widget columns
            if hasattr(current_item, 'setText'):
                if hasattr(current_item, 'columnCount'):
                    # Tree widget item
                    current_item.setText(0, display_text)
                    current_item.setText(1, new_priority)
                    current_item.setText(2, f"{new_steps} steps")
                    current_item.setText(3, new_time)
                    current_item.setText(4, new_risk)
                else:
                    # List widget item
                    current_item.setText(display_text)
            
            # Set background color based on priority
            if new_priority == "High":
                current_item.setBackground(0, QtGui.QBrush(QtCore.Qt.red))
            elif new_priority == "Medium":
                current_item.setBackground(0, QtGui.QBrush(QtCore.Qt.yellow))
            else:  # Low
                current_item.setBackground(0, QtGui.QBrush(QtCore.Qt.green))
            
            print(f"Queue item updated: {new_text} with priority {new_priority}")
        
    def _update_queue_info(self):
        """Update queue statistics display."""
        total_items = self.queue_list.topLevelItemCount()
        visible_items = 0
        high_priority = 0
        medium_priority = 0
        low_priority = 0
        
        # Count visible items and priorities
        for i in range(total_items):
            item = self.queue_list.topLevelItem(i)
            if item and not item.isHidden():
                visible_items += 1
                
                # Count by priority
                item_text = item.text(0)
                if " [High]" in item_text:
                    high_priority += 1
                elif " [Low]" in item_text:
                    low_priority += 1
                else:
                    medium_priority += 1
        
        # Update stats label
        if hasattr(self, 'queue_stats_label'):
            if visible_items != total_items:
                stats_text = f"{visible_items}/{total_items} tasks (H:{high_priority} M:{medium_priority} L:{low_priority})"
            else:
                stats_text = f"{total_items} tasks (H:{high_priority} M:{medium_priority} L:{low_priority})"
            self.queue_stats_label.setText(stats_text)
        
    def _remove_queue_item(self):
        """Remove selected queue item."""
        current_item = self.queue_list.currentItem()
        if current_item:
            row = self.queue_list.row(current_item)
            self.queue_list.takeItem(row)
            print(f"Removed queue item at row {row}")
        else:
            print("No queue item selected for removal")
        
    def _set_task_priority(self):
        """Set priority for selected task."""
        current_row = self.queue_list.currentRow()
        if current_row < 0:
            QtWidgets.QMessageBox.information(
                self, "No Selection", "Please select a task to set priority."
            )
            return
        
        # Get current item
        current_item = self.queue_list.item(current_row)
        if not current_item:
            return
        
        # Create priority setting dialog
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Set Task Priority")
        dialog.setMinimumSize(300, 150)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # Task info
        layout.addWidget(QtWidgets.QLabel(f"Task: {current_item.text()}"))
        
        # Priority selection
        priority_layout = QtWidgets.QHBoxLayout()
        priority_layout.addWidget(QtWidgets.QLabel("Priority:"))
        
        priority_combo = QtWidgets.QComboBox()
        priority_combo.addItems(["High", "Medium", "Low"])
        priority_combo.setCurrentText("Medium")  # Default
        priority_layout.addWidget(priority_combo)
        
        layout.addLayout(priority_layout)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        ok_btn = QtWidgets.QPushButton("OK")
        cancel_btn = QtWidgets.QPushButton("Cancel")
        
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        # Execute dialog
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            priority = priority_combo.currentText()
            
            # Update item text with priority
            original_text = current_item.text()
            # Remove existing priority if present
            if " [" in original_text and original_text.endswith("]"):
                original_text = original_text.split(" [")[0]
            
            new_text = f"{original_text} [{priority}]"
            current_item.setText(new_text)
            
            # Set color based on priority
            if priority == "High":
                current_item.setBackground(QtCore.Qt.red)
            elif priority == "Medium":
                current_item.setBackground(QtCore.Qt.yellow)
            else:  # Low
                current_item.setBackground(QtCore.Qt.green)
            
            print(f"Task priority set to {priority}")
        
    def _export_settings(self):
        """Export current agent settings."""
        # Get file path from user
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export Agent Settings",
            "agent_settings.json",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if not filename:
            return
        
        try:
            # Collect current settings
            settings = {
                "export_timestamp": QtCore.QDateTime.currentDateTime().toString(),
                "queue_items": [],
                "execution_state": {
                    "running": getattr(self, 'execution_running', False),
                    "current_task_id": getattr(self, 'current_task_id', None)
                },
                "ui_settings": {
                    "queue_count": self.queue_list.count()
                }
            }
            
            # Export queue items with their properties
            for i in range(self.queue_list.count()):
                item = self.queue_list.item(i)
                if item:
                    item_data = {
                        "text": item.text(),
                        "background_color": item.background().color().name() if item.background() != QtCore.Qt.NoBrush else None
                    }
                    settings["queue_items"].append(item_data)
            
            # Write to file
            import json
            with open(filename, 'w') as f:
                json.dump(settings, f, indent=2)
            
            QtWidgets.QMessageBox.information(
                self, "Export Complete", f"Settings exported to {filename}"
            )
            print(f"Settings exported to {filename}")
            
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, "Export Error", f"Failed to export settings: {str(e)}"
            )
            print(f"Export error: {e}")

    def _clear_queue(self):
        """Clear the task queue."""
        # Ask for confirmation before clearing
        reply = QtWidgets.QMessageBox.question(
            self, 
            "Clear Queue", 
            "Are you sure you want to clear all tasks from the queue?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            # Clear the queue list widget
            self.queue_list.clear()
            
            # Clear internal queue data if it exists
            if hasattr(self, 'task_queue'):
                self.task_queue.clear()
            
            # Update queue info
            self._update_queue_info()
            
            print("Queue cleared successfully")

    def _move_queue_item_up(self):
        """Move selected queue item up."""
        current_row = self.queue_list.currentRow()
        if current_row > 0:
            # Get the current item
            current_item = self.queue_list.takeItem(current_row)
            
            # Re-insert it one position up
            self.queue_list.insertItem(current_row - 1, current_item)
            
            # Update selection
            self.queue_list.setCurrentRow(current_row - 1)
            
            # Update internal queue data if it exists
            if hasattr(self, 'task_queue') and current_row < len(self.task_queue):
                task = self.task_queue.pop(current_row)
                self.task_queue.insert(current_row - 1, task)
            
            print(f"Moved queue item from position {current_row} to {current_row - 1}")
        else:
            print("Cannot move item up - already at top or no item selected")

    def _move_queue_item_down(self):
        """Move selected queue item down."""
        current_row = self.queue_list.currentRow()
        if current_row >= 0 and current_row < self.queue_list.count() - 1:
            # Get the current item
            current_item = self.queue_list.takeItem(current_row)
            
            # Re-insert it one position down
            self.queue_list.insertItem(current_row + 1, current_item)
            
            # Update selection
            self.queue_list.setCurrentRow(current_row + 1)
            
            # Update internal queue data if it exists
            if hasattr(self, 'task_queue') and current_row < len(self.task_queue):
                task = self.task_queue.pop(current_row)
                self.task_queue.insert(current_row + 1, task)
            
            print(f"Moved queue item from position {current_row} to {current_row + 1}")
        else:
            print("Cannot move item down - already at bottom or no item selected")

    def _send_command(self):
        """Send command to agent."""
        command = self.command_input.text().strip()
        if not command:
            return
            
        # Add command to history
        timestamp = datetime.now().strftime("%H:%M:%S")
        history_item = f"[{timestamp}] {command}"
        self.history_list.addItem(history_item)
        
        # Clear input
        self.command_input.clear()
        
        # Update status
        self.state_label.setText("Processing")
        self.operation_label.setText(command[:50] + "..." if len(command) > 50 else command)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # TODO: Send to agent manager when available
        if self.agent_manager:
            try:
                # Agent manager integration would go here
                print(f"Sending command to agent: {command}")
            except Exception as e:
                print(f"Error sending command: {e}")
        else:
            print(f"Agent manager not available. Command: {command}")
            
        # Simulate completion after a moment (remove when real integration is added)
        QtCore.QTimer.singleShot(2000, self._simulate_command_completion)

    def _simulate_command_completion(self):
        """Simulate command completion (remove when real integration is added)."""
        self.state_label.setText("Idle")
        self.operation_label.setText("None")
        self.progress_bar.setVisible(False)

    def _clear_history(self):
        """Clear execution history."""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear the execution history?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            self.history_list.clear()

    def set_agent_manager(self, agent_manager):
        """Set the agent manager reference."""
        self.agent_manager = agent_manager

    def set_provider_service(self, provider_service):
        """Set the provider service reference."""
        self.provider_service = provider_service
        
        if hasattr(self, 'provider_selector') and provider_service:
            self.provider_selector.set_provider_service(provider_service)
