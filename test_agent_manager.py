#!/usr/bin/env python3
"""
FreeCAD AI Agent Manager Test

This script tests the initialization of the AgentManager in FreeCAD AI.
"""

import os
import sys
import traceback
import datetime
import importlib

# Add paths to sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
freecad_ai_dir = os.path.join(script_dir, 'freecad-ai')

if freecad_ai_dir not in sys.path:
    sys.path.insert(0, freecad_ai_dir)

# Create timestamped log file
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
log_path = os.path.join(script_dir, f"agent_manager_test_{timestamp}.log")

def log(message):
    """Write a message to the log file and print it"""
    print(message)
    with open(log_path, "a") as f:
        f.write(message + "\n")

# Start logging
log("="*50)
log(f"FreeCAD AI Agent Manager Test - {datetime.datetime.now().isoformat()}")
log("="*50)
log("")

# Test importing FreeCAD
try:
    import FreeCAD
    log(f"✅ Successfully imported FreeCAD")
    log(f"   Version: {'.'.join(FreeCAD.Version)}")
    log(f"   Build Date: {FreeCAD.BuildDate}")
    log(f"   GUI Enabled: {getattr(FreeCAD, 'GuiUp', False)}")
except ImportError as e:
    log(f"❌ Failed to import FreeCAD: {e}")
except Exception as e:
    log(f"❌ Error importing FreeCAD: {type(e).__name__}: {str(e)}")
    log(traceback.format_exc())

log("")
log("--- Testing freecad_ai.ai.agent_manager imports ---")

# Try importing with different methods
import_paths = [
    "freecad_ai.ai.agent_manager",
    "freecad-ai.ai.agent_manager",
    "ai.agent_manager"
]

agent_manager_module = None

for path in import_paths:
    try:
        module_name = path
        if "-" in path:
            module_name = path.replace("-", "_")
            
        log(f"Trying to import: {module_name}")
        agent_manager_module = importlib.import_module(module_name)
        log(f"✅ Successfully imported {module_name}")
        break
    except ImportError as e:
        log(f"❌ Failed to import {module_name}: {e}")
    except Exception as e:
        log(f"❌ Error importing {module_name}: {type(e).__name__}: {str(e)}")
        log(traceback.format_exc())

if not agent_manager_module:
    # Try direct file import
    try:
        log("Trying direct file import...")
        agent_manager_path = os.path.join(freecad_ai_dir, "ai", "agent_manager.py")
        log(f"Agent manager path: {agent_manager_path}")
        
        if not os.path.exists(agent_manager_path):
            log(f"❌ File does not exist: {agent_manager_path}")
        else:
            log(f"✅ File exists, trying to load it")
            
            spec = importlib.util.spec_from_file_location("agent_manager", agent_manager_path)
            agent_manager_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(agent_manager_module)
            
            log(f"✅ Successfully loaded agent_manager.py directly")
    except Exception as e:
        log(f"❌ Error with direct file import: {type(e).__name__}: {str(e)}")
        log(traceback.format_exc())

# If we have the module, check for AgentManager class
if agent_manager_module:
    log("")
    log("--- Testing AgentManager class ---")
    
    # Check if AgentManager class exists
    if hasattr(agent_manager_module, "AgentManager"):
        log(f"✅ AgentManager class found in module")
        
        # Try to instantiate
        try:
            agent_manager = agent_manager_module.AgentManager()
            log(f"✅ Successfully created AgentManager instance")
            
            # Check basic properties
            if hasattr(agent_manager, "agents"):
                log(f"   Agents: {len(agent_manager.agents)}")
            else:
                log(f"❌ AgentManager has no 'agents' attribute")
                
            if hasattr(agent_manager, "active_agent"):
                log(f"   Active agent: {agent_manager.active_agent}")
            else:
                log(f"❌ AgentManager has no 'active_agent' attribute")
                
        except Exception as e:
            log(f"❌ Error creating AgentManager instance: {type(e).__name__}: {str(e)}")
            log(traceback.format_exc())
    else:
        log(f"❌ AgentManager class not found in module")
        log(f"   Available attributes: {dir(agent_manager_module)}")

# Check paths and module structure
log("")
log("--- Python Path and Module Structure ---")
log(f"Python executable: {sys.executable}")
log(f"Working directory: {os.getcwd()}")
log("sys.path:")
for p in sys.path:
    log(f"   - {p}")

# Check freecad-ai structure
log("")
log("--- FreeCAD AI Structure ---")

if not os.path.exists(freecad_ai_dir):
    log(f"❌ freecad-ai directory not found: {freecad_ai_dir}")
else:
    log(f"✅ freecad-ai directory exists: {freecad_ai_dir}")
    
    # Check key files
    for path in ["__init__.py", "ai/agent_manager.py", "api/provider_service.py"]:
        full_path = os.path.join(freecad_ai_dir, path)
        if os.path.exists(full_path):
            log(f"✅ File exists: {path}")
        else:
            log(f"❌ File missing: {path}")

log("")
log(f"Test completed. Log saved to: {log_path}")
