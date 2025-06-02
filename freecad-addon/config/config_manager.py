"""
Configuration Manager for MCP FreeCAD Addon

Handles loading, saving, and managing configuration settings for the addon.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path


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
                self.config_dir = Path(user_dir) / "Mod" / "MCP_Integration"
            except ImportError:
                # Fallback to user home directory
                self.config_dir = Path.home() / ".freecad" / "MCP_Integration"
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration file path
        self.config_file = self.config_dir / "addon_config.json"
        
        # Load configuration
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
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
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False