"""Conversation Widget - Clean AI Conversation Interface"""

from PySide2 import QtCore, QtGui, QtWidgets


class ConversationWidget(QtWidgets.QWidget):
    """Widget for AI conversation interface only."""

    # Signals
    message_sent = QtCore.Signal(str, str)  # provider, message

    def __init__(self, parent=None):
        super(ConversationWidget, self).__init__(parent)

        # Initialize services
        self.ai_manager = None
        self.config_manager = None
        self.provider_service = None
        self.agent_manager = None
        self.conversation_history = []
        self.current_provider = None
        self.current_mode = None

        # Execution tracking
        self.current_execution = None
        self.execution_widget = None

        self._setup_services()
        self._setup_ui()
        self._load_providers_fallback()

    def _setup_services(self):
        """Setup AI manager and config manager."""
        try:
            from ..ai.ai_manager import AIManager

            self.ai_manager = AIManager()
        except ImportError:
            self.ai_manager = None

        # Try multiple import strategies for config manager
        try:
            from ..config.config_manager import ConfigManager

            self.config_manager = ConfigManager()
        except ImportError:
            try:
                from config.config_manager import ConfigManager

                self.config_manager = ConfigManager()
            except ImportError:
                self.config_manager = None

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Create sections
        self._create_provider_selection(layout)
        self._create_conversation_display(layout)
        self._create_message_input(layout)
        self._create_conversation_controls(layout)

    def _create_provider_selection(self, layout):
        """Create provider selection section."""
        provider_group = QtWidgets.QGroupBox("Active Provider")
        provider_layout = QtWidgets.QHBoxLayout(provider_group)

        provider_layout.addWidget(QtWidgets.QLabel("Provider:"))

        self.provider_combo = QtWidgets.QComboBox()
        self.provider_combo.setMinimumWidth(200)
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        provider_layout.addWidget(self.provider_combo)

        # Provider status
        self.provider_status_label = QtWidgets.QLabel("Not Connected")
        self.provider_status_label.setStyleSheet(
            "color: red; font-weight: bold; padding: 5px;"
        )
        provider_layout.addWidget(self.provider_status_label)

        # Refresh button for debugging
        self.refresh_providers_btn = QtWidgets.QPushButton("⟳")
        self.refresh_providers_btn.setMaximumWidth(35)
        self.refresh_providers_btn.setToolTip("Refresh providers list")
        self.refresh_providers_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
                padding: 2px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f5f5f5;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-color: #999;
            }
        """)
        self.refresh_providers_btn.clicked.connect(self.refresh_providers)
        provider_layout.addWidget(self.refresh_providers_btn)

        # Debug button
        self.debug_providers_btn = QtWidgets.QPushButton("DBG")
        self.debug_providers_btn.setMaximumWidth(35)
        self.debug_providers_btn.setToolTip("Debug provider status")
        self.debug_providers_btn.setStyleSheet("""
            QPushButton {
                font-size: 10px;
                font-weight: bold;
                padding: 2px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f5f5f5;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-color: #999;
            }
        """)
        self.debug_providers_btn.clicked.connect(self._debug_providers)
        provider_layout.addWidget(self.debug_providers_btn)

        provider_layout.addStretch()

        # Quick settings
        self.context_check = QtWidgets.QCheckBox("Use CAD Context")
        self.context_check.setChecked(True)
        self.context_check.setToolTip(
            "Include current FreeCAD document state in AI queries"
        )
        provider_layout.addWidget(self.context_check)

        layout.addWidget(provider_group)

    def _create_conversation_display(self, layout):
        """Create conversation display section."""
        conversation_group = QtWidgets.QGroupBox("Conversation")
        conversation_layout = QtWidgets.QVBoxLayout(conversation_group)

        # Conversation display
        self.conversation_text = QtWidgets.QTextEdit()
        self.conversation_text.setMinimumHeight(300)
        self.conversation_text.setReadOnly(True)
        self.conversation_text.setStyleSheet(
            """
            QTextEdit {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                font-size: 12px;
                background-color: #fafafa;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
            }
        """
        )
        conversation_layout.addWidget(self.conversation_text)

        layout.addWidget(conversation_group)

    def _create_message_input(self, layout):
        """Create message input section."""
        input_group = QtWidgets.QGroupBox("Send Message")
        input_layout = QtWidgets.QVBoxLayout(input_group)

        # Message input area
        message_layout = QtWidgets.QHBoxLayout()

        self.message_input = QtWidgets.QLineEdit()
        self.message_input.setPlaceholderText("Ask the AI about FreeCAD operations...")
        self.message_input.setStyleSheet("QLineEdit { padding: 8px; font-size: 12px; }")
        message_layout.addWidget(self.message_input)

        self.send_btn = QtWidgets.QPushButton("Send")
        self.send_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """
        )
        message_layout.addWidget(self.send_btn)

        input_layout.addLayout(message_layout)

        # Execution controls (visible in agent mode)
        self.execution_controls = QtWidgets.QWidget()
        exec_layout = QtWidgets.QHBoxLayout(self.execution_controls)
        exec_layout.setContentsMargins(0, 5, 0, 0)

        self.pause_btn = QtWidgets.QPushButton("⏸️ Pause")
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self._pause_execution)
        exec_layout.addWidget(self.pause_btn)

        self.resume_btn = QtWidgets.QPushButton("▶️ Resume")
        self.resume_btn.setEnabled(False)
        self.resume_btn.clicked.connect(self._resume_execution)
        exec_layout.addWidget(self.resume_btn)

        self.cancel_btn = QtWidgets.QPushButton("⏹️ Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_execution)
        exec_layout.addWidget(self.cancel_btn)

        exec_layout.addStretch()

        self.execution_controls.setVisible(False)
        input_layout.addWidget(self.execution_controls)

        # Quick action buttons
        quick_actions_layout = QtWidgets.QHBoxLayout()

        quick_actions_layout.addWidget(QtWidgets.QLabel("Quick Actions:"))

        self.explain_btn = QtWidgets.QPushButton("Explain Current Model")
        self.explain_btn.setToolTip(
            "Ask AI to explain the currently active FreeCAD model"
        )
        self.explain_btn.clicked.connect(
            lambda: self._send_quick_message(
                "Please explain the current FreeCAD model and its components."
            )
        )
        quick_actions_layout.addWidget(self.explain_btn)

        self.suggest_btn = QtWidgets.QPushButton("Suggest Improvements")
        self.suggest_btn.setToolTip(
            "Ask AI for suggestions to improve the current model"
        )
        self.suggest_btn.clicked.connect(
            lambda: self._send_quick_message(
                "What improvements or modifications would you suggest for this FreeCAD model?"
            )
        )
        quick_actions_layout.addWidget(self.suggest_btn)

        self.help_btn = QtWidgets.QPushButton("General Help")
        self.help_btn.setToolTip("Get general FreeCAD help")
        self.help_btn.clicked.connect(
            lambda: self._send_quick_message(
                "I'm working with FreeCAD. Can you provide some general tips and guidance?"
            )
        )
        quick_actions_layout.addWidget(self.help_btn)

        quick_actions_layout.addStretch()
        input_layout.addLayout(quick_actions_layout)

        layout.addWidget(input_group)

        # Connect signals
        self.message_input.returnPressed.connect(self._on_send_message)
        self.send_btn.clicked.connect(self._on_send_message)

    def _create_conversation_controls(self, layout):
        """Create conversation controls section."""
        controls_layout = QtWidgets.QHBoxLayout()

        # History and management
        self.history_btn = QtWidgets.QPushButton("View History")
        self.history_btn.setToolTip("View conversation history")
        self.history_btn.clicked.connect(self._view_history)
        controls_layout.addWidget(self.history_btn)

        self.clear_btn = QtWidgets.QPushButton("Clear")
        self.clear_btn.setToolTip("Clear current conversation")
        self.clear_btn.clicked.connect(self._clear_conversation)
        controls_layout.addWidget(self.clear_btn)

        self.save_btn = QtWidgets.QPushButton("Save")
        self.save_btn.setToolTip("Save conversation to file")
        self.save_btn.clicked.connect(self._save_conversation)
        controls_layout.addWidget(self.save_btn)

        controls_layout.addStretch()

        # Usage stats
        self.usage_label = QtWidgets.QLabel("Messages: 0")
        self.usage_label.setStyleSheet("color: #666; font-style: italic;")
        controls_layout.addWidget(self.usage_label)

        layout.addLayout(controls_layout)

    def _on_provider_changed(self, provider_name):
        """Handle provider selection change."""
        if provider_name:
            self.current_provider = provider_name
            self._update_provider_status()
            self._add_system_message(f"Switched to provider: {provider_name}")

    def _update_provider_status(self):
        """Update provider status display."""
        if self.current_provider:
            # Check if provider is active
            if self.provider_service:
                providers = self.provider_service.get_all_providers()
                provider_info = providers.get(self.current_provider)
                if provider_info:
                    status = provider_info.get("status", "unknown")
                    if status == "connected":
                        self.provider_status_label.setText("Connected")
                        self.provider_status_label.setStyleSheet(
                            "color: green; font-weight: bold; padding: 5px;"
                        )
                        self.send_btn.setEnabled(True)
                    elif status == "initialized":
                        self.provider_status_label.setText("Ready")
                        self.provider_status_label.setStyleSheet(
                            "color: blue; font-weight: bold; padding: 5px;"
                        )
                        self.send_btn.setEnabled(True)
                    elif status == "testing":
                        self.provider_status_label.setText("Testing...")
                        self.provider_status_label.setStyleSheet(
                            "color: orange; font-weight: bold; padding: 5px;"
                        )
                        self.send_btn.setEnabled(False)
                    elif status == "error":
                        self.provider_status_label.setText("Error")
                        self.provider_status_label.setStyleSheet(
                            "color: red; font-weight: bold; padding: 5px;"
                        )
                        self.send_btn.setEnabled(False)
                    else:
                        self.provider_status_label.setText("Connecting...")
                        self.provider_status_label.setStyleSheet(
                            "color: orange; font-weight: bold; padding: 5px;"
                        )
                        self.send_btn.setEnabled(False)
                else:
                    self.provider_status_label.setText("Not Available")
                    self.provider_status_label.setStyleSheet(
                        "color: red; font-weight: bold; padding: 5px;"
                    )
                    self.send_btn.setEnabled(False)
            else:
                # Fallback if no provider service - check if we have config
                if self.config_manager:
                    api_key = self.config_manager.get_api_key(
                        self.current_provider.lower()
                    )
                    if api_key:
                        self.provider_status_label.setText("Configured")
                        self.provider_status_label.setStyleSheet(
                            "color: blue; font-weight: bold; padding: 5px;"
                        )
                        self.send_btn.setEnabled(True)
                    else:
                        self.provider_status_label.setText("Not Configured")
                        self.provider_status_label.setStyleSheet(
                            "color: red; font-weight: bold; padding: 5px;"
                        )
                        self.send_btn.setEnabled(False)
                else:
                    self.provider_status_label.setText("Service Unavailable")
                    self.provider_status_label.setStyleSheet(
                        "color: red; font-weight: bold; padding: 5px;"
                    )
                    self.send_btn.setEnabled(False)
        else:
            self.provider_status_label.setText("No Provider")
            self.provider_status_label.setStyleSheet(
                "color: red; font-weight: bold; padding: 5px;"
            )
            self.send_btn.setEnabled(False)

    def _load_providers_fallback(self):
        """Load providers directly from config if service is not available."""
        if not self.config_manager:
            return

        try:
            # Get configured API keys as a fallback
            api_keys = self.config_manager.list_api_keys()
            if api_keys:
                for provider_key in api_keys:
                    # Normalize provider names for display
                    display_name = self._get_provider_display_name(provider_key)
                    if self.provider_combo.findText(display_name) == -1:
                        self.provider_combo.addItem(display_name)

                # Set default provider
                default_provider = self.config_manager.get_default_provider()
                if default_provider:
                    index = self.provider_combo.findText(default_provider)
                    if index >= 0:
                        self.provider_combo.setCurrentIndex(index)

        except Exception as e:
            print(f"Error loading providers fallback: {e}")

    def _get_provider_display_name(self, provider_key: str) -> str:
        """Get display name for provider."""
        name_map = {
            "anthropic": "Anthropic",
            "openai": "OpenAI",
            "google": "Google",
            "openrouter": "OpenRouter",
        }
        return name_map.get(provider_key.lower(), provider_key.title())

    def _debug_providers(self):
        """Debug provider status and configuration."""
        debug_info = []
        debug_info.append("=== PROVIDER DEBUG INFO ===")
        debug_info.append(f"Current Provider: {self.current_provider}")
        debug_info.append(
            f"Provider Service Available: {self.provider_service is not None}"
        )
        debug_info.append(
            f"Config Manager Available: {self.config_manager is not None}"
        )
        debug_info.append(f"AI Manager Available: {self.ai_manager is not None}")
        debug_info.append("")

        # Provider combo box contents
        debug_info.append("Provider Combo Box Contents:")
        for i in range(self.provider_combo.count()):
            debug_info.append(f"  {i}: {self.provider_combo.itemText(i)}")
        debug_info.append("")

        # Provider service status
        if self.provider_service:
            debug_info.append("Provider Service Status:")
            all_providers = self.provider_service.get_all_providers()
            for name, status in all_providers.items():
                debug_info.append(f"  {name}: {status}")
            debug_info.append("")

        # Config manager status
        if self.config_manager:
            debug_info.append("Config Manager Status:")
            api_keys = self.config_manager.list_api_keys()
            debug_info.append(f"  API Keys: {api_keys}")
            default_provider = self.config_manager.get_default_provider()
            debug_info.append(f"  Default Provider: {default_provider}")
            debug_info.append("")

        # AI manager status
        if self.ai_manager:
            debug_info.append("AI Manager Status:")
            debug_info.append(f"  Providers: {list(self.ai_manager.providers.keys())}")
            debug_info.append(f"  Active Provider: {self.ai_manager.active_provider}")

        # Show debug dialog
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Provider Debug Information")
        dialog.resize(600, 400)

        layout = QtWidgets.QVBoxLayout(dialog)

        text_edit = QtWidgets.QTextEdit()
        text_edit.setPlainText("\n".join(debug_info))
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("font-family: monospace; font-size: 10px;")
        layout.addWidget(text_edit)

        button_layout = QtWidgets.QHBoxLayout()

        refresh_btn = QtWidgets.QPushButton("Refresh Providers")
        refresh_btn.clicked.connect(lambda: (self.refresh_providers(), dialog.accept()))
        button_layout.addWidget(refresh_btn)

        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)
        dialog.exec_()

    def _on_send_message(self):
        """Handle send message button click."""
        message = self.message_input.text().strip()
        if not message:
            return

        if not self.current_provider:
            QtWidgets.QMessageBox.warning(
                self, "Error", "Please select an AI provider first"
            )
            return

        self._send_message(message)

    def _send_quick_message(self, message):
        """Send a predefined quick message."""
        if not self.current_provider:
            QtWidgets.QMessageBox.warning(
                self, "Error", "Please select an AI provider first"
            )
            return

        self._send_message(message)

    def _send_message(self, message):
        """Send message to AI provider or agent."""
        if not message:
            return

        # Clear input
        self.message_input.clear()

        # Add user message to conversation
        self._add_conversation_message("You", message)

        # Show thinking indicator
        self._add_thinking_indicator()

        # Update usage count
        self.conversation_history.append({
            "sender": "You",
            "message": message,
            "timestamp": QtCore.QDateTime.currentDateTime().toString()
        })
        self.usage_label.setText(f"Messages: {len(self.conversation_history)}")

        # Process based on current mode
        if self.current_mode and str(self.current_mode).endswith("AGENT"):
            # Agent mode - use agent manager
            self._process_with_agent(message)
        else:
            # Chat mode - direct AI response
            self._process_with_chat(message)

    def _process_with_chat(self, message):
        """Process message in chat mode."""
        try:
            # Gather context if enabled
            context = {}
            if self.context_check.isChecked():
                context = self._gather_freecad_context()

            if self.agent_manager:
                # Use agent manager for chat mode processing
                response = self.agent_manager.process_message(message, context)
                self._handle_agent_response(response)
            else:
                # Fallback to direct provider communication
                self._send_to_provider(message, context)
                
        except Exception as e:
            self._remove_thinking_indicator()
            self._add_system_message(f"Error in chat mode: {str(e)}")

    def _send_to_provider(self, message, context):
        """Send message directly to AI provider (fallback method)."""
        if not self.current_provider:
            self._remove_thinking_indicator()
            self._add_system_message("No provider selected")
            return

        try:
            # Build context message
            context_text = ""
            if context and context.get("freecad_state"):
                freecad_state = context["freecad_state"]
                if freecad_state.get("has_active_document"):
                    context_text += f"\nFreeCAD Context:\n"
                    context_text += f"- Active document: {freecad_state.get('document_name', 'Unknown')}\n"
                    
                    if freecad_state.get("selected_objects"):
                        context_text += f"- Selected objects: {len(freecad_state['selected_objects'])}\n"
                        for obj in freecad_state["selected_objects"][:3]:  # Show first 3
                            context_text += f"  * {obj['name']} ({obj['type']})\n"
                    
                    if freecad_state.get("document_objects"):
                        context_text += f"- Total objects in document: {len(freecad_state['document_objects'])}\n"

            full_message = message + context_text
            
            # Simulate AI response (in real implementation, this would call the actual provider)
            self._simulate_ai_response(full_message)
            
        except Exception as e:
            self._remove_thinking_indicator()
            self._add_system_message(f"Error communicating with provider: {str(e)}")

    def _process_with_agent(self, message):
        """Process message through agent manager."""
        if not self.agent_manager:
            self._remove_thinking_indicator()
            self._add_system_message("Agent manager not available")
            return

        # Gather context if enabled
        context = {}
        if self.context_check.isChecked():
            context = self._gather_freecad_context()

        # Set AI provider if available
        if self.provider_service and self.current_provider:
            try:
                provider = self.provider_service.get_provider(self.current_provider)
                if provider:
                    self.agent_manager.set_ai_provider(provider)
            except Exception as e:
                print(f"Warning: Could not set AI provider: {e}")

        # Process message
        try:
            response = self.agent_manager.process_message(message, context)
            self._handle_agent_response(response)
        except Exception as e:
            self._remove_thinking_indicator()
            self._add_system_message(f"Error processing message: {str(e)}")

    def _handle_agent_response(self, response):
        """Handle response from agent manager."""
        mode = response.get("mode", "unknown")

        if mode == "chat":
            # Chat mode - display instructions
            self._remove_thinking_indicator()

            instructions = response.get("instructions", [])
            if instructions:
                self._add_conversation_message("AI", "Here's how to do that:")
                for instruction in instructions:
                    if instruction.strip():  # Skip empty instructions
                        self._add_conversation_message("AI", instruction)

            # Show suggested tools
            suggested_tools = response.get("suggested_tools", [])
            if suggested_tools:
                tool_names = [tool.get('name', tool.get('id', 'Unknown')) for tool in suggested_tools]
                self._add_conversation_message("AI", f"\nSuggested tools: {', '.join(tool_names)}")
                
                # Add helpful tip about agent mode
                self._add_conversation_message("AI", 
                    "\n💡 Tip: Switch to Agent mode to have me execute these tools automatically!")

        elif mode == "agent":
            # Agent mode - show execution plan and progress
            self._remove_thinking_indicator()

            plan = response.get("plan")
            if plan:
                self._display_execution_plan(plan)

            # Check if approval required
            if response.get("approval_required"):
                self._show_approval_dialog(plan)
            else:
                # Show execution result
                execution_result = response.get("execution_result")
                if execution_result:
                    self._display_execution_result(execution_result)
                    
        # Handle errors
        if response.get("error"):
            self._add_conversation_message("AI", f"❌ Error: {response['error']}")

    def _display_execution_plan(self, plan):
        """Display the execution plan."""
        self._add_conversation_message("AI", f"📋 Execution Plan (ID: {plan['id'][:8]}...)")

        # Display plan summary
        step_count = len(plan.get("steps", []))
        duration = plan.get("estimated_duration", 0)
        risk = plan.get("risk_level", "unknown")
        
        self._add_conversation_message("AI", 
            f"📊 Plan Summary: {step_count} steps, ~{duration:.1f}s, {risk} risk")

        # Display plan steps
        for step in plan.get("steps", []):
            step_text = f"  {step['order']}. {step['description']}"
            if step.get("parameters"):
                param_summary = ", ".join([f"{k}={v}" for k, v in step["parameters"].items()])
                step_text += f" ({param_summary})"
            self._add_conversation_message("AI", step_text)

    def _display_execution_result(self, result):
        """Display execution result."""
        if result.get("success"):
            self._add_conversation_message("AI", "✅ Execution completed successfully!")
            
            # Show executed steps count
            executed_count = len(result.get("executed_steps", []))
            if executed_count > 0:
                self._add_conversation_message("AI", f"✓ Completed {executed_count} steps")

            # Show outputs
            outputs = result.get("outputs", [])
            if outputs:
                for output in outputs:
                    if output:  # Skip empty outputs
                        self._add_conversation_message("AI", f"📤 Output: {output}")
        else:
            self._add_conversation_message("AI", "❌ Execution failed")

            # Show errors
            errors = result.get("errors", [])
            if errors:
                for error in errors:
                    if error:  # Skip empty errors
                        self._add_conversation_message("AI", f"🚨 Error: {error}")

            # Show failed step
            failed_step = result.get("failed_step")
            if failed_step:
                step_desc = failed_step.get("description", "Unknown step")
                self._add_conversation_message("AI", f"❌ Failed at: {step_desc}")
                
            # Suggest troubleshooting
            self._add_conversation_message("AI", 
                "💡 Try: Check object selection, verify parameters, or switch to Chat mode for manual steps")

    def _show_approval_dialog(self, plan):
        """Show approval dialog for execution plan."""
        dialog = QtWidgets.QMessageBox(self)
        dialog.setWindowTitle("Approve Execution Plan")
        dialog.setText(f"The AI has created an execution plan with {len(plan.get('steps', []))} steps.")
        dialog.setInformativeText("Do you want to proceed with the execution?")
        dialog.setDetailedText(self._format_plan_details(plan))
        dialog.setStandardButtons(
            QtWidgets.QMessageBox.Yes |
            QtWidgets.QMessageBox.No |
            QtWidgets.QMessageBox.Cancel
        )
        dialog.setDefaultButton(QtWidgets.QMessageBox.Yes)

        result = dialog.exec_()

        if result == QtWidgets.QMessageBox.Yes:
            if self.agent_manager:
                self.agent_manager.approve_plan(plan["id"])
                self._add_system_message("✅ Execution approved - starting...")
                # Show execution controls
                self.execution_controls.setVisible(True)
        elif result == QtWidgets.QMessageBox.No:
            if self.agent_manager:
                self.agent_manager.reject_plan(plan["id"])
                self._add_system_message("❌ Execution rejected")
        else:
            self._add_system_message("🚫 Execution cancelled")

    def _format_plan_details(self, plan):
        """Format plan details for display."""
        details = f"Plan ID: {plan.get('id', 'Unknown')}\n"
        details += f"Risk Level: {plan.get('risk_level', 'Unknown')}\n"
        details += f"Estimated Duration: {plan.get('estimated_duration', 0):.1f}s\n\n"
        details += "Steps:\n"

        for step in plan.get("steps", []):
            details += f"{step.get('order', '?')}. {step.get('tool', 'Unknown')}: {step.get('description', 'No description')}\n"
            parameters = step.get("parameters", {})
            if parameters:
                for param, value in parameters.items():
                    details += f"   - {param}: {value}\n"

        return details

    def set_agent_mode(self, mode):
        """Set the agent mode."""
        self.current_mode = mode

        # Update UI based on mode
        if str(mode).endswith("CHAT"):
            self._add_system_message("💬 Switched to Chat Mode - AI will provide instructions")
            if self.context_check:
                self.context_check.setToolTip("Include current FreeCAD document state in AI queries for better instructions")
            # Hide execution controls in chat mode
            self.execution_controls.setVisible(False)
            # Update send button text
            self.send_btn.setText("Ask AI")
        else:
            self._add_system_message("🤖 Switched to Agent Mode - AI will execute tools autonomously")
            if self.context_check:
                self.context_check.setToolTip("Include current FreeCAD document state for autonomous execution")
            # Show execution controls in agent mode if needed
            # (will be shown when execution starts)
            # Update send button text
            self.send_btn.setText("Execute")

    def _on_execution_start(self, step_num, total_steps, step):
        """Handle execution start callback."""
        self._add_system_message(f"▶️ Executing step {step_num}/{total_steps}: {step.get('description', 'Unknown step')}")

        # Enable execution controls
        if step_num == 1:  # First step
            self.execution_controls.setVisible(True)
            self.pause_btn.setEnabled(True)
            self.cancel_btn.setEnabled(True)
            self.resume_btn.setEnabled(False)

    def _on_execution_complete(self, step_num, total_steps, result):
        """Handle execution complete callback."""
        status = result.get("status")
        if hasattr(status, 'value'):
            status_val = status.value
        else:
            status_val = str(status)
            
        if status_val == "completed" or result.get("success"):
            self._add_system_message(f"✅ Step {step_num}/{total_steps} completed")
        else:
            error_msg = result.get("error", "Unknown error")
            self._add_system_message(f"❌ Step {step_num}/{total_steps} failed: {error_msg}")

        # Reset controls if this was the last step or execution failed
        if step_num == total_steps or not result.get("success"):
            self._reset_execution_controls()

    def _on_plan_created(self, plan):
        """Handle plan created callback."""
        step_count = len(plan.get("steps", []))
        self._add_system_message(f"📋 Created execution plan with {step_count} steps")

    def _pause_execution(self):
        """Pause the current execution."""
        if self.agent_manager:
            self.agent_manager.pause_execution()
            self._add_system_message("⏸️ Execution paused")
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(True)

    def _resume_execution(self):
        """Resume the paused execution."""
        if self.agent_manager:
            self.agent_manager.resume_execution()
            self._add_system_message("▶️ Execution resumed")
            self.pause_btn.setEnabled(True)
            self.resume_btn.setEnabled(False)

    def _cancel_execution(self):
        """Cancel the current execution."""
        if self.agent_manager:
            reply = QtWidgets.QMessageBox.question(
                self,
                "Cancel Execution",
                "Are you sure you want to cancel the current execution?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )

            if reply == QtWidgets.QMessageBox.Yes:
                self.agent_manager.cancel_execution()
                self._add_system_message("⏹️ Execution cancelled")
                self._reset_execution_controls()

    def _reset_execution_controls(self):
        """Reset execution control buttons."""
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        # Hide execution controls in chat mode
        if self.current_mode and str(self.current_mode).endswith("CHAT"):
            self.execution_controls.setVisible(False)

    def _add_conversation_message(self, sender, message):
        """Add message to conversation display."""
        from datetime import datetime

        timestamp = datetime.now().strftime("%H:%M")

        # Add to history
        self.conversation_history.append(
            {"sender": sender, "message": message, "timestamp": timestamp}
        )

        # Add message with formatting
        cursor = self.conversation_text.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)

        # Add sender with styling
        format_sender = QtGui.QTextCharFormat()
        if sender == "You":
            format_sender.setForeground(QtGui.QColor("#2196F3"))
        elif sender == "AI":
            format_sender.setForeground(QtGui.QColor("#4CAF50"))
        else:  # System
            format_sender.setForeground(QtGui.QColor("#FF9800"))
        format_sender.setFontWeight(QtGui.QFont.Bold)

        cursor.insertText(f"{sender} ({timestamp}): ", format_sender)
        cursor.insertText(f"{message}\n\n")

        # Auto-scroll to bottom
        self.conversation_text.moveCursor(QtGui.QTextCursor.End)

    def _add_system_message(self, message):
        """Add system message to conversation."""
        self._add_conversation_message("System", message)

    def _clear_conversation(self):
        """Clear conversation history."""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Clear Conversation",
            "Are you sure you want to clear the conversation history?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        )

        if reply == QtWidgets.QMessageBox.Yes:
            self.conversation_text.clear()
            self.conversation_history.clear()
            self.usage_label.setText("Messages: 0")
            self._add_system_message("Conversation cleared")

    def _save_conversation(self):
        """Save conversation to file."""
        if not self.conversation_history:
            QtWidgets.QMessageBox.information(self, "Info", "No conversation to save")
            return

        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save Conversation",
            f"freecad_ai_conversation_{self.current_provider or 'unknown'}_{QtCore.QDateTime.currentDateTime().toString('yyyyMMdd_HHmmss')}.txt",
            "Text Files (*.txt);;Markdown Files (*.md);;All Files (*)",
        )

        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"FreeCAD AI Conversation\n")
                    f.write(f"Provider: {self.current_provider or 'Unknown'}\n")
                    f.write(f"Date: {QtCore.QDateTime.currentDateTime().toString()}\n")
                    f.write("=" * 50 + "\n\n")

                    for entry in self.conversation_history:
                        f.write(
                            f"{entry['sender']} ({entry['timestamp']}): {entry['message']}\n\n"
                        )

                QtWidgets.QMessageBox.information(
                    self, "Success", f"Conversation saved to {filename}"
                )
            except Exception as e:
                QtWidgets.QMessageBox.warning(
                    self, "Error", f"Failed to save conversation: {str(e)}"
                )

    def _view_history(self):
        """View conversation history in a dialog."""
        dialog = ConversationHistoryDialog(self.conversation_history, self)
        dialog.exec_()

    def refresh_providers(self):
        """Refresh the provider list."""
        current_provider = self.provider_combo.currentText()
        self.provider_combo.clear()

        providers_found = False

        # Get providers from provider service first
        if self.provider_service:
            try:
                providers = self.provider_service.get_all_providers()
                for provider_name in providers.keys():
                    self.provider_combo.addItem(provider_name)
                    providers_found = True
            except Exception as e:
                print(f"Error getting providers from service: {e}")

        # Get providers from AI manager
        if self.ai_manager:
            try:
                for provider_name in self.ai_manager.providers.keys():
                    if self.provider_combo.findText(provider_name) == -1:
                        self.provider_combo.addItem(provider_name)
                        providers_found = True
            except Exception as e:
                print(f"Error getting providers from AI manager: {e}")

        # Fallback: load from config manager
        if not providers_found:
            self._load_providers_fallback()

        # Restore previous selection if available
        if current_provider:
            index = self.provider_combo.findText(current_provider)
            if index >= 0:
                self.provider_combo.setCurrentIndex(index)

        # Set default provider if no current selection
        if not current_provider and self.config_manager:
            try:
                default_provider = self.config_manager.get_default_provider()
                if default_provider:
                    index = self.provider_combo.findText(default_provider)
                    if index >= 0:
                        self.provider_combo.setCurrentIndex(index)
            except Exception as e:
                print(f"Error setting default provider: {e}")

        # Update status after refresh
        self._update_provider_status()

    def set_provider_service(self, provider_service):
        """Set the provider integration service."""
        self.provider_service = provider_service

        if provider_service:
            provider_service.provider_status_changed.connect(
                self._on_provider_status_changed
            )
            provider_service.providers_updated.connect(self.refresh_providers)

            # Initial refresh
            self.refresh_providers()

    def _on_provider_status_changed(
        self, provider_name: str, status: str, message: str
    ):
        """Handle provider status change."""
        if provider_name == self.current_provider:
            self._update_provider_status()
            if status == "connected":
                self._add_system_message(f"Provider {provider_name} connected")
            elif status == "error":
                self._add_system_message(f"Provider {provider_name} error: {message}")

    def get_conversation_history(self):
        """Get the conversation history."""
        return self.conversation_history.copy()

    def load_conversation_history(self, history):
        """Load conversation history from external source."""
        self.conversation_history = history.copy()
        self._rebuild_conversation_display()

    def _rebuild_conversation_display(self):
        """Rebuild conversation display from history."""
        self.conversation_text.clear()
        for entry in self.conversation_history:
            self._add_conversation_message(entry["sender"], entry["message"])

    def set_agent_manager(self, agent_manager):
        """Set the agent manager reference."""
        self.agent_manager = agent_manager

        # Register callbacks for execution updates
        if self.agent_manager:
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

    def _gather_freecad_context(self):
        """Gather current FreeCAD context."""
        context = {
            "timestamp": QtCore.QDateTime.currentDateTime().toString(),
            "has_active_document": False,
            "selected_objects": [],
            "document_objects": []
        }

        try:
            import FreeCAD
            import FreeCADGui

            # Check for active document
            if FreeCAD.ActiveDocument:
                context["has_active_document"] = True
                context["document_name"] = FreeCAD.ActiveDocument.Name
                context["document_label"] = FreeCAD.ActiveDocument.Label

                # Get all objects
                for obj in FreeCAD.ActiveDocument.Objects:
                    context["document_objects"].append({
                        "name": obj.Name,
                        "label": obj.Label,
                        "type": obj.TypeId
                    })

            # Get selected objects
            if FreeCADGui:
                selection = FreeCADGui.Selection.getSelection()
                for obj in selection:
                    context["selected_objects"].append({
                        "name": obj.Name,
                        "label": obj.Label,
                        "type": obj.TypeId
                    })

        except Exception as e:
            context["error"] = str(e)

        return context

    def _add_thinking_indicator(self):
        """Add the thinking indicator to conversation."""
        self.conversation_text.append("AI: Thinking...")

    def _remove_thinking_indicator(self):
        """Remove the thinking indicator from conversation."""
        text = self.conversation_text.toPlainText()
        if "AI: Thinking..." in text:
            # Find and remove the last "Thinking..." message
            lines = text.split("\n")
            for i in range(len(lines) - 1, -1, -1):
                if "AI" in lines[i] and "Thinking..." in lines[i]:
                    lines.pop(i)
                    if i < len(lines) and lines[i].strip() == "":
                        lines.pop(i)
                    break
            self.conversation_text.setPlainText("\n".join(lines))

    def _simulate_ai_response(self, user_message):
        """Simulate AI response with helpful FreeCAD guidance when no provider is available."""
        # Remove thinking indicator
        self._remove_thinking_indicator()

        # Analyze user message
        message_lower = user_message.lower()

        # Generate contextual FreeCAD-specific responses
        if any(word in message_lower for word in ["box", "cube", "rectangular"]):
            response = """To create a box/cube in FreeCAD:

**Method 1 - Using the Tools Widget:**
1. Go to the Tools tab
2. Click the □ (Box) icon under "Basic Shapes"
3. Enter dimensions:
   - Length, Width, Height (in mm)
   - Name (optional)

**Method 2 - Using Workbenches:**
1. Switch to Part Workbench (View → Workbench → Part)
2. Click Part → Primitives → Box
3. Set your dimensions in the dialog

**Pro tip:** For a perfect cube, use equal dimensions for all three values.

💡 Switch to Agent mode to have me create this automatically!"""

        elif any(word in message_lower for word in ["cylinder", "tube", "pipe", "rod"]):
            response = """To create a cylinder in FreeCAD:

**Basic Cylinder:**
1. Tools tab → Basic Shapes → ○ (Cylinder) icon
2. Parameters:
   - Radius: defines the width
   - Height: defines the length

**Hollow Cylinder (Tube):**
1. Tools tab → Advanced Shapes → ◎ (Tube) icon
2. You'll need:
   - Outer radius
   - Inner radius (thickness)
   - Height

**Tips:**
• For a pipe, make inner radius = outer radius - wall thickness
• For a solid rod, use regular cylinder
• You can create threads on cylinders using Advanced Shapes → Thread

💡 Switch to Agent mode for automatic execution!"""

        elif "sphere" in message_lower or "ball" in message_lower:
            response = """To create a sphere in FreeCAD:

1. **Using Tools Widget:**
   - Tools tab → Basic Shapes → ● (Sphere) icon
   - Enter radius (e.g., 25mm for a 50mm diameter ball)

2. **Creating half-sphere or dome:**
   - Create a full sphere first
   - Use Tools → Operations → Cut (−) with a box to cut it in half

3. **Ellipsoid (oval sphere):**
   - Tools → Advanced Shapes → ⬭ (Ellipsoid)
   - Set different radii for X, Y, Z axes

**Tip:** For a hollow sphere, create two spheres of different sizes and use Boolean Cut operation.

💡 Agent mode can handle this automatically!"""

        elif any(word in message_lower for word in ["car", "vehicle", "automobile"]):
            response = """I'll help you create a 3D car model in FreeCAD:

**Simple Car Approach:**
1. **Create the car body:** Box (100×50×30mm)
2. **Add the cabin:** Box (50×45×25mm), move on top
3. **Combine parts:** Union operation
4. **Add wheels:** 4 cylinders (radius=10mm, height=10mm)
5. **Position wheels:** Move to corners
6. **Round edges:** Fillet operation

**For Agent Mode:**
Just say "Create a simple car" and I'll execute all steps automatically!

Would you like detailed step-by-step instructions or prefer Agent mode execution?"""

        elif any(word in message_lower for word in ["measure", "dimension", "size"]):
            response = """FreeCAD measurement tools:

**Available Measurements:**
• ↔ **Distance**: Between points/edges
• ∠ **Angle**: Between edges/faces  
• ³ **Volume**: Total volume of objects
• ² **Area**: Surface area
• ━ **Length**: Edge/curve length
• ⌀ **Radius**: Circular edges
• ▭ **BBox**: Bounding box dimensions
• ⊕ **CoG**: Center of gravity

**How to measure:**
1. Select the element(s) to measure
2. Tools → Measure section → Choose tool
3. Results appear in report view

💡 Agent mode can measure and analyze automatically!"""

        elif any(word in message_lower for word in ["boolean", "combine", "merge", "cut"]):
            response = """Boolean operations in FreeCAD:

**Union (∪) - Combine:**
• Merges multiple objects into one
• Select objects → Tools → Operations → Union

**Cut (−) - Subtract:**
• Removes one shape from another
• Select base object first, then cutting object
• Creates holes or cavities

**Intersection (∩) - Common Volume:**
• Keeps only overlapping volume
• Useful for complex joints

**Tips:**
• Order matters for Cut operation
• Objects must overlap
• Keep originals option available
• Use Ctrl+Z for undo

💡 Agent mode can handle complex Boolean sequences!"""

        elif any(word in message_lower for word in ["export", "save", "stl", "step"]):
            response = """Export your FreeCAD model:

**For 3D Printing (STL):**
1. Select model → Tools → Import/Export → ▲S (Export STL)
2. Choose location and filename

**For CAD Exchange (STEP):**
1. Select model → Tools → Import/Export → ▲P (Export STEP)
2. STEP preserves more information

**Other formats:**
• IGES: Older CAD format
• OBJ: 3D graphics/rendering
• FCStd: FreeCAD native format

**Before exporting:**
• Check volume with Tools → Measure → ³
• Complete all Boolean operations
• Consider simplifying if file too large

💡 Agent mode can prepare and export automatically!"""

        elif any(word in message_lower for word in ["help", "start", "tutorial"]):
            response = """Welcome to FreeCAD AI Assistant! 🤖

**What I can help with:**
• Creating shapes (box, cylinder, sphere, etc.)
• Boolean operations (combine, cut, intersect)
• Measurements and analysis
• Modifying shapes (fillet, chamfer)
• Export for 3D printing or CAD

**Two modes available:**
💬 **Chat Mode**: I provide step-by-step instructions
🤖 **Agent Mode**: I execute tools automatically

**Quick start projects:**
1. Simple shapes with rounded edges
2. Basic house or building
3. Mechanical parts (gears, tools)
4. Vehicle models
5. Custom designs

**Available tool categories:**
• Basic & Advanced Shapes
• Operations & Modifications  
• Measurements & Analysis
• Import/Export functions

What would you like to create today?"""

        else:
            # Generic helpful response
            response = f"""I understand you want to work with: "{user_message}"

Here's how I can help with FreeCAD:

**Creating Objects:**
• Basic shapes (box, cylinder, sphere, cone)
• Advanced shapes (gear, spring, text)
• Custom profiles with extrude/revolve

**Modifying Objects:**
• Boolean operations (combine, cut, intersect)
• Transform (move, rotate, scale, mirror)
• Edge operations (fillet, chamfer)

**Analysis & Export:**
• Measure dimensions and properties
• Export to various formats (STL, STEP, etc.)

**Two ways to work:**
💬 **Chat Mode**: I'll guide you step-by-step
🤖 **Agent Mode**: I'll execute automatically

Could you be more specific? For example:
- "Create a box with rounded edges"
- "How do I make a hole in an object"
- "Export my model for 3D printing"
- "Create a simple car"

I'm here to guide you through FreeCAD!"""

        self._add_conversation_message("AI", response)


class ConversationHistoryDialog(QtWidgets.QDialog):
    """Dialog for viewing conversation history."""

    def __init__(self, history, parent=None):
        super(ConversationHistoryDialog, self).__init__(parent)
        self.history = history
        self.setWindowTitle("Conversation History")
        self.resize(600, 400)
        self._setup_ui()

    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QtWidgets.QVBoxLayout(self)

        # History list
        self.history_list = QtWidgets.QListWidget()
        for i, entry in enumerate(self.history):
            item_text = (
                f"{entry['sender']} ({entry['timestamp']}): {entry['message'][:50]}..."
            )
            item = QtWidgets.QListWidgetItem(item_text)
            item.setData(QtCore.Qt.UserRole, i)
            self.history_list.addItem(item)

        self.history_list.itemClicked.connect(self._on_item_selected)
        layout.addWidget(self.history_list)

        # Detail view
        self.detail_text = QtWidgets.QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setMaximumHeight(150)
        layout.addWidget(self.detail_text)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()

        self.export_btn = QtWidgets.QPushButton("Export")
        self.export_btn.clicked.connect(self._export_history)
        button_layout.addWidget(self.export_btn)

        button_layout.addStretch()

        self.close_btn = QtWidgets.QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def _on_item_selected(self, item):
        """Handle history item selection."""
        index = item.data(QtCore.Qt.UserRole)
        if 0 <= index < len(self.history):
            entry = self.history[index]
            self.detail_text.setPlainText(
                f"Sender: {entry['sender']}\nTime: {entry['timestamp']}\n\nMessage:\n{entry['message']}"
            )

    def _export_history(self):
        """Export conversation history."""
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export History",
            f"conversation_history_{QtCore.QDateTime.currentDateTime().toString('yyyyMMdd_HHmmss')}.txt",
            "Text Files (*.txt);;All Files (*)",
        )

        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    for entry in self.history:
                        f.write(
                            f"{entry['sender']} ({entry['timestamp']}): {entry['message']}\n\n"
                        )
                QtWidgets.QMessageBox.information(
                    self, "Success", f"History exported to {filename}"
                )
            except Exception as e:
                QtWidgets.QMessageBox.warning(
                    self, "Error", f"Failed to export history: {str(e)}"
                )
