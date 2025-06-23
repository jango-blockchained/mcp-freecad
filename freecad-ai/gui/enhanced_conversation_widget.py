"""Enhanced Conversation Widget with Keyboard Shortcuts and Search"""

import re
from PySide2 import QtCore, QtGui, QtWidgets

from .conversation_formatter import (
    ConversationFormat,
    ConversationFormatter,
    FormatSelectionWidget,
)
from .provider_selector_widget import ProviderSelectorWidget


class ConversationSearchWidget(QtWidgets.QWidget):
    """Search widget for conversations."""
    
    search_requested = QtCore.Signal(str, bool)  # query, case_sensitive
    search_closed = QtCore.Signal()
    
    def __init__(self, parent=None):
        super(ConversationSearchWidget, self).__init__(parent)
        self._setup_ui()
        self.setVisible(False)
        
    def _setup_ui(self):
        """Setup search widget UI."""
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Search icon
        search_icon = QtWidgets.QLabel("🔍")
        layout.addWidget(search_icon)
        
        # Search input
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("Search conversation...")
        self.search_input.textChanged.connect(self._on_search_text_changed)
        self.search_input.returnPressed.connect(self._on_search_enter)
        layout.addWidget(self.search_input)
        
        # Case sensitive checkbox
        self.case_sensitive_check = QtWidgets.QCheckBox("Case sensitive")
        self.case_sensitive_check.stateChanged.connect(self._on_search_options_changed)
        layout.addWidget(self.case_sensitive_check)
        
        # Results label
        self.results_label = QtWidgets.QLabel("")
        self.results_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.results_label)
        
        # Close button
        close_btn = QtWidgets.QPushButton("×")
        close_btn.setFixedSize(25, 25)
        close_btn.clicked.connect(self._on_close)
        layout.addWidget(close_btn)
        
    def _on_search_text_changed(self, text):
        """Handle search text change."""
        if text.strip():
            self.search_requested.emit(text, self.case_sensitive_check.isChecked())
        else:
            self.results_label.setText("")
            
    def _on_search_enter(self):
        """Handle Enter key in search."""
        text = self.search_input.text().strip()
        if text:
            self.search_requested.emit(text, self.case_sensitive_check.isChecked())
            
    def _on_search_options_changed(self):
        """Handle search options change."""
        text = self.search_input.text().strip()
        if text:
            self.search_requested.emit(text, self.case_sensitive_check.isChecked())
            
    def _on_close(self):
        """Handle close button."""
        self.setVisible(False)
        self.search_closed.emit()
        
    def show_search(self):
        """Show and focus search widget."""
        self.setVisible(True)
        self.search_input.setFocus()
        self.search_input.selectAll()
        
    def update_results(self, total_matches, current_match=None):
        """Update search results display."""
        if total_matches == 0:
            self.results_label.setText("No matches")
        elif current_match is not None:
            self.results_label.setText(f"{current_match + 1} of {total_matches}")
        else:
            self.results_label.setText(f"{total_matches} matches")


class EnhancedConversationWidget(QtWidgets.QWidget):
    """Enhanced conversation widget with additional features."""

    # Signals
    message_sent = QtCore.Signal(str, str)  # provider, message

    def __init__(self, parent=None):
        super(EnhancedConversationWidget, self).__init__(parent)

        # Initialize services and state
        self.ai_manager = None
        self.config_manager = None
        self.provider_service = None
        self.agent_manager = None
        self.conversation_history = []
        self.current_provider = None
        self.current_model = None
        self.current_mode = None
        self.current_plan = None

        # Search functionality
        self.search_matches = []
        self.current_search_index = -1

        # Execution tracking
        self.current_execution = None
        self.execution_widget = None

        # UI elements that will be created later
        self.history_btn = None
        self.save_btn = None
        self.provider_selector = None
        self.context_check = None
        self.format_selector = None
        self.search_btn = None
        self.export_btn = None
        self.clear_btn = None
        self.conversation_text = None
        self.usage_label = None
        self.search_info_label = None
        self.mode_label = None
        self.switch_mode_btn = None
        self.message_input = None
        self.send_btn = None

        # Conversation formatter
        self.formatter = ConversationFormatter()

        self._setup_keyboard_shortcuts()
        self._setup_services()
        self._setup_ui()
        self._load_providers_fallback()

    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for better UX."""
        # Ctrl+Enter to send message
        send_shortcut = QtWidgets.QShortcut(
            QtGui.QKeySequence("Ctrl+Return"), self
        )
        send_shortcut.activated.connect(self._on_send_message)
        
        # Ctrl+F to search
        search_shortcut = QtWidgets.QShortcut(
            QtGui.QKeySequence("Ctrl+F"), self
        )
        search_shortcut.activated.connect(self._show_search)
        
        # Escape to close search
        escape_shortcut = QtWidgets.QShortcut(
            QtGui.QKeySequence("Escape"), self
        )
        escape_shortcut.activated.connect(self._hide_search)
        
        # Ctrl+L to clear conversation
        clear_shortcut = QtWidgets.QShortcut(
            QtGui.QKeySequence("Ctrl+L"), self
        )
        clear_shortcut.activated.connect(self._clear_conversation)
        
        # F3 for next search result
        next_search_shortcut = QtWidgets.QShortcut(
            QtGui.QKeySequence("F3"), self
        )
        next_search_shortcut.activated.connect(self._next_search_result)
        
        # Shift+F3 for previous search result
        prev_search_shortcut = QtWidgets.QShortcut(
            QtGui.QKeySequence("Shift+F3"), self
        )
        prev_search_shortcut.activated.connect(self._prev_search_result)
        
    def _setup_services(self):
        """Setup AI manager and config manager."""
        # Same as original implementation
        self.ai_manager = None
        self.config_manager = None

        # Try to import AI Manager
        try:
            try:
                from ..ai.ai_manager import AIManager
                self.ai_manager = AIManager()
                print("EnhancedConversationWidget: AI Manager imported via relative path")
            except ImportError:
                from ai.ai_manager import AIManager
                self.ai_manager = AIManager()
                print("EnhancedConversationWidget: AI Manager imported via direct path")
        except ImportError as e:
            print(f"EnhancedConversationWidget: Failed to import AI Manager: {e}")
            self.ai_manager = None

        # Try multiple import strategies for config manager
        try:
            try:
                from ..config.config_manager import ConfigManager
                self.config_manager = ConfigManager()
                print("EnhancedConversationWidget: Config Manager imported via relative path")
            except ImportError:
                try:
                    from config.config_manager import ConfigManager
                    self.config_manager = ConfigManager()
                    print("EnhancedConversationWidget: Config Manager imported via direct path")
                except ImportError:
                    import os
                    import sys
                    parent_dir = os.path.dirname(
                        os.path.dirname(os.path.abspath(__file__))
                    )
                    if parent_dir not in sys.path:
                        sys.path.insert(0, parent_dir)
                    from config.config_manager import ConfigManager
                    self.config_manager = ConfigManager()
                    print("EnhancedConversationWidget: Config Manager imported after sys.path modification")
        except ImportError as e:
            print(f"EnhancedConversationWidget: Failed to import Config Manager: {e}")
            self.config_manager = None
        except Exception as e:
            print(f"EnhancedConversationWidget: Error setting up Config Manager: {e}")
            self.config_manager = None

    def _setup_ui(self):
        """Setup the enhanced user interface."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Add search widget first (hidden by default)
        self.search_widget = ConversationSearchWidget()
        self.search_widget.search_requested.connect(self._perform_search)
        self.search_widget.search_closed.connect(self._hide_search)
        layout.addWidget(self.search_widget)

        # Create sections
        self._create_provider_selector(layout)
        self._create_conversation_display(layout)
        self._create_message_input(layout)
        self._create_conversation_controls(layout)

    def _create_provider_selector(self, layout):
        """Create provider selection section using shared widget."""
        provider_group = QtWidgets.QGroupBox("AI Provider Selection")
        provider_layout = QtWidgets.QHBoxLayout(provider_group)

        # Create the shared provider selector widget
        self.provider_selector = ProviderSelectorWidget()
        self.provider_selector.provider_changed.connect(self._on_provider_changed)
        self.provider_selector.refresh_requested.connect(self._on_provider_refresh)
        provider_layout.addWidget(self.provider_selector)

        # Context options
        provider_layout.addStretch()
        self.context_check = QtWidgets.QCheckBox("Use CAD Context")
        self.context_check.setChecked(True)
        self.context_check.setToolTip(
            "Include current FreeCAD document state in AI queries"
        )
        provider_layout.addWidget(self.context_check)

        layout.addWidget(provider_group)

    def _create_conversation_display(self, layout):
        """Create enhanced conversation display section."""
        conversation_group = QtWidgets.QGroupBox("Conversation")
        conversation_layout = QtWidgets.QVBoxLayout(conversation_group)

        # Format selection header
        format_header = QtWidgets.QHBoxLayout()

        # Format selector
        self.format_selector = FormatSelectionWidget()
        self.format_selector.format_changed.connect(self._on_format_changed)
        format_header.addWidget(self.format_selector)

        format_header.addStretch()
        
        # Search button
        self.search_btn = QtWidgets.QPushButton("🔍 Search")
        self.search_btn.setMaximumWidth(80)
        self.search_btn.setToolTip("Search conversation (Ctrl+F)")
        self.search_btn.clicked.connect(self._show_search)
        format_header.addWidget(self.search_btn)

        # Export button
        self.export_btn = QtWidgets.QPushButton("📥 Export")
        self.export_btn.setMaximumWidth(80)
        self.export_btn.clicked.connect(self._export_conversation)
        format_header.addWidget(self.export_btn)

        # Clear button
        self.clear_btn = QtWidgets.QPushButton("🗑️ Clear")
        self.clear_btn.setMaximumWidth(70)
        self.clear_btn.setToolTip("Clear conversation (Ctrl+L)")
        self.clear_btn.setStyleSheet(
            "QPushButton { background-color: #ff4444; color: white; }"
        )
        self.clear_btn.clicked.connect(self._clear_conversation)
        format_header.addWidget(self.clear_btn)

        conversation_layout.addLayout(format_header)

        # Conversation text display
        self.conversation_text = QtWidgets.QTextBrowser()
        self.conversation_text.setMinimumHeight(200)
        self.conversation_text.setOpenExternalLinks(True)
        self.conversation_text.setStyleSheet(
            """
            QTextBrowser {
                background-color: #ffffff;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
                font-family: Arial, sans-serif;
            }
        """
        )
        conversation_layout.addWidget(self.conversation_text)

        # Usage info bar
        usage_layout = QtWidgets.QHBoxLayout()
        usage_layout.addWidget(QtWidgets.QLabel("💬"))
        self.usage_label = QtWidgets.QLabel("Messages: 0")
        usage_layout.addWidget(self.usage_label)
        usage_layout.addStretch()
        
        # Add search results info
        self.search_info_label = QtWidgets.QLabel("")
        self.search_info_label.setStyleSheet("color: #666; font-style: italic;")
        usage_layout.addWidget(self.search_info_label)
        
        conversation_layout.addLayout(usage_layout)

        layout.addWidget(conversation_group)

    def _create_message_input(self, layout):
        """Create enhanced message input section."""
        input_group = QtWidgets.QGroupBox("Send Message")
        input_layout = QtWidgets.QVBoxLayout(input_group)

        # Mode indicator
        mode_layout = QtWidgets.QHBoxLayout()
        self.mode_label = QtWidgets.QLabel("💬 Chat Mode")
        self.mode_label.setStyleSheet(
            "font-weight: bold; color: #2196F3; padding: 5px;"
        )
        mode_layout.addWidget(self.mode_label)

        mode_layout.addStretch()

        self.switch_mode_btn = QtWidgets.QPushButton("Switch to Agent Mode")
        self.switch_mode_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """
        )
        self.switch_mode_btn.clicked.connect(self._toggle_mode)
        mode_layout.addWidget(self.switch_mode_btn)

        input_layout.addLayout(mode_layout)

        # Message input area with enhanced features
        message_layout = QtWidgets.QHBoxLayout()

        # Use QTextEdit for multi-line input
        self.message_input = QtWidgets.QTextEdit()
        self.message_input.setMaximumHeight(80)
        self.message_input.setPlaceholderText("Ask the AI about FreeCAD operations... (Ctrl+Enter to send)")
        self.message_input.setStyleSheet("QTextEdit { padding: 8px; font-size: 12px; }")
        
        # Handle Ctrl+Enter in text edit
        self.message_input.installEventFilter(self)
        
        message_layout.addWidget(self.message_input)

        # Send button with tooltip
        self.send_btn = QtWidgets.QPushButton("Send")
        self.send_btn.setToolTip("Send message (Ctrl+Enter)")
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

        # Continue with existing sections...
        # [Rest of the method remains the same as original]
        
        layout.addWidget(input_group)

        # Connect signals
        self.send_btn.clicked.connect(self._on_send_message)

    def eventFilter(self, source, event):
        """Handle events for enhanced input."""
        if source == self.message_input and event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
                if event.modifiers() == QtCore.Qt.ControlModifier:
                    self._on_send_message()
                    return True
        return super().eventFilter(source, event)

    def _show_search(self):
        """Show search widget."""
        self.search_widget.show_search()

    def _hide_search(self):
        """Hide search widget."""
        self.search_widget.setVisible(False)
        self.search_matches.clear()
        self.current_search_index = -1
        self.search_info_label.setText("")
        # Clear any search highlighting
        self._clear_search_highlighting()

    def _perform_search(self, query, case_sensitive):
        """Perform search in conversation history."""
        self.search_matches.clear()
        self.current_search_index = -1
        
        if not query.strip():
            self.search_widget.update_results(0)
            return
            
        # Search through conversation history
        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = re.escape(query)
        
        for i, entry in enumerate(self.conversation_history):
            message = entry.get("message", "")
            sender = entry.get("sender", "")
            
            # Search in message content
            if re.search(pattern, message, flags):
                self.search_matches.append({
                    "index": i,
                    "type": "message",
                    "text": message,
                    "sender": sender
                })
                
            # Search in sender name
            if re.search(pattern, sender, flags):
                self.search_matches.append({
                    "index": i,
                    "type": "sender", 
                    "text": sender,
                    "sender": sender
                })
        
        # Update search widget with results
        self.search_widget.update_results(len(self.search_matches))
        
        if self.search_matches:
            self.current_search_index = 0
            self._highlight_search_result()
            
    def _next_search_result(self):
        """Go to next search result."""
        if self.search_matches and self.current_search_index < len(self.search_matches) - 1:
            self.current_search_index += 1
            self._highlight_search_result()
            
    def _prev_search_result(self):
        """Go to previous search result."""
        if self.search_matches and self.current_search_index > 0:
            self.current_search_index -= 1
            self._highlight_search_result()
            
    def _highlight_search_result(self):
        """Highlight current search result."""
        if not self.search_matches or self.current_search_index < 0:
            return
            
        # Update search widget display
        self.search_widget.update_results(len(self.search_matches), self.current_search_index)
        
        # Update info label
        current = self.current_search_index + 1
        total = len(self.search_matches)
        self.search_info_label.setText(f"Search: {current}/{total}")
        
        # Highlight current search match
        if self.search_matches:
            cursor = self.conversation_display.textCursor()
            cursor.setPosition(self.search_matches[self.current_search_index])
            cursor.movePosition(cursor.Right, cursor.KeepAnchor, len(self.current_search_query))
            
            # Set background color for highlight
            format = cursor.charFormat()
            format.setBackground(QtCore.Qt.yellow)
            cursor.setCharFormat(format)
            
            # Move viewport to show the highlighted text
            self.conversation_display.setTextCursor(cursor)
            self.conversation_display.ensureCursorVisible()
        
    def _clear_search_highlighting(self):
        """Clear search highlighting."""
        # Clear all highlighting by resetting the document format
        cursor = self.conversation_display.textCursor()
        cursor.select(cursor.Document)
        format = cursor.charFormat()
        format.setBackground(QtCore.Qt.transparent)
        cursor.setCharFormat(format)
        
        # Reset search state
        self.search_matches = []
        self.current_search_index = 0
        self.search_info_label.setText("Search: 0/0")

    def _on_send_message(self):
        """Handle send message with enhanced input."""
        if hasattr(self.message_input, 'toPlainText'):
            message = self.message_input.toPlainText().strip()
        else:
            message = self.message_input.text().strip()
            
        if not message:
            return

        if not self.current_provider:
            QtWidgets.QMessageBox.warning(
                self, "Error", "Please select an AI provider first"
            )
            return

        self._send_message(message)
        
        # Clear input
        if hasattr(self.message_input, 'clear'):
            self.message_input.clear()

    def _send_message(self, message):
        """Send message to the AI."""
        if not message.strip():
            return

        # Get current provider selection from provider selector
        current_selection = None
        if hasattr(self, "provider_selector"):
            current_selection = self.provider_selector.get_current_selection()
            if current_selection and current_selection["provider"]:
                self.current_provider = current_selection["provider"]
                self.current_model = current_selection.get("model")

        # Fallback to stored provider if selector not available
        if not self.current_provider:
            QtWidgets.QMessageBox.warning(
                self, "Error", "Please select an AI provider first"
            )
            return

        # Check if agent manager is available for agent mode
        if self.agent_manager and hasattr(self.agent_manager, 'get_mode') and self.agent_manager.get_mode().value == "agent":
            # Agent mode - process with agent manager
            self._process_with_agent(message)
        else:
            # Chat mode - use direct AI call
            self._process_with_chat(message)

    def _process_with_chat(self, message):
        """Process message in chat mode."""
        # Clear input already done in _on_send_message

        # Add user message to conversation
        self._add_conversation_message("You", message)

        # Show thinking indicator
        self._add_thinking_indicator()

        # Gather context
        context = (
            self._gather_freecad_context() if self.context_check.isChecked() else {}
        )

        # Send to AI
        self._send_to_provider(message, context)

    def _process_with_agent(self, message):
        """Process message in agent mode."""
        if not self.agent_manager:
            self._add_system_message("Agent manager not available")
            return

        # Add user message to conversation
        self._add_conversation_message("You", message)

        # Show thinking indicator
        self._add_thinking_indicator()

        try:
            # Gather context
            context = (
                self._gather_freecad_context() if self.context_check.isChecked() else {}
            )

            # Send to agent manager
            response = self.agent_manager.process_message(message, context)

            # Handle response
            self._handle_agent_response(response)

        except Exception as e:
            self._remove_thinking_indicator()
            self._add_system_message(f"Error processing agent request: {e}")
            print(f"EnhancedConversationWidget: Agent processing error: {e}")

    def _send_to_provider(self, message, context):
        """Send message to the AI provider."""
        if not self.provider_service:
            self._remove_thinking_indicator()
            self._add_system_message("Provider service not available")
            return

        # Make the AI call in a thread or directly
        self._make_ai_call(message, context)

    def _make_ai_call(self, message, context):
        """Make the actual AI API call asynchronously."""
        try:
            # Call the provider service to send message to AI
            response = self.provider_service.send_message_to_provider(
                self.current_provider, message, context
            )

            # Handle the response
            self._handle_ai_response(response)

        except Exception as e:
            self._remove_thinking_indicator()
            error_msg = str(e)
            self._add_system_message(f"❌ Error communicating with AI: {error_msg}")

    def _handle_ai_response(self, response):
        """Handle the AI provider response."""
        self._remove_thinking_indicator()

        if response and isinstance(response, str):
            # Clean up the response if it contains system prompt echoes
            cleaned_response = self._clean_ai_response(response)
            self._add_conversation_message("AI", cleaned_response)
        else:
            self._add_system_message("Received empty or invalid response from AI")

    def _clean_ai_response(self, response):
        """Clean up AI response to remove system prompt echoes."""
        # Remove any system prompt repetition that might occur
        lines = response.split("\n")
        cleaned_lines = []

        for line in lines:
            # Skip lines that look like system prompt echoes
            if not (
                line.startswith("You are an AI assistant")
                or line.startswith("IMPORTANT:")
                or line.startswith("AVAILABLE TOOL")
                or line.startswith("CONTEXT AWARENESS:")
                or line.startswith("RESPONSE STYLE:")
            ):
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()

    def _handle_agent_response(self, response):
        """Handle response from agent manager."""
        self._remove_thinking_indicator()

        if response.get("error"):
            self._add_system_message(f"Error: {response['error']}")
            return

        # Display intent and plan
        plan = response.get("plan", {})

        if plan:
            # Store current plan for approval/modification
            self.current_plan = plan

            # Show task preview if available
            if hasattr(self, '_display_task_preview'):
                self._display_task_preview(plan)

            # Check if approval is required
            if response.get("approval_required", False):
                self._add_system_message(
                    "Tasks created. Please review and execute when ready."
                )
            else:
                # Auto-execute if approval not required
                self._add_system_message("Executing tasks automatically...")
                execution_result = response.get("execution_result", {})
                if hasattr(self, '_display_execution_result'):
                    self._display_execution_result(execution_result)

    def _add_thinking_indicator(self):
        """Add thinking indicator to show AI is processing."""
        self._add_system_message("🤔 AI is thinking...")

    def _remove_thinking_indicator(self):
        """Remove thinking indicator."""
        # Simple implementation - could be improved to actually remove the last thinking message
        return

    def _gather_freecad_context(self):
        """Gather FreeCAD context information for the AI."""
        context = {"freecad_state": {}}
        
        try:
            import FreeCAD
            import FreeCADGui
            
            # Document information
            if FreeCAD.ActiveDocument:
                doc = FreeCAD.ActiveDocument
                context["freecad_state"]["active_document"] = {
                    "name": doc.Name,
                    "label": doc.Label,
                    "object_count": len(doc.Objects),
                }

                # Object type counts
                type_counts = {}
                for obj in doc.Objects:
                    obj_type = obj.TypeId.split("::")[-1]  # Get simplified type name
                    type_counts[obj_type] = type_counts.get(obj_type, 0) + 1
                context["freecad_state"]["object_type_counts"] = type_counts

            # Selected objects
            if hasattr(FreeCADGui, "Selection"):
                selection = FreeCADGui.Selection.getSelection()
                context["freecad_state"]["selected_objects"] = [
                    {
                        "name": obj.Name,
                        "label": getattr(obj, "Label", obj.Name),
                        "type": obj.TypeId,
                    }
                    for obj in selection
                ]

                # Selection info
                context["freecad_state"]["selection_count"] = len(selection)
                if selection:
                    context["freecad_state"]["primary_selection"] = {
                        "name": selection[0].Name,
                        "type": selection[0].TypeId,
                    }

            # Current workbench
            try:
                wb = FreeCADGui.activeWorkbench()
                if wb:
                    context["freecad_state"]["active_workbench"] = {
                        "name": wb.name() if hasattr(wb, "name") else "Unknown",
                        "menu_text": (
                            wb.MenuText if hasattr(wb, "MenuText") else "Unknown"
                        ),
                    }
            except (AttributeError, ImportError):
                # AttributeError: Missing workbench attributes
                # ImportError: Missing workbench modules
                context["freecad_state"]["active_workbench"] = {
                    "name": "Unknown",
                    "menu_text": "Unknown",
                }

        except ImportError:
            context["freecad_state"]["error"] = "FreeCAD not available"
        except Exception as e:
            context["freecad_state"]["error"] = f"Error gathering context: {str(e)}"

        return context

    def _add_conversation_message(self, sender, message):
        """Add a message to the conversation display with formatting."""
        timestamp = QtCore.QDateTime.currentDateTime().toString("hh:mm:ss")

        # Add to history
        self.conversation_history.append(
            {"sender": sender, "message": message, "timestamp": timestamp}
        )

        # Format and display message
        formatted_message = self.formatter.format_message(sender, message, timestamp)

        # Move cursor to end and insert formatted message
        cursor = self.conversation_text.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)

        # Insert based on format type
        if self.formatter.format_type in [
            ConversationFormat.RICH_TEXT,
            ConversationFormat.MARKDOWN,
            ConversationFormat.HTML,
        ]:
            cursor.insertHtml(formatted_message)
        else:
            cursor.insertText(formatted_message)

        # Scroll to bottom
        self.conversation_text.verticalScrollBar().setValue(
            self.conversation_text.verticalScrollBar().maximum()
        )

        # Update usage counter
        self.usage_label.setText(f"Messages: {len(self.conversation_history)}")

    def _add_system_message(self, message):
        """Add a system message to the conversation."""
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

    def _create_conversation_controls(self, layout):
        """Create conversation controls section."""
        controls_layout = QtWidgets.QHBoxLayout()

        # History and management
        self.history_btn = QtWidgets.QPushButton("View History")
        self.history_btn.setToolTip("View conversation history")
        self.history_btn.clicked.connect(self._view_history)
        controls_layout.addWidget(self.history_btn)

        self.save_btn = QtWidgets.QPushButton("Save")
        self.save_btn.setToolTip("Save conversation to file")
        self.save_btn.clicked.connect(self._save_conversation)
        controls_layout.addWidget(self.save_btn)

        controls_layout.addStretch()

        layout.addLayout(controls_layout)

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
                    f.write("FreeCAD AI Conversation\n")
                    f.write("Provider: {}\n".format(self.current_provider or 'Unknown'))
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
        # Create a simple history dialog
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Conversation History")
        dialog.setMinimumSize(600, 400)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # Create text display for history
        text_display = QtWidgets.QTextEdit()
        text_display.setReadOnly(True)
        
        # Add conversation history
        history_text = ""
        for entry in self.conversation_history:
            timestamp = entry.get('timestamp', 'Unknown')
            role = entry.get('role', 'Unknown')
            content = entry.get('content', '')
            history_text += f"[{timestamp}] {role.upper()}:\n{content}\n\n"
        
        text_display.setPlainText(history_text)
        layout.addWidget(text_display)
        
        # Add close button
        button_layout = QtWidgets.QHBoxLayout()
        close_button = QtWidgets.QPushButton("Close")
        close_button.clicked.connect(dialog.accept)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
        
        dialog.exec_()

    def _on_provider_changed(self, provider_name, model_name):
        """Handle provider selection change from provider selector."""
        print(
            f"EnhancedConversationWidget: Provider changed to {provider_name} with model {model_name}"
        )
        self.current_provider = provider_name
        self.current_model = model_name

        # Save the selected provider to settings
        try:
            settings = QtCore.QSettings("FreeCAD", "AI_ConversationWidget")
            settings.setValue("last_selected_provider", provider_name)
            settings.setValue("last_selected_model", model_name)
            settings.sync()
        except Exception as e:
            print(f"EnhancedConversationWidget: Failed to save provider preference: {e}")

    def _on_provider_refresh(self):
        """Handle provider refresh request."""
        print("EnhancedConversationWidget: Provider refresh requested")
        if self.provider_service:
            # Trigger a refresh of providers
            try:
                if hasattr(self.provider_service, "refresh_providers"):
                    self.provider_service.refresh_providers()
                elif hasattr(self.provider_service, "initialize_providers_from_config"):
                    self.provider_service.initialize_providers_from_config()
            except Exception as e:
                print(f"EnhancedConversationWidget: Error refreshing providers: {e}")

    def _load_providers_fallback(self):
        """Load providers directly from config if service is not available."""
        if not self.config_manager:
            if hasattr(self, 'send_btn'):
                self.send_btn.setEnabled(False)
            return

        try:
            # Get configured API keys as a fallback
            api_keys = self.config_manager.list_api_keys()
            if api_keys:
                # Use the default provider or first available
                default_provider = self.config_manager.get_default_provider()
                if default_provider and default_provider.lower() in [
                    k.lower() for k in api_keys
                ]:
                    self.current_provider = default_provider
                    if hasattr(self, 'send_btn'):
                        self.send_btn.setEnabled(True)
                elif api_keys:
                    # Use first available provider
                    first_key = api_keys[0]
                    self.current_provider = first_key
                    if hasattr(self, 'send_btn'):
                        self.send_btn.setEnabled(True)
        except Exception as e:
            print(f"EnhancedConversationWidget: Error in provider fallback: {e}")

    def _on_format_changed(self, new_format: ConversationFormat):
        """Handle format change."""
        self.formatter.format_type = new_format
        self._rebuild_conversation_display()

    def _export_conversation(self):
        """Export conversation in selected format."""
        if not self.conversation_history:
            QtWidgets.QMessageBox.information(
                self, "Export", "No conversation to export"
            )
            return

        # Get export format
        format_type = self.format_selector.get_current_format()

        # Get file extension based on format
        extensions = {
            ConversationFormat.PLAIN_TEXT: "txt",
            ConversationFormat.MARKDOWN: "md",
            ConversationFormat.HTML: "html",
            ConversationFormat.RICH_TEXT: "html",
        }

        ext = extensions.get(format_type, "txt")

        # Get save file path
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export Conversation",
            f"conversation.{ext}",
            f"{format_type.value.title()} Files (*.{ext});;All Files (*.*)",
        )

        if file_path:
            try:
                # Export conversation
                exported_content = self.formatter.export_conversation(
                    self.conversation_history, format_type
                )

                # Write to file
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(exported_content)

                QtWidgets.QMessageBox.information(
                    self, "Export Complete", f"Conversation exported to:\n{file_path}"
                )

            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self, "Export Error", f"Failed to export conversation:\n{str(e)}"
                )

    def _rebuild_conversation_display(self):
        """Rebuild conversation display from history with current format."""
        self.conversation_text.clear()

        for entry in self.conversation_history:
            formatted_message = self.formatter.format_message(
                entry["sender"], entry["message"], entry["timestamp"]
            )

            # Insert based on format type
            cursor = self.conversation_text.textCursor()
            cursor.movePosition(QtGui.QTextCursor.End)

            if self.formatter.format_type in [
                ConversationFormat.RICH_TEXT,
                ConversationFormat.MARKDOWN,
                ConversationFormat.HTML,
            ]:
                cursor.insertHtml(formatted_message)
            else:
                cursor.insertText(formatted_message)

    def set_provider_service(self, provider_service):
        """Set the provider integration service."""
        self.provider_service = provider_service

        if provider_service:
            # Connect to provider service signals
            provider_service.provider_status_changed.connect(
                self._on_provider_status_changed
            )
            provider_service.providers_updated.connect(self.refresh_providers)

            # Get the AI manager from provider service instead of creating our own
            if hasattr(provider_service, "get_ai_manager"):
                self.ai_manager = provider_service.get_ai_manager()
                print("EnhancedConversationWidget: Using AI manager from provider service")
            else:
                print(
                    "EnhancedConversationWidget: Provider service has no AI manager - using local one"
                )

            # Connect to provider selector
            if hasattr(self, "provider_selector"):
                self.provider_selector.set_provider_service(provider_service)

            # Also set config manager if available
            if self.config_manager and hasattr(self, "provider_selector"):
                self.provider_selector.set_config_manager(self.config_manager)

            # Initial refresh
            self.refresh_providers()

    def _on_provider_status_changed(self, provider_name: str, status: str, message: str):
        """Handle provider status change."""
        if provider_name == self.current_provider:
            if status == "connected":
                self._add_system_message(f"Provider {provider_name} connected")
            elif status == "error":
                self._add_system_message(f"Provider {provider_name} error: {message}")

    def refresh_providers(self):
        """Refresh the provider list and status."""
        print("EnhancedConversationWidget: Refreshing providers...")

        if self.provider_service:
            print(
                "EnhancedConversationWidget: Provider service available, getting active providers..."
            )

            # Get active providers
            active_providers = self.provider_service.get_active_providers()
            print(f"EnhancedConversationWidget: Found {len(active_providers)} active providers")

            if active_providers:
                # Try to restore last selected provider
                last_selected_provider = None
                try:
                    settings = QtCore.QSettings("FreeCAD", "AI_ConversationWidget")
                    saved_provider = settings.value("last_selected_provider", None)
                    if saved_provider and saved_provider in active_providers:
                        last_selected_provider = saved_provider
                        print(
                            f"EnhancedConversationWidget: Restored last selected provider: {saved_provider}"
                        )
                except Exception as e:
                    print(
                        f"EnhancedConversationWidget: Failed to restore provider preference: {e}"
                    )

                # Use the last selected, default, or first active provider
                selected_provider = None

                if last_selected_provider:
                    selected_provider = last_selected_provider
                else:
                    # Look for default provider
                    for name, provider in active_providers.items():
                        if provider.get("is_default", False):
                            selected_provider = name
                            break

                    # Fall back to first provider
                    if not selected_provider and active_providers:
                        selected_provider = list(active_providers.keys())[0]

                if selected_provider:
                    self.current_provider = selected_provider
                    provider_info = active_providers[selected_provider]
                    status = provider_info.get("status", "unknown")

                    if status in ["connected", "initialized"] and hasattr(self, 'send_btn'):
                        self.send_btn.setEnabled(True)
                    elif hasattr(self, 'send_btn'):
                        self.send_btn.setEnabled(False)
            elif hasattr(self, 'send_btn'):
                self.send_btn.setEnabled(False)
        else:
            print("EnhancedConversationWidget: Provider service not available, using fallback")
            self._load_providers_fallback()

    def set_agent_manager(self, agent_manager):
        """Set the agent manager reference."""
        self.agent_manager = agent_manager

        # Register callbacks for execution updates if available
        if self.agent_manager and hasattr(self.agent_manager, 'register_callback'):
            try:
                self.agent_manager.register_callback(
                    "on_execution_start", self._on_execution_start
                )
                self.agent_manager.register_callback(
                    "on_execution_complete", self._on_execution_complete
                )
                self.agent_manager.register_callback(
                    "on_plan_created", self._on_plan_created
                )
            except Exception as e:
                print(f"EnhancedConversationWidget: Error registering agent callbacks: {e}")

    def _on_execution_start(self, step_num, total_steps, step):
        """Handle execution start callback."""
        self._add_system_message(f"▶️ Starting step {step_num}/{total_steps}: {step.get('description', 'Unknown step')}")

    def _on_execution_complete(self, step_num, total_steps, result):
        """Handle execution complete callback."""
        status = result.get("status")
        if hasattr(status, "value"):
            status_val = status.value
        else:
            status_val = str(status)

        if status_val == "completed" or result.get("success"):
            self._add_system_message(f"✅ Step {step_num}/{total_steps} completed")
        else:
            error_msg = result.get("error", "Unknown error")
            self._add_system_message(
                f"❌ Step {step_num}/{total_steps} failed: {error_msg}"
            )

    def _on_plan_created(self, plan):
        """Handle plan created callback."""
        step_count = len(plan.get("steps", []))
        self._add_system_message(f"📋 Created execution plan with {step_count} steps")

    def _toggle_mode(self):
        """Toggle between chat and agent mode."""
        if not self.agent_manager:
            self._add_system_message(
                "Agent manager not available. Please check configuration."
            )
            return

        try:
            from ..core.agent_manager import AgentMode

            current_mode = self.agent_manager.get_mode()
            if current_mode == AgentMode.CHAT:
                self.agent_manager.set_mode(AgentMode.AGENT)
                self.mode_label.setText("🤖 Agent Mode")
                self.mode_label.setStyleSheet(
                    "font-weight: bold; color: #FF9800; padding: 5px;"
                )
                self.switch_mode_btn.setText("Switch to Chat Mode")
                # Enhanced widgets may not have task_preview, so check first
                if hasattr(self, 'task_preview'):
                    self.task_preview.setVisible(True)
                self._add_system_message(
                    "Switched to Agent Mode - AI will execute tasks autonomously"
                )
            else:
                self.agent_manager.set_mode(AgentMode.CHAT)
                self.mode_label.setText("💬 Chat Mode")
                self.mode_label.setStyleSheet(
                    "font-weight: bold; color: #2196F3; padding: 5px;"
                )
                self.switch_mode_btn.setText("Switch to Agent Mode")
                # Enhanced widgets may not have task_preview, so check first
                if hasattr(self, 'task_preview'):
                    self.task_preview.setVisible(False)
                self._add_system_message(
                    "Switched to Chat Mode - AI will provide instructions only"
                )

        except Exception as e:
            self._add_system_message(f"Error switching mode: {e}")

    def get_conversation_history(self):
        """Get the conversation history."""
        return self.conversation_history.copy()

    def load_conversation_history(self, history):
        """Load conversation history from external source."""
        self.conversation_history = history.copy()
        self._rebuild_conversation_display()
