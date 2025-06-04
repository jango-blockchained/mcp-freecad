"""Gemini Provider - Google Gemini API integration"""

import aiohttp
import json
from typing import Dict, List, Any, Optional
from .base_provider import AIProvider


class GeminiProvider(AIProvider):
    """Provider for Google Gemini AI models."""

    AVAILABLE_MODELS = [
        "gemini-2.5-pro-latest",          # Latest 2.5 Pro model (March 2025)
        "gemini-2.5-pro-preview",         # 2.5 Pro Preview/I/O edition
        "gemini-1.5-pro-latest",          # Previous flagship
        "gemini-1.5-flash-latest",        # Fast inference model
        "gemini-exp-1114"                 # Experimental features
    ]

    API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        """Initialize Gemini provider."""
        super().__init__(api_key, config)
        self.config.setdefault('model', self.AVAILABLE_MODELS[0])
        self.config.setdefault('max_tokens', 4096)
        self.config.setdefault('temperature', 0.7)

    async def send_message(self, message: str, context: Optional[Dict] = None) -> str:
        """Send message to Gemini API."""
        if not self._session:
            self._session = aiohttp.ClientSession()

        url = f"{self.API_BASE_URL}/models/{self.config['model']}:generateContent"

        headers = {"Content-Type": "application/json"}

        payload = {
            "contents": [{"parts": [{"text": message}]}],
            "generationConfig": {
                "maxOutputTokens": self.config['max_tokens'],
                "temperature": self.config['temperature']
            }
        }

        try:
            async with self._session.post(
                f"{url}?key={self.api_key}",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['candidates'][0]['content']['parts'][0]['text']
                else:
                    error_text = await response.text()
                    self.logger.error(f"Gemini API error: {response.status} - {error_text}")
                    return f"Error: {response.status}"
        except Exception as e:
            self.logger.error(f"Gemini API exception: {e}")
            return f"Error: {str(e)}"

    def get_available_models(self) -> List[str]:
        """Get available Gemini models."""
        return self.AVAILABLE_MODELS.copy()

    def validate_api_key(self) -> bool:
        """Validate Gemini API key."""
        return bool(self.api_key and len(self.api_key) > 10)

    def get_provider_name(self) -> str:
        """Get provider name."""
        return "Gemini"
