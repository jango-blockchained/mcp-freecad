"""
Clients for FreeCAD AI addon.

This module contains client implementations for FreeCAD and MCP bridge.
"""

# Import clients
CLIENTS_AVAILABLE = False
available_clients = []

# Try importing each client individually to be more robust
clients_to_import = [
    ("freecad_client", "FreeCADClient"),
    ("cursor_mcp_bridge", "main")  # Import the main function instead of a class
]

for module_name, item_name in clients_to_import:
    try:
        module = __import__(f"clients.{module_name}", fromlist=[item_name])
        if hasattr(module, item_name):
            # Special handling for cursor_mcp_bridge
            if module_name == "cursor_mcp_bridge":
                globals()["CursorMCPBridge"] = getattr(module, item_name)
                available_clients.append("CursorMCPBridge")
            else:
                globals()[item_name] = getattr(module, item_name)
                available_clients.append(item_name)
    except ImportError as e:
        try:
            import FreeCAD
            FreeCAD.Console.PrintWarning(f"FreeCAD AI: Failed to import {item_name}: {e}\n")
        except ImportError:
            print(f"FreeCAD AI: Failed to import {item_name}: {e}")

if available_clients:
    CLIENTS_AVAILABLE = True

__all__ = available_clients + ["CLIENTS_AVAILABLE"]
