"""Fallback Configuration Manager for AI Provider Settings"""

import json
from pathlib import Path


class FallbackConfigManager:
    """Simple fallback config manager for basic functionality."""

    def __init__(self):
        """Initialize fallback config manager."""
        self.config_dir = Path.home() / ".freecad" / "freecad-ai"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "addon_config.json"
        self.keys_file = self.config_dir / "api_keys.json"
        self.config = self.load_config()

    def load_config(self):
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError, PermissionError):
                # json.JSONDecodeError: Invalid JSON format
                # IOError: File read error
                # PermissionError: No read permission
                pass
        return {"providers": {}, "connection": {"default_provider": "Anthropic"}}

    def save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=2)
            return True
        except (IOError, PermissionError, OSError):
            # IOError: File write error
            # PermissionError: No write permission
            # OSError: System-level write error
            return False

    def set_provider_config(self, provider, config):
        """Set provider configuration."""
        if "providers" not in self.config:
            self.config["providers"] = {}
        self.config["providers"][provider] = config
        return self.save_config()

    def get_provider_config(self, provider):
        """Get provider configuration."""
        return self.config.get("providers", {}).get(provider, {})

    def set_api_key(self, provider, key):
        """Store API key for provider."""
        try:
            api_keys = {}
            if self.keys_file.exists():
                with open(self.keys_file, "r") as f:
                    api_keys = json.load(f)
            api_keys[provider] = key
            with open(self.keys_file, "w") as f:
                json.dump(api_keys, f, indent=2)
            return True
        except (IOError, PermissionError, json.JSONDecodeError, OSError):
            # IOError: File read/write error
            # PermissionError: No file permission
            # json.JSONDecodeError: Invalid JSON
            # OSError: System-level file error
            return False

    def get_api_key(self, provider):
        """Retrieve API key for provider."""
        try:
            if self.keys_file.exists():
                with open(self.keys_file, "r") as f:
                    api_keys = json.load(f)
                return api_keys.get(provider)
        except (IOError, PermissionError, json.JSONDecodeError):
            # IOError: File read error
            # PermissionError: No read permission
            # json.JSONDecodeError: Invalid JSON format
            pass
        return None

    def validate_api_key(self, provider, key):
        """Basic API key validation."""
        if provider == "openai":
            return key.startswith("sk-") and len(key) > 20
        elif provider == "anthropic":
            return key.startswith("sk-ant-") and len(key) > 20
        elif provider == "google":
            return len(key) > 20
        elif provider == "vertexai":
            # Vertex AI can use service account JSON keys or API keys
            # Service account keys are JSON format, API keys are strings
            if key.startswith("{") and key.endswith("}"):
                # Looks like JSON service account key
                try:
                    json.loads(key)
                    return True
                except json.JSONDecodeError:
                    return False
            else:
                # Regular API key format
                return len(key) > 20
        return len(key) > 10

    def list_api_keys(self):
        """List configured API key providers."""
        try:
            if self.keys_file.exists():
                with open(self.keys_file, "r") as f:
                    api_keys = json.load(f)
                return list(api_keys.keys())
        except (IOError, PermissionError, json.JSONDecodeError):
            # IOError: File read error
            # PermissionError: No read permission
            # json.JSONDecodeError: Invalid JSON format
            pass
        return []

    def set_default_provider(self, provider):
        """Set default provider."""
        if "connection" not in self.config:
            self.config["connection"] = {}
        self.config["connection"]["default_provider"] = provider
        return self.save_config()

    def get_default_provider(self):
        """Get default provider."""
        return self.config.get("connection", {}).get("default_provider", "Anthropic")
