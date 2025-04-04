#!/usr/bin/env python3

import sys
import os

print("Python version:", sys.version)
print("Current directory:", os.getcwd())

# Add the FreeCAD module path to Python path
freecad_module_path = "/usr/lib/freecad-python3/lib"
if os.path.exists(freecad_module_path):
    sys.path.append(freecad_module_path)
    print(f"Added {freecad_module_path} to Python path")
else:
    print(f"Error: FreeCAD module path {freecad_module_path} does not exist!")

# Try to import FreeCAD
try:
    import FreeCAD
    print("\nSuccessfully imported FreeCAD module!")
    print("FreeCAD Version:", FreeCAD.Version)
    print("FreeCAD module location:", FreeCAD.__file__)
except ImportError as e:
    print(f"\nFailed to import FreeCAD module: {e}")
    print("Python path:")
    for path in sys.path:
        print(f"  - {path}")
    sys.exit(1)

# Try to import FreeCADGui
try:
    import FreeCADGui
    print("\nSuccessfully imported FreeCADGui module!")
    print("FreeCADGui module location:", FreeCADGui.__file__)
except ImportError as e:
    print(f"\nFailed to import FreeCADGui module: {e}")
    print("This may be normal if running in a non-GUI environment")

print("\nFreeCAD import verification completed successfully!")
