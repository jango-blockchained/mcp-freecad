"""
Provider Integration Service - Coordinates AI provider connections across the addon

This service bridges the gap between configuration management (API keys),
AI provider instances, and GUI components to provide seamless AI provider
connection functionality.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
from PySide2 import QtCore
from .ai_manager import AIManager
from .claude_provider import ClaudeProvider
from .gemini_provider import GeminiProvider
from .openrouter_provider import OpenRouterProvider


class ProviderIntegrationService(QtCore.QObject):
    """Service that coordinates AI provider integration across the addon."""

    # Signals for provider status changes
    provider_added = QtCore.Signal(str, str)  # provider_name, provider_type
    provider_removed = QtCore.Signal(str)  # provider_name
    provider_status_changed = QtCore.Signal(str, str, str)  # provider_name, status, message
    providers_updated = QtCore.Signal()  # general providers list updated

    _instance = None

    def __new__(cls):
        """Singleton pattern to ensure only one service instance."""
        if cls._instance is None:
            cls._instance = super(ProviderIntegrationService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the provider integration service."""
        if hasattr(self, '_initialized'):
            return

        super(ProviderIntegrationService, self).__init__()
        self.logger = logging.getLogger(__name__)

        # Core components
        self.config_manager = None
        self.ai_manager = AIManager()

        # Provider status tracking
        self.provider_status: Dict[str, Dict[str, Any]] = {}

        # Connection callbacks
        self.status_callbacks: List[Callable] = []

        # Initialize service
        self._setup_config_manager()
        self._initialized = True

    def _setup_config_manager(self):
        """Setup configuration manager integration."""
        try:
            from ..config.config_manager import ConfigManager
            self.config_manager = ConfigManager()
            self.logger.info("ConfigManager integration established")
        except ImportError as e:
            self.logger.error(f"Failed to setup ConfigManager: {e}")
            self.config_manager = None

    def initialize_providers_from_config(self) -> bool:
        """Initialize AI providers based on saved configuration."""
        if not self.config_manager:
            self.logger.error("ConfigManager not available")
            return False

        try:
            # Get available providers and their API keys
            providers_to_init = ["openai", "anthropic", "google"]
            initialized_count = 0

            for provider_name in providers_to_init:
                api_key = self.config_manager.get_api_key(provider_name)
                provider_config = self.config_manager.get_provider_config(provider_name)

                if api_key and provider_config.get("enabled", False):
                    success = self._initialize_provider(provider_name, api_key, provider_config)
                    if success:
                        initialized_count += 1
                        self.logger.info(f"Initialized provider: {provider_name}")

            self.logger.info(f"Initialized {initialized_count} providers from configuration")
            self.providers_updated.emit()
            return initialized_count > 0

        except Exception as e:
            self.logger.error(f"Error initializing providers from config: {e}")
            return False

    def _initialize_provider(self, provider_name: str, api_key: str, config: Dict[str, Any]) -> bool:
        """Initialize a specific AI provider."""
        try:
            # Map provider names to types
            provider_type_map = {
                "openai": "openrouter",  # Using OpenRouter for OpenAI compatibility
                "anthropic": "claude",
                "google": "gemini"
            }

            provider_type = provider_type_map.get(provider_name, provider_name)

            # Add provider to AI manager
            success = self.ai_manager.add_provider(
                name=f"{provider_name}_main",
                provider_type=provider_type,
                api_key=api_key,
                config=config
            )

            if success:
                # Initialize provider status
                self.provider_status[provider_name] = {
                    "type": provider_type,
                    "status": "initialized",
                    "message": "Provider initialized successfully",
                    "last_test": None,
                    "config": config
                }

                # Emit signals
                self.provider_added.emit(provider_name, provider_type)
                self.provider_status_changed.emit(provider_name, "initialized", "Provider ready")

                return True
            else:
                self.logger.error(f"Failed to add provider {provider_name} to AI manager")
                return False

        except Exception as e:
            self.logger.error(f"Error initializing provider {provider_name}: {e}")
            self._update_provider_status(provider_name, "error", str(e))
            return False

    def add_provider(self, provider_name: str, api_key: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """Add a new AI provider with the given configuration."""
        if not self.config_manager:
            return False

        try:
            # Save API key to config
            if not self.config_manager.set_api_key(provider_name, api_key):
                return False

            # Save provider config
            if config:
                if not self.config_manager.set_provider_config(provider_name, config):
                    return False

            # Initialize the provider
            effective_config = config or self.config_manager.get_provider_config(provider_name)
            return self._initialize_provider(provider_name, api_key, effective_config)

        except Exception as e:
            self.logger.error(f"Error adding provider {provider_name}: {e}")
            return False

    def remove_provider(self, provider_name: str) -> bool:
        """Remove an AI provider."""
        try:
            # Remove from AI manager
            ai_manager_name = f"{provider_name}_main"
            self.ai_manager.remove_provider(ai_manager_name)

            # Remove from status tracking
            if provider_name in self.provider_status:
                del self.provider_status[provider_name]

            # Emit signals
            self.provider_removed.emit(provider_name)
            self.providers_updated.emit()

            return True

        except Exception as e:
            self.logger.error(f"Error removing provider {provider_name}: {e}")
            return False

    def test_provider_connection(self, provider_name: str) -> None:
        """Test connection to a specific provider (async)."""
        if provider_name not in self.provider_status:
            self.provider_status_changed.emit(provider_name, "error", "Provider not found")
            return

        # Update status to testing
        self._update_provider_status(provider_name, "testing", "Testing connection...")

        # Perform async test
        QtCore.QTimer.singleShot(100, lambda: self._perform_connection_test(provider_name))

    def _perform_connection_test(self, provider_name: str):
        """Perform the actual connection test."""
        try:
            ai_manager_name = f"{provider_name}_main"
            provider = self.ai_manager.providers.get(ai_manager_name)

            if not provider:
                self._update_provider_status(provider_name, "error", "Provider not initialized")
                return

            # Try to validate the provider
            if hasattr(provider, 'validate_connection'):
                # Use provider's validation method if available
                result = provider.validate_connection()
                if result:
                    self._update_provider_status(provider_name, "connected", "Connection successful")
                else:
                    self._update_provider_status(provider_name, "error", "Connection failed")
            else:
                # Fallback: basic API key validation
                api_key = self.config_manager.get_api_key(provider_name) if self.config_manager else None
                if api_key and len(api_key) > 20:
                    self._update_provider_status(provider_name, "connected", "API key format valid")
                else:
                    self._update_provider_status(provider_name, "error", "Invalid API key")

        except Exception as e:
            self._update_provider_status(provider_name, "error", f"Test failed: {str(e)}")

    def _update_provider_status(self, provider_name: str, status: str, message: str):
        """Update provider status and notify listeners."""
        if provider_name not in self.provider_status:
            self.provider_status[provider_name] = {}

        self.provider_status[provider_name].update({
            "status": status,
            "message": message,
            "last_test": QtCore.QDateTime.currentDateTime().toString()
        })

        # Emit signal
        self.provider_status_changed.emit(provider_name, status, message)

        # Call registered callbacks
        for callback in self.status_callbacks:
            try:
                callback(provider_name, status, message)
            except Exception as e:
                self.logger.error(f"Error in status callback: {e}")

    def get_provider_status(self, provider_name: str) -> Dict[str, Any]:
        """Get current status of a provider."""
        return self.provider_status.get(provider_name, {
            "status": "unknown",
            "message": "Provider not found",
            "last_test": None
        })

    def get_all_providers(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers."""
        return self.provider_status.copy()

    def get_active_providers(self) -> List[str]:
        """Get list of active (connected) providers."""
        return [
            name for name, status in self.provider_status.items()
            if status.get("status") == "connected"
        ]

    def register_status_callback(self, callback: Callable):
        """Register a callback for provider status changes."""
        if callback not in self.status_callbacks:
            self.status_callbacks.append(callback)

    def unregister_status_callback(self, callback: Callable):
        """Unregister a status callback."""
        if callback in self.status_callbacks:
            self.status_callbacks.remove(callback)

    def update_provider_from_settings(self, provider_name: str):
        """Update provider configuration when settings change."""
        if not self.config_manager:
            return

        try:
            api_key = self.config_manager.get_api_key(provider_name)
            config = self.config_manager.get_provider_config(provider_name)

            if api_key and config.get("enabled", False):
                # Re-initialize provider with new settings
                self.remove_provider(provider_name)
                self._initialize_provider(provider_name, api_key, config)
            else:
                # Remove provider if disabled or no API key
                self.remove_provider(provider_name)

        except Exception as e:
            self.logger.error(f"Error updating provider {provider_name} from settings: {e}")

    def send_message_to_provider(self, provider_name: str, message: str, context: Optional[Dict] = None) -> str:
        """Send a message to a specific provider."""
        try:
            ai_manager_name = f"{provider_name}_main"

            # Use asyncio.run for async call (simplified for Qt integration)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    self.ai_manager.send_message(message, ai_manager_name, context)
                )
                return result
            finally:
                loop.close()

        except Exception as e:
            self.logger.error(f"Error sending message to provider {provider_name}: {e}")
            return f"Error: {str(e)}"


# Global service instance
_service_instance = None

def get_provider_service() -> ProviderIntegrationService:
    """Get the global provider integration service instance."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ProviderIntegrationService()
    return _service_instance
