"""
Gemini AI Provider

Google Gemini integration with multimodal capabilities and large context windows.
Provides excellent performance for CAD documentation analysis and multimodal tasks.

Author: jango-blockchained
"""

import asyncio
import json
import time
import aiohttp
from typing import Dict, List, Optional, Any

from ai.providers.base_provider import BaseAIProvider, AIResponse, AIMessage, MessageRole


class GeminiProvider(BaseAIProvider):
    """Gemini AI provider implementation."""

    # Gemini API endpoint
    API_BASE = "https://generativelanguage.googleapis.com/v1beta"

    # Supported Gemini models
    GEMINI_MODELS = [
        "gemini-2.5-pro-latest",
        "gemini-1.5-pro-latest",
        "gemini-1.5-flash-latest",
        "gemini-1.0-pro-latest",
    ]

    # Model context windows
    MODEL_CONTEXTS = {
        "gemini-2.5-pro-latest": 1000000,  # 1M tokens
        "gemini-1.5-pro-latest": 1000000,  # 1M tokens
        "gemini-1.5-flash-latest": 1000000,  # 1M tokens
        "gemini-1.0-pro-latest": 30720,  # 30K tokens
    }

    def __init__(self, api_key: str, model: str = "gemini-2.5-pro-latest", **kwargs):
        """Initialize Gemini provider.

        Args:
            api_key: Google AI Studio API key
            model: Gemini model to use
            **kwargs: Additional configuration
        """
        super().__init__(api_key, model, **kwargs)

        # Default to Gemini 2.5 Pro for best performance
        if not self.model:
            self.model = "gemini-2.5-pro-latest"

        # Gemini-specific configuration
        self.max_tokens = kwargs.get("max_tokens", 8192)
        self.temperature = kwargs.get("temperature", 0.7)
        self.top_p = kwargs.get("top_p", 0.95)
        self.top_k = kwargs.get("top_k", 40)
        self.system_prompt = kwargs.get(
            "system_prompt", self._get_default_system_prompt()
        )

    @property
    def name(self) -> str:
        """Return provider name."""
        return "Gemini (Google)"

    @property
    def supported_models(self) -> List[str]:
        """Return supported Gemini models."""
        return self.GEMINI_MODELS.copy()

    @property
    def supports_thinking_mode(self) -> bool:
        """Return whether thinking mode is supported."""
        return False  # Gemini doesn't support thinking mode yet

    def _get_default_system_prompt(self) -> str:
        """Get default system prompt for CAD operations."""
        return """You are an expert CAD assistant integrated with FreeCAD through the Model Context Protocol (MCP).

Your capabilities include:
- Creating 3D primitives (boxes, cylinders, spheres, cones)
- Performing boolean operations (union, cut, intersection)
- Managing documents and objects
- Exporting models to various formats (STL, STEP, IGES)
- Measuring distances, angles, and volumes
- Generating FreeCAD Python scripts
- Providing CAD design guidance and optimization

When users ask for CAD operations, you can execute them directly using MCP tools. Always explain what you're doing and provide helpful design insights.

You have access to Gemini's multimodal capabilities, so you can:
- Analyze images of technical drawings or existing designs
- Generate detailed documentation with diagrams
- Process large CAD files and documentation
- Provide visual explanations of complex concepts

Be precise with measurements and technical details. When working with visual content, describe what you observe clearly."""

    def _convert_to_gemini_format(
        self, messages: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """Convert messages to Gemini format.

        Args:
            messages: List of messages in standard format

        Returns:
            Messages in Gemini format
        """
        gemini_messages = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            # Gemini uses 'user' and 'model' as roles
            if role == "assistant":
                role = "model"
            elif role == "system":
                # Prepend system message to first user message
                if not gemini_messages:
                    continue
                # Add as context to the conversation
                content = f"Context: {content}\n\nUser: {messages[1]['content'] if len(messages) > 1 else ''}"
                role = "user"

            gemini_messages.append({"role": role, "parts": [{"text": content}]})

        return gemini_messages

    async def send_message(self, message: str, **kwargs) -> AIResponse:
        """Send message to Gemini API.

        Args:
            message: User message
            **kwargs: Additional parameters

        Returns:
            AIResponse with Gemini's response
        """
        start_time = time.time()

        try:
            # Apply rate limiting
            await self._rate_limit()

            # Prepare the request
            model_name = self.model.replace(
                "-latest", ""
            )  # Remove -latest suffix for API
            url = f"{self.API_BASE}/models/{model_name}:generateContent?key={self.api_key}"

            # Build conversation history
            messages = []

            # Add system prompt as first message
            if self.system_prompt:
                messages.append({"role": "system", "content": self.system_prompt})

            # Add conversation history
            for hist_msg in self.conversation_history[-10:]:  # Last 10 messages
                messages.append(
                    {"role": hist_msg.role.value, "content": hist_msg.content}
                )

            # Add current message
            messages.append({"role": "user", "content": message})

            # Convert to Gemini format
            gemini_messages = self._convert_to_gemini_format(messages)

            # Build request data
            request_data = {
                "contents": gemini_messages,
                "generationConfig": {
                    "temperature": kwargs.get("temperature", self.temperature),
                    "topP": kwargs.get("top_p", self.top_p),
                    "topK": kwargs.get("top_k", self.top_k),
                    "maxOutputTokens": kwargs.get("max_tokens", self.max_tokens),
                },
                "safetySettings": [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_ONLY_HIGH",
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH",
                        "threshold": "BLOCK_ONLY_HIGH",
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_ONLY_HIGH",
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_ONLY_HIGH",
                    },
                ],
            }

            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=request_data, timeout=aiohttp.ClientTimeout(total=120)
                ) as response:

                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(
                            f"Gemini API error {response.status}: {error_text}"
                        )

                    result = await response.json()

            # Process response
            ai_response = self._process_response(result)

            # Update statistics
            response_time = time.time() - start_time
            tokens_used = ai_response.usage.get("output_tokens", 0)
            self._update_stats(response_time, tokens_used)

            # Add to conversation history
            user_msg = AIMessage(MessageRole.USER, message)
            assistant_msg = AIMessage(MessageRole.ASSISTANT, ai_response.content)

            self.add_message_to_history(user_msg)
            self.add_message_to_history(assistant_msg)

            return ai_response

        except Exception as e:
            response_time = time.time() - start_time
            self._update_stats(response_time, error=True)
            raise Exception(f"Gemini request failed: {str(e)}")

    def _process_response(self, response_data: Dict[str, Any]) -> AIResponse:
        """Process Gemini API response.

        Args:
            response_data: Raw API response

        Returns:
            Processed AIResponse
        """
        # Extract content from candidates
        content = ""

        if "candidates" in response_data and response_data["candidates"]:
            candidate = response_data["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"]:
                for part in candidate["content"]["parts"]:
                    if "text" in part:
                        content += part["text"]

        # Extract usage information
        usage = {}
        if "usageMetadata" in response_data:
            usage_data = response_data["usageMetadata"]
            usage = {
                "input_tokens": usage_data.get("promptTokenCount", 0),
                "output_tokens": usage_data.get("candidatesTokenCount", 0),
                "total_tokens": usage_data.get("totalTokenCount", 0),
            }

        # Create response object
        return AIResponse(
            content=content.strip(),
            model=self.model,
            usage=usage,
            metadata={
                "provider": "gemini",
                "safety_ratings": response_data.get("candidates", [{}])[0].get(
                    "safetyRatings", []
                ),
            },
        )

    async def test_connection(self) -> bool:
        """Test connection to Gemini API."""
        try:
            test_response = await self.send_message(
                "Hello! Please respond with just 'Connection successful' to test the API.",
                max_tokens=50,
                temperature=0.1,
            )
            return "successful" in test_response.content.lower()
        except Exception:
            return False

    def get_model_info(self, model: str = None) -> Dict[str, Any]:
        """Get detailed information about a Gemini model."""
        target_model = model or self.model

        base_info = super().get_model_info(target_model)

        # Add Gemini-specific information
        model_details = {
            "gemini-2.5-pro-latest": {
                "description": "Most advanced Gemini model with 1M token context",
                "release_date": "December 2024",
                "strengths": ["Multimodal", "Large context", "Complex reasoning"],
                "context_window": 1000000,
                "supports_images": True,
                "supports_video": True,
                "supports_audio": True,
            },
            "gemini-1.5-pro-latest": {
                "description": "Previous generation with excellent performance",
                "release_date": "May 2024",
                "strengths": ["Multimodal", "Large context", "Stable"],
                "context_window": 1000000,
                "supports_images": True,
                "supports_video": True,
                "supports_audio": True,
            },
            "gemini-1.5-flash-latest": {
                "description": "Fast and efficient for quick tasks",
                "release_date": "May 2024",
                "strengths": ["Speed", "Cost-effective", "Good quality"],
                "context_window": 1000000,
                "supports_images": True,
                "supports_video": False,
                "supports_audio": False,
            },
            "gemini-1.0-pro-latest": {
                "description": "Stable model for production use",
                "release_date": "December 2023",
                "strengths": ["Reliability", "Well-tested", "Good baseline"],
                "context_window": 30720,
                "supports_images": False,
                "supports_video": False,
                "supports_audio": False,
            },
        }

        if target_model in model_details:
            base_info.update(model_details[target_model])

        return base_info

    async def analyze_image(
        self, image_path: str, prompt: str = "Describe this image"
    ) -> AIResponse:
        """Analyze an image using Gemini's multimodal capabilities.

        Args:
            image_path: Path to the image file
            prompt: Prompt for image analysis

        Returns:
            AIResponse with analysis
        """
        # This would require image encoding and multimodal API support
        # For now, return a placeholder
        raise NotImplementedError(
            "Image analysis will be implemented with multimodal support"
        )

    def get_context_window(self) -> int:
        """Get the context window size for current model."""
        return self.MODEL_CONTEXTS.get(self.model, 30720)
