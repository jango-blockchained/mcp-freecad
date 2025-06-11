"""Enhanced Agent Control Widget with Advanced Diagnostics and Management"""

from datetime import datetime
import json
import traceback

from PySide2 import QtCore, QtWidgets, QtGui

from .provider_selector_widget import ProviderSelectorWidget
from .theme_system import get_theme_manager, apply_theme_to_widget


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
                    status_lines.append(f"   ├─ Tool Registry: ✅ Available")
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

        # Header with theme selector
        self._create_header(layout)

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

    def _create_header(self, layout):
        """Create header with theme controls."""
        header_group = QtWidgets.QGroupBox()
        header_layout = QtWidgets.QHBoxLayout(header_group)
        
        # Main title
        title_label = QtWidgets.QLabel("🤖 Enhanced Agent Control Panel")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Theme selector
        theme_label = QtWidgets.QLabel("Theme:")
        header_layout.addWidget(theme_label)
        
        self.theme_combo = QtWidgets.QComboBox()
        self.theme_combo.addItems(["Light", "Dark", "Auto"])
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        header_layout.addWidget(self.theme_combo)
        
        layout.addWidget(header_group)

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
        self.play_pause_btn.clicked.connect(self._toggle_execution)
        primary_layout.addWidget(self.play_pause_btn)

        # Stop button
        self.stop_btn = QtWidgets.QPushButton("⏹ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_execution)
        primary_layout.addWidget(self.stop_btn)

        # Step button
        self.step_btn = QtWidgets.QPushButton("⏭ Step")
        self.step_btn.setEnabled(False)
        self.step_btn.setToolTip("Execute one step at a time")
        self.step_btn.clicked.connect(self._step_execution)
        primary_layout.addWidget(self.step_btn)

        primary_layout.addStretch()
        control_layout.addLayout(primary_layout)

        # Secondary controls
        secondary_layout = QtWidgets.QHBoxLayout()
        
        # Enhanced diagnostic button
        self.diagnostic_btn = QtWidgets.QPushButton("🔍 Advanced Diagnostics")
        self.diagnostic_btn.setToolTip("Open comprehensive diagnostic dialog")
        self.diagnostic_btn.clicked.connect(self._show_advanced_diagnostics)
        secondary_layout.addWidget(self.diagnostic_btn)

        # Quick status button
        self.quick_status_btn = QtWidgets.QPushButton("⚡ Quick Status")
        self.quick_status_btn.setToolTip("Show quick status overview")
        self.quick_status_btn.clicked.connect(self._show_quick_status)
        secondary_layout.addWidget(self.quick_status_btn)

        # Clear queue button
        self.clear_queue_btn = QtWidgets.QPushButton("🗑️ Clear Queue")
        self.clear_queue_btn.clicked.connect(self._clear_queue)
        secondary_layout.addWidget(self.clear_queue_btn)

        # Export settings button
        self.export_settings_btn = QtWidgets.QPushButton("📤 Export Settings")
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

    def _on_theme_changed(self, theme_name):
        """Handle theme change."""
        theme_manager = get_theme_manager()
        
        if theme_name == "Light":
            from .theme_system import Theme
            theme_manager.set_theme(Theme.LIGHT)
        elif theme_name == "Dark":
            from .theme_system import Theme
            theme_manager.set_theme(Theme.DARK)
        else:  # Auto
            from .theme_system import Theme
            theme_manager.set_theme(Theme.AUTO)
            
        # Re-apply theme to this widget
        apply_theme_to_widget(self)

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
        # TODO: Implement execution toggle
        print("Toggle execution called")

    def _stop_execution(self):
        """Stop current execution."""
        # TODO: Implement execution stop
        print("Stop execution called")

    def _step_execution(self):
        """Execute one step."""
        # TODO: Implement step execution
        print("Step execution called")

    # Additional methods for enhanced functionality

    # Placeholder methods for the rest of the enhanced functionality
    def _create_command_section(self, layout):
        """Create enhanced command input section."""
        # Implementation similar to original but with theme support
        pass
        
    def _create_status_section(self, layout):
        """Create enhanced status section.""" 
        # Implementation similar to original but with theme support
        pass
        
    def _create_enhanced_safety_section(self, layout):
        """Create enhanced safety settings."""
        # Implementation with additional safety features
        pass
        
    def _create_enhanced_history_section(self, layout):
        """Create enhanced history section with filtering."""
        # Implementation with search and filter capabilities
        pass

    # Additional methods for enhanced functionality
    def _filter_queue_by_priority(self, priority):
        """Filter queue display by priority."""
        # TODO: Implement queue filtering
        print(f"Filter queue by priority: {priority}")
        
    def _edit_queue_item(self):
        """Edit selected queue item."""
        # TODO: Implement queue item editing
        print("Edit queue item called")
        
    def _set_task_priority(self):
        """Set priority for selected task."""
        # TODO: Implement task priority setting
        print("Set task priority called")
        
    def _export_settings(self):
        """Export current agent settings."""
        # TODO: Implement settings export
        print("Export settings called")

    def _clear_queue(self):
        """Clear the task queue."""
        # TODO: Implement queue clearing
        print("Clear queue called")

    def _move_queue_item_up(self):
        """Move selected queue item up."""
        # TODO: Implement queue item reordering
        print("Move queue item up called")

    def _move_queue_item_down(self):
        """Move selected queue item down."""
        # TODO: Implement queue item reordering
        print("Move queue item down called")

    def _remove_queue_item(self):
        """Remove selected queue item."""
        # TODO: Implement queue item removal
        print("Remove queue item called")

    def set_agent_manager(self, agent_manager):
        """Set the agent manager reference."""
        self.agent_manager = agent_manager

    def set_provider_service(self, provider_service):
        """Set the provider service reference."""
        self.provider_service = provider_service
        
        if hasattr(self, 'provider_selector') and provider_service:
            self.provider_selector.set_provider_service(provider_service)
