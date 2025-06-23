"""Import utility functions for dynamic module loading"""

import importlib.util
import os
import sys


def try_import_ai_manager():
    """Try to import AIManager with fallback strategies."""
    try:
        from ...ai.ai_manager import AIManager
        return AIManager()
    except ImportError:
        return None


def try_import_config_manager():
    """Try to import ConfigManager with multiple fallback strategies."""
    # Strategy 1: Relative import
    try:
        from ...config.config_manager import ConfigManager
        return ConfigManager()
    except ImportError:
        pass

    # Strategy 2: Absolute import assuming we're in the addon
    try:
        from config.config_manager import ConfigManager
        return ConfigManager()
    except ImportError:
        pass

    # Strategy 3: Direct path import
    try:
        # Get the addon directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        gui_dir = os.path.dirname(current_dir)
        addon_dir = os.path.dirname(gui_dir)
        config_dir = os.path.join(addon_dir, "config")
        
        if config_dir not in sys.path:
            sys.path.insert(0, config_dir)
        from config_manager import ConfigManager
        return ConfigManager()
    except ImportError:
        pass

    # Strategy 4: Try importing from the current package using importlib
    try:
        # Get the path to config_manager.py
        current_dir = os.path.dirname(os.path.abspath(__file__))
        gui_dir = os.path.dirname(current_dir)
        addon_dir = os.path.dirname(gui_dir)
        config_file = os.path.join(addon_dir, "config", "config_manager.py")

        if os.path.exists(config_file):
            spec = importlib.util.spec_from_file_location(
                "config_manager", config_file
            )
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)
            ConfigManager = config_module.ConfigManager
            return ConfigManager()
    except Exception:
        pass

    return None