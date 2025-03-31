#!/usr/bin/env python3
"""
FreeCAD CLI Test Script

This script uses the FreeCAD command-line interface to execute Python code
inside the FreeCAD environment.
"""

import os
import subprocess
import json
import tempfile
import sys

def run_freecad_script(script_content):
    """
    Run a Python script in FreeCAD using the command-line interface
    
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
        
        # Run the script with the FreeCAD CLI
        process = subprocess.run(
            ["freecad", "-c", temp_path],
            capture_output=True,
            text=True
        )
        
        return process.stdout, process.stderr
    finally:
        # Clean up the temporary file
        os.unlink(temp_path)

def get_freecad_version():
    """Get the FreeCAD version"""
    script = """
import json
import FreeCAD
print(json.dumps({
    "version": FreeCAD.Version,
    "build_date": FreeCAD.BuildDate,
    "success": True
}))
"""
    
    stdout, stderr = run_freecad_script(script)
    
    print("STDOUT:", stdout)
    print("STDERR:", stderr)
    
    if stderr and not stdout:
        print(f"Error: {stderr}")
        return None
    
    try:
        # Find the JSON output in the stdout
        for line in stdout.strip().split('\n'):
            if line.startswith('{') and line.endswith('}'):
                return json.loads(line)
        return None
    except json.JSONDecodeError:
        print(f"Failed to parse output: {stdout}")
        return None

def create_box():
    """Create a box in FreeCAD"""
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
    
    stdout, stderr = run_freecad_script(script)
    
    print("STDOUT:", stdout)
    print("STDERR:", stderr)
    
    if stderr and not stdout:
        print(f"Error: {stderr}")
        return None
    
    try:
        # Find the JSON output in the stdout
        for line in stdout.strip().split('\n'):
            if line.startswith('{') and line.endswith('}'):
                return json.loads(line)
        return None
    except json.JSONDecodeError:
        print(f"Failed to parse output: {stdout}")
        return None

if __name__ == "__main__":
    print("Checking FreeCAD version...")
    version_info = get_freecad_version()
    
    if version_info and version_info.get("success"):
        print(f"FreeCAD Version: {version_info['version']}")
        print(f"Build Date: {version_info['build_date']}")
        
        print("\nCreating a box...")
        box_info = create_box()
        
        if box_info and box_info.get("success"):
            print(f"Created box: {box_info['name']}")
            print(f"Dimensions: {box_info['dimensions']}")
            print("\nAll operations completed successfully!")
        else:
            print("Failed to create a box")
    else:
        print("Failed to get FreeCAD version") 