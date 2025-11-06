"""Google Vertex AI Provider for FreeCAD AI Integration"""

import logging
from typing import Dict, Any, List

from .base_provider import BaseAIProvider


class VertexAIProvider(BaseAIProvider):
    """Provider for Google Vertex AI integration."""

    def __init__(
        self, api_key: str = None, project_id: str = None, location: str = "us-central1"
    ):
        """
        Initialize the Vertex AI provider.

        Args:
            api_key: Service account JSON string or API key
            project_id: Google Cloud project ID
            location: Google Cloud region for Vertex AI
        """
        super().__init__()
        self.api_key = api_key
        self.project_id = project_id
        self.location = location
        self.client = None
        self.logger = logging.getLogger(__name__)

    def get_provider_name(self) -> str:
        """Get the name of this provider."""
        return "vertexai"

    def get_display_name(self) -> str:
        """Get the display name of this provider."""
        return "Google Vertex AI"

    def is_configured(self) -> bool:
        """Check if the provider is properly configured."""
        return bool(self.api_key and self.project_id)

    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        return [
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.0-pro",
            "text-bison",
            "code-bison",
        ]

    def get_default_model(self) -> str:
        """Get the default model for this provider."""
        return "gemini-1.5-pro"

    def initialize(self) -> bool:
        """Initialize the Vertex AI client."""
        try:
            if not self.is_configured():
                self.logger.error("Vertex AI provider not properly configured")
                return False

            # Try to import Vertex AI client
            try:
                from google.cloud import aiplatform
                from vertexai.generative_models import GenerativeModel

                # Initialize Vertex AI
                aiplatform.init(project=self.project_id, location=self.location)

                # Store the GenerativeModel class for later use
                self.GenerativeModel = GenerativeModel

                self.logger.info(
                    f"Vertex AI provider initialized for project {self.project_id}"
                )
                return True

            except ImportError as e:
                self.logger.error(f"Failed to import Vertex AI dependencies: {e}")
                self.logger.error("Please install: pip install google-cloud-aiplatform")
                return False

        except Exception as e:
            self.logger.error(f"Failed to initialize Vertex AI provider: {e}")
            return False

    def generate_response(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate a response using Vertex AI.

        Args:
            prompt: The input prompt
            model: Model to use (defaults to default model)
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters

        Returns:
            Dict containing response and metadata
        """
        try:
            if not self.GenerativeModel:
                return {
                    "success": False,
                    "error": "Vertex AI not initialized",
                    "response": "",
                }

            if model is None:
                model = self.get_default_model()

            # Create model instance
            model_instance = self.GenerativeModel(model)

            # Configure generation parameters
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }

            # Generate response
            response = model_instance.generate_content(
                prompt, generation_config=generation_config
            )

            if response and response.text:
                return {
                    "success": True,
                    "response": response.text,
                    "model": model,
                    "usage": {
                        "prompt_tokens": len(prompt.split()),  # Rough estimate
                        "completion_tokens": len(
                            response.text.split()
                        ),  # Rough estimate
                    },
                }
            else:
                return {
                    "success": False,
                    "error": "Empty response from Vertex AI",
                    "response": "",
                }

        except Exception as e:
            self.logger.error(f"Error generating response with Vertex AI: {e}")
            return {"success": False, "error": str(e), "response": ""}

    def test_connection(self) -> Dict[str, Any]:
        """Test the connection to Vertex AI."""
        try:
            if not self.is_configured():
                return {
                    "success": False,
                    "error": "Provider not configured - missing API key or project ID",
                }

            # Test with a simple prompt
            test_result = self.generate_response(
                "Hello, this is a test. Please respond with 'Connection successful.'",
                max_tokens=50,
            )

            if test_result["success"]:
                return {
                    "success": True,
                    "message": "Vertex AI connection successful",
                    "response": test_result["response"],
                }
            else:
                return {
                    "success": False,
                    "error": f"Connection test failed: {test_result.get('error', 'Unknown error')}",
                }

        except Exception as e:
            return {"success": False, "error": f"Connection test error: {str(e)}"}

    def get_configuration(self) -> Dict[str, Any]:
        """Get current provider configuration."""
        return {
            "provider": self.get_provider_name(),
            "display_name": self.get_display_name(),
            "configured": self.is_configured(),
            "project_id": self.project_id,
            "location": self.location,
            "default_model": self.get_default_model(),
            "available_models": self.get_available_models(),
        }

    def update_configuration(self, config: Dict[str, Any]) -> bool:
        """Update provider configuration."""
        try:
            if "api_key" in config:
                self.api_key = config["api_key"]
            if "project_id" in config:
                self.project_id = config["project_id"]
            if "location" in config:
                self.location = config["location"]

            # Re-initialize if configured
            if self.is_configured():
                return self.initialize()
            return True

        except Exception as e:
            self.logger.error(f"Failed to update Vertex AI configuration: {e}")
            return False
