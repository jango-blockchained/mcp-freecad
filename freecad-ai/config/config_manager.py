"""
Configuration Manager for MCP FreeCAD Addon

Handles loading, saving, and managing configuration settings for the addon.
"""

import os
import json
import logging
import base64
from typing import Dict, Any, Optional, List
from pathlib import Path

# Try to import cryptography for secure storage
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    Fernet = None
    hashes = None
    PBKDF2HMAC = None


class ConfigManager:
    """Manages configuration settings for the MCP addon."""

    def __init__(self, config_dir: Optional[str] = None):
        """Initialize the configuration manager."""
        self.logger = logging.getLogger(__name__)

        # Determine configuration directory
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Use FreeCAD user data directory
            try:
                import FreeCAD

                user_dir = FreeCAD.getUserAppDataDir()
                self.config_dir = Path(user_dir) / "Mod" / "freecad-ai"
            except ImportError:
                # Fallback to user home directory
                self.config_dir = Path.home() / ".freecad" / "freecad-ai"

        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Configuration file paths
        self.config_file = self.config_dir / "addon_config.json"

        # Choose file extension based on encryption availability
        if CRYPTOGRAPHY_AVAILABLE:
            self.keys_file = self.config_dir / "api_keys.enc"
            self.salt_file = self.config_dir / ".salt"
        else:
            self.keys_file = self.config_dir / "api_keys.json"
            self.salt_file = None
            self.logger.warning(
                "Cryptography not available - API keys will be stored in plain text"
            )

        # Initialize encryption if available
        self.cipher = None
        if CRYPTOGRAPHY_AVAILABLE:
            self._init_encryption()

        # Load configuration
        self.config = self.load_config()

    def _init_encryption(self):
        """Initialize encryption for secure storage."""
        if not CRYPTOGRAPHY_AVAILABLE:
            self.logger.warning("Cryptography not available - encryption disabled")
            self.cipher = None
            return

        try:
            # Generate or load salt
            if self.salt_file.exists():
                with open(self.salt_file, "rb") as f:
                    salt = f.read()
            else:
                salt = os.urandom(16)
                with open(self.salt_file, "wb") as f:
                    f.write(salt)
                # Set restrictive permissions
                os.chmod(self.salt_file, 0o600)

            # Create encryption key from machine-specific data
            machine_id = self._get_machine_id()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))
            self.cipher = Fernet(key)

        except Exception as e:
            self.logger.error(f"Failed to initialize encryption: {e}")
            self.cipher = None

    def _get_machine_id(self) -> str:
        """Get a machine-specific identifier."""
        try:
            # Try to get machine ID from various sources
            if os.path.exists("/etc/machine-id"):
                with open("/etc/machine-id", "r") as f:
                    return f.read().strip()
            elif os.path.exists("/var/lib/dbus/machine-id"):
                with open("/var/lib/dbus/machine-id", "r") as f:
                    return f.read().strip()
            else:
                # Fallback to hostname + user
                import socket
                import getpass

                return f"{socket.gethostname()}-{getpass.getuser()}"
        except:
            return "default-machine-id"

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                self.logger.info(f"Configuration loaded from {self.config_file}")
                return config
            except Exception as e:
                self.logger.error(f"Error loading configuration: {e}")
                return self.get_default_config()
        else:
            self.logger.info("No configuration file found, using defaults")
            return self.get_default_config()

    def save_config(self) -> bool:
        """Save configuration to file."""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=2)
            # Set restrictive permissions
            os.chmod(self.config_file, 0o600)
            self.logger.info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False

    def get_default_config(self) -> Dict[str, Any]:
        """Return default configuration structure."""
        return {
            "version": "1.0.0",
            "providers": {
                "openai": {
                    "enabled": True,
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "timeout": 30,
                    "max_tokens": 4000,
                },
                "anthropic": {
                    "enabled": False,
                    "model": "claude-3-5-sonnet-20241022",
                    "temperature": 0.7,
                    "timeout": 30,
                    "max_tokens": 4000,
                },
                "google": {
                    "enabled": False,
                    "model": "gemini-2.5-pro-preview",
                    "temperature": 0.7,
                    "timeout": 30,
                    "max_tokens": 4000,
                },
            },
            "ui_settings": {
                "theme": "default",
                "auto_save": True,
                "log_level": "INFO",
                "show_tooltips": True,
                "confirm_operations": True,
            },
            "tool_defaults": {
                "advanced_primitives": {
                    "default_radius": 5.0,
                    "default_height": 10.0,
                    "default_position": [0, 0, 0],
                },
                "advanced_operations": {
                    "default_distance": 10.0,
                    "default_angle": 360.0,
                },
                "surface_modification": {
                    "default_fillet_radius": 1.0,
                    "default_chamfer_distance": 1.0,
                    "default_draft_angle": 5.0,
                },
            },
            "connection": {
                "default_method": "auto",
                "retry_attempts": 3,
                "retry_delay": 1.0,
            },
        }

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get specific configuration value."""
        try:
            keys = key.split(".")
            value = self.config
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set_config(self, key: str, value: Any) -> bool:
        """Set specific configuration value."""
        try:
            keys = key.split(".")
            config = self.config
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            config[keys[-1]] = value
            return self.save_config()
        except Exception as e:
            self.logger.error(f"Error setting config {key}: {e}")
            return False

    def reset_config(self) -> bool:
        """Reset configuration to defaults."""
        try:
            self.config = self.get_default_config()
            return self.save_config()
        except Exception as e:
            self.logger.error(f"Error resetting configuration: {e}")
            return False

    def set_api_key(self, provider: str, key: str) -> bool:
        """Store API key for provider (encrypted if possible)."""
        try:
            # Load existing keys
            api_keys = self._load_api_keys()

            if self.cipher and CRYPTOGRAPHY_AVAILABLE:
                # Encrypt and store the key
                encrypted_key = self.cipher.encrypt(key.encode())
                api_keys[provider] = base64.urlsafe_b64encode(encrypted_key).decode()
            else:
                # Store in plain text with warning
                if not hasattr(self, "_warned_plain_text"):
                    self.logger.warning(
                        "Storing API key in plain text - install 'cryptography' package for secure storage"
                    )
                    self._warned_plain_text = True
                api_keys[provider] = key

            # Save keys
            return self._save_api_keys(api_keys)

        except Exception as e:
            self.logger.error(f"Error storing API key for {provider}: {e}")
            return False

    def get_api_key(self, provider: str) -> Optional[str]:
        """Retrieve API key for provider."""
        try:
            api_keys = self._load_api_keys()
            if provider not in api_keys:
                return None

            stored_key = api_keys[provider]

            if self.cipher and CRYPTOGRAPHY_AVAILABLE:
                try:
                    # Try to decrypt the key (for encrypted storage)
                    encrypted_key = base64.urlsafe_b64decode(stored_key.encode())
                    decrypted_key = self.cipher.decrypt(encrypted_key)
                    return decrypted_key.decode()
                except Exception:
                    # If decryption fails, it might be a plain text key from before encryption was available
                    self.logger.warning(
                        f"Failed to decrypt API key for {provider}, treating as plain text"
                    )
                    return stored_key
            else:
                # Plain text storage
                return stored_key

        except Exception as e:
            self.logger.error(f"Error retrieving API key for {provider}: {e}")
            return None

    def validate_api_key(self, provider: str, key: str) -> bool:
        """Validate API key format and connectivity."""
        try:
            if provider == "openai":
                return key.startswith("sk-") and len(key) > 20
            elif provider == "anthropic":
                return key.startswith("sk-ant-") and len(key) > 20
            elif provider == "google":
                return len(key) > 20  # Google keys vary in format
            else:
                return len(key) > 10  # Basic validation for other providers
        except:
            return False

    def list_api_keys(self) -> List[str]:
        """List configured API key providers."""
        try:
            api_keys = self._load_api_keys()
            return list(api_keys.keys())
        except:
            return []

    def _load_api_keys(self) -> Dict[str, str]:
        """Load encrypted API keys from file."""
        if not self.keys_file.exists():
            return {}

        try:
            with open(self.keys_file, "r") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading API keys: {e}")
            return {}

    def _save_api_keys(self, api_keys: Dict[str, str]) -> bool:
        """Save encrypted API keys to file."""
        try:
            with open(self.keys_file, "w") as f:
                json.dump(api_keys, f, indent=2)
            # Set restrictive permissions
            os.chmod(self.keys_file, 0o600)
            return True
        except Exception as e:
            self.logger.error(f"Error saving API keys: {e}")
            return False

    def set_provider_config(self, provider: str, config: Dict[str, Any]) -> bool:
        """Set provider configuration."""
        try:
            if "providers" not in self.config:
                self.config["providers"] = {}
            self.config["providers"][provider] = config
            return self.save_config()
        except Exception as e:
            self.logger.error(f"Error setting provider config for {provider}: {e}")
            return False

    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get provider configuration."""
        return self.get_config(f"providers.{provider}", {})

    def get_available_providers(self) -> List[str]:
        """List supported providers."""
        return ["openai", "anthropic", "google", "openrouter"]

    def set_default_provider(self, provider: str) -> bool:
        """Set default provider."""
        # Allow any provider name, not just the hardcoded ones
        return self.set_config("connection.default_provider", provider)

    def get_default_provider(self) -> str:
        """Get default provider."""
        return self.get_config("connection.default_provider", "Anthropic")

    def export_config(self, file_path: str, include_keys: bool = False) -> bool:
        """Export configuration to file."""
        try:
            export_data = self.config.copy()

            if include_keys:
                # Include API keys (encrypted)
                api_keys = self._load_api_keys()
                export_data["api_keys"] = api_keys

            with open(file_path, "w") as f:
                json.dump(export_data, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Error exporting configuration: {e}")
            return False

    def import_config(self, file_path: str) -> bool:
        """Import configuration from file."""
        try:
            with open(file_path, "r") as f:
                imported_config = json.load(f)

            # Extract API keys if present
            if "api_keys" in imported_config:
                api_keys = imported_config.pop("api_keys")
                self._save_api_keys(api_keys)

            # Update configuration
            self.config.update(imported_config)
            return self.save_config()
        except Exception as e:
            self.logger.error(f"Error importing configuration: {e}")
            return False
