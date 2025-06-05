"""Agent Control Widget - Control panel for autonomous agent execution"""

from PySide2 import QtCore, QtGui, QtWidgets
from datetime import datetime


class AgentControlWidget(QtWidgets.QWidget):
    """Widget for controlling agent execution and settings."""

    def __init__(self, parent=None):
        super(AgentControlWidget, self).__init__(parent)

        self.agent_manager = None
        self.current_plan = None
        self.execution_queue = []

        self._setup_ui()

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)

        # Header
        header = QtWidgets.QLabel("🤖 Agent Control Panel")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(header)

        # Execution Status
        self._create_status_section(layout)

        # Execution Controls
        self._create_control_section(layout)

        # Execution Queue
        self._create_queue_section(layout)

        # Safety Settings
        self._create_safety_section(layout)

        # Execution History
        self._create_history_section(layout)

        layout.addStretch()

    def _create_status_section(self, layout):
        """Create execution status section."""
        status_group = QtWidgets.QGroupBox("Execution Status")
        status_layout = QtWidgets.QVBoxLayout(status_group)

        # Current state
        state_layout = QtWidgets.QHBoxLayout()
        state_layout.addWidget(QtWidgets.QLabel("State:"))
        self.state_label = QtWidgets.QLabel("Idle")
        self.state_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                padding: 5px 10px;
                background-color: #f0f0f0;
                border-radius: 4px;
            }
        """)
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

    def _create_control_section(self, layout):
        """Create execution control section."""
        control_group = QtWidgets.QGroupBox("Execution Controls")
        control_layout = QtWidgets.QHBoxLayout(control_group)

        # Play/Pause button
        self.play_pause_btn = QtWidgets.QPushButton("▶️ Start")
        self.play_pause_btn.setEnabled(False)
        self.play_pause_btn.clicked.connect(self._toggle_execution)
        self.play_pause_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        control_layout.addWidget(self.play_pause_btn)

        # Stop button
        self.stop_btn = QtWidgets.QPushButton("⏹️ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_execution)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 15px;
                font-size: 14px;
            }
        """)
        control_layout.addWidget(self.stop_btn)

        # Step button
        self.step_btn = QtWidgets.QPushButton("⏭️ Step")
        self.step_btn.setEnabled(False)
        self.step_btn.setToolTip("Execute one step at a time")
        self.step_btn.clicked.connect(self._step_execution)
        control_layout.addWidget(self.step_btn)

        control_layout.addStretch()

        # Clear queue button
        self.clear_queue_btn = QtWidgets.QPushButton("🗑️ Clear Queue")
        self.clear_queue_btn.clicked.connect(self._clear_queue)
        control_layout.addWidget(self.clear_queue_btn)

        layout.addWidget(control_group)

    def _create_queue_section(self, layout):
        """Create execution queue section."""
        queue_group = QtWidgets.QGroupBox("Execution Queue")
        queue_layout = QtWidgets.QVBoxLayout(queue_group)

        # Queue list
        self.queue_list = QtWidgets.QListWidget()
        self.queue_list.setMaximumHeight(150)
        self.queue_list.setAlternatingRowColors(True)
        queue_layout.addWidget(self.queue_list)

        # Queue controls
        queue_controls = QtWidgets.QHBoxLayout()

        self.move_up_btn = QtWidgets.QPushButton("⬆️")
        self.move_up_btn.setToolTip("Move selected item up")
        self.move_up_btn.clicked.connect(self._move_queue_item_up)
        queue_controls.addWidget(self.move_up_btn)

        self.move_down_btn = QtWidgets.QPushButton("⬇️")
        self.move_down_btn.setToolTip("Move selected item down")
        self.move_down_btn.clicked.connect(self._move_queue_item_down)
        queue_controls.addWidget(self.move_down_btn)

        self.remove_item_btn = QtWidgets.QPushButton("❌")
        self.remove_item_btn.setToolTip("Remove selected item")
        self.remove_item_btn.clicked.connect(self._remove_queue_item)
        queue_controls.addWidget(self.remove_item_btn)

        queue_controls.addStretch()

        queue_layout.addLayout(queue_controls)

        layout.addWidget(queue_group)

    def _create_safety_section(self, layout):
        """Create safety settings section."""
        safety_group = QtWidgets.QGroupBox("Safety Settings")
        safety_layout = QtWidgets.QFormLayout(safety_group)

        # Approval required
        self.approval_check = QtWidgets.QCheckBox("Require approval before execution")
        self.approval_check.setChecked(False)
        self.approval_check.stateChanged.connect(self._update_safety_settings)
        safety_layout.addRow("Approval:", self.approval_check)

        # Auto rollback
        self.rollback_check = QtWidgets.QCheckBox("Auto-rollback on failure")
        self.rollback_check.setChecked(True)
        self.rollback_check.stateChanged.connect(self._update_safety_settings)
        safety_layout.addRow("Rollback:", self.rollback_check)

        # Safety checks
        self.safety_check = QtWidgets.QCheckBox("Enable safety checks")
        self.safety_check.setChecked(True)
        self.safety_check.stateChanged.connect(self._update_safety_settings)
        safety_layout.addRow("Safety:", self.safety_check)

        # Execution timeout
        self.timeout_spin = QtWidgets.QSpinBox()
        self.timeout_spin.setRange(10, 600)
        self.timeout_spin.setValue(300)
        self.timeout_spin.setSuffix(" seconds")
        self.timeout_spin.valueChanged.connect(self._update_safety_settings)
        safety_layout.addRow("Timeout:", self.timeout_spin)

        # Max retries
        self.retries_spin = QtWidgets.QSpinBox()
        self.retries_spin.setRange(0, 10)
        self.retries_spin.setValue(3)
        self.retries_spin.valueChanged.connect(self._update_safety_settings)
        safety_layout.addRow("Max Retries:", self.retries_spin)

        layout.addWidget(safety_group)

    def _create_history_section(self, layout):
        """Create execution history section."""
        history_group = QtWidgets.QGroupBox("Execution History")
        history_layout = QtWidgets.QVBoxLayout(history_group)

        # History list
        self.history_list = QtWidgets.QListWidget()
        self.history_list.setMaximumHeight(100)
        self.history_list.setAlternatingRowColors(True)
        history_layout.addWidget(self.history_list)

        # History controls
        history_controls = QtWidgets.QHBoxLayout()

        self.view_details_btn = QtWidgets.QPushButton("📋 View Details")
        self.view_details_btn.clicked.connect(self._view_history_details)
        history_controls.addWidget(self.view_details_btn)

        self.export_history_btn = QtWidgets.QPushButton("💾 Export")
        self.export_history_btn.clicked.connect(self._export_history)
        history_controls.addWidget(self.export_history_btn)

        self.clear_history_btn = QtWidgets.QPushButton("🗑️ Clear")
        self.clear_history_btn.clicked.connect(self._clear_history)
        history_controls.addWidget(self.clear_history_btn)

        history_controls.addStretch()

        history_layout.addLayout(history_controls)

        layout.addWidget(history_group)

    def set_agent_manager(self, agent_manager):
        """Set the agent manager reference."""
        self.agent_manager = agent_manager

        if self.agent_manager:
            # Register callbacks
            self.agent_manager.register_callback(
                "on_state_change",
                self._on_state_changed
            )
            self.agent_manager.register_callback(
                "on_execution_start",
                self._on_execution_start
            )
            self.agent_manager.register_callback(
                "on_execution_complete",
                self._on_execution_complete
            )
            self.agent_manager.register_callback(
                "on_plan_created",
                self._on_plan_created
            )

            # Load current settings
            self._load_agent_settings()
            
            # Update UI with current state
            self._update_ui_from_agent_state()

    def _update_ui_from_agent_state(self):
        """Update UI elements based on current agent state."""
        if not self.agent_manager:
            return
            
        # Update state display
        current_state = self.agent_manager.execution_state
        self._on_state_changed(None, current_state)
        
        # Update mode display
        current_mode = self.agent_manager.current_mode
        mode_text = "Chat Mode" if current_mode.value == "chat" else "Agent Mode"
        
        # Add mode indicator to header
        self.findChild(QtWidgets.QLabel).setText(f"🤖 Agent Control Panel - {mode_text}")
        
        # Show available tools info
        available_tools = self.agent_manager.get_available_tools()
        tool_count = sum(len(methods) for methods in available_tools.values())
        
        if tool_count > 0:
            self.state_label.setToolTip(f"Agent has access to {tool_count} tools across {len(available_tools)} categories")

    def _load_agent_settings(self):
        """Load current agent settings."""
        if not self.agent_manager:
            return

        config = self.agent_manager.config
        self.approval_check.setChecked(config.get("require_approval", False))
        self.rollback_check.setChecked(config.get("auto_rollback", True))
        self.safety_check.setChecked(config.get("safety_checks", True))
        self.timeout_spin.setValue(config.get("execution_timeout", 300))
        self.retries_spin.setValue(config.get("max_retries", 3))

    def _update_safety_settings(self):
        """Update safety settings in agent manager."""
        if not self.agent_manager:
            return

        config = {
            "require_approval": self.approval_check.isChecked(),
            "auto_rollback": self.rollback_check.isChecked(),
            "safety_checks": self.safety_check.isChecked(),
            "execution_timeout": self.timeout_spin.value(),
            "max_retries": self.retries_spin.value()
        }

        self.agent_manager.update_config(config)

    def _on_state_changed(self, old_state, new_state):
        """Handle agent state change."""
        state_text = new_state.value.title()
        self.state_label.setText(state_text)

        # Update state label style
        state_colors = {
            "idle": "#f0f0f0",
            "planning": "#fff3e0",
            "executing": "#e3f2fd",
            "paused": "#fff9c4",
            "error": "#ffcdd2",
            "completed": "#c8e6c9"
        }

        color = state_colors.get(new_state.value, "#f0f0f0")
        self.state_label.setStyleSheet(f"""
            QLabel {{
                font-weight: bold;
                padding: 5px 10px;
                background-color: {color};
                border-radius: 4px;
            }}
        """)

        # Update button states
        if new_state.value == "executing":
            self.play_pause_btn.setText("⏸️ Pause")
            self.play_pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            self.step_btn.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.operation_label.setText("Agent is executing...")
        elif new_state.value == "paused":
            self.play_pause_btn.setText("▶️ Resume")
            self.play_pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            self.step_btn.setEnabled(True)
            self.operation_label.setText("Execution paused")
        elif new_state.value == "planning":
            self.play_pause_btn.setText("⏳ Planning")
            self.play_pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.step_btn.setEnabled(False)
            self.operation_label.setText("Creating execution plan...")
        elif new_state.value == "error":
            self.play_pause_btn.setText("▶️ Start")
            self.play_pause_btn.setEnabled(len(self.execution_queue) > 0)
            self.stop_btn.setEnabled(False)
            self.step_btn.setEnabled(False)
            self.progress_bar.setVisible(False)
            self.operation_label.setText("Error occurred")
        else:
            self.play_pause_btn.setText("▶️ Start")
            self.play_pause_btn.setEnabled(len(self.execution_queue) > 0)
            self.stop_btn.setEnabled(False)
            self.step_btn.setEnabled(False)
            self.progress_bar.setVisible(False)
            if new_state.value == "completed":
                self.operation_label.setText("Execution completed")
            else:
                self.operation_label.setText("Ready")

    def _on_execution_start(self, step_num, total_steps, step):
        """Handle execution start."""
        step_desc = step.get('description', 'Unknown step')
        self.operation_label.setText(f"Step {step_num}/{total_steps}: {step_desc}")
        self.progress_bar.setMaximum(total_steps)
        self.progress_bar.setValue(step_num)

    def _on_execution_complete(self, step_num, total_steps, result):
        """Handle execution complete."""
        # Add to history
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Handle different result formats
        success = result.get("success", False)
        if hasattr(result.get("status"), 'value'):
            success = result["status"].value == "completed"
        
        status = "✅" if success else "❌"
        step_desc = result.get("output", f"Step {step_num}")
        history_item = f"{timestamp} - {status} {step_desc}"
        self.history_list.insertItem(0, history_item)

        # Keep history limited
        while self.history_list.count() > 50:
            self.history_list.takeItem(self.history_list.count() - 1)

    def _on_plan_created(self, plan):
        """Handle plan created callback."""
        # Automatically add plan to queue
        self.add_to_queue(plan)

    def add_to_queue(self, plan):
        """Add a plan to the execution queue."""
        self.execution_queue.append(plan)

        # Update queue display
        plan_id = plan.get('id', 'unknown')
        steps = plan.get('steps', [])
        duration = plan.get('estimated_duration', 0)
        risk = plan.get('risk_level', 'unknown')
        
        queue_item = f"Plan {plan_id[:8]}... ({len(steps)} steps, {duration:.1f}s, {risk} risk)"
        self.queue_list.addItem(queue_item)

        # Enable start button if idle
        if self.agent_manager and self.agent_manager.execution_state.value == "idle":
            self.play_pause_btn.setEnabled(True)

    def _toggle_execution(self):
        """Toggle execution play/pause."""
        if not self.agent_manager:
            return

        state = self.agent_manager.execution_state.value

        if state == "idle" and self.execution_queue:
            # Start execution
            plan = self.execution_queue.pop(0)
            self.queue_list.takeItem(0)
            plan_id = plan.get('id')
            if plan_id:
                # Check if approval is required
                if self.agent_manager.config.get("require_approval", False):
                    # The approval dialog will be shown by the conversation widget
                    # Here we just prepare for execution
                    pass
                else:
                    # Auto-approve and execute
                    self.agent_manager.approve_plan(plan_id)
        elif state == "executing":
            # Pause execution
            self.agent_manager.pause_execution()
        elif state == "paused":
            # Resume execution
            self.agent_manager.resume_execution()

    def _stop_execution(self):
        """Stop current execution."""
        if self.agent_manager:
            self.agent_manager.cancel_execution()

    def _step_execution(self):
        """Execute one step."""
        # This would require modification to the execution pipeline
        # to support single-step execution
        if self.agent_manager and self.agent_manager.execution_state.value == "paused":
            # For now, just resume (single step execution would need pipeline changes)
            self.agent_manager.resume_execution()

    def _clear_queue(self):
        """Clear the execution queue."""
        if self.execution_queue:
            reply = QtWidgets.QMessageBox.question(
                self,
                "Clear Queue",
                f"Are you sure you want to clear {len(self.execution_queue)} pending plans?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            
            if reply == QtWidgets.QMessageBox.Yes:
                self.execution_queue.clear()
                self.queue_list.clear()
                self.play_pause_btn.setEnabled(False)

    def _move_queue_item_up(self):
        """Move selected queue item up."""
        current_row = self.queue_list.currentRow()
        if current_row > 0:
            # Swap items
            item = self.queue_list.takeItem(current_row)
            self.queue_list.insertItem(current_row - 1, item)
            self.queue_list.setCurrentRow(current_row - 1)

            # Swap in execution queue
            self.execution_queue[current_row], self.execution_queue[current_row - 1] = \
                self.execution_queue[current_row - 1], self.execution_queue[current_row]

    def _move_queue_item_down(self):
        """Move selected queue item down."""
        current_row = self.queue_list.currentRow()
        if current_row < self.queue_list.count() - 1 and current_row >= 0:
            # Swap items
            item = self.queue_list.takeItem(current_row)
            self.queue_list.insertItem(current_row + 1, item)
            self.queue_list.setCurrentRow(current_row + 1)

            # Swap in execution queue
            self.execution_queue[current_row], self.execution_queue[current_row + 1] = \
                self.execution_queue[current_row + 1], self.execution_queue[current_row]

    def _remove_queue_item(self):
        """Remove selected queue item."""
        current_row = self.queue_list.currentRow()
        if current_row >= 0:
            # Get plan info for confirmation
            plan = self.execution_queue[current_row]
            plan_id = plan.get('id', 'unknown')[:8]
            
            reply = QtWidgets.QMessageBox.question(
                self,
                "Remove Plan",
                f"Remove plan {plan_id}... from queue?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            
            if reply == QtWidgets.QMessageBox.Yes:
                self.queue_list.takeItem(current_row)
                del self.execution_queue[current_row]

                # Disable start button if queue is empty
                if not self.execution_queue:
                    self.play_pause_btn.setEnabled(False)

    def _view_history_details(self):
        """View details of selected history item."""
        current_item = self.history_list.currentItem()
        if current_item and self.agent_manager:
            # Show detailed history dialog
            history = self.agent_manager.get_execution_history()
            
            if history:
                dialog = QtWidgets.QDialog(self)
                dialog.setWindowTitle("Execution History Details")
                dialog.resize(600, 400)
                
                layout = QtWidgets.QVBoxLayout(dialog)
                
                # Create text view
                text_view = QtWidgets.QTextEdit()
                text_view.setReadOnly(True)
                
                # Format history details
                details = ""
                for i, entry in enumerate(reversed(history)):  # Show newest first
                    details += f"=== Execution {len(history) - i} ===\n"
                    details += f"Timestamp: {entry.get('timestamp', 'Unknown')}\n"
                    
                    plan = entry.get('plan', {})
                    details += f"Plan ID: {plan.get('id', 'Unknown')}\n"
                    details += f"Steps: {len(plan.get('steps', []))}\n"
                    details += f"Risk Level: {plan.get('risk_level', 'Unknown')}\n"
                    
                    result = entry.get('result', {})
                    details += f"Success: {result.get('success', False)}\n"
                    
                    if result.get('errors'):
                        details += f"Errors: {', '.join(result['errors'])}\n"
                        
                    details += "\n"
                
                text_view.setPlainText(details)
                layout.addWidget(text_view)
                
                # Close button
                close_btn = QtWidgets.QPushButton("Close")
                close_btn.clicked.connect(dialog.accept)
                layout.addWidget(close_btn)
                
                dialog.exec_()

    def _export_history(self):
        """Export execution history."""
        if not self.agent_manager:
            return

        history = self.agent_manager.get_execution_history()
        
        if not history:
            QtWidgets.QMessageBox.information(
                self,
                "No History",
                "No execution history to export."
            )
            return

        # Show file dialog
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export Execution History",
            f"agent_execution_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json);;Text Files (*.txt)"
        )

        if filename:
            try:
                import json
                
                # Prepare export data
                export_data = {
                    "export_timestamp": datetime.now().isoformat(),
                    "agent_mode": self.agent_manager.current_mode.value,
                    "total_executions": len(history),
                    "agent_config": self.agent_manager.config,
                    "history": history
                }
                
                if filename.endswith('.json'):
                    with open(filename, 'w') as f:
                        json.dump(export_data, f, indent=2)
                else:
                    # Export as text
                    with open(filename, 'w') as f:
                        f.write(f"FreeCAD AI Agent Execution History\n")
                        f.write(f"Export Date: {export_data['export_timestamp']}\n")
                        f.write(f"Total Executions: {export_data['total_executions']}\n")
                        f.write(f"Agent Mode: {export_data['agent_mode']}\n\n")
                        
                        for i, entry in enumerate(history, 1):
                            f.write(f"=== Execution {i} ===\n")
                            f.write(f"Timestamp: {entry.get('timestamp', 'Unknown')}\n")
                            
                            plan = entry.get('plan', {})
                            f.write(f"Plan ID: {plan.get('id', 'Unknown')}\n")
                            f.write(f"Steps: {len(plan.get('steps', []))}\n")
                            
                            result = entry.get('result', {})
                            f.write(f"Success: {result.get('success', False)}\n")
                            
                            if result.get('errors'):
                                f.write(f"Errors: {', '.join(result['errors'])}\n")
                            f.write("\n")
                
                QtWidgets.QMessageBox.information(
                    self,
                    "Export Complete",
                    f"History exported to {filename}"
                )
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Export Error",
                    f"Failed to export history: {str(e)}"
                )

    def _clear_history(self):
        """Clear execution history."""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear the execution history?\n\nThis will clear the visual history list but not the agent's internal history.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            self.history_list.clear()
            # Note: This doesn't clear the agent manager's history
            # That would require adding a method to the agent manager
            
    def get_queue_status(self):
        """Get current queue status."""
        return {
            "queue_length": len(self.execution_queue),
            "queue_items": [
                {
                    "plan_id": plan.get('id', 'unknown')[:8],
                    "steps": len(plan.get('steps', [])),
                    "risk_level": plan.get('risk_level', 'unknown'),
                    "estimated_duration": plan.get('estimated_duration', 0)
                }
                for plan in self.execution_queue
            ]
        }
