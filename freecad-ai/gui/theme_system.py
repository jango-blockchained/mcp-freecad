"""Centralized Theme System for FreeCAD AI GUI Components - Material Design 3"""

from enum import Enum
from PySide2 import QtWidgets


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
        """Load colors based on theme - Material Design 3 inspired."""
        if self.theme == Theme.LIGHT:
            self.colors = {
                # Background colors - Material Design 3 surfaces
                "background_primary": "#fdfcff",
                "background_secondary": "#f5f5f5",
                "background_tertiary": "#eceff1",
                "background_accent": "#e7f2ff",
                "background_elevated": "#ffffff",
                "background_card": "#ffffff",
                # Text colors - MD3 on-surface variants
                "text_primary": "#1c1b1f",
                "text_secondary": "#49454f",
                "text_muted": "#73777f",
                "text_inverse": "#ffffff",
                "text_on_primary": "#ffffff",
                # Brand colors - MD3 primary/secondary scheme
                "primary": "#0061a6",
                "primary_container": "#d1e4ff",
                "on_primary": "#ffffff",
                "on_primary_container": "#001d35",
                "secondary": "#535f70",
                "secondary_container": "#d7e3f7",
                "on_secondary": "#ffffff",
                "on_secondary_container": "#101c2b",
                # Semantic colors
                "success": "#006e1c",
                "success_container": "#97f682",
                "on_success": "#ffffff",
                "on_success_container": "#002204",
                "warning": "#785900",
                "warning_container": "#ffdea6",
                "on_warning": "#ffffff",
                "on_warning_container": "#261900",
                "error": "#ba1a1a",
                "error_container": "#ffdad6",
                "on_error": "#ffffff",
                "on_error_container": "#410002",
                "info": "#0061a6",
                "info_container": "#d1e4ff",
                # Chat-specific colors - using MD3 containers
                "user_message_bg": "#d1e4ff",
                "ai_message_bg": "#97f682",
                "system_message_bg": "#ffdea6",
                "user_text": "#001d35",
                "ai_text": "#002204",
                "system_text": "#261900",
                # UI element colors
                "border": "#c4c6d0",
                "border_focus": "#0061a6",
                "border_light": "#e7e9f5",
                "divider": "#c4c6d0",
                "button_primary": "#0061a6",
                "button_success": "#006e1c",
                "button_warning": "#785900",
                "button_danger": "#ba1a1a",
                # Status colors
                "status_connected": "#006e1c",
                "status_warning": "#785900",
                "status_error": "#ba1a1a",
                "status_unknown": "#73777f",
                # Shadows and overlays
                "shadow": "rgba(0, 0, 0, 0.12)",
                "overlay": "rgba(0, 0, 0, 0.05)",
            }
        else:  # DARK theme - Material Design 3 dark surfaces
            self.colors = {
                # Background colors - MD3 dark surfaces
                "background_primary": "#1c1b1f",
                "background_secondary": "#2b2930",
                "background_tertiary": "#44464f",
                "background_accent": "#003258",
                "background_elevated": "#2b2930",
                "background_card": "#2b2930",
                # Text colors - MD3 on-surface dark
                "text_primary": "#e6e1e5",
                "text_secondary": "#cac4d0",
                "text_muted": "#938f99",
                "text_inverse": "#1c1b1f",
                "text_on_primary": "#003258",
                # Brand colors - MD3 dark primary/secondary
                "primary": "#a0caff",
                "primary_container": "#004881",
                "on_primary": "#003258",
                "on_primary_container": "#d1e4ff",
                "secondary": "#bbc7db",
                "secondary_container": "#3c4858",
                "on_secondary": "#253140",
                "on_secondary_container": "#d7e3f7",
                # Semantic colors - MD3 dark
                "success": "#7cda64",
                "success_container": "#005313",
                "on_success": "#003a09",
                "on_success_container": "#97f682",
                "warning": "#f5bf42",
                "warning_container": "#5d4200",
                "on_warning": "#3f2e00",
                "on_warning_container": "#ffdea6",
                "error": "#ffb4ab",
                "error_container": "#93000a",
                "on_error": "#690005",
                "on_error_container": "#ffdad6",
                "info": "#a0caff",
                "info_container": "#004881",
                # Chat-specific colors - MD3 dark containers
                "user_message_bg": "#003258",
                "ai_message_bg": "#003a09",
                "system_message_bg": "#3f2e00",
                "user_text": "#d1e4ff",
                "ai_text": "#97f682",
                "system_text": "#ffdea6",
                # UI element colors
                "border": "#44464f",
                "border_focus": "#a0caff",
                "border_light": "#2b2930",
                "divider": "#44464f",
                "button_primary": "#a0caff",
                "button_success": "#7cda64",
                "button_warning": "#f5bf42",
                "button_danger": "#ffb4ab",
                # Status colors
                "status_connected": "#7cda64",
                "status_warning": "#f5bf42",
                "status_error": "#ffb4ab",
                "status_unknown": "#938f99",
                # Shadows and overlays
                "shadow": "rgba(0, 0, 0, 0.30)",
                "overlay": "rgba(255, 255, 255, 0.05)",
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

    def get_button_style(self, button_type: str = "primary", elevated: bool = False) -> str:
        """Get button stylesheet with Material Design 3 principles.
        
        Args:
            button_type: Type of button (primary, success, warning, danger)
            elevated: Whether to add shadow elevation (default: False for backward compatibility)
        """
        color_map = {
            "primary": (self.colors.get_color("button_primary"), self.colors.get_color("on_primary")),
            "success": (self.colors.get_color("button_success"), self.colors.get_color("on_success")),
            "warning": (self.colors.get_color("button_warning"), self.colors.get_color("on_warning")),
            "danger": (self.colors.get_color("button_danger"), self.colors.get_color("on_error")),
        }

        base_color, text_color = color_map.get(button_type, (self.colors.get_color("primary"), self.colors.get_color("on_primary")))
        hover_color = self._lighten_color(base_color, 0.15)
        pressed_color = self._darken_color(base_color, 0.15)

        shadow = "box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);" if elevated else ""
        hover_shadow = "box-shadow: 0 3px 6px rgba(0,0,0,0.16), 0 3px 6px rgba(0,0,0,0.23);" if elevated else ""

        return f"""
        QPushButton {{
            background-color: {base_color};
            color: {text_color};
            border: none;
            padding: 10px 24px;
            border-radius: 20px;
            font-weight: 500;
            font-size: 14px;
            min-height: 36px;
            {shadow}
        }}
        QPushButton:hover {{
            background-color: {hover_color};
            {hover_shadow}
        }}
        QPushButton:pressed {{
            background-color: {pressed_color};
        }}
        QPushButton:disabled {{
            background-color: {self.colors.get_color("text_muted")};
            color: {self.colors.get_color("background_primary")};
        }}
        """

    def get_compact_button_style(self, button_type: str = "primary") -> str:
        """Get compact circular button stylesheet for icons.
        
        Args:
            button_type: Type of button (primary, success, warning, danger)
        """
        color_map = {
            "primary": (self.colors.get_color("button_primary"), self.colors.get_color("on_primary")),
            "success": (self.colors.get_color("button_success"), self.colors.get_color("on_success")),
            "warning": (self.colors.get_color("button_warning"), self.colors.get_color("on_warning")),
            "danger": (self.colors.get_color("button_danger"), self.colors.get_color("on_error")),
        }

        base_color, text_color = color_map.get(button_type, (self.colors.get_color("primary"), self.colors.get_color("on_primary")))
        hover_color = self.colors.get_color("primary_container") if button_type == "primary" else self._lighten_color(base_color, 0.2)

        return f"""
        QPushButton {{
            background-color: {base_color};
            color: {text_color};
            border: none;
            border-radius: 50%;
            font-size: 18px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {hover_color};
        }}
        QPushButton:pressed {{
            background-color: {self._darken_color(base_color, 0.1)};
        }}
        """

    def get_input_style(self) -> str:
        """Get input field stylesheet with Material Design 3 outlined style."""
        return f"""
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {self.colors.get_color("background_primary")};
            border: 1px solid {self.colors.get_color("border")};
            border-radius: 8px;
            padding: 12px 16px;
            color: {self.colors.get_color("text_primary")};
            font-size: 14px;
            selection-background-color: {self.colors.get_color("primary_container")};
        }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 2px solid {self.colors.get_color("border_focus")};
            padding: 11px 15px;
        }}
        QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
            background-color: {self.colors.get_color("background_secondary")};
            color: {self.colors.get_color("text_muted")};
        }}
        """

    def get_groupbox_style(self) -> str:
        """Get group box stylesheet with modern card design."""
        return f"""
        QGroupBox {{
            background-color: {self.colors.get_color("background_card")};
            border: 1px solid {self.colors.get_color("border_light")};
            border-radius: 12px;
            margin-top: 16px;
            padding: 16px;
            color: {self.colors.get_color("text_primary")};
            font-weight: 600;
            font-size: 14px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 16px;
            padding: 0 8px 0 8px;
            background-color: {self.colors.get_color("background_card")};
            color: {self.colors.get_color("primary")};
        }}
        """

    def get_conversation_style(self) -> str:
        """Get conversation display stylesheet with modern styling."""
        return f"""
        QTextBrowser {{
            background-color: {self.colors.get_color("background_primary")};
            border: 1px solid {self.colors.get_color("border_light")};
            border-radius: 12px;
            padding: 16px;
            color: {self.colors.get_color("text_primary")};
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            font-size: 14px;
            line-height: 1.5;
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
        """Get tab widget stylesheet with modern Material Design."""
        return f"""
        QTabWidget::pane {{
            border: none;
            background-color: {self.colors.get_color("background_primary")};
            border-radius: 12px;
            margin-top: 8px;
        }}
        QTabBar::tab {{
            background-color: transparent;
            color: {self.colors.get_color("text_secondary")};
            padding: 12px 24px;
            margin-right: 4px;
            border: none;
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
            font-weight: 500;
            font-size: 14px;
            min-width: 80px;
        }}
        QTabBar::tab:selected {{
            background-color: {self.colors.get_color("primary")};
            color: {self.colors.get_color("text_on_primary")};
        }}
        QTabBar::tab:hover:!selected {{
            background-color: {self.colors.get_rgba("primary", 0.12)};
            color: {self.colors.get_color("primary")};
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

    def _lighten_color(self, hex_color: str, factor: float) -> str:
        """Lighten a hex color by factor (0.0 to 1.0)."""
        if hex_color.startswith("#"):
            hex_color = hex_color[1:]

        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))

        return f"#{r:02x}{g:02x}{b:02x}"

    def get_card_style(self, elevated: bool = True) -> str:
        """Get card container stylesheet with Material Design elevation."""
        shadow = """
            border: 1px solid rgba(0, 0, 0, 0.04);
            background-color: {bg};
        """ if elevated else f"background-color: {self.colors.get_color('background_card')};"
        
        return f"""
        QFrame {{
            {shadow.format(bg=self.colors.get_color('background_card'))}
            border-radius: 16px;
            padding: 16px;
        }}
        """

    def get_chip_style(self, chip_type: str = "default") -> str:
        """Get chip/badge stylesheet for status indicators."""
        type_colors = {
            "default": (self.colors.get_color("background_secondary"), self.colors.get_color("text_primary")),
            "primary": (self.colors.get_color("primary_container"), self.colors.get_color("on_primary_container")),
            "success": (self.colors.get_color("success_container"), self.colors.get_color("on_success_container")),
            "warning": (self.colors.get_color("warning_container"), self.colors.get_color("on_warning_container")),
            "error": (self.colors.get_color("error_container"), self.colors.get_color("on_error_container")),
        }
        
        bg_color, text_color = type_colors.get(chip_type, type_colors["default"])
        
        return f"""
        QLabel {{
            background-color: {bg_color};
            color: {text_color};
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 12px;
            font-weight: 500;
        }}
        """

    def get_combobox_style(self) -> str:
        """Get combobox dropdown stylesheet."""
        return f"""
        QComboBox {{
            background-color: {self.colors.get_color("background_primary")};
            border: 1px solid {self.colors.get_color("border")};
            border-radius: 8px;
            padding: 10px 32px 10px 16px;
            color: {self.colors.get_color("text_primary")};
            font-size: 14px;
            min-height: 36px;
        }}
        QComboBox:hover {{
            border-color: {self.colors.get_color("primary")};
        }}
        QComboBox:focus {{
            border: 2px solid {self.colors.get_color("border_focus")};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 32px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {self.colors.get_color("text_secondary")};
            margin-right: 12px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {self.colors.get_color("background_elevated")};
            border: 1px solid {self.colors.get_color("border")};
            border-radius: 8px;
            padding: 4px;
            selection-background-color: {self.colors.get_color("primary_container")};
            selection-color: {self.colors.get_color("on_primary_container")};
        }}
        """


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
            widget.setStyleSheet(
                f"""
            QWidget {{
                background-color: {self.color_scheme.get_color("background_primary")};
                color: {self.color_scheme.get_color("text_primary")};
            }}
            """
            )

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
            if (
                "danger" in button.objectName().lower()
                or "delete" in button.text().lower()
                or "remove" in button.text().lower()
            ):
                button.setStyleSheet(self.stylesheet.get_button_style("danger"))
            elif (
                "success" in button.objectName().lower()
                or "save" in button.text().lower()
                or "connect" in button.text().lower()
            ):
                button.setStyleSheet(self.stylesheet.get_button_style("success"))
            elif "warning" in button.objectName().lower():
                button.setStyleSheet(self.stylesheet.get_button_style("warning"))
            else:
                button.setStyleSheet(self.stylesheet.get_button_style("primary"))

        # Style input fields
        inputs = widget.findChildren(QtWidgets.QLineEdit) + widget.findChildren(
            QtWidgets.QTextEdit
        ) + widget.findChildren(QtWidgets.QPlainTextEdit)
        for input_widget in inputs:
            input_widget.setStyleSheet(self.stylesheet.get_input_style())

        # Style combo boxes
        comboboxes = widget.findChildren(QtWidgets.QComboBox)
        for combobox in comboboxes:
            combobox.setStyleSheet(self.stylesheet.get_combobox_style())

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
