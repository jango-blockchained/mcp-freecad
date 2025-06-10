"""
Provider Integration Service - Coordinates AI provider connections across the addon

This service bridges the gap between configuration management (API keys),
AI provider instances, and GUI components to provide seamless AI provider
connection functionality.
"""

import os
import sys

# Ensure the addon directory is in the Python path
addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if addon_dir not in sys.path:
    sys.path.insert(0, addon_dir)

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional
import datetime

# Import using multiple strategies to handle different file locations
ai_manager_imported = False
providers_imported = False

# Strategy 1: Try providers subdirectory first (preferred structure)
try:
    from .ai_manager import AIManager
    from .providers.claude_provider import ClaudeProvider
    from .providers.gemini_provider import GeminiProvider
    from .providers.openrouter_provider import OpenRouterProvider

    ai_manager_imported = True
    providers_imported = True
    logging.info("Imported AI components from providers subdirectory")
except ImportError as e:
    logging.warning(f"Could not import from providers subdirectory: {e}")

# Strategy 2: Try direct imports from ai directory (legacy structure)
if not providers_imported:
    try:
        from ai.ai_manager import AIManager
        from ai.claude_provider import ClaudeProvider
        from ai.gemini_provider import GeminiProvider
        from ai.openrouter_provider import OpenRouterProvider

        ai_manager_imported = True
        providers_imported = True
        logging.info("Imported AI components from ai directory (legacy)")
    except ImportError as e:
        logging.warning(f"Could not import from ai directory: {e}")

# Strategy 3: Try absolute imports with providers subdirectory
if not providers_imported:
    try:
        from ai.ai_manager import AIManager
        from ai.providers.claude_provider import ClaudeProvider
        from ai.providers.gemini_provider import GeminiProvider
        from ai.providers.openrouter_provider import OpenRouterProvider

        ai_manager_imported = True
        providers_imported = True
        logging.info(
            "Imported AI components using absolute imports with providers subdirectory"
        )
    except ImportError as e:
        logging.warning(f"Could not import with absolute paths: {e}")

# Strategy 4: Fallback imports with module references
if not providers_imported:
    try:
        import ai.ai_manager
        import ai.providers.claude_provider
        import ai.providers.gemini_provider
        import ai.providers.openrouter_provider

        AIManager = ai.ai_manager.AIManager
        ClaudeProvider = ai.providers.claude_provider.ClaudeProvider
        GeminiProvider = ai.providers.gemini_provider.GeminiProvider
        OpenRouterProvider = ai.providers.openrouter_provider.OpenRouterProvider
        ai_manager_imported = True
        providers_imported = True
        logging.info("Imported AI components using module references")
    except ImportError:
        # Try legacy locations
        try:
            import ai.ai_manager
            import ai.claude_provider
            import ai.gemini_provider
            import ai.openrouter_provider

            AIManager = ai.ai_manager.AIManager
            ClaudeProvider = ai.claude_provider.ClaudeProvider
            GeminiProvider = ai.gemini_provider.GeminiProvider
            OpenRouterProvider = ai.openrouter_provider.OpenRouterProvider
            ai_manager_imported = True
            providers_imported = True
            logging.info("Imported AI components from legacy locations")
        except ImportError as e:
            logging.error(f"All import strategies failed: {e}")

# Final fallback: Create dummy classes if all imports fail
if not providers_imported:
    logging.error("Creating dummy AI classes as fallback")

    class AIManager:
        def __init__(self):
            self.providers = {}
            logging.warning("Using dummy AIManager - no real functionality")

        def add_provider(self, **kwargs):
            logging.warning("Dummy AIManager: add_provider called")
            return False

        def remove_provider(self, name):
            logging.warning("Dummy AIManager: remove_provider called")
            return False

        def get_providers(self):
            return {}

    class ClaudeProvider:
        def __init__(self, **kwargs):
            logging.warning("Using dummy ClaudeProvider")

    class GeminiProvider:
        def __init__(self, **kwargs):
            logging.warning("Using dummy GeminiProvider")

    class OpenRouterProvider:
        def __init__(self, **kwargs):
            logging.warning("Using dummy OpenRouterProvider")


# SignalHolder class removed - Qt signals will be created dynamically when needed


class ProviderIntegrationService:
    """Service that coordinates AI provider integration across the addon."""

    _instance = None

    def __new__(cls):
        """Singleton pattern to ensure only one service instance."""
        if cls._instance is None:
            cls._instance = super(ProviderIntegrationService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the provider integration service."""
        # Check if already initialized (singleton)
        if hasattr(self, "_initialized"):
            return

        self.logger = logging.getLogger(__name__)

        # Core components
        self.config_manager = None
        self.ai_manager = AIManager()

        # Provider status tracking
        self.provider_status: Dict[str, Dict[str, Any]] = {}

        # Connection callbacks
        self.status_callbacks: List[Callable] = []
        self.provider_added_callbacks: List[Callable] = []
        self.provider_removed_callbacks: List[Callable] = []
        self.provider_status_changed_callbacks: List[Callable] = []
        self.providers_updated_callbacks: List[Callable] = []
        self.provider_selection_changed_callbacks: List[Callable] = []

        # Current provider selection for synchronization
        self.current_provider_selection = {'provider': None, 'model': None}

        # Flag to prevent callback calls during early initialization
        self._callbacks_enabled = False

        # Initialize service
        self._setup_config_manager()
        self._initialized = True

    # Signal-like callback interface
    @property
    def provider_added(self):
        """Signal-like interface for provider_added callbacks."""

        class CallbackSignal:
            def __init__(self, callbacks):
                self.callbacks = callbacks

            def connect(self, callback):
                if callback not in self.callbacks:
                    self.callbacks.append(callback)
                logging.debug(f"Connected callback to provider_added: {callback}")

            def emit(self, *args):
                for callback in self.callbacks:
                    try:
                        callback(*args)
                    except Exception as e:
                        logging.error(f"Error in provider_added callback: {e}")

        return CallbackSignal(self.provider_added_callbacks)

    @property
    def provider_removed(self):
        """Signal-like interface for provider_removed callbacks."""

        class CallbackSignal:
            def __init__(self, callbacks):
                self.callbacks = callbacks

            def connect(self, callback):
                if callback not in self.callbacks:
                    self.callbacks.append(callback)
                logging.debug(f"Connected callback to provider_removed: {callback}")

            def emit(self, *args):
                for callback in self.callbacks:
                    try:
                        callback(*args)
                    except Exception as e:
                        logging.error(f"Error in provider_removed callback: {e}")

        return CallbackSignal(self.provider_removed_callbacks)

    @property
    def provider_status_changed(self):
        """Signal-like interface for provider_status_changed callbacks."""

        class CallbackSignal:
            def __init__(self, callbacks):
                self.callbacks = callbacks

            def connect(self, callback):
                if callback not in self.callbacks:
                    self.callbacks.append(callback)
                logging.debug(
                    f"Connected callback to provider_status_changed: {callback}"
                )

            def emit(self, *args):
                for callback in self.callbacks:
                    try:
                        callback(*args)
                    except Exception as e:
                        logging.error(f"Error in provider_status_changed callback: {e}")

        return CallbackSignal(self.provider_status_changed_callbacks)

    @property
    def providers_updated(self):
        """Signal-like interface for providers_updated callbacks."""

        class CallbackSignal:
            def __init__(self, callbacks):
                self.callbacks = callbacks

            def connect(self, callback):
                if callback not in self.callbacks:
                    self.callbacks.append(callback)
                logging.debug(f"Connected callback to providers_updated: {callback}")

            def emit(self, *args):
                for callback in self.callbacks:
                    try:
                        callback(*args)
                    except Exception as e:
                        logging.error(f"Error in providers_updated callback: {e}")

        return CallbackSignal(self.providers_updated_callbacks)

    @property
    def provider_selection_changed(self):
        """Signal-like interface for provider_selection_changed callbacks."""

        class CallbackSignal:
            def __init__(self, callbacks):
                self.callbacks = callbacks

            def connect(self, callback):
                if callback not in self.callbacks:
                    self.callbacks.append(callback)
                logging.debug(f"Connected callback to provider_selection_changed: {callback}")

            def emit(self, *args):
                for callback in self.callbacks:
                    try:
                        callback(*args)
                    except Exception as e:
                        logging.error(f"Error in provider_selection_changed callback: {e}")

        return CallbackSignal(self.provider_selection_changed_callbacks)

    def _setup_config_manager(self):
        """Setup configuration manager integration."""
        try:
            # Import ConfigManager using absolute path after sys.path setup
            from config.config_manager import ConfigManager

            self.config_manager = ConfigManager()
            self.logger.info("ConfigManager integration established")
        except ImportError as e:
            self.logger.error(f"Failed to setup ConfigManager: {e}")
            self.config_manager = None

    def _normalize_provider_name(self, provider_name: str) -> str:
        """Normalize provider name to lowercase for consistent handling."""
        return provider_name.lower()

    def _resolve_provider_name(self, provider_name: str) -> str:
        """Resolve provider name to the correct format, handling both capitalized and lowercase variants."""
        if not provider_name:
            return provider_name

        # Check if we have both formats in config and prefer the enabled one
        if self.config_manager:
            lowercase_name = provider_name.lower()
            capitalized_name = self._get_provider_display_name(lowercase_name)

            # Check which format exists and is enabled
            lowercase_config = self.config_manager.get_provider_config(lowercase_name)
            capitalized_config = self.config_manager.get_provider_config(capitalized_name)

            # If both exist, prefer the enabled one
            if lowercase_config and capitalized_config:
                if capitalized_config.get("enabled", False) and not lowercase_config.get(
                    "enabled", False
                ):
                    return capitalized_name
                elif lowercase_config.get("enabled", False) and not capitalized_config.get(
                    "enabled", False
                ):
                    return lowercase_name
                # If both enabled or both disabled, prefer capitalized format
                return capitalized_name
            elif capitalized_config:
                return capitalized_name
            elif lowercase_config:
                return lowercase_name

        # Fallback to display name format
        return self._get_provider_display_name(provider_name)

    def _cleanup_duplicate_providers(self) -> bool:
        """Clean up duplicate provider entries in configuration, keeping the enabled ones."""
        if not self.config_manager:
            return False

        try:
            self.logger.info("Cleaning up duplicate provider entries...")

            # Get all provider configs
            all_configs = {}
            config_data = self.config_manager.config_data.get("providers", {})

            for provider_name, config in config_data.items():
                all_configs[provider_name] = config

            # Group by normalized name to find duplicates
            provider_groups = {}
            for provider_name in all_configs.keys():
                normalized = self._normalize_provider_name(provider_name)
                if normalized not in provider_groups:
                    provider_groups[normalized] = []
                provider_groups[normalized].append(provider_name)

            # Process duplicates
            changes_made = False
            for normalized_name, variants in provider_groups.items():
                if len(variants) > 1:
                    self.logger.info(f"Found duplicate providers for {normalized_name}: {variants}")

                    # Find the best variant to keep
                    enabled_variants = [v for v in variants if all_configs[v].get("enabled", False)]

                    if enabled_variants:
                        # Keep the first enabled variant (prefer capitalized)
                        capitalized_variants = [v for v in enabled_variants if v != v.lower()]
                        keep_variant = capitalized_variants[0] if capitalized_variants else enabled_variants[0]
                    else:
                        # No enabled variants, keep capitalized format if available
                        capitalized_variants = [v for v in variants if v != v.lower()]
                        keep_variant = capitalized_variants[0] if capitalized_variants else variants[0]

                    # Remove other variants
                    for variant in variants:
                        if variant != keep_variant:
                            self.logger.info(f"Removing duplicate provider entry: {variant}")
                            del self.config_manager.config_data["providers"][variant]
                            changes_made = True

            if changes_made:
                # Save the cleaned configuration
                self.config_manager.save_config()
                self.logger.info("Configuration cleaned up and saved")
                return True
            else:
                self.logger.info("No duplicate providers found")
                return False

        except Exception as e:
            self.logger.error(f"Error cleaning up duplicate providers: {e}")
            return False

    def _get_provider_display_name(self, provider_name: str) -> str:
        """Get the display name for a provider (capitalized)."""
        name_map = {
            "anthropic": "Anthropic",
            "openai": "OpenAI",
            "google": "Google",
            "openrouter": "OpenRouter",
        }
        normalized = self._normalize_provider_name(provider_name)
        return name_map.get(normalized, provider_name.title())

    def initialize_providers_from_config(self) -> bool:
        """Initialize AI providers based on saved configuration."""
        if not self.config_manager:
            self.logger.error("ConfigManager not available")
            return False

        try:
            self.logger.info("Starting provider initialization from configuration...")
            
            # First, clean up any duplicate provider entries
            self._cleanup_duplicate_providers()

            # Get all configured providers (both default and custom)
            all_api_keys = self.config_manager.list_api_keys()
            self.logger.info(f"Found API keys for providers: {all_api_keys}")

            initialized_count = 0

            # Try to initialize any provider that has an API key
            for provider_key in all_api_keys:
                # Use the new resolution method to handle name consistency
                resolved_name = self._resolve_provider_name(provider_key)
                normalized_name = self._normalize_provider_name(resolved_name)

                api_key = self.config_manager.get_api_key(provider_key)
                if not api_key:
                    self.logger.warning(f"No API key found for {provider_key}")
                    continue

                # Get provider config using resolved name
                provider_config = self.config_manager.get_provider_config(resolved_name)
                if not provider_config:
                    # Try alternate formats if not found
                    provider_config = self.config_manager.get_provider_config(provider_key)
                    if not provider_config:
                        provider_config = self.config_manager.get_provider_config(normalized_name)

                if not provider_config:
                    # Create default config if none exists
                    provider_config = {
                        "enabled": True,  # Default to enabled if API key exists
                        "model": self._get_default_model_for_provider(normalized_name),
                        "temperature": 0.7,
                        "timeout": 30,
                        "max_tokens": 4000,
                    }
                    self.logger.info(f"Created default config for {resolved_name}")

                # Only initialize if enabled
                if provider_config.get("enabled", False):
                    self.logger.info(
                        f"Attempting to initialize {resolved_name} with config: {provider_config}"
                    )
                    success = self._initialize_provider(
                        resolved_name, api_key, provider_config
                    )
                    if success:
                        initialized_count += 1
                        self.logger.info(
                            f"Successfully initialized provider: {resolved_name}"
                        )
                    else:
                        self.logger.error(f"Failed to initialize provider: {resolved_name}")
                else:
                    self.logger.info(f"Skipping disabled provider: {resolved_name}")

            self.logger.info(
                f"Initialized {initialized_count} providers from configuration"
            )
            if self._callbacks_enabled:
                self.providers_updated.emit()
            return initialized_count > 0

        except Exception as e:
            self.logger.error(f"Error initializing providers from config: {e}")
            import traceback

            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    def _get_default_model_for_provider(self, provider_name: str) -> str:
        """Get default model for a provider type."""
        model_map = {
            "anthropic": "claude-4-20241120",
            "openai": "gpt-4o-mini",
            "google": "gemini-1.5-flash",
            "openrouter": "anthropic/claude-3.5-sonnet",
        }
        return model_map.get(provider_name, "default-model")

    def _initialize_provider(
        self, provider_name: str, api_key: str, config: Dict[str, Any]
    ) -> bool:
        """Initialize a specific AI provider."""
        try:
            normalized_name = self._normalize_provider_name(provider_name)

            # Map provider names to types - using 'anthropic' consistently
            provider_type_map = {
                "openai": "openrouter",  # Using OpenRouter for OpenAI compatibility
                "anthropic": "anthropic",  # Use 'anthropic' consistently
                "claude": "anthropic",  # Map 'claude' to 'anthropic' for backward compatibility
                "google": "gemini",
                "openrouter": "openrouter",
            }

            provider_type = provider_type_map.get(normalized_name, normalized_name)
            self.logger.info(f"Initializing {provider_name} as type {provider_type}")

            # Add provider to AI manager with consistent naming
            ai_manager_name = f"{normalized_name}_main"
            success = self.ai_manager.add_provider(
                name=ai_manager_name,
                provider_type=provider_type,
                api_key=api_key,
                config=config,
            )

            if success:
                # Initialize provider status
                self.provider_status[provider_name] = {
                    "type": provider_type,
                    "status": "initialized",
                    "message": "Provider initialized successfully",
                    "last_test": None,
                    "config": config,
                }

                # Emit callbacks only if UI is ready
                if self._callbacks_enabled:
                    self.provider_added.emit(provider_name, provider_type)
                    self.provider_status_changed.emit(
                        provider_name, "initialized", "Provider ready"
                    )

                # Test connection directly without timer to avoid crashes
                try:
                    self.test_provider_connection(provider_name)
                except Exception as e:
                    self.logger.error(f"Connection test failed: {e}")

                return True
            else:
                self.logger.error(
                    f"Failed to add provider {provider_name} to AI manager"
                )
                self._update_provider_status(
                    provider_name, "error", "Failed to initialize in AI manager"
                )
                return False

        except Exception as e:
            self.logger.error(f"Error initializing provider {provider_name}: {e}")
            import traceback

            self.logger.error(f"Traceback: {traceback.format_exc()}")
            self._update_provider_status(provider_name, "error", str(e))
            return False

    def add_provider(
        self, provider_name: str, api_key: str, config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add a new AI provider with the given configuration."""
        if not self.config_manager:
            return False

        try:
            # Use resolved name for consistency
            resolved_name = self._resolve_provider_name(provider_name)
            normalized_name = self._normalize_provider_name(resolved_name)

            # Save API key to config
            if not self.config_manager.set_api_key(normalized_name, api_key):
                return False

            # Save provider config
            if config:
                if not self.config_manager.set_provider_config(resolved_name, config):
                    return False

            # Initialize the provider
            effective_config = config or self.config_manager.get_provider_config(
                resolved_name
            )
            success = self._initialize_provider(resolved_name, api_key, effective_config)
            
            # Emit signals only if UI is ready and initialization was successful
            if success and self._callbacks_enabled:
                self.provider_added.emit(resolved_name)
                self.providers_updated.emit()
                
            return success

        except Exception as e:
            self.logger.error(f"Error adding provider {provider_name}: {e}")
            return False

    def remove_provider(self, provider_name: str) -> bool:
        """Remove an AI provider."""
        try:
            # Use resolved name for consistency
            resolved_name = self._resolve_provider_name(provider_name)
            normalized_name = self._normalize_provider_name(resolved_name)

            # Remove from AI manager
            ai_manager_name = f"{normalized_name}_main"
            self.ai_manager.remove_provider(ai_manager_name)

            # Remove from status tracking
            if resolved_name in self.provider_status:
                del self.provider_status[resolved_name]
            if provider_name in self.provider_status:
                del self.provider_status[provider_name]

            # Emit callbacks only if UI is ready
            if self._callbacks_enabled:
                self.provider_removed.emit(resolved_name)
                self.providers_updated.emit()

            return True

        except Exception as e:
            self.logger.error(f"Error removing provider {provider_name}: {e}")
            return False

    def test_provider_connection(self, provider_name: str) -> None:
        """Test connection to a specific provider (async)."""
        if provider_name not in self.provider_status:
            self.provider_status_changed.emit(
                provider_name, "error", "Provider not found"
            )
            return

        # Update status to testing
        self._update_provider_status(provider_name, "testing", "Testing connection...")

        # Perform test directly without timer to avoid crashes
        try:
            self._perform_connection_test(provider_name)
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            self._update_provider_status(
                provider_name, "error", f"Test failed: {str(e)}"
            )

    def _perform_connection_test(self, provider_name: str):
        """Perform the actual connection test."""
        try:
            normalized_name = self._normalize_provider_name(provider_name)
            ai_manager_name = f"{normalized_name}_main"
            provider = self.ai_manager.providers.get(ai_manager_name)

            if not provider:
                self._update_provider_status(
                    provider_name, "error", "Provider not initialized"
                )
                return

            # Try to validate the provider
            if hasattr(provider, "validate_connection"):
                # Use provider's validation method
                result = provider.validate_connection()
                if result:
                    self._update_provider_status(
                        provider_name, "connected", "Connection successful"
                    )
                else:
                    self._update_provider_status(
                        provider_name, "error", "Connection validation failed"
                    )
            else:
                # Fallback: basic API key validation
                if hasattr(provider, "validate_api_key"):
                    result = provider.validate_api_key()
                    if result:
                        self._update_provider_status(
                            provider_name, "connected", "API key format valid"
                        )
                    else:
                        self._update_provider_status(
                            provider_name, "error", "Invalid API key format"
                        )
                else:
                    # Last resort: assume connected if provider exists
                    self._update_provider_status(
                        provider_name, "connected", "Provider available"
                    )

        except Exception as e:
            self._update_provider_status(
                provider_name, "error", f"Test failed: {str(e)}"
            )

    def _update_provider_status(self, provider_name: str, status: str, message: str):
        """Update provider status and notify listeners."""
        if provider_name not in self.provider_status:
            self.provider_status[provider_name] = {}

        # Update status with datetime handling
        timestamp = datetime.datetime.now().isoformat()

        self.provider_status[provider_name].update(
            {
                "status": status,
                "message": message,
                "last_test": timestamp,
            }
        )

        # Emit callbacks only if UI is ready
        if self._callbacks_enabled:
            self.provider_status_changed.emit(provider_name, status, message)

        # Call registered callbacks
        for callback in self.status_callbacks:
            try:
                callback(provider_name, status, message)
            except Exception as e:
                self.logger.error(f"Error in status callback: {e}")

    def get_provider_status(self, provider_name: str) -> Dict[str, Any]:
        """Get current status of a provider."""
        return self.provider_status.get(
            provider_name,
            {"status": "unknown", "message": "Provider not found", "last_test": None},
        )

    def get_all_providers(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers."""
        return self.provider_status.copy()

    def get_active_providers(self) -> Dict[str, Dict[str, Any]]:
        """Get dictionary of active (connected) providers with their info."""
        return {
            name: status_info
            for name, status_info in self.provider_status.items()
            if status_info.get("status") in ["connected", "initialized"]
        }

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
            normalized_name = self._normalize_provider_name(provider_name)
            api_key = self.config_manager.get_api_key(normalized_name)
            config = self.config_manager.get_provider_config(provider_name)

            if api_key:
                # Re-initialize provider with new settings
                self.remove_provider(provider_name)
                self._initialize_provider(provider_name, api_key, config or {})
            else:
                # Remove provider if no API key
                self.remove_provider(provider_name)

        except Exception as e:
            self.logger.error(
                f"Error updating provider {provider_name} from settings: {e}"
            )

    def get_ai_manager(self):
        """Get the AI manager instance."""
        return self.ai_manager

    def send_message_to_provider(
        self, provider_name: str, message: str, context: Optional[Dict] = None
    ) -> str:
        """Send a message to a specific provider."""
        try:
            normalized_name = self._normalize_provider_name(provider_name)
            ai_manager_name = f"{normalized_name}_main"

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

    def enable_signals(self):
        """Enable callback emission after UI is ready."""
        self._callbacks_enabled = True
        self.logger.info("Callbacks enabled")
        # Emit an update callback to refresh any UI components
        self.providers_updated.emit()

    def update_provider_model(self, provider_name: str, model_name: str) -> bool:
        """Update the model for a specific provider."""
        try:
            self.logger.info(f"Updating model for {provider_name} to {model_name}")

            # Update config manager
            if self.config_manager:
                provider_config = self.config_manager.get_provider_config(provider_name)
                if not provider_config:
                    provider_config = {}

                provider_config["model"] = model_name
                success = self.config_manager.set_provider_config(provider_name, provider_config)

                if not success:
                    self.logger.error(f"Failed to save model config for {provider_name}")
                    return False

            # Update AI manager provider if it exists
            normalized_name = self._normalize_provider_name(provider_name)
            ai_manager_name = f"{normalized_name}_main"

            if ai_manager_name in self.ai_manager.providers:
                provider = self.ai_manager.providers[ai_manager_name]
                if hasattr(provider, "set_model"):
                    provider.set_model(model_name)
                    self.logger.info(f"Updated AI manager provider {ai_manager_name} to model {model_name}")
                elif hasattr(provider, "config"):
                    provider.config["model"] = model_name
                    self.logger.info(f"Updated AI manager provider config for {ai_manager_name}")

            # Notify UI components of the change
            if self._callbacks_enabled:
                self.provider_status_changed.emit(provider_name, "updated", f"Model changed to {model_name}")
                self.providers_updated.emit()

            return True

        except Exception as e:
            self.logger.error(f"Error updating model for {provider_name}: {e}")
            return False

    def get_provider_models(self, provider_name: str) -> List[str]:
        """Get available models for a provider."""
        try:
            # Try to get from AI manager first
            normalized_name = self._normalize_provider_name(provider_name)
            ai_manager_name = f"{normalized_name}_main"

            if ai_manager_name in self.ai_manager.providers:
                provider = self.ai_manager.providers[ai_manager_name]
                if hasattr(provider, "get_available_models"):
                    models = provider.get_available_models()
                    if models:
                        return models

            # Fallback to default models based on provider type
            provider_type = self._normalize_provider_name(provider_name)
            default_models = {
                "anthropic": ["claude-4-20241120", "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"],
                "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
                "google": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"],
                "openrouter": ["anthropic/claude-3.5-sonnet", "openai/gpt-4o", "google/gemini-pro"],
            }

            return default_models.get(provider_type, ["default-model"])

        except Exception as e:
            self.logger.error(f"Error getting models for {provider_name}: {e}")
            return ["default-model"]

    def get_current_provider_model(self, provider_name: str) -> str:
        """Get the currently configured model for a provider."""
        try:
            if self.config_manager:
                provider_config = self.config_manager.get_provider_config(provider_name)
                if provider_config and "model" in provider_config:
                    return provider_config["model"]

            # Fallback to default model
            return self._get_default_model_for_provider(provider_name)

        except Exception as e:
            self.logger.error(f"Error getting current model for {provider_name}: {e}")
            return self._get_default_model_for_provider(provider_name)

    def refresh_providers(self) -> bool:
        """Refresh all providers and their configurations."""
        try:
            self.logger.info("Refreshing all providers")

            # Re-initialize providers from config
            success = self.initialize_providers_from_config()

            # Emit update signal
            if self._callbacks_enabled:
                self.providers_updated.emit()

            return success

        except Exception as e:
            self.logger.error(f"Error refreshing providers: {e}")
            return False

    def set_current_provider_selection(self, provider_name: str, model_name: str = None) -> bool:
        """Set the current provider selection and notify all connected widgets."""
        try:
            resolved_name = self._resolve_provider_name(provider_name)
            
            # Verify the provider exists and is enabled
            provider_config = self.config_manager.get_provider_config(resolved_name) if self.config_manager else None
            if not provider_config or not provider_config.get('enabled', False):
                self.logger.warning(f"Provider {resolved_name} is not enabled or not found")
                return False
                
            # Store the current selection
            self.current_provider_selection = {
                'provider': resolved_name,
                'model': model_name or provider_config.get('model', 'default')
            }
            
            # Update the default provider if this is a manual selection
            if self.config_manager:
                self.set_default_provider(resolved_name)
            
            # Emit selection change signal to synchronize all provider selector widgets
            if self._callbacks_enabled:
                self.provider_selection_changed.emit(resolved_name, self.current_provider_selection['model'])
                
            self.logger.info(f"Provider selection updated: {resolved_name} with model {self.current_provider_selection['model']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting provider selection: {e}")
            return False

    def get_current_provider_selection(self) -> Dict[str, str]:
        """Get the current provider selection."""
        return getattr(self, 'current_provider_selection', {'provider': None, 'model': None})

    def get_default_provider(self) -> Optional[str]:
        """Get the default provider, resolving name conflicts if necessary."""
        if not self.config_manager:
            return None
            
        try:
            # Get the configured default provider
            default_provider = self.config_manager.config_data.get('connection', {}).get('default_provider')
            if not default_provider:
                return None
                
            # Resolve the name to handle capitalization mismatches
            resolved_name = self._resolve_provider_name(default_provider)
            
            # Verify the provider is enabled and available
            provider_config = self.config_manager.get_provider_config(resolved_name)
            if provider_config and provider_config.get('enabled', False):
                return resolved_name
            else:
                self.logger.warning(f"Default provider {resolved_name} is not enabled")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting default provider: {e}")
            return None

    def set_default_provider(self, provider_name: str) -> bool:
        """Set the default provider, using resolved name format."""
        if not self.config_manager:
            return False
            
        try:
            resolved_name = self._resolve_provider_name(provider_name)
            
            # Update the configuration
            if 'connection' not in self.config_manager.config_data:
                self.config_manager.config_data['connection'] = {}
            self.config_manager.config_data['connection']['default_provider'] = resolved_name
            
            # Save the configuration
            self.config_manager.save_config()
            self.logger.info(f"Set default provider to: {resolved_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting default provider: {e}")
            return False


# Global singleton instance access function
_provider_service_instance = None

def get_provider_service():
    """
    Get the singleton instance of ProviderIntegrationService.
    
    Returns:
        ProviderIntegrationService: The singleton service instance
    """
    global _provider_service_instance
    if _provider_service_instance is None:
        _provider_service_instance = ProviderIntegrationService()
    return _provider_service_instance
