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
        self.conversation_history = []
        self.current_provider = None

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
        self.refresh_providers_btn = QtWidgets.QPushButton("🔄")
        self.refresh_providers_btn.setMaximumWidth(30)
        self.refresh_providers_btn.setToolTip("Refresh providers list")
        self.refresh_providers_btn.clicked.connect(self.refresh_providers)
        provider_layout.addWidget(self.refresh_providers_btn)

        # Debug button
        self.debug_providers_btn = QtWidgets.QPushButton("🐛")
        self.debug_providers_btn.setMaximumWidth(30)
        self.debug_providers_btn.setToolTip("Debug provider status")
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
        """Send message to AI provider."""
        # Add user message to conversation
        self._add_conversation_message("You", message)
        self.message_input.clear()

        # Emit signal for message sent
        self.message_sent.emit(self.current_provider, message)

        # Show thinking indicator
        self._add_conversation_message("AI", "Thinking...")

        # Try to send via provider service first, then fallback to simulation
        if self.provider_service:
            try:
                # Use provider service to send message
                QtCore.QTimer.singleShot(
                    100, lambda: self._send_via_provider_service(message)
                )
            except Exception as e:
                self._add_system_message(f"Error using provider service: {e}")
                QtCore.QTimer.singleShot(
                    1500, lambda: self._simulate_ai_response(message)
                )
        else:
            # Fallback to simulation
            QtCore.QTimer.singleShot(1500, lambda: self._simulate_ai_response(message))

        # Update usage statistics
        current_count = len(self.conversation_history)
        self.usage_label.setText(f"Messages: {current_count}")

    def _send_via_provider_service(self, message):
        """Send message via provider service."""
        try:
            response = self.provider_service.send_message_to_provider(
                self.current_provider, message
            )

            # Remove thinking indicator
            self._remove_thinking_indicator()

            # Add AI response
            self._add_conversation_message("AI", response)

        except Exception as e:
            # Remove thinking indicator
            self._remove_thinking_indicator()

            # Add error message
            self._add_conversation_message("AI", f"Error: {str(e)}")

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
        """Simulate AI response (placeholder for real implementation)."""
        # Remove thinking indicator
        self._remove_thinking_indicator()

        # Generate simulated response based on message content
        if "box" in user_message.lower() or "cube" in user_message.lower():
            response = "I can help you create a box in FreeCAD. You can use the Part Workbench and select 'Create Box' or use the MCP tool freecad.create_box with parameters like length, width, and height."
        elif "cylinder" in user_message.lower():
            response = "To create a cylinder in FreeCAD, you can use the freecad.create_cylinder tool. You'll need to specify the radius and height parameters."
        elif "export" in user_message.lower() and "stl" in user_message.lower():
            response = "You can export your model to STL format using the freecad.export_stl tool. This will create a file suitable for 3D printing."
        elif "explain" in user_message.lower() and "model" in user_message.lower():
            response = "I'd be happy to explain your FreeCAD model. Please ensure you have an active document open, and I can analyze its components, structure, and suggest any improvements or modifications."
        elif "improvement" in user_message.lower() or "suggest" in user_message.lower():
            response = "To suggest improvements, I would need to see your current model structure. Consider optimizing geometry for your intended use case, checking for manufacturing constraints if applicable, and ensuring proper parametric relationships between features."
        elif "help" in user_message.lower():
            response = "I'm here to help with FreeCAD! I can assist with:\n• Creating and modifying 3D objects\n• Workbench navigation\n• Parametric modeling techniques\n• Export options\n• Troubleshooting common issues\n\nWhat specific area would you like help with?"
        else:
            response = f"I understand you're asking about: '{user_message}'. I can help you with FreeCAD operations including creating primitives, performing boolean operations, managing workbenches, and exporting models. What specific operation would you like to perform?"

        self._add_conversation_message("AI", response)

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
