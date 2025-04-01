#!/usr/bin/env python3
import subprocess
import sys
import os
import json

def test_freecad_connection():
    print("Testing FreeCAD connection via subprocess...")
    
    # Create a temporary Python script to be executed by FreeCAD
    temp_script = "temp_freecad_test.py"
    
    with open(temp_script, "w") as f:
        f.write("""
import FreeCAD
import sys
import json

info = {
    "version": FreeCAD.Version,
    "build_date": FreeCAD.BuildDate,
    "build_version": FreeCAD.BuildVersionMajor,
    "is_gui_up": FreeCAD.GuiUp,
    "active_document": FreeCAD.ActiveDocument.Name if FreeCAD.ActiveDocument else None
}

print(json.dumps(info))
sys.exit(0)
""")
    
    # Find FreeCAD executable
    freecad_path = "/usr/bin/freecad"
    if not os.path.exists(freecad_path):
        print(f"FreeCAD executable not found at {freecad_path}")
        return False
    
    # Run FreeCAD with our script
    try:
        result = subprocess.run(
            [freecad_path, "-c", temp_script],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse output
        for line in result.stdout.splitlines():
            try:
                data = json.loads(line)
                print("\nSuccessfully connected to FreeCAD!")
                print(f"Version: {data.get('version')}")
                print(f"Build Date: {data.get('build_date')}")
                print(f"Build Version: {data.get('build_version')}")
                print(f"GUI Up: {data.get('is_gui_up')}")
                print(f"Active Document: {data.get('active_document')}")
                return True
            except json.JSONDecodeError:
                continue
                
        print("Could not parse FreeCAD output")
        print("stdout:", result.stdout)
        print("stderr:", result.stderr)
        return False
        
    except subprocess.CalledProcessError as e:
        print(f"Error running FreeCAD: {e}")
        print("stdout:", e.stdout)
        print("stderr:", e.stderr)
        return False
    finally:
        # Clean up
        if os.path.exists(temp_script):
            os.remove(temp_script)

if __name__ == "__main__":
    success = test_freecad_connection()
    sys.exit(0 if success else 1) 