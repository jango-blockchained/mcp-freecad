"""
Provider Service - Service for managing AI providers and API interactions

This module provides a service layer for managing AI providers and handling
API interactions within the FreeCAD AI system.
"""

import logging
from typing import Any, Dict, List, Optional

try:
    import FreeCAD
    FREECAD_AVAILABLE = True
except ImportError:
    FREECAD_AVAILABLE = False

class ProviderService:
    """Service for managing AI providers and API interactions."""

    def __init__(self):
        """Initialize the provider service."""
        self.logger = logging.getLogger(__name__)
        self.providers: Dict[str, Any] = {}
        self.active_provider: Optional[str] = None
        self.initialized = False
        
        try:
            self._initialize()
            self.initialized = True
        except Exception as e:
            self.logger.error(f"Failed to initialize ProviderService: {e}")

    def _initialize(self):
        """Initialize the provider service."""
        self.logger.info("Initializing ProviderService")
        
        # Try to import AI manager
        try:
            from ai.ai_manager import AIManager
            self.ai_manager = AIManager()
            self.logger.info("AI Manager initialized successfully")
        except ImportError as e:
            self.logger.warning(f"Could not import AI Manager: {e}")
            self.ai_manager = None

    def is_available(self) -> bool:
        """Check if the provider service is available."""
        return self.initialized

    def add_provider(self, name: str, provider_type: str, api_key: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """Add an AI provider."""
        try:
            if self.ai_manager:
                return self.ai_manager.add_provider(name, provider_type, api_key, config)
            else:
                # Fallback implementation
                self.providers[name] = {
                    'type': provider_type,
                    'api_key': api_key,
                    'config': config or {}
                }
                return True
        except Exception as e:
            self.logger.error(f"Error adding provider {name}: {e}")
            return False

    def remove_provider(self, name: str) -> bool:
        """Remove an AI provider."""
        try:
            if self.ai_manager and hasattr(self.ai_manager, 'remove_provider'):
                return self.ai_manager.remove_provider(name)
            else:
                if name in self.providers:
                    del self.providers[name]
                    return True
                return False
        except Exception as e:
            self.logger.error(f"Error removing provider {name}: {e}")
            return False

    def set_active_provider(self, name: str) -> bool:
        """Set the active AI provider."""
        try:
            if self.ai_manager and hasattr(self.ai_manager, 'set_active_provider'):
                return self.ai_manager.set_active_provider(name)
            else:
                if name in self.providers:
                    self.active_provider = name
                    return True
                return False
        except Exception as e:
            self.logger.error(f"Error setting active provider {name}: {e}")
            return False

    def get_active_provider(self) -> Optional[str]:
        """Get the active AI provider."""
        try:
            if self.ai_manager and hasattr(self.ai_manager, 'active_provider'):
                return self.ai_manager.active_provider
            else:
                return self.active_provider
        except Exception as e:
            self.logger.error(f"Error getting active provider: {e}")
            return None

    def list_providers(self) -> List[str]:
        """List all available providers."""
        try:
            if self.ai_manager and hasattr(self.ai_manager, 'providers'):
                return list(self.ai_manager.providers.keys())
            else:
                return list(self.providers.keys())
        except Exception as e:
            self.logger.error(f"Error listing providers: {e}")
            return []

    def send_message(self, message: str, provider: Optional[str] = None) -> Optional[str]:
        """Send a message to an AI provider."""
        try:
            target_provider = provider or self.active_provider
            if not target_provider:
                self.logger.error("No active provider set")
                return None
                
            if self.ai_manager and hasattr(self.ai_manager, 'send_message'):
                return self.ai_manager.send_message(message, target_provider)
            else:
                # Fallback - just return a placeholder response
                return f"Response from {target_provider}: {message}"
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return None

# Global instance
_provider_service_instance = None

def get_provider_service() -> ProviderService:
    """Get the global provider service instance."""
    global _provider_service_instance
    if _provider_service_instance is None:
        _provider_service_instance = ProviderService()
    return _provider_service_instance
