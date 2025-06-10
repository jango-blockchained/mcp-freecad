"""Enhanced Conversation Widget with Keyboard Shortcuts and Search"""

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
        self.current_mode = None

        # Search functionality
        self.search_matches = []
        self.current_search_index = -1

        # Execution tracking
        self.current_execution = None
        self.execution_widget = None

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
        
        # TODO: Implement actual highlighting in the text browser
        # This would require modifying the HTML content or using QTextCursor
        
    def _clear_search_highlighting(self):
        """Clear search highlighting."""
        # TODO: Implement clearing of search highlights
        pass

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

    # Include all other methods from the original ConversationWidget
    # [Methods like _send_message, _create_conversation_controls, etc. remain the same]
    
    def get_conversation_history(self):
        """Get the conversation history."""
        return self.conversation_history.copy()

    def load_conversation_history(self, history):
        """Load conversation history from external source."""
        self.conversation_history = history.copy()
        self._rebuild_conversation_display()
