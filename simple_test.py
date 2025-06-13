#!/usr/bin/env python3
"""
Simple test to verify our crash fixes
"""

import sys
import os
import subprocess
from pathlib import Path

print("Starting simple test...")

# Test 1: Check if FreeCAD AppImage exists
appimage_path = Path("data/FreeCAD_1.0.0-conda-Linux-x86_64-py311.AppImage")
print(f"Checking AppImage at: {appimage_path.absolute()}")

if appimage_path.exists():
    print("✅ AppImage found")
    
    # Test 2: Check if it's executable
    if os.access(appimage_path, os.X_OK):
        print("✅ AppImage is executable")
        
        # Test 3: Try to run version check
        try:
            print("Testing AppImage version check...")
            result = subprocess.run(
                [str(appimage_path), "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            print(f"Return code: {result.returncode}")
            print(f"Stdout: {result.stdout}")
            print(f"Stderr: {result.stderr}")
            
            if result.returncode == 0:
                print("✅ AppImage version check successful")
            else:
                print("❌ AppImage version check failed")
                
        except subprocess.TimeoutExpired:
            print("❌ AppImage version check timed out")
        except Exception as e:
            print(f"❌ Error running AppImage: {e}")
    else:
        print("❌ AppImage is not executable")
        # Try to make it executable
        try:
            os.chmod(appimage_path, 0o755)
            print("✅ Made AppImage executable")
        except Exception as e:
            print(f"❌ Failed to make AppImage executable: {e}")
else:
    print("❌ AppImage not found")

# Test 4: Try to import our bridge
print("\nTesting bridge import...")
sys.path.insert(0, "src")

try:
    from mcp_freecad.server.freecad_bridge import FreeCADBridge
    print("✅ Successfully imported FreeCADBridge")
    
    # Test 5: Create bridge instance with AppImage
    try:
        bridge = FreeCADBridge(str(appimage_path.absolute()))
        print("✅ Bridge instance created")
        
        # Test 6: Check availability
        try:
            available = bridge.is_available()
            print(f"Bridge availability: {available}")
            
            if available:
                print("✅ FreeCAD is available through bridge")
                
                # Test 7: Try version check through bridge
                try:
                    version_info = bridge.get_version()
                    print(f"Version info: {version_info}")
                    
                    if version_info.get("success"):
                        print("✅ Version check through bridge successful")
                        print(f"FreeCAD version: {version_info.get('version')}")
                    else:
                        print(f"❌ Version check failed: {version_info.get('error')}")
                        
                except Exception as e:
                    print(f"❌ Version check through bridge crashed: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("❌ FreeCAD not available through bridge")
                
        except Exception as e:
            print(f"❌ Availability check failed: {e}")
            
    except Exception as e:
        print(f"❌ Failed to create bridge instance: {e}")
        
except ImportError as e:
    print(f"❌ Failed to import bridge: {e}")
    import traceback
    traceback.print_exc()

print("\nTest completed!")
