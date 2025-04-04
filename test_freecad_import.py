import sys
import os
import traceback

print("Python version:", sys.version)
print("Python Path:", sys.path)
print("Current directory:", os.getcwd())

# Check if /usr/lib/freecad-python3/lib exists and list its contents
freecad_lib_path = "/usr/lib/freecad-python3/lib"
if os.path.exists(freecad_lib_path):
    print(f"FreeCAD lib path exists: {freecad_lib_path}")
    print("Contents:")
    for item in os.listdir(freecad_lib_path):
        print(f"  - {item}")
else:
    print(f"FreeCAD lib path does not exist: {freecad_lib_path}")

# Try importing specific FreeCAD-related modules
try:
    import FreeCAD
    print("\nSuccessfully imported FreeCAD module")
    print("FreeCAD Version:", FreeCAD.Version)
    print("FreeCAD location:", FreeCAD.__file__)
except ImportError as e:
    print("\nFailed to import FreeCAD module:", e)
except Exception as e:
    print("\nOther error importing FreeCAD:", e)
    traceback.print_exc()

# Try importing FreeCADGui
try:
    import FreeCADGui
    print("\nSuccessfully imported FreeCADGui module")
    print("FreeCADGui location:", FreeCADGui.__file__)
except ImportError as e:
    print("\nFailed to import FreeCADGui module:", e)
except Exception as e:
    print("\nOther error importing FreeCADGui:", e)
    traceback.print_exc()

print("\nDone.")
