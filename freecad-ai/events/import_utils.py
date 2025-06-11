"""
Import utilities for the events system.

This module provides consistent import handling with proper fallbacks
for when modules are loaded in different contexts.
"""

import os
import sys
import logging
from typing import Any, Optional, Type

logger = logging.getLogger(__name__)


def safe_import_from_events(module_name: str, class_name: str, addon_dir: Optional[str] = None) -> Optional[Type[Any]]:
    """
    Safely import a class from the events module with proper fallbacks.
    
    Args:
        module_name: Name of the module to import from (e.g., 'base', 'event_router')
        class_name: Name of the class to import
        addon_dir: Optional addon directory path for fallback imports
        
    Returns:
        The imported class or None if import failed
    """
    try:
        # Try relative import first
        if module_name == 'base':
            from .base import EventProvider
            return EventProvider if class_name == 'EventProvider' else getattr(__import__(f'.{module_name}', fromlist=[class_name], level=1), class_name)
        else:
            module = __import__(f'.{module_name}', fromlist=[class_name], level=1)
            return getattr(module, class_name)
            
    except (ImportError, AttributeError) as e:
        logger.debug(f"Relative import failed for {module_name}.{class_name}: {e}")
        
        # Try absolute import with path manipulation
        try:
            if addon_dir is None:
                addon_dir = os.path.dirname(os.path.dirname(__file__))
            
            if addon_dir not in sys.path:
                sys.path.insert(0, addon_dir)
            
            module_path = f"events.{module_name}"
            module = __import__(module_path, fromlist=[class_name])
            return getattr(module, class_name)
            
        except (ImportError, AttributeError) as e2:
            logger.warning(f"Failed to import {class_name} from {module_name}: {e2}")
            return None


def safe_import_freecad_util(util_name: str, addon_dir: Optional[str] = None) -> Optional[Any]:
    """
    Safely import a utility from the utils module.
    
    Args:
        util_name: Name of the utility to import
        addon_dir: Optional addon directory path for fallback imports
        
    Returns:
        The imported utility or None if import failed
    """
    try:
        # Try relative import first
        from ..utils.safe_async import freecad_safe_emit
        if util_name == 'freecad_safe_emit':
            return freecad_safe_emit
        # Add other utilities as needed
        
    except ImportError as e:
        logger.debug(f"Relative import failed for utils.{util_name}: {e}")
        
        # Try absolute import with path manipulation
        try:
            if addon_dir is None:
                addon_dir = os.path.dirname(os.path.dirname(__file__))
            
            if addon_dir not in sys.path:
                sys.path.insert(0, addon_dir)
            
            module = __import__("utils.safe_async", fromlist=[util_name])
            return getattr(module, util_name)
            
        except (ImportError, AttributeError) as e2:
            logger.warning(f"Failed to import {util_name} from utils: {e2}")
            return None


def log_freecad_message(message: str, level: str = "info"):
    """
    Log a message using FreeCAD console if available, otherwise use standard logging.
    
    Args:
        message: Message to log
        level: Log level ('info', 'warning', 'error')
    """
    try:
        import FreeCAD
        console_method = {
            'info': FreeCAD.Console.PrintMessage,
            'warning': FreeCAD.Console.PrintWarning,
            'error': FreeCAD.Console.PrintError
        }.get(level, FreeCAD.Console.PrintMessage)
        
        console_method(f"FreeCAD AI Events: {message}\n")
        
    except ImportError:
        # Fallback to standard logging
        log_method = {
            'info': logger.info,
            'warning': logger.warning,
            'error': logger.error
        }.get(level, logger.info)
        
        log_method(f"FreeCAD AI Events: {message}")
