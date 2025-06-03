"""
OpenRouter AI Provider

OpenRouter integration providing access to multiple AI models through a single interface.
Supports Claude, GPT, and open source models with unified API access.

Author: jango-blockchained
"""

import asyncio
import json
import time
import aiohttp
from typing import Dict, List, Optional, Any

from .base_provider import BaseAIProvider, AIResponse, AIMessage, MessageRole


class OpenRouterProvider(BaseAIProvider):
    """OpenRouter AI provider implementation."""

    # OpenRouter API endpoint
    API_BASE = "https://openrouter.ai/api/v1"

    # Supported models through OpenRouter
    OPENROUTER_MODELS = [
        # Anthropic Claude models
        "anthropic/claude-4-opus",
        "anthropic/claude-4-sonnet",
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3-opus",
        "anthropic/claude-3-haiku",

        # OpenAI models
        "openai/gpt-4.1-turbo",
        "openai/gpt-4-turbo",
        "openai/gpt-3.5-turbo",
        "openai/o3-mini",

        # Google models
        "google/gemini-2.5-pro",
        "google/gemini-1.5-pro",
        "google/gemini-1.5-flash",

        # Meta models
        "meta/llama-3.1-405b-instruct",
        "meta/llama-3.1-70b-instruct",

        # Mistral models
        "mistralai/mistral-large",
        "mistralai/mixtral-8x7b-instruct",

        # Open source models
        "huggingface/qwen-2.5-72b-instruct",
        "deepseek/deepseek-v3"
    ]

    # Models that support thinking mode (Claude models)
    THINKING_MODE_MODELS = [
        "anthropic/claude-4-opus",
        "anthropic/claude-4-sonnet"
    ]

    def __init__(self, api_key: str, model: str = "anthropic/claude-4-sonnet", **kwargs):
        """Initialize OpenRouter provider.

        Args:
            api_key: OpenRouter API key
            model: Model to use (provider/model format)
            **kwargs: Additional configuration
        """
        super().__init__(api_key, model, **kwargs)

        # Default to Claude 4 Sonnet for best CAD performance
        if not self.model:
            self.model = "anthropic/claude-4-sonnet"

        # OpenRouter-specific configuration
        self.max_tokens = kwargs.get('max_tokens', 4000)
        self.temperature = kwargs.get('temperature', 0.7)
        self.top_p = kwargs.get('top_p', 0.9)
        self.system_prompt = kwargs.get('system_prompt', self._get_default_system_prompt())

        # OpenRouter requires site URL and app name
        self.site_url = kwargs.get('site_url', 'https://github.com/jango-blockchained/mcp-freecad')
        self.app_name = kwargs.get('app_name', 'MCP-FreeCAD')

        # Headers for API requests
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": self.site_url,
            "X-Title": self.app_name,
            "Content-Type": "application/json"
        }

    @property
    def name(self) -> str:
        """Return provider name."""
        return "OpenRouter"

    @property
    def supported_models(self) -> List[str]:
        """Return supported models."""
        return self.OPENROUTER_MODELS.copy()

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

Since you're accessed through OpenRouter, you have the flexibility of multiple AI models. Each model has different strengths:
- Claude models: Best for complex reasoning and code generation
- GPT models: Excellent for general tasks and explanations
- Gemini models: Great for multimodal tasks and large contexts
- Open source models: Cost-effective for routine tasks

Be precise with measurements and technical details. Adapt your response style based on the model being used."""

    async def send_message(self, message: str, **kwargs) -> AIResponse:
        """Send message to OpenRouter API.

        Args:
            message: User message
            **kwargs: Additional parameters

        Returns:
            AIResponse with model's response
        """
        start_time = time.time()

        try:
            # Apply rate limiting
            await self._rate_limit()

            # Build messages array
            messages = []

            # Add system prompt
            if self.system_prompt:
                messages.append({
                    "role": "system",
                    "content": self.system_prompt
                })

            # Add conversation history
            for hist_msg in self.conversation_history[-10:]:  # Last 10 messages
                role = hist_msg.role.value
                # OpenRouter uses standard OpenAI roles
                if role == 'user':
                    role = 'user'
                elif role == 'assistant':
                    role = 'assistant'

                msg_dict = {
                    "role": role,
                    "content": hist_msg.content
                }

                # Add thinking content for Claude models if available
                if hist_msg.thinking_process and self.supports_thinking_mode:
                    msg_dict["thinking"] = hist_msg.thinking_process

                messages.append(msg_dict)

            # Add current message
            messages.append({
                "role": "user",
                "content": message
            })

            # Build request data
            request_data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": kwargs.get('max_tokens', self.max_tokens),
                "temperature": kwargs.get('temperature', self.temperature),
                "top_p": kwargs.get('top_p', self.top_p),
                "stream": False  # We don't support streaming yet
            }

            # Add thinking mode parameters for Claude models
            if self.thinking_mode_enabled and self.supports_thinking_mode:
                request_data["provider"] = {
                    "anthropic": {
                        "thinking": {
                            "enabled": True,
                            "max_thinking_tokens": self.thinking_budget
                        }
                    }
                }

            # Add provider-specific parameters based on model
            if "openai" in self.model:
                request_data["provider"] = request_data.get("provider", {})
                request_data["provider"]["openai"] = {
                    "frequency_penalty": kwargs.get('frequency_penalty', 0.0),
                    "presence_penalty": kwargs.get('presence_penalty', 0.0)
                }

            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.API_BASE}/chat/completions",
                    headers=self.headers,
                    json=request_data,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:

                    if response.status != 200:
                        error_text = await response.text()
                        error_json = {}
                        try:
                            error_json = json.loads(error_text)
                        except:
                            pass

                        error_message = error_json.get('error', {}).get('message', error_text)
                        raise Exception(f"OpenRouter API error {response.status}: {error_message}")

                    result = await response.json()

            # Process response
            ai_response = self._process_response(result)

            # Update statistics
            response_time = time.time() - start_time
            tokens_used = ai_response.usage.get('completion_tokens', 0)
            self._update_stats(response_time, tokens_used)

            # Add to conversation history
            user_msg = AIMessage(MessageRole.USER, message)
            assistant_msg = AIMessage(
                MessageRole.ASSISTANT,
                ai_response.content,
                thinking_process=ai_response.thinking_process
            )

            self.add_message_to_history(user_msg)
            self.add_message_to_history(assistant_msg)

            return ai_response

        except Exception as e:
            response_time = time.time() - start_time
            self._update_stats(response_time, error=True)
            raise Exception(f"OpenRouter request failed: {str(e)}")

    def _process_response(self, response_data: Dict[str, Any]) -> AIResponse:
        """Process OpenRouter API response.

        Args:
            response_data: Raw API response

        Returns:
            Processed AIResponse
        """
        # Extract content
        content = ""
        thinking_process = None

        if "choices" in response_data and response_data["choices"]:
            choice = response_data["choices"][0]
            message = choice.get("message", {})
            content = message.get("content", "")

            # Extract thinking process if available (Claude models)
            if "thinking" in message:
                thinking_process = message["thinking"]

        # Extract usage information
        usage = response_data.get("usage", {})

        # Get model info from response (OpenRouter includes model details)
        model_info = response_data.get("model", self.model)

        # Create response object
        return AIResponse(
            content=content.strip(),
            thinking_process=thinking_process,
            model=model_info,
            usage=usage,
            metadata={
                "provider": "openrouter",
                "id": response_data.get("id"),
                "created": response_data.get("created"),
                "model": model_info,
                "provider_name": response_data.get("provider", {}).get("name", "unknown")
            }
        )

    async def test_connection(self) -> bool:
        """Test connection to OpenRouter API."""
        try:
            # Test with a simple model to minimize cost
            original_model = self.model
            self.model = "openai/gpt-3.5-turbo"  # Cheap model for testing

            test_response = await self.send_message(
                "Hello! Please respond with just 'Connection successful' to test the API.",
                max_tokens=20,
                temperature=0.1
            )

            # Restore original model
            self.model = original_model

            return "successful" in test_response.content.lower()
        except Exception as e:
            # Restore original model even on error
            self.model = original_model
            return False

    def enable_thinking_mode(self, budget: int = 2000):
        """Enable thinking mode for supported models."""
        if not self.supports_thinking_mode:
            raise ValueError(f"Model {self.model} does not support thinking mode. "
                           f"Supported models: {self.THINKING_MODE_MODELS}")

        super().enable_thinking_mode(budget)

    def get_model_info(self, model: str = None) -> Dict[str, Any]:
        """Get detailed information about a model."""
        target_model = model or self.model

        base_info = super().get_model_info(target_model)

        # Add OpenRouter-specific model information
        model_categories = {
            "anthropic/claude": {
                "provider": "Anthropic",
                "strengths": ["Complex reasoning", "Code generation", "Long context"],
                "thinking_mode": "claude-4" in target_model
            },
            "openai/gpt": {
                "provider": "OpenAI",
                "strengths": ["General tasks", "Fast responses", "Wide knowledge"],
                "thinking_mode": False
            },
            "google/gemini": {
                "provider": "Google",
                "strengths": ["Multimodal", "Large context", "Technical tasks"],
                "thinking_mode": False
            },
            "meta/llama": {
                "provider": "Meta",
                "strengths": ["Open source", "Customizable", "Cost-effective"],
                "thinking_mode": False
            },
            "mistralai": {
                "provider": "Mistral AI",
                "strengths": ["European AI", "Efficient", "Multilingual"],
                "thinking_mode": False
            }
        }

        # Find matching category
        for prefix, info in model_categories.items():
            if target_model.startswith(prefix.split('/')[0]):
                base_info.update(info)
                break

        # Add specific model details
        if "claude-4" in target_model:
            base_info["description"] = "Latest Claude model with advanced reasoning"
            base_info["context_window"] = 200000
        elif "gpt-4" in target_model:
            base_info["description"] = "OpenAI's most capable model"
            base_info["context_window"] = 128000
        elif "gemini-2.5-pro" in target_model:
            base_info["description"] = "Google's latest multimodal model"
            base_info["context_window"] = 1000000
        elif "llama-3.1-405b" in target_model:
            base_info["description"] = "Meta's largest open source model"
            base_info["context_window"] = 128000

        # Add cost information (approximate)
        base_info["cost_category"] = self._get_cost_category(target_model)

        return base_info

    def _get_cost_category(self, model: str) -> str:
        """Get cost category for a model."""
        if any(expensive in model for expensive in ["claude-4-opus", "gpt-4", "gemini-2.5-pro"]):
            return "Premium"
        elif any(mid in model for mid in ["claude-4-sonnet", "claude-3.5", "llama-3.1-405b"]):
            return "Standard"
        elif any(cheap in model for cheap in ["gpt-3.5", "claude-3-haiku", "mistral-7b"]):
            return "Economy"
        else:
            return "Variable"

    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of currently available models from OpenRouter."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.API_BASE}/models",
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:

                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", [])
                    else:
                        return []
        except:
            # Return static list if API call fails
            return [{"id": model} for model in self.OPENROUTER_MODELS]

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> Dict[str, float]:
        """Estimate cost for the current model.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Dictionary with cost estimates
        """
        # Approximate costs per 1M tokens (these are rough estimates)
        cost_per_million = {
            "claude-4-opus": {"input": 15.0, "output": 75.0},
            "claude-4-sonnet": {"input": 3.0, "output": 15.0},
            "gpt-4": {"input": 10.0, "output": 30.0},
            "gpt-3.5": {"input": 0.5, "output": 1.5},
            "gemini-2.5-pro": {"input": 1.25, "output": 5.0},
            "llama-3.1-405b": {"input": 3.0, "output": 3.0}
        }

        # Find matching cost
        model_costs = None
        for model_key, costs in cost_per_million.items():
            if model_key in self.model:
                model_costs = costs
                break

        if not model_costs:
            # Default/unknown model costs
            model_costs = {"input": 1.0, "output": 2.0}

        input_cost = (input_tokens / 1_000_000) * model_costs["input"]
        output_cost = (output_tokens / 1_000_000) * model_costs["output"]
        total_cost = input_cost + output_cost

        return {
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(total_cost, 6),
            "currency": "USD"
        }
