"""Tests for AI providers"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ai.ai_manager import AIManager
from ai.claude_provider import ClaudeProvider
from ai.gemini_provider import GeminiProvider
from ai.openrouter_provider import OpenRouterProvider


class TestAIProviders(unittest.TestCase):
    """Test AI provider implementations."""

    def setUp(self):
        """Set up test fixtures."""
        self.ai_manager = AIManager()

    def test_claude_provider_creation(self):
        """Test Claude provider creation."""
        provider = ClaudeProvider("test_key")
        self.assertEqual(provider.get_provider_name(), "Claude")
        self.assertIn("claude-3-5-sonnet-20241022", provider.get_available_models())

    def test_gemini_provider_creation(self):
        """Test Gemini provider creation."""
        provider = GeminiProvider("test_key")
        self.assertEqual(provider.get_provider_name(), "Gemini")
        self.assertIn("gemini-1.5-pro-latest", provider.get_available_models())

    def test_openrouter_provider_creation(self):
        """Test OpenRouter provider creation."""
        provider = OpenRouterProvider("sk-test_key")
        self.assertEqual(provider.get_provider_name(), "OpenRouter")
        self.assertIn("anthropic/claude-3.5-sonnet", provider.get_available_models())

    def test_ai_manager_add_providers(self):
        """Test adding providers to AI manager."""
        success = self.ai_manager.add_provider("claude", "claude", "test_key")
        self.assertTrue(success)

        success = self.ai_manager.add_provider("gemini", "gemini", "test_key")
        self.assertTrue(success)

        success = self.ai_manager.add_provider(
            "openrouter", "openrouter", "sk-test_key"
        )
        self.assertTrue(success)

        self.assertEqual(len(self.ai_manager.providers), 3)


if __name__ == "__main__":
    unittest.main()
