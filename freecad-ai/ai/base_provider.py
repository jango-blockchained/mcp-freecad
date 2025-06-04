"""Base AI Provider - Abstract base class for AI model providers"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import logging


class AIProvider(ABC):
    """Abstract base class for AI model providers."""

    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the AI provider."""
        self.api_key = api_key
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self._session = None

    @abstractmethod
    async def send_message(self, message: str, context: Optional[Dict] = None) -> str:
        """Send a message to the AI model and get response."""
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models for this provider."""
        pass

    @abstractmethod
    def validate_api_key(self) -> bool:
        """Validate the API key."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of this provider."""
        pass

    def validate_connection(self) -> bool:
        """Validate connection to the provider."""
        # Default implementation - just validate API key format
        return self.validate_api_key()

    def set_model(self, model: str) -> bool:
        """Set the active model."""
        if model in self.get_available_models():
            self.config["model"] = model
            return True
        return False

    def get_current_model(self) -> Optional[str]:
        """Get the currently selected model."""
        return self.config.get("model")

    async def close(self):
        """Close any open connections."""
        if self._session:
            await self._session.close()
            self._session = None
