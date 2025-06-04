"""
Base AI Provider

Abstract base class and common data structures for AI providers.
Provides standardized interface for different AI service integrations.

Author: jango-blockchained
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union


class MessageRole(Enum):
    """Message roles for conversation history."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class AIMessage:
    """Represents a message in the conversation history."""

    role: MessageRole
    content: str
    thinking_process: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AIResponse:
    """Represents a response from an AI provider."""

    content: str
    thinking_process: Optional[str] = None
    model: Optional[str] = None
    usage: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    response_time: float = 0.0
    timestamp: float = field(default_factory=time.time)


class BaseAIProvider(ABC):
    """Abstract base class for AI providers."""

    def __init__(self, api_key: str, model: str = None, **kwargs):
        """Initialize the AI provider.

        Args:
            api_key: API key for the service
            model: Model to use (provider-specific)
            **kwargs: Additional configuration options
        """
        self.api_key = api_key
        self.model = model

        # Configuration
        self.max_tokens = kwargs.get("max_tokens", 4000)
        self.temperature = kwargs.get("temperature", 0.7)
        self.timeout = kwargs.get("timeout", 120)

        # Conversation management
        self.conversation_history: List[AIMessage] = []
        self.max_history_length = kwargs.get("max_history_length", 50)

        # Rate limiting
        self.rate_limit_delay = kwargs.get("rate_limit_delay", 1.0)  # seconds
        self.last_request_time = 0.0

        # Statistics tracking
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0,
            "total_response_time": 0.0,
            "average_response_time": 0.0,
        }

        # Thinking mode configuration
        self.thinking_mode_enabled = kwargs.get("thinking_mode_enabled", False)
        self.thinking_budget = kwargs.get("thinking_budget", 2000)

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name."""
        pass

    @property
    @abstractmethod
    def supported_models(self) -> List[str]:
        """Return list of supported models."""
        pass

    @property
    def supports_thinking_mode(self) -> bool:
        """Return whether the provider supports thinking mode."""
        return False

    @abstractmethod
    async def send_message(self, message: str, **kwargs) -> AIResponse:
        """Send a message to the AI provider.

        Args:
            message: The message to send
            **kwargs: Additional parameters

        Returns:
            AIResponse with the provider's response
        """
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test the connection to the AI provider.

        Returns:
            True if connection is successful, False otherwise
        """
        pass

    def add_message_to_history(self, message: AIMessage):
        """Add a message to the conversation history.

        Args:
            message: The message to add
        """
        self.conversation_history.append(message)

        # Trim history if it exceeds max length
        if len(self.conversation_history) > self.max_history_length:
            # Keep system messages and trim older user/assistant messages
            system_messages = [
                msg
                for msg in self.conversation_history
                if msg.role == MessageRole.SYSTEM
            ]
            other_messages = [
                msg
                for msg in self.conversation_history
                if msg.role != MessageRole.SYSTEM
            ]

            # Keep the most recent messages
            recent_messages = other_messages[
                -(self.max_history_length - len(system_messages)) :
            ]
            self.conversation_history = system_messages + recent_messages

    def clear_conversation_history(self):
        """Clear the conversation history."""
        self.conversation_history.clear()

    def get_conversation_history(self, include_system: bool = True) -> List[AIMessage]:
        """Get the conversation history.

        Args:
            include_system: Whether to include system messages

        Returns:
            List of messages in the conversation history
        """
        if include_system:
            return self.conversation_history.copy()
        else:
            return [
                msg
                for msg in self.conversation_history
                if msg.role != MessageRole.SYSTEM
            ]

    async def _rate_limit(self):
        """Apply rate limiting to prevent API abuse."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            await asyncio.sleep(sleep_time)

        self.last_request_time = time.time()

    def _update_stats(
        self, response_time: float, tokens_used: int = 0, error: bool = False
    ):
        """Update provider statistics.

        Args:
            response_time: Time taken for the request
            tokens_used: Number of tokens used
            error: Whether the request resulted in an error
        """
        self.stats["total_requests"] += 1

        if error:
            self.stats["failed_requests"] += 1
        else:
            self.stats["successful_requests"] += 1
            self.stats["total_tokens"] += tokens_used

        self.stats["total_response_time"] += response_time

        # Calculate average response time
        if self.stats["total_requests"] > 0:
            self.stats["average_response_time"] = (
                self.stats["total_response_time"] / self.stats["total_requests"]
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get provider statistics.

        Returns:
            Dictionary containing provider statistics
        """
        return self.stats.copy()

    def reset_stats(self):
        """Reset provider statistics."""
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0,
            "total_response_time": 0.0,
            "average_response_time": 0.0,
        }

    def enable_thinking_mode(self, budget: int = 2000):
        """Enable thinking mode if supported.

        Args:
            budget: Token budget for thinking process
        """
        if self.supports_thinking_mode:
            self.thinking_mode_enabled = True
            self.thinking_budget = budget
        else:
            raise NotImplementedError(f"{self.name} does not support thinking mode")

    def disable_thinking_mode(self):
        """Disable thinking mode."""
        self.thinking_mode_enabled = False

    def get_model_info(self, model: str = None) -> Dict[str, Any]:
        """Get information about a model.

        Args:
            model: Model name (defaults to current model)

        Returns:
            Dictionary containing model information
        """
        target_model = model or self.model

        return {
            "name": target_model,
            "provider": self.name,
            "supports_thinking_mode": self.supports_thinking_mode,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }

    def set_system_prompt(self, prompt: str):
        """Set or update the system prompt.

        Args:
            prompt: The system prompt to set
        """
        # Remove existing system messages
        self.conversation_history = [
            msg for msg in self.conversation_history if msg.role != MessageRole.SYSTEM
        ]

        # Add new system message at the beginning
        system_message = AIMessage(MessageRole.SYSTEM, prompt)
        self.conversation_history.insert(0, system_message)

    def __str__(self) -> str:
        """String representation of the provider."""
        return f"{self.name} (Model: {self.model})"

    def __repr__(self) -> str:
        """Detailed string representation of the provider."""
        return (
            f"{self.__class__.__name__}("
            f"model='{self.model}', "
            f"thinking_mode={self.thinking_mode_enabled}, "
            f"requests={self.stats['total_requests']}"
            f")"
        )
