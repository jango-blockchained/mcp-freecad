#!/usr/bin/env python3
import sys
import os

print("Python version:", sys.version)
print("Current working directory:", os.getcwd())
print("Current sys.path:", sys.path)

# Add paths to the extracted AppImage
current_dir = os.getcwd()
appimage_paths = [
    os.path.join(current_dir, "squashfs-root/usr/bin"),
    os.path.join(current_dir, "squashfs-root/usr/lib"),
    os.path.join(current_dir, "squashfs-root/usr/Mod"),
    os.path.join(current_dir, "squashfs-root/usr")
]

# Set Python path to use the AppImage's Python
python_bin = os.path.join(current_dir, "squashfs-root/usr/bin/python")
print(f"AppImage Python path: {python_bin}")
print(f"AppImage Python exists: {os.path.exists(python_bin)}")

# Try different possible paths, including AppImage paths
possible_paths = [
    # AppImage paths
    *appimage_paths,
    # Standard system paths
    "/usr/lib/freecad-python3/lib",
    "/usr/lib/freecad",
    "/usr/lib/freecad/lib",
    "/usr/share/freecad/Mod",
    "/usr/lib/python3/dist-packages",
    "/usr/lib/python3/dist-packages/freecad"
]

# List the contents of squashfs-root/usr for debugging
print("\nListing contents of squashfs-root/usr:")
usr_path = os.path.join(current_dir, "squashfs-root/usr")
if os.path.exists(usr_path):
    for item in os.listdir(usr_path):
        item_path = os.path.join(usr_path, item)
        print(f"  {item} {'(dir)' if os.path.isdir(item_path) else '(file)'}")

# Try to import FreeCAD from each path
for path in possible_paths:
    if os.path.exists(path):
        print(f"\nTrying path: {path}")
        # List the contents of this directory
        print(f"Contents of {path}:")
        try:
            for item in os.listdir(path):
                print(f"  {item}")
        except PermissionError:
            print("  Permission denied")
        
        # Add to sys.path and try to import
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