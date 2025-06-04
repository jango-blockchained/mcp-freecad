"""AI Manager - Manages AI model providers and interactions"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from .base_provider import AIProvider
from .claude_provider import ClaudeProvider
from .gemini_provider import GeminiProvider
from .openrouter_provider import OpenRouterProvider


class AIManager:
    """Manages AI model providers and interactions."""
    
    def __init__(self):
        """Initialize the AI manager."""
        self.logger = logging.getLogger(__name__)
        self.providers: Dict[str, AIProvider] = {}
        self.active_provider: Optional[str] = None
    
    def add_provider(self, name: str, provider_type: str, api_key: str, 
                    config: Optional[Dict[str, Any]] = None) -> bool:
        """Add an AI provider."""
        try:
            if provider_type.lower() == "claude":
                provider = ClaudeProvider(api_key, config)
            elif provider_type.lower() == "gemini":
                provider = GeminiProvider(api_key, config) 
            elif provider_type.lower() == "openrouter":
                provider = OpenRouterProvider(api_key, config)
            else:
                self.logger.error(f"Unknown provider type: {provider_type}")
                return False
            
            self.providers[name] = provider
            
            # Set as active if first provider
            if not self.active_provider:
                self.active_provider = name
                
            self.logger.info(f"Added {provider_type} provider: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add provider {name}: {e}")
            return False
    
    def remove_provider(self, name: str) -> bool:
        """Remove an AI provider."""
        if name in self.providers:
            del self.providers[name]
            if self.active_provider == name:
                self.active_provider = list(self.providers.keys())[0] if self.providers else None
            return True
        return False
    
    def set_active_provider(self, name: str) -> bool:
        """Set the active AI provider."""
        if name in self.providers:
            self.active_provider = name
            return True
        return False
    
    def get_active_provider(self) -> Optional[AIProvider]:
        """Get the active AI provider."""
        if self.active_provider and self.active_provider in self.providers:
            return self.providers[self.active_provider]
        return None
    
    async def send_message(self, message: str, provider_name: Optional[str] = None,
                          context: Optional[Dict] = None) -> str:
        """Send message to AI provider."""
        provider = None
        
        if provider_name and provider_name in self.providers:
            provider = self.providers[provider_name]
        else:
            provider = self.get_active_provider()
        
        if not provider:
            return "Error: No AI provider available"
        
        try:
            response = await provider.send_message(message, context)
            return response
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return f"Error: {str(e)}"