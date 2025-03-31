#!/usr/bin/env python3
import sys
import os

print("Python version:", sys.version)
print("Current working directory:", os.getcwd())
print("Current sys.path:", sys.path)

# Try different possible paths
possible_paths = [
    "/usr/lib/freecad-python3/lib",
    "/usr/lib/freecad",
    "/usr/lib/freecad/lib",
    "/usr/share/freecad/Mod",
    "/usr/lib/python3/dist-packages",
    "/usr/lib/python3/dist-packages/freecad"
]

for path in possible_paths:
    if os.path.exists(path):
        print(f"\nTrying path: {path}")
        if path not in sys.path:
            sys.path.append(path)
        try:
            import FreeCAD
            print("SUCCESS! FreeCAD imported from", path)
            print("FreeCAD version:", FreeCAD.Version)
            break
        except ImportError as e:
            print(f"Failed to import FreeCAD: {e}")
    else:
        print(f"\nPath does not exist: {path}")
else:
    print("\nCould not import FreeCAD from any of the paths") 