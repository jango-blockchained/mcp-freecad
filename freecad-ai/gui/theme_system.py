"""Centralized Theme System for FreeCAD AI GUI Components"""

from enum import Enum
from PySide2 import QtCore, QtWidgets


class Theme(Enum):
    """Available themes."""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"  # Follow system theme


class ColorScheme:
    """Color scheme definitions."""
    
    def __init__(self, theme: Theme = Theme.LIGHT):
        self.theme = theme
        self._load_colors()
        
    def _load_colors(self):
        """Load colors based on theme."""
        if self.theme == Theme.LIGHT:
            self.colors = {
                # Background colors
                "background_primary": "#ffffff",
                "background_secondary": "#f8f9fa",
                "background_tertiary": "#e9ecef",
                "background_accent": "#e3f2fd",
                
                # Text colors
                "text_primary": "#212529",
                "text_secondary": "#6c757d",
                "text_muted": "#adb5bd",
                "text_inverse": "#ffffff",
                
                # Brand colors
                "primary": "#2196F3",
                "secondary": "#6c757d",
                "success": "#4CAF50",
                "warning": "#FF9800",
                "error": "#f44336",
                "info": "#17a2b8",
                
                # Chat-specific colors
                "user_message_bg": "#e3f2fd",
                "ai_message_bg": "#e8f5e9",
                "system_message_bg": "#fff3e0",
                "user_text": "#2196F3",
                "ai_text": "#4CAF50",
                "system_text": "#FF9800",
                
                # UI element colors
                "border": "#dee2e6",
                "border_focus": "#2196F3",
                "button_primary": "#2196F3",
                "button_success": "#4CAF50",
                "button_warning": "#FF9800",
                "button_danger": "#f44336",
                
                # Status colors
                "status_connected": "#4CAF50",
                "status_warning": "#FF9800", 
                "status_error": "#f44336",
                "status_unknown": "#9E9E9E",
            }
        else:  # DARK theme
            self.colors = {
                # Background colors
                "background_primary": "#1a1a1a",
                "background_secondary": "#2d2d2d",
                "background_tertiary": "#3a3a3a",
                "background_accent": "#1e3a5f",
                
                # Text colors
                "text_primary": "#ffffff",
                "text_secondary": "#b3b3b3",
                "text_muted": "#808080",
                "text_inverse": "#000000",
                
                # Brand colors (slightly adjusted for dark theme)
                "primary": "#42A5F5",
                "secondary": "#9e9e9e",
                "success": "#66BB6A",
                "warning": "#FFA726",
                "error": "#EF5350",
                "info": "#29B6F6",
                
                # Chat-specific colors
                "user_message_bg": "#1e3a5f",
                "ai_message_bg": "#2e5d33",
                "system_message_bg": "#4a3326",
                "user_text": "#42A5F5",
                "ai_text": "#66BB6A",
                "system_text": "#FFA726",
                
                # UI element colors
                "border": "#4a4a4a",
                "border_focus": "#42A5F5",
                "button_primary": "#42A5F5",
                "button_success": "#66BB6A",
                "button_warning": "#FFA726",
                "button_danger": "#EF5350",
                
                # Status colors
                "status_connected": "#66BB6A",
                "status_warning": "#FFA726",
                "status_error": "#EF5350", 
                "status_unknown": "#9E9E9E",
            }
    
    def get_color(self, color_name: str) -> str:
        """Get color by name."""
        return self.colors.get(color_name, "#000000")
        
    def get_rgba(self, color_name: str, alpha: float = 1.0) -> str:
        """Get color as rgba string."""
        hex_color = self.get_color(color_name)
        if hex_color.startswith("#"):
            hex_color = hex_color[1:]
            
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        return f"rgba({r}, {g}, {b}, {alpha})"


class StyleSheet:
    """Generate consistent stylesheets."""
    
    def __init__(self, color_scheme: ColorScheme):
        self.colors = color_scheme
        
    def get_button_style(self, button_type: str = "primary") -> str:
        """Get button stylesheet."""
        color_map = {
            "primary": self.colors.get_color("button_primary"),
            "success": self.colors.get_color("button_success"),
            "warning": self.colors.get_color("button_warning"),
            "danger": self.colors.get_color("button_danger"),
        }
        
        base_color = color_map.get(button_type, self.colors.get_color("primary"))
        hover_color = self._darken_color(base_color, 0.1)
        
        return f"""
        QPushButton {{
            background-color: {base_color};
            color: {self.colors.get_color("text_inverse")};
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {hover_color};
        }}
        QPushButton:pressed {{
            background-color: {self._darken_color(base_color, 0.2)};
        }}
        QPushButton:disabled {{
            background-color: {self.colors.get_color("text_muted")};
        }}
        """
        
    def get_input_style(self) -> str:
        """Get input field stylesheet."""
        return f"""
        QLineEdit, QTextEdit {{
            background-color: {self.colors.get_color("background_primary")};
            border: 2px solid {self.colors.get_color("border")};
            border-radius: 4px;
            padding: 8px;
            color: {self.colors.get_color("text_primary")};
        }}
        QLineEdit:focus, QTextEdit:focus {{
            border-color: {self.colors.get_color("border_focus")};
        }}
        """
        
    def get_groupbox_style(self) -> str:
        """Get group box stylesheet."""
        return f"""
        QGroupBox {{
            background-color: {self.colors.get_color("background_secondary")};
            border: 1px solid {self.colors.get_color("border")};
            border-radius: 6px;
            margin-top: 10px;
            padding-top: 10px;
            color: {self.colors.get_color("text_primary")};
            font-weight: bold;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }}
        """
        
    def get_conversation_style(self) -> str:
        """Get conversation display stylesheet."""
        return f"""
        QTextBrowser {{
            background-color: {self.colors.get_color("background_primary")};
            border: 1px solid {self.colors.get_color("border")};
            border-radius: 4px;
            padding: 10px;
            color: {self.colors.get_color("text_primary")};
            font-family: Arial, sans-serif;
        }}
        """
        
    def get_status_indicator_style(self, status: str) -> str:
        """Get status indicator stylesheet."""
        status_colors = {
            "connected": self.colors.get_color("status_connected"),
            "warning": self.colors.get_color("status_warning"),
            "error": self.colors.get_color("status_error"),
            "unknown": self.colors.get_color("status_unknown"),
        }
        
        color = status_colors.get(status, self.colors.get_color("status_unknown"))
        
        return f"""
        QLabel {{
            color: {color};
            font-weight: bold;
            font-size: 16px;
        }}
        """
        
    def get_tab_style(self) -> str:
        """Get tab widget stylesheet."""
        return f"""
        QTabWidget::pane {{
            border: 1px solid {self.colors.get_color("border")};
            background-color: {self.colors.get_color("background_primary")};
        }}
        QTabBar::tab {{
            background-color: {self.colors.get_color("background_secondary")};
            color: {self.colors.get_color("text_primary")};
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        QTabBar::tab:selected {{
            background-color: {self.colors.get_color("primary")};
            color: {self.colors.get_color("text_inverse")};
        }}
        QTabBar::tab:hover {{
            background-color: {self.colors.get_rgba("primary", 0.2)};
        }}
        """
        
    def _darken_color(self, hex_color: str, factor: float) -> str:
        """Darken a hex color by factor (0.0 to 1.0)."""
        if hex_color.startswith("#"):
            hex_color = hex_color[1:]
            
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        r = max(0, int(r * (1 - factor)))
        g = max(0, int(g * (1 - factor)))
        b = max(0, int(b * (1 - factor)))
        
        return f"#{r:02x}{g:02x}{b:02x}"


class ThemeManager:
    """Manages themes across the application."""
    
    def __init__(self):
        self.current_theme = Theme.LIGHT
        self.color_scheme = ColorScheme(self.current_theme)
        self.stylesheet = StyleSheet(self.color_scheme)
        self._theme_changed_callbacks = []
        
    def set_theme(self, theme: Theme):
        """Set application theme."""
        if theme == self.current_theme:
            return
            
        self.current_theme = theme
        self.color_scheme = ColorScheme(theme)
        self.stylesheet = StyleSheet(self.color_scheme)
        
        # Notify callbacks
        for callback in self._theme_changed_callbacks:
            try:
                callback(theme)
            except Exception as e:
                print(f"ThemeManager: Error in theme change callback: {e}")
                
    def register_theme_change_callback(self, callback):
        """Register callback for theme changes."""
        self._theme_changed_callbacks.append(callback)
        
    def apply_theme_to_widget(self, widget: QtWidgets.QWidget):
        """Apply current theme to a widget."""
        try:
            # Apply base styling
            widget.setStyleSheet(f"""
            QWidget {{
                background-color: {self.color_scheme.get_color("background_primary")};
                color: {self.color_scheme.get_color("text_primary")};
            }}
            """)
            
            # Apply specific styling based on widget type
            self._apply_specific_styling(widget)
            
        except Exception as e:
            print(f"ThemeManager: Error applying theme to widget: {e}")
            
    def _apply_specific_styling(self, widget: QtWidgets.QWidget):
        """Apply theme-specific styling to widget types."""
        # Find and style specific widget types
        buttons = widget.findChildren(QtWidgets.QPushButton)
        for button in buttons:
            # Determine button type from style or text
            if "danger" in button.objectName().lower() or "delete" in button.text().lower():
                button.setStyleSheet(self.stylesheet.get_button_style("danger"))
            elif "success" in button.objectName().lower() or "save" in button.text().lower():
                button.setStyleSheet(self.stylesheet.get_button_style("success"))
            elif "warning" in button.objectName().lower():
                button.setStyleSheet(self.stylesheet.get_button_style("warning"))
            else:
                button.setStyleSheet(self.stylesheet.get_button_style("primary"))
                
        # Style input fields
        inputs = widget.findChildren(QtWidgets.QLineEdit) + widget.findChildren(QtWidgets.QTextEdit)
        for input_widget in inputs:
            input_widget.setStyleSheet(self.stylesheet.get_input_style())
            
        # Style group boxes
        groupboxes = widget.findChildren(QtWidgets.QGroupBox)
        for groupbox in groupboxes:
            groupbox.setStyleSheet(self.stylesheet.get_groupbox_style())
            
        # Style tab widgets
        tabwidgets = widget.findChildren(QtWidgets.QTabWidget)
        for tabwidget in tabwidgets:
            tabwidget.setStyleSheet(self.stylesheet.get_tab_style())


# Global theme manager instance
_theme_manager = None

def get_theme_manager() -> ThemeManager:
    """Get global theme manager instance."""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager


def apply_theme_to_widget(widget: QtWidgets.QWidget, theme: Theme = None):
    """Convenience function to apply theme to widget."""
    manager = get_theme_manager()
    if theme and theme != manager.current_theme:
        manager.set_theme(theme)
    manager.apply_theme_to_widget(widget)


def get_current_color_scheme() -> ColorScheme:
    """Get current color scheme."""
    return get_theme_manager().color_scheme


def get_current_stylesheet() -> StyleSheet:
    """Get current stylesheet generator."""
    return get_theme_manager().stylesheet
