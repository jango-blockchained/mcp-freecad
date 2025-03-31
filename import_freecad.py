#!/usr/bin/env python3
"""
FreeCAD Import Script

This script demonstrates how to use the FreeCAD AppImage's built-in Python 
interpreter to execute FreeCAD commands.

Instead of trying to import the FreeCAD module directly (which often fails due to
Python version and library incompatibilities), we use subprocess to run commands
with the AppImage's own Python interpreter.
"""

import os
import subprocess
import json
import tempfile
import sys

# Path to the extracted AppImage
APPIMAGE_ROOT = os.path.join(os.getcwd(), "squashfs-root")
APPIMAGE_PYTHON = os.path.join(APPIMAGE_ROOT, "usr/bin/python")

def run_freecad_command(script_content):
    """
    Run a Python script using the AppImage's Python interpreter
    
    Args:
        script_content (str): Python script content to run
        
    Returns:
        tuple: (stdout, stderr)
    """
    # Create a temporary script
    fd, temp_path = tempfile.mkstemp(suffix='.py')
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(script_content)
        
        # Set up environment variables for the AppImage's Python
        env = os.environ.copy()
        env["LD_LIBRARY_PATH"] = os.path.join(APPIMAGE_ROOT, "usr/lib")
        env["PYTHONPATH"] = os.pathsep.join([
            os.path.join(APPIMAGE_ROOT, "usr/lib"),
            os.path.join(APPIMAGE_ROOT, "usr/Mod"),
            os.path.join(APPIMAGE_ROOT, "usr/bin")
        ])
        
        # Use the AppRun script instead of directly calling Python
        # This ensures all AppImage environment variables are set correctly
        process = subprocess.run(
            [os.path.join(APPIMAGE_ROOT, "AppRun"), "-c", f"exec(open('{temp_path}').read())"],
            capture_output=True,
            text=True,
            env=env
        )
        
        return process.stdout, process.stderr
    finally:
        # Clean up the temporary file
        os.unlink(temp_path)

def get_freecad_version():
    """Get the FreeCAD version"""
    script = """
import sys
import os
print("Python path:", sys.path)
print("Current working directory:", os.getcwd())
print("Environment variables:", {k: v for k, v in os.environ.items() if 'PYTHON' in k or 'LD_' in k or 'PATH' in k})

try:
    import FreeCAD
    print(json.dumps({
        "version": FreeCAD.Version,
        "build_date": FreeCAD.BuildDate,
        "success": True
    }))
except ImportError as e:
    print(json.dumps({
        "error": str(e),
        "success": False
    }))
    """
    
    stdout, stderr = run_freecad_command(f"import json\n{script}")
    
    print(f"STDOUT: {stdout}")
    print(f"STDERR: {stderr}")
    
    if stderr:
        print(f"Error: {stderr}")
        return None
    
    try:
        # Extract the JSON part from the output
        for line in stdout.strip().split('\n'):
            if line.startswith('{') and line.endswith('}'):
                return json.loads(line)
        
        print(f"Failed to find JSON output in: {stdout}")
        return None
    except json.JSONDecodeError:
        print(f"Failed to parse output: {stdout}")
        return None

def create_simple_object():
    """Create a simple box object and return its dimensions"""
    script = """
import json
try:
    import FreeCAD
    import Part
    
    # Create a new document
    doc = FreeCAD.newDocument("Example")
    
    # Create a box
    box = doc.addObject("Part::Box", "Box")
    box.Length = 10.0
    box.Width = 5.0
    box.Height = 3.0
    
    # Recompute the document
    doc.recompute()
    
    # Return information about the box
    print(json.dumps({
        "name": box.Name,
        "dimensions": {
            "length": box.Length,
            "width": box.Width,
            "height": box.Height
        },
        "success": True
    }))
except Exception as e:
    print(json.dumps({
        "error": str(e),
        "success": False
    }))
    """
    
    stdout, stderr = run_freecad_command(f"import json\n{script}")
    
    print(f"STDOUT: {stdout}")
    print(f"STDERR: {stderr}")
    
    if stderr:
        print(f"Error: {stderr}")
        return None
    
    try:
        # Extract the JSON part from the output
        for line in stdout.strip().split('\n'):
            if line.startswith('{') and line.endswith('}'):
                return json.loads(line)
        
        print(f"Failed to find JSON output in: {stdout}")
        return None
    except json.JSONDecodeError:
        print(f"Failed to parse output: {stdout}")
        return None

# Alternative approach: use the system FreeCAD installation
def use_system_freecad():
    """Try using the system-installed FreeCAD"""
    script = """
import sys
import os

# Try to find the FreeCAD module path
freecad_paths = [
    "/usr/lib/freecad/lib",
    "/usr/lib/freecad-python3/lib",
    "/usr/share/freecad/Mod"
]

# Try each path
for path in freecad_paths:
    if os.path.exists(path) and path not in sys.path:
        sys.path.append(path)

try:
    import FreeCAD
    print(json.dumps({
        "version": FreeCAD.Version,
        "build_date": FreeCAD.BuildDate,
        "success": True
    }))
except ImportError as e:
    print(json.dumps({
        "error": str(e),
        "success": False
    }))
    """
    
    # Create a temporary script
    fd, temp_path = tempfile.mkstemp(suffix='.py')
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(f"import json\n{script}")
        
        # Run the script with the system Python
        process = subprocess.run(
            [sys.executable, temp_path],
            capture_output=True,
            text=True
        )
        
        print(f"STDOUT: {process.stdout}")
        print(f"STDERR: {process.stderr}")
        
        if process.stderr:
            print(f"Error: {process.stderr}")
            return None
        
        try:
            # Extract the JSON part from the output
            for line in process.stdout.strip().split('\n'):
                if line.startswith('{') and line.endswith('}'):
                    return json.loads(line)
            
            print(f"Failed to find JSON output in: {process.stdout}")
            return None
        except json.JSONDecodeError:
            print(f"Failed to parse output: {process.stdout}")
            return None
    finally:
        # Clean up the temporary file
        os.unlink(temp_path)

# Create a function to run FreeCAD through the freecad CLI
def run_freecad_cli(script_content):
    """
    Run a script using the freecad CLI
    
    Args:
        script_content (str): Python script content to run
        
    Returns:
        str: Output from FreeCAD
    """
    # Create a temporary script
    fd, temp_path = tempfile.mkstemp(suffix='.py')
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(script_content)
        
        # Run the script with the FreeCAD CLI
        process = subprocess.run(
            ["/usr/bin/freecad", "-c", temp_path],
            capture_output=True,
            text=True
        )
        
        print(f"STDOUT: {process.stdout}")
        print(f"STDERR: {process.stderr}")
        
        return process.stdout
    finally:
        # Clean up the temporary file
        os.unlink(temp_path)

# Try to get FreeCAD version using the CLI
def get_freecad_cli_version():
    """Get the FreeCAD version using the CLI"""
    script = """
import json
import FreeCAD
print(json.dumps({
    "version": FreeCAD.Version,
    "build_date": FreeCAD.BuildDate,
    "success": True
}))
"""
    
    output = run_freecad_cli(f"import json\n{script}")
    
    try:
        # Extract the JSON part from the output
        for line in output.strip().split('\n'):
            if line.startswith('{') and line.endswith('}'):
                return json.loads(line)
        
        print(f"Failed to find JSON output in: {output}")
        return None
    except json.JSONDecodeError:
        print(f"Failed to parse output: {output}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    # Check if the AppImage exists
    if not os.path.exists(os.path.join(APPIMAGE_ROOT, "AppRun")):
        print(f"Error: AppRun not found at {os.path.join(APPIMAGE_ROOT, 'AppRun')}")
        print("Trying alternative methods...")
    else:
        print(f"Using AppImage: {APPIMAGE_ROOT}")
        
        # Get FreeCAD version
        print("\nGetting FreeCAD version using AppImage...")
        version_info = get_freecad_version()
        if version_info and version_info.get("success"):
            print(f"FreeCAD Version: {version_info['version']}")
            print(f"Build Date: {version_info['build_date']}")
        else:
            print("Failed to get FreeCAD version using AppImage")
    
    # Try using system FreeCAD
    print("\nTrying to use system FreeCAD...")
    sys_version_info = use_system_freecad()
    if sys_version_info and sys_version_info.get("success"):
        print(f"FreeCAD Version: {sys_version_info['version']}")
        print(f"Build Date: {sys_version_info['build_date']}")
    else:
        print("Failed to get FreeCAD version using system installation")
    
    # Try using FreeCAD CLI
    print("\nTrying to use FreeCAD CLI...")
    cli_version_info = get_freecad_cli_version()
    if cli_version_info and cli_version_info.get("success"):
        print(f"FreeCAD Version: {cli_version_info['version']}")
        print(f"Build Date: {cli_version_info['build_date']}")
        
        # Create a simple object using the CLI
        print("\nCreating a simple box object using CLI...")
        script = """
import json
import FreeCAD
import Part

# Create a new document
doc = FreeCAD.newDocument("Example")

# Create a box
box = doc.addObject("Part::Box", "Box")
box.Length = 10.0
box.Width = 5.0
box.Height = 3.0

# Recompute the document
doc.recompute()

# Return information about the box
print(json.dumps({
    "name": box.Name,
    "dimensions": {
        "length": box.Length,
        "width": box.Width,
        "height": box.Height
    },
    "success": True
}))
"""
        
        output = run_freecad_cli(f"import json\n{script}")
        try:
            for line in output.strip().split('\n'):
                if line.startswith('{') and line.endswith('}'):
                    box_info = json.loads(line)
                    if box_info and box_info.get("success"):
                        print(f"Created box: {box_info['name']}")
                        print(f"Dimensions: {box_info['dimensions']}")
                        print("\nAll operations completed successfully!")
                        break
            else:
                print("Failed to create box")
        except Exception as e:
            print(f"Error processing box output: {e}")
    else:
        print("Failed to get FreeCAD version using CLI") 