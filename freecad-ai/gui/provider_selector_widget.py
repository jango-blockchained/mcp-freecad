"""Shared Provider Selector Widget - Reusable provider selection component"""

from PySide2 import QtCore, QtWidgets


class ProviderSelectorWidget(QtWidgets.QWidget):
    """Reusable widget for provider selection with status indicators."""

    # Signals
    provider_changed = QtCore.Signal(str, str)  # provider_name, model_name
    refresh_requested = QtCore.Signal()

    def __init__(self, parent=None):
        super(ProviderSelectorWidget, self).__init__(parent)

        # Services
        self.provider_service = None
        self.config_manager = None

        # Current selection
        self.current_provider = None
        self.current_model = None

        # Available providers and their models
        self.available_providers = {}

        self._setup_ui()
        self._setup_services()

    def _setup_ui(self):
        """Setup the user interface with modern styling."""
        # Import theme system
        try:
            from .theme_system import get_theme_manager, get_current_color_scheme
            theme_manager = get_theme_manager()
            colors = get_current_color_scheme()
        except ImportError:
            theme_manager = None
            colors = None
            
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # Provider label
        provider_label = QtWidgets.QLabel("Provider:")
        if colors:
            provider_label.setStyleSheet(f"color: {colors.get_color('text_secondary')}; font-weight: 500;")
        layout.addWidget(provider_label)

        # Provider selection dropdown with modern styling
        self.provider_combo = QtWidgets.QComboBox()
        self.provider_combo.setMinimumWidth(140)
        self.provider_combo.setToolTip("Select AI provider")
        if theme_manager:
            self.provider_combo.setStyleSheet(theme_manager.stylesheet.get_combobox_style())
        self.provider_combo.currentTextChanged.connect(
            self._on_provider_selection_changed
        )
        layout.addWidget(self.provider_combo)

        # Model label
        model_label = QtWidgets.QLabel("Model:")
        if colors:
            model_label.setStyleSheet(f"color: {colors.get_color('text_secondary')}; font-weight: 500;")
        layout.addWidget(model_label)

        # Model selection dropdown with modern styling
        self.model_combo = QtWidgets.QComboBox()
        self.model_combo.setMinimumWidth(180)
        self.model_combo.setToolTip("Select model for current provider")
        if theme_manager:
            self.model_combo.setStyleSheet(theme_manager.stylesheet.get_combobox_style())
        self.model_combo.currentTextChanged.connect(self._on_model_selection_changed)
        layout.addWidget(self.model_combo)

        # Status indicator with modern chip style
        self.status_label = QtWidgets.QLabel("●")
        self.status_label.setFixedSize(28, 28)
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        self.status_label.setToolTip("Provider connection status")
        if colors:
            self.status_label.setStyleSheet(f"""
                font-size: 16px;
                border-radius: 14px;
                background-color: {colors.get_color("background_secondary")};
            """)
        self._update_status_indicator("unknown", "Checking...")
        layout.addWidget(self.status_label)

        # Refresh button with modern styling
        self.refresh_btn = QtWidgets.QPushButton("⟳")
        self.refresh_btn.setFixedSize(36, 36)
        self.refresh_btn.setToolTip("Refresh providers")
        if theme_manager:
            # Use primary button style but keep it compact
            self.refresh_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors.get_color("primary") if colors else "#0061a6"};
                    color: {colors.get_color("on_primary") if colors else "white"};
                    border: none;
                    border-radius: 18px;
                    font-size: 18px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {colors.get_color("primary_container") if colors else "#d1e4ff"};
                }}
            """)
        self.refresh_btn.clicked.connect(self._on_refresh_clicked)
        layout.addWidget(self.refresh_btn)

        layout.addStretch()

    def _setup_services(self):
        """Setup service connections."""
        # Services will be set via set_provider_service method
        pass

    def showEvent(self, event):
        """Handle show event to refresh providers when widget becomes visible."""
        super().showEvent(event)
        # Refresh providers when shown for the first time or if empty
        if not self.available_providers:
            print("ProviderSelector: Widget shown, refreshing providers...")
            self._refresh_providers()

    def set_provider_service(self, provider_service):
        """Set the provider service instance."""
        self.provider_service = provider_service

        # Connect to provider service signals
        if self.provider_service:
            # Connect to provider service signals
            if hasattr(self.provider_service, "provider_status_changed"):
                self.provider_service.provider_status_changed.connect(
                    self._on_provider_status_changed
                )
            if hasattr(self.provider_service, "providers_updated"):
                self.provider_service.providers_updated.connect(
                    self._on_providers_updated
                )
            if hasattr(self.provider_service, "provider_selection_changed"):
                self.provider_service.provider_selection_changed.connect(
                    self._on_external_provider_selection_changed
                )

            # Load current providers
            self._refresh_providers()

            # Restore current selection if available
            current_selection = self.provider_service.get_current_provider_selection()
            if current_selection["provider"]:
                self.set_current_selection(
                    current_selection["provider"], current_selection["model"]
                )

    def set_config_manager(self, config_manager):
        """Set the config manager instance."""
        self.config_manager = config_manager
        # Refresh providers when config manager becomes available
        if config_manager and not self.available_providers:
            self._refresh_providers()

    def refresh_on_show(self):
        """Refresh providers when widget becomes visible (e.g., tab activation)."""
        if not self.available_providers:
            print("ProviderSelector: Refreshing on show")
            self._refresh_providers()

    def _refresh_providers(self):
        """Refresh the list of available providers."""
        print("ProviderSelector: Refreshing providers...")

        if not self.provider_service:
            print("ProviderSelector: No provider service available")
            self._update_status_indicator("error", "Provider service not available")
            # Fall back to default providers if no service
            self._load_fallback_providers()
            return

        try:
            # Get active providers from service
            active_providers = self.provider_service.get_active_providers()
            all_providers = self.provider_service.get_all_providers()

            print(
                f"ProviderSelector: Active providers: {list(active_providers.keys()) if active_providers else 'None'}"
            )
            print(
                f"ProviderSelector: All providers: {list(all_providers.keys()) if all_providers else 'None'}"
            )

            # Update available providers dict
            self.available_providers = {}

            # Clear dropdowns
            self.provider_combo.clear()
            self.model_combo.clear()

            if not all_providers:
                print("ProviderSelector: No providers from service, using fallback")
                self._load_fallback_providers()
                return

            # Add providers to dropdown
            current_provider_found = False
            for provider_name, provider_info in all_providers.items():
                self.provider_combo.addItem(provider_name)

                # Get available models for this provider
                models = self._get_provider_models(provider_name, provider_info)
                self.available_providers[provider_name] = {
                    "models": models,
                    "status": (
                        "active" if provider_name in active_providers else "inactive"
                    ),
                    "info": provider_info,
                }

                # Check if this was the previously selected provider
                if provider_name == self.current_provider:
                    current_provider_found = True

            # Restore previous selection or select default
            if current_provider_found and self.current_provider:
                index = self.provider_combo.findText(self.current_provider)
                if index >= 0:
                    self.provider_combo.setCurrentIndex(index)
            elif self.provider_combo.count() > 0:
                # Select first provider as default
                self.provider_combo.setCurrentIndex(0)

            # Update status
            active_count = len(active_providers)
            total_count = len(all_providers)
            if active_count > 0:
                self._update_status_indicator(
                    "connected", f"{active_count}/{total_count} providers active"
                )
            else:
                self._update_status_indicator("warning", "No active providers")

        except Exception as e:
            print(f"ProviderSelector: Error refreshing providers: {e}")
            self._update_status_indicator("error", f"Error: {str(e)}")
            # Fall back to default providers on error
            self._load_fallback_providers()

    def _load_fallback_providers(self):
        """Load fallback default providers when service is unavailable."""
        print("ProviderSelector: Loading fallback providers")

        # Clear dropdowns
        self.provider_combo.clear()
        self.model_combo.clear()

        # Default providers that should always be available
        fallback_providers = {
            "Anthropic": {
                "type": "anthropic",
                "models": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"],
                "status": "inactive",
            },
            "OpenAI": {
                "type": "openai",
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
                "status": "inactive",
            },
            "Google": {
                "type": "google",
                "models": ["gemini-1.5-pro", "gemini-1.5-flash"],
                "status": "inactive",
            },
            "Google Vertex AI": {
                "type": "vertexai",
                "models": ["gemini-1.5-pro", "gemini-1.5-flash", "text-bison"],
                "status": "inactive",
            },
            "OpenRouter": {
                "type": "openrouter",
                "models": ["anthropic/claude-3.5-sonnet", "openai/gpt-4o"],
                "status": "inactive",
            },
        }

        self.available_providers = {}

        for provider_name, provider_data in fallback_providers.items():
            self.provider_combo.addItem(provider_name)
            self.available_providers[provider_name] = {
                "models": provider_data["models"],
                "status": provider_data["status"],
                "info": {"type": provider_data["type"]},
            }

        # Select first provider as default
        if self.provider_combo.count() > 0:
            self.provider_combo.setCurrentIndex(0)

        self._update_status_indicator(
            "warning", "Using default providers - configure in Providers tab"
        )

    def _get_provider_models(self, provider_name, provider_info):
        """Get available models for a provider."""
        try:
            # Try to get models from provider service first
            if self.provider_service and hasattr(
                self.provider_service, "get_provider_models"
            ):
                models = self.provider_service.get_provider_models(provider_name)
                if models:
                    return models

            # Try to get models from provider service (alternative method)
            if hasattr(self.provider_service, "get_provider_models"):
                models = self.provider_service.get_provider_models(provider_name)
                if models:
                    return models

            # Fallback to default models based on provider type
            provider_type = provider_info.get("type", "").lower()
            if not provider_type:
                # Try to infer from provider name
                provider_type = provider_name.lower()

            default_models = {
                "anthropic": [
                    "claude-3-5-sonnet-20241022",
                    "claude-3-5-haiku-20241022",
                    "claude-3-opus-20240229",
                ],
                "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
                "google": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"],
                "vertexai": [
                    "gemini-1.5-pro",
                    "gemini-1.5-flash",
                    "gemini-1.0-pro",
                    "text-bison",
                    "code-bison",
                ],
                "openrouter": [
                    "anthropic/claude-3.5-sonnet",
                    "openai/gpt-4o",
                    "google/gemini-pro",
                ],
            }

            return default_models.get(provider_type, ["default-model"])

        except Exception as e:
            print(f"ProviderSelector: Error getting models for {provider_name}: {e}")
            return ["default-model"]

    def _on_provider_selection_changed(self, provider_name):
        """Handle provider selection change."""
        if not provider_name or provider_name == "No providers configured":
            return

        self.current_provider = provider_name

        # Update model dropdown
        self._update_model_dropdown(provider_name)

        # Update status for selected provider
        if provider_name in self.available_providers:
            provider_data = self.available_providers[provider_name]
            status = provider_data["status"]
            if status == "active":
                self._update_status_indicator("connected", f"{provider_name} active")
            else:
                self._update_status_indicator("warning", f"{provider_name} inactive")

    def _update_model_dropdown(self, provider_name):
        """Update the model dropdown for the selected provider."""
        self.model_combo.clear()

        if provider_name not in self.available_providers:
            self.model_combo.addItem("No models available")
            return

        models = self.available_providers[provider_name]["models"]
        self.model_combo.addItems(models)

        # Try to restore previous model selection for this provider
        if self.current_provider == provider_name and self.current_model:
            index = self.model_combo.findText(self.current_model)
            if index >= 0:
                self.model_combo.setCurrentIndex(index)

        # If no previous selection, try to get default from config
        if self.config_manager and self.model_combo.currentText() == models[0]:
            try:
                provider_config = self.config_manager.get_provider_config(provider_name)
                if provider_config and "model" in provider_config:
                    default_model = provider_config["model"]
                    index = self.model_combo.findText(default_model)
                    if index >= 0:
                        self.model_combo.setCurrentIndex(index)
            except Exception as e:
                print(f"ProviderSelector: Error loading default model: {e}")

    def _on_model_selection_changed(self, model_name):
        """Handle model selection change."""
        if not model_name or model_name == "No models available":
            return

        self.current_model = model_name

        # Save the model selection via provider service
        if self.provider_service and self.current_provider:
            try:
                if hasattr(self.provider_service, "update_provider_model"):
                    success = self.provider_service.update_provider_model(
                        self.current_provider, model_name
                    )
                    if success:
                        print(
                            f"ProviderSelector: Updated model {model_name} for provider {self.current_provider}"
                        )
                    else:
                        print(
                            "ProviderSelector: Failed to update model via provider service"
                        )
                else:
                    print(
                        "ProviderSelector: Provider service doesn't support model updates"
                    )
            except Exception as e:
                print(
                    f"ProviderSelector: Error updating model via provider service: {e}"
                )

        # Fallback: Save to config manager directly
        if self.config_manager and self.current_provider:
            try:
                provider_config = self.config_manager.get_provider_config(
                    self.current_provider
                )
                if not provider_config:
                    provider_config = {}

                provider_config["model"] = model_name
                self.config_manager.set_provider_config(
                    self.current_provider, provider_config
                )

                print(
                    f"ProviderSelector: Saved model {model_name} for provider {self.current_provider}"
                )
            except Exception as e:
                print(f"ProviderSelector: Error saving model selection: {e}")

        # Emit signal for other components
        if self.current_provider:
            self.provider_changed.emit(self.current_provider, model_name)

    def _on_refresh_clicked(self):
        """Handle refresh button click."""
        self._refresh_providers()
        self.refresh_requested.emit()

    def _on_provider_status_changed(self, provider_name, status, message):
        """Handle provider status change signal."""
        # Update status if this is the currently selected provider
        if provider_name == self.current_provider:
            self._update_status_indicator(status, f"{provider_name}: {message}")

        # Update available providers data
        if provider_name in self.available_providers:
            self.available_providers[provider_name]["status"] = status

    def _on_providers_updated(self):
        """Handle providers list update signal."""
        self._refresh_providers()

    def _on_external_provider_selection_changed(self, provider_name, model_name):
        """Handle provider selection change from external signal."""
        if provider_name == self.current_provider and model_name == self.current_model:
            return  # No change

        # Update provider selection
        self.set_current_selection(provider_name, model_name)

    def _update_status_indicator(self, status, tooltip):
        """Update the status indicator with modern styling."""
        # Import theme colors
        try:
            from .theme_system import get_current_color_scheme
            colors = get_current_color_scheme()
            
            status_colors = {
                "connected": colors.get_color("status_connected"),
                "active": colors.get_color("status_connected"),
                "warning": colors.get_color("status_warning"),
                "inactive": colors.get_color("status_warning"),
                "error": colors.get_color("status_error"),
                "unknown": colors.get_color("status_unknown"),
            }
        except ImportError:
            # Fallback to Material Design 3 light theme colors
            status_colors = {
                "connected": "#006e1c",
                "active": "#006e1c",
                "warning": "#785900",
                "inactive": "#785900",
                "error": "#ba1a1a",
                "unknown": "#73777f",
            }

        color = status_colors.get(status, "#73777f")
        self.status_label.setStyleSheet(f"""
            color: {color}; 
            font-weight: bold; 
            font-size: 16px;
            border-radius: 14px;
            background-color: rgba(0, 0, 0, 0.05);
        """)
        self.status_label.setToolTip(tooltip)

    def get_current_selection(self):
        """Get the current provider and model selection."""
        return {"provider": self.current_provider, "model": self.current_model}

    def set_current_selection(self, provider_name, model_name=None):
        """Set the current provider and model selection."""
        # Set provider
        if provider_name:
            index = self.provider_combo.findText(provider_name)
            if index >= 0:
                self.provider_combo.setCurrentIndex(index)
                self.current_provider = provider_name

                # Update model dropdown
                self._update_model_dropdown(provider_name)

                # Set model if specified
                if model_name:
                    model_index = self.model_combo.findText(model_name)
                    if model_index >= 0:
                        self.model_combo.setCurrentIndex(model_index)
                        self.current_model = model_name

    def is_provider_available(self):
        """Check if a provider is currently available."""
        return (
            self.current_provider is not None
            and self.current_provider in self.available_providers
            and self.available_providers[self.current_provider]["status"] == "active"
        )
