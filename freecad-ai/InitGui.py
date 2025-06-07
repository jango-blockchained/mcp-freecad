"""
InitGui.py - FreeCAD GUI Initialization for FreeCAD AI Addon

This file is automatically loaded by FreeCAD when the addon is activated.
It registers the AI workbench and initializes GUI components.
"""

import os
import sys

import FreeCAD
import FreeCADGui

# Add addon directory to Python path
try:
    # Try to get the directory from __file__ (works in most cases)
    addon_dir = os.path.dirname(__file__)
except NameError:
    # __file__ not available in FreeCAD's addon loading context
    # Use inspect to get the current file location
    import inspect

    current_file = inspect.getfile(inspect.currentframe())
    addon_dir = os.path.dirname(os.path.abspath(current_file))

if addon_dir not in sys.path:
    sys.path.insert(0, addon_dir)

# Import the main workbench class with comprehensive error handling
workbench_imported = False
workbench = None

try:
    FreeCAD.Console.PrintMessage("FreeCAD AI Addon: Starting initialization...\n")
    FreeCAD.Console.PrintMessage(f"FreeCAD AI Addon: Addon directory: {addon_dir}\n")

    # Strategy 1: Direct import
    try:
        from freecad_ai_workbench import MCPWorkbench
        workbench_imported = True
        FreeCAD.Console.PrintMessage("FreeCAD AI Addon: Workbench imported successfully\n")
    except ImportError as e:
        FreeCAD.Console.PrintWarning(f"FreeCAD AI Addon: Direct import failed: {e}\n")

    # Strategy 2: Add current directory to path and retry
    if not workbench_imported:
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
            from freecad_ai_workbench import MCPWorkbench
            workbench_imported = True
            FreeCAD.Console.PrintMessage("FreeCAD AI Addon: Workbench imported with path modification\n")
        except ImportError as e:
            FreeCAD.Console.PrintWarning(f"FreeCAD AI Addon: Import with path modification failed: {e}\n")

    # Strategy 3: Try importing from parent directory
    if not workbench_imported:
        try:
            parent_dir = os.path.dirname(addon_dir)
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            from freecad_ai_workbench import MCPWorkbench
            workbench_imported = True
            FreeCAD.Console.PrintMessage("FreeCAD AI Addon: Workbench imported from parent directory\n")
        except ImportError as e:
            FreeCAD.Console.PrintWarning(f"FreeCAD AI Addon: Parent directory import failed: {e}\n")

    if not workbench_imported:
        FreeCAD.Console.PrintError("FreeCAD AI Addon: Failed to import workbench with all strategies\n")
        FreeCAD.Console.PrintError(f"FreeCAD AI Addon: Python path: {sys.path}\n")
        FreeCAD.Console.PrintError(f"FreeCAD AI Addon: Addon directory contents: {os.listdir(addon_dir) if os.path.exists(addon_dir) else 'Directory not found'}\n")
        raise ImportError("Could not import MCPWorkbench with any strategy")

    # Create workbench instance with error handling
    try:
        workbench = MCPWorkbench()
        FreeCAD.Console.PrintMessage("FreeCAD AI Addon: Workbench instance created successfully\n")
    except Exception as e:
        FreeCAD.Console.PrintError(f"FreeCAD AI Addon: Failed to create workbench instance: {e}\n")
        raise e

    # Register the workbench with FreeCAD with comprehensive error handling
    try:
        # Check if workbench already exists and handle gracefully
        existing_workbenches = []
        try:
            # Try to get list of existing workbenches
            if hasattr(FreeCADGui, 'listWorkbenches'):
                existing_workbenches = list(FreeCADGui.listWorkbenches().keys())
            FreeCAD.Console.PrintMessage(f"FreeCAD AI Addon: Existing workbenches: {existing_workbenches}\n")
        except Exception as e:
            FreeCAD.Console.PrintWarning(f"FreeCAD AI Addon: Could not list existing workbenches: {e}\n")

        # Attempt to register the workbench
        FreeCADGui.addWorkbench(workbench)
        FreeCAD.Console.PrintMessage("FreeCAD AI Addon: Workbench registered successfully\n")

    except KeyError as ke:
        if "already exists" in str(ke).lower():
            FreeCAD.Console.PrintWarning(f"FreeCAD AI Addon: Workbench already registered, skipping: {ke}\n")
        else:
            FreeCAD.Console.PrintError(f"FreeCAD AI Addon: Workbench registration KeyError: {ke}\n")
            raise ke
    except AttributeError as ae:
        FreeCAD.Console.PrintError(f"FreeCAD AI Addon: FreeCADGui.addWorkbench not available: {ae}\n")
        raise ae
    except Exception as e:
        FreeCAD.Console.PrintError(f"FreeCAD AI Addon: Workbench registration failed: {e}\n")
        raise e

except ImportError as e:
    FreeCAD.Console.PrintError(f"FreeCAD AI Addon: Failed to import workbench: {e}\n")
    FreeCAD.Console.PrintError(f"FreeCAD AI Addon: Python path: {sys.path}\n")
    FreeCAD.Console.PrintError(f"FreeCAD AI Addon: Working directory: {os.getcwd()}\n")
    # Try to provide helpful debugging information
    try:
        FreeCAD.Console.PrintError(f"FreeCAD AI Addon: Addon directory exists: {os.path.exists(addon_dir)}\n")
        if os.path.exists(addon_dir):
            files = [f for f in os.listdir(addon_dir) if f.endswith('.py')]
            FreeCAD.Console.PrintError(f"FreeCAD AI Addon: Python files in addon directory: {files}\n")
    except Exception:
        pass
except Exception as e:
    FreeCAD.Console.PrintError(f"FreeCAD AI Addon: Initialization error: {e}\n")
    import traceback
    FreeCAD.Console.PrintError(f"FreeCAD AI Addon: Traceback: {traceback.format_exc()}\n")

# Addon metadata for FreeCAD
__version__ = "0.7.11"
__title__ = "FreeCAD AI"
__author__ = "jango-blockchained"
__url__ = "https://github.com/jango-blockchained/mcp-freecad"
