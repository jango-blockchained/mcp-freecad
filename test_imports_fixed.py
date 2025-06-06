#!/usr/bin/env python3
"""Test script to verify FreeCAD AI addon imports after fixes"""

import sys
import os

# Add freecad-ai directory to path
addon_dir = os.path.join(os.path.dirname(__file__), 'freecad-ai')
sys.path.insert(0, addon_dir)

print("Testing FreeCAD AI addon imports...")
print(f"Addon directory: {addon_dir}")
print("-" * 60)

# Test main modules
modules_to_test = [
    ("InitGui", "Main initialization file"),
    ("freecad_ai_workbench", "Workbench module"),
    ("tools", "Tools module"),
    ("resources", "Resources module"), 
    ("events", "Events module"),
    ("api", "API module"),
    ("clients", "Clients module"),
    ("ai", "AI providers module"),
]

results = []

for module_name, description in modules_to_test:
    try:
        module = __import__(module_name)
        
        # Check for expected attributes
        if module_name == "tools" and hasattr(module, "TOOLS_AVAILABLE"):
            status = f"✓ OK (TOOLS_AVAILABLE={module.TOOLS_AVAILABLE})"
        elif module_name == "resources" and hasattr(module, "RESOURCES_AVAILABLE"):
            status = f"✓ OK (RESOURCES_AVAILABLE={module.RESOURCES_AVAILABLE})"
        elif module_name == "events" and hasattr(module, "EVENTS_AVAILABLE"):
            status = f"✓ OK (EVENTS_AVAILABLE={module.EVENTS_AVAILABLE})"
        elif module_name == "api" and hasattr(module, "API_AVAILABLE"):
            status = f"✓ OK (API_AVAILABLE={module.API_AVAILABLE})"
        elif module_name == "clients" and hasattr(module, "CLIENTS_AVAILABLE"):
            status = f"✓ OK (CLIENTS_AVAILABLE={module.CLIENTS_AVAILABLE})"
        elif module_name == "ai" and hasattr(module, "AVAILABLE_PROVIDERS"):
            provider_count = len(getattr(module, "AVAILABLE_PROVIDERS", {}))
            status = f"✓ OK ({provider_count} providers available)"
        else:
            status = "✓ OK"
            
        results.append((module_name, description, status))
        
    except ImportError as e:
        results.append((module_name, description, f"✗ FAILED: {e}"))
    except Exception as e:
        results.append((module_name, description, f"✗ ERROR: {e}"))

# Print results
print("\nImport Test Results:")
print("-" * 60)
for module_name, description, status in results:
    print(f"{module_name:20} {description:25} {status}")

# Test workbench class
print("\n" + "-" * 60)
print("Testing MCPWorkbench class...")
try:
    from freecad_ai_workbench import MCPWorkbench
    workbench = MCPWorkbench()
    print(f"✓ MCPWorkbench instantiated successfully")
    print(f"  - MenuText: {workbench.MenuText}")
    print(f"  - ToolTip: {workbench.ToolTip}")
except Exception as e:
    print(f"✗ Failed to instantiate MCPWorkbench: {e}")

print("\n" + "-" * 60)
print("Import test completed.")