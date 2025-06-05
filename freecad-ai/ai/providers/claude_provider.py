"""
Claude AI Provider

Anthropic Claude integration with support for Claude 4 models and thinking mode.
Provides advanced reasoning capabilities for complex CAD operations.

Author: jango-blockchained
"""

import asyncio
import json
import time
import aiohttp
from typing import Dict, List, Optional, Any

from ai.providers.base_provider import BaseAIProvider, AIResponse, AIMessage, MessageRole


class ClaudeProvider(BaseAIProvider):
    """Claude AI provider implementation."""

    # Claude API endpoint
    API_BASE = "https://api.anthropic.com/v1"

    # Supported Claude models
    CLAUDE_MODELS = [
        "claude-4-opus-20250522",  # Most capable - May 2025
        "claude-4-sonnet-20250522",  # Best coding - May 2025
        "claude-3-7-sonnet-20250224",  # Hybrid reasoning - Feb 2025
        "claude-3-5-sonnet-20241022",  # Reliable baseline - Oct 2024
        "claude-3-opus-20240229",  # Legacy complex reasoning
        "claude-3-haiku-20240307",  # Fast and cost-effective
    ]

    # Models that support thinking mode
    THINKING_MODE_MODELS = [
        "claude-4-opus-20250522",
        "claude-4-sonnet-20250522",
        "claude-3-7-sonnet-20250224",
    ]

    def __init__(self, api_key: str, model: str = "claude-4-sonnet-20250522", **kwargs):
        """Initialize Claude provider.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
            **kwargs: Additional configuration
        """
        super().__init__(api_key, model, **kwargs)

        # Default to Claude 4 Sonnet for best coding performance
        if not self.model:
            self.model = "claude-4-sonnet-20250522"

        # Claude-specific configuration
        self.max_tokens = kwargs.get("max_tokens", 4000)
        self.temperature = kwargs.get("temperature", 0.7)
        self.system_prompt = kwargs.get(
            "system_prompt", self._get_default_system_prompt()
        )

        # Headers for API requests
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        # Add thinking mode header if supported
        if self.thinking_mode_enabled and self.supports_thinking_mode:
            self.headers["anthropic-beta"] = "thinking-2024-12-19"

    @property
    def name(self) -> str:
        """Return provider name."""
        return "Claude (Anthropic)"

    @property
    def supported_models(self) -> List[str]:
        """Return supported Claude models."""
        return self.CLAUDE_MODELS.copy()

    @property
    def supports_thinking_mode(self) -> bool:
        """Return whether current model supports thinking mode."""
        return self.model in self.THINKING_MODE_MODELS

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

For complex problems, think through the solution step by step, considering:
- Design requirements and constraints
- Manufacturing considerations
- Material properties and stress analysis
- Optimization opportunities
- Best CAD practices

Be precise with measurements and technical details."""

    async def send_message(self, message: str, **kwargs) -> AIResponse:
        """Send message to Claude API.

        Args:
            message: User message
            **kwargs: Additional parameters

        Returns:
            AIResponse with Claude's response
        """
        start_time = time.time()

        try:
            # Apply rate limiting
            await self._rate_limit()

            # Prepare the request
            request_data = self._prepare_request(message, **kwargs)

            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.API_BASE}/messages",
                    headers=self.headers,
                    json=request_data,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as response:

                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(
                            f"Claude API error {response.status}: {error_text}"
                        )

                    result = await response.json()

            # Process response
            ai_response = self._process_response(result)

            # Update statistics
            response_time = time.time() - start_time
            tokens_used = result.get("usage", {}).get("output_tokens", 0)
            self._update_stats(response_time, tokens_used)

            # Add to conversation history
            user_msg = AIMessage(MessageRole.USER, message)
            assistant_msg = AIMessage(
                MessageRole.ASSISTANT,
                ai_response.content,
                thinking_process=ai_response.thinking_process,
            )

            self.add_message_to_history(user_msg)
            self.add_message_to_history(assistant_msg)

            return ai_response

        except Exception as e:
            response_time = time.time() - start_time
            self._update_stats(response_time, error=True)
            raise Exception(f"Claude request failed: {str(e)}")

    def _prepare_request(self, message: str, **kwargs) -> Dict[str, Any]:
        """Prepare the request data for Claude API."""

        # Build messages array
        messages = []

        # Add conversation history
        for hist_msg in self.conversation_history[-10:]:  # Last 10 messages for context
            messages.append({"role": hist_msg.role.value, "content": hist_msg.content})

        # Add current message
        messages.append({"role": "user", "content": message})

        # Base request data
        request_data = {
            "model": self.model,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
            "system": kwargs.get("system_prompt", self.system_prompt),
            "messages": messages,
        }

        # Add thinking mode parameters if enabled and supported
        if self.thinking_mode_enabled and self.supports_thinking_mode:
            request_data["thinking"] = {"max_thinking_tokens": self.thinking_budget}

        return request_data

    def _process_response(self, response_data: Dict[str, Any]) -> AIResponse:
        """Process Claude API response."""

        # Extract main content
        content = ""
        thinking_process = None

        if "content" in response_data:
            for block in response_data["content"]:
                if block["type"] == "text":
                    content += block["text"]
                elif block["type"] == "thinking" and self.thinking_mode_enabled:
                    thinking_process = block["text"]

        # Extract usage information
        usage = response_data.get("usage", {})

        # Create response object
        return AIResponse(
            content=content.strip(),
            thinking_process=thinking_process,
            model=self.model,
            usage=usage,
            metadata={
                "provider": "claude",
                "thinking_mode": self.thinking_mode_enabled,
                "thinking_tokens": (
                    usage.get("thinking_tokens", 0) if thinking_process else 0
                ),
            },
        )

    async def test_connection(self) -> bool:
        """Test connection to Claude API."""
        try:
            test_response = await self.send_message(
                "Hello! Please respond with just 'Connection successful' to test the API.",
                max_tokens=50,
            )
            return "successful" in test_response.content.lower()
        except Exception:
            return False

    def enable_thinking_mode(self, budget: int = 2000):
        """Enable thinking mode for Claude."""
        if not self.supports_thinking_mode:
            raise ValueError(
                f"Model {self.model} does not support thinking mode. "
                f"Supported models: {self.THINKING_MODE_MODELS}"
            )

        super().enable_thinking_mode(budget)

        # Update headers
        self.headers["anthropic-beta"] = "thinking-2024-12-19"

    def disable_thinking_mode(self):
        """Disable thinking mode."""
        super().disable_thinking_mode()

        # Remove thinking mode header
        self.headers.pop("anthropic-beta", None)

    def get_model_info(self, model: str = None) -> Dict[str, Any]:
        """Get detailed information about a Claude model."""
        target_model = model or self.model

        base_info = super().get_model_info(target_model)

        # Add Claude-specific information
        model_details = {
            "claude-4-opus-20250522": {
                "description": "Most capable model for complex analysis & research",
                "release_date": "May 2025",
                "strengths": ["Complex reasoning", "Research", "Analysis"],
                "thinking_mode": True,
            },
            "claude-4-sonnet-20250522": {
                "description": "Best coding performance with advanced reasoning",
                "release_date": "May 2025",
                "strengths": ["Coding", "Development", "Technical tasks"],
                "thinking_mode": True,
            },
            "claude-3-7-sonnet-20250224": {
                "description": "Hybrid reasoning with transparent thought process",
                "release_date": "February 2025",
                "strengths": ["Extended reasoning", "Problem solving"],
                "thinking_mode": True,
            },
            "claude-3-5-sonnet-20241022": {
                "description": "Reliable baseline with excellent performance",
                "release_date": "October 2024",
                "strengths": ["General purpose", "Reliable", "Fast"],
                "thinking_mode": False,
            },
        }

        if target_model in model_details:
            base_info.update(model_details[target_model])

        return base_info

    def get_thinking_budget_recommendations(self) -> Dict[str, int]:
        """Get recommended thinking budgets for different use cases."""
        return {
            "light_analysis": 500,
            "standard_tasks": 2000,
            "complex_problems": 5000,
            "research_level": 10000,
            "unlimited": 20000,
        }
