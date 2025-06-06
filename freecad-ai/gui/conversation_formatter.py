"""Conversation Formatter - Handles different conversation display formats"""

import re
from enum import Enum

from PySide2 import QtCore, QtGui, QtWidgets


class ConversationFormat(Enum):
    """Available conversation formats."""

    PLAIN_TEXT = "plain"
    MARKDOWN = "markdown"
    HTML = "html"
    RICH_TEXT = "rich"


class ConversationFormatter:
    """Formats conversation messages in different styles."""

    def __init__(self, format_type: ConversationFormat = ConversationFormat.RICH_TEXT):
        self.format_type = format_type

    def format_message(self, sender: str, message: str, timestamp: str = None) -> str:
        """Format a message based on the current format type."""
        if self.format_type == ConversationFormat.PLAIN_TEXT:
            return self._format_plain_text(sender, message, timestamp)
        elif self.format_type == ConversationFormat.MARKDOWN:
            return self._format_markdown(sender, message, timestamp)
        elif self.format_type == ConversationFormat.HTML:
            return self._format_html(sender, message, timestamp)
        else:  # RICH_TEXT
            return self._format_rich_text(sender, message, timestamp)

    def _format_plain_text(self, sender: str, message: str, timestamp: str) -> str:
        """Format as plain text."""
        if timestamp:
            return f"[{timestamp}] {sender}: {message}\n"
        else:
            return f"{sender}: {message}\n"

    def _format_markdown(self, sender: str, message: str, timestamp: str) -> str:
        """Format as markdown."""
        # Convert common markdown patterns
        formatted_message = message

        # Bold
        formatted_message = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", formatted_message)

        # Italic
        formatted_message = re.sub(r"\*(.*?)\*", r"<i>\1</i>", formatted_message)

        # Code blocks
        formatted_message = re.sub(
            r"```(.*?)```", r"<pre>\1</pre>", formatted_message, flags=re.DOTALL
        )

        # Inline code
        formatted_message = re.sub(r"`(.*?)`", r"<code>\1</code>", formatted_message)

        # Headers
        formatted_message = re.sub(
            r"^# (.*?)$", r"<h1>\1</h1>", formatted_message, flags=re.MULTILINE
        )
        formatted_message = re.sub(
            r"^## (.*?)$", r"<h2>\1</h2>", formatted_message, flags=re.MULTILINE
        )
        formatted_message = re.sub(
            r"^### (.*?)$", r"<h3>\1</h3>", formatted_message, flags=re.MULTILINE
        )

        # Lists
        formatted_message = re.sub(
            r"^- (.*?)$", r"• \1", formatted_message, flags=re.MULTILINE
        )
        formatted_message = re.sub(
            r"^\* (.*?)$", r"• \1", formatted_message, flags=re.MULTILINE
        )
        formatted_message = re.sub(
            r"^\d+\. (.*?)$", r"⦿ \1", formatted_message, flags=re.MULTILINE
        )

        # Line breaks
        formatted_message = formatted_message.replace("\n", "<br>")

        if timestamp:
            header = (
                f'<span style="color: #888; font-size: 10px;">[{timestamp}]</span> '
            )
        else:
            header = ""

        sender_style = self._get_sender_style(sender)

        return f'{header}<span style="{sender_style}">{sender}:</span><br>{formatted_message}<br><br>'

    def _format_html(self, sender: str, message: str, timestamp: str) -> str:
        """Format as HTML."""
        # Escape HTML characters
        message = (
            message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )
        message = message.replace("\n", "<br>")

        if timestamp:
            header = (
                f'<span style="color: #888; font-size: 10px;">[{timestamp}]</span> '
            )
        else:
            header = ""

        sender_style = self._get_sender_style(sender)

        return f'{header}<span style="{sender_style}">{sender}:</span><br>{message}<br><br>'

    def _format_rich_text(self, sender: str, message: str, timestamp: str) -> str:
        """Format as rich text with full styling."""
        # Process markdown-like syntax
        formatted_message = self._process_rich_text_formatting(message)

        if timestamp:
            header = (
                f'<span style="color: #888; font-size: 10px;">[{timestamp}]</span> '
            )
        else:
            header = ""

        sender_style = self._get_sender_style(sender)
        message_style = self._get_message_style(sender)

        # Create message block with proper styling
        return f"""
        <div style="margin: 5px 0; padding: 8px; background-color: {self._get_background_color(sender)}; border-radius: 8px;">
            {header}<span style="{sender_style}">{sender}</span><br>
            <div style="{message_style}">{formatted_message}</div>
        </div>
        """

    def _process_rich_text_formatting(self, text: str) -> str:
        """Process rich text formatting with enhanced styles."""
        # Bold
        text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)

        # Italic
        text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)

        # Code blocks with syntax highlighting simulation
        def format_code_block(match):
            code = match.group(1).strip()
            return f'<pre style="background-color: #f5f5f5; padding: 10px; border-radius: 4px; font-family: monospace; overflow-x: auto;">{code}</pre>'

        text = re.sub(r"```(.*?)```", format_code_block, text, flags=re.DOTALL)

        # Inline code
        text = re.sub(
            r"`(.*?)`",
            r'<code style="background-color: #f0f0f0; padding: 2px 4px; border-radius: 3px; font-family: monospace;">\1</code>',
            text,
        )

        # Headers
        text = re.sub(
            r"^# (.*?)$",
            r'<h1 style="color: #333; margin: 10px 0 5px 0;">\1</h1>',
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r"^## (.*?)$",
            r'<h2 style="color: #444; margin: 8px 0 4px 0;">\1</h2>',
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r"^### (.*?)$",
            r'<h3 style="color: #555; margin: 6px 0 3px 0;">\1</h3>',
            text,
            flags=re.MULTILINE,
        )

        # Lists with better styling
        text = re.sub(
            r"^- (.*?)$",
            r'<span style="color: #2196F3;">•</span> \1',
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r"^\* (.*?)$",
            r'<span style="color: #2196F3;">•</span> \1',
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r"^(\d+)\. (.*?)$",
            r'<span style="color: #2196F3;">\1.</span> \2',
            text,
            flags=re.MULTILINE,
        )

        # Links (basic support)
        text = re.sub(
            r"\[([^\]]+)\]\(([^\)]+)\)",
            r'<a href="\2" style="color: #2196F3; text-decoration: underline;">\1</a>',
            text,
        )

        # Line breaks
        text = text.replace("\n", "<br>")

        return text

    def _get_sender_style(self, sender: str) -> str:
        """Get style for sender name."""
        if sender.lower() == "you":
            return "font-weight: bold; color: #2196F3; font-size: 12px;"
        elif sender.lower() in ["ai", "assistant", "claude", "gpt", "gemini"]:
            return "font-weight: bold; color: #4CAF50; font-size: 12px;"
        elif sender.lower() == "system":
            return "font-weight: bold; color: #FF9800; font-size: 12px;"
        else:
            return "font-weight: bold; color: #666; font-size: 12px;"

    def _get_message_style(self, sender: str) -> str:
        """Get style for message content."""
        return "margin-top: 4px; font-size: 11px; line-height: 1.5;"

    def _get_background_color(self, sender: str) -> str:
        """Get background color for message block."""
        if sender.lower() == "you":
            return "#e3f2fd"
        elif sender.lower() in ["ai", "assistant", "claude", "gpt", "gemini"]:
            return "#e8f5e9"
        elif sender.lower() == "system":
            return "#fff3e0"
        else:
            return "#f5f5f5"

    def export_conversation(
        self, messages: list, format_type: ConversationFormat = None
    ) -> str:
        """Export entire conversation in specified format."""
        if format_type:
            original_format = self.format_type
            self.format_type = format_type

        exported = ""

        if self.format_type == ConversationFormat.MARKDOWN:
            exported = "# Conversation Export\n\n"
        elif self.format_type == ConversationFormat.HTML:
            exported = """
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                    .message { margin: 10px 0; padding: 10px; border-radius: 8px; }
                    .user { background-color: #e3f2fd; }
                    .ai { background-color: #e8f5e9; }
                    .system { background-color: #fff3e0; }
                </style>
            </head>
            <body>
                <h1>Conversation Export</h1>
            """

        for msg in messages:
            sender = msg.get("sender", "Unknown")
            content = msg.get("message", "")
            timestamp = msg.get("timestamp", "")

            if self.format_type == ConversationFormat.HTML:
                css_class = (
                    "user"
                    if sender.lower() == "you"
                    else "ai" if sender.lower() in ["ai", "assistant"] else "system"
                )
                exported += f'<div class="message {css_class}">'

            exported += self.format_message(sender, content, timestamp)

            if self.format_type == ConversationFormat.HTML:
                exported += "</div>"

        if self.format_type == ConversationFormat.HTML:
            exported += "</body></html>"

        if format_type:
            self.format_type = original_format

        return exported


class FormatSelectionWidget(QtWidgets.QWidget):
    """Widget for selecting conversation format."""

    format_changed = QtCore.Signal(ConversationFormat)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_format = ConversationFormat.RICH_TEXT
        self._setup_ui()

    def _setup_ui(self):
        """Setup the UI."""
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QtWidgets.QLabel("Format:"))

        self.format_combo = QtWidgets.QComboBox()
        self.format_combo.addItem("Rich Text", ConversationFormat.RICH_TEXT)
        self.format_combo.addItem("Plain Text", ConversationFormat.PLAIN_TEXT)
        self.format_combo.addItem("Markdown", ConversationFormat.MARKDOWN)
        self.format_combo.addItem("HTML", ConversationFormat.HTML)

        self.format_combo.currentIndexChanged.connect(self._on_format_changed)
        layout.addWidget(self.format_combo)

        layout.addStretch()

    def _on_format_changed(self, index):
        """Handle format change."""
        self.current_format = self.format_combo.itemData(index)
        self.format_changed.emit(self.current_format)

    def get_current_format(self) -> ConversationFormat:
        """Get current selected format."""
        return self.current_format
