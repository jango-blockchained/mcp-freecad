#!/usr/bin/env python3
"""
Test script to verify FreeCAD AI workbench layout fixes
"""

import os
import subprocess
import sys
import time


def test_freecad_ai_layout():
    """Test that FreeCAD AI workbench loads without layout errors"""
    
    print("🧪 Testing FreeCAD AI workbench layout fixes...")
    
    # Set up paths
    freecad_path = "/home/jango/Git/mcp-freecad/FreeCAD_1.0.0-conda-Linux-x86_64-py311.AppImage"
    log_file = "/tmp/layout_fix_test.log"
    
    # Remove old log
    if os.path.exists(log_file):
        os.remove(log_file)
    
    print(f"📝 Starting FreeCAD with log: {log_file}")
    
    # Start FreeCAD in background
    process = subprocess.Popen([
        freecad_path,
        "--log-file", log_file,
        "--console"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait for startup
    print("⏳ Waiting for FreeCAD to start...")
    time.sleep(10)
    
    # Check for errors
    success = True
    errors = []
    
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            content = f.read()
            
        # Check for layout errors
        if "QLayout: Attempting to add QLayout" in content:
            success = False
            errors.append("❌ QLayout error still present")
        else:
            print("✅ No QLayout errors found")
            
        # Check for successful initialization
        if "Full initialization completed successfully" in content:
            print("✅ Workbench initialized successfully")
        else:
            success = False
            errors.append("❌ Workbench initialization failed")
            
        # Check for UI setup
        if "Full UI setup complete" in content:
            print("✅ UI setup completed")
        else:
            success = False
            errors.append("❌ UI setup failed")
            
        # Check for crashes
        if "Segmentation fault" in content or "core dumped" in content:
            success = False
            errors.append("❌ Segmentation fault detected")
        else:
            print("✅ No crashes detected")
    
    # Clean up
    try:
        process.terminate()
        process.wait(timeout=5)
    except:
        process.kill()
    
    # Report results
    print("\n📊 Test Results:")
    if success:
        print("🎉 SUCCESS: FreeCAD AI workbench layout fixes working correctly!")
        print("   - No QLayout errors")
        print("   - Successful initialization")
        print("   - UI setup complete")
        print("   - No crashes")
        return True
    else:
        print("❌ FAILURE: Issues detected:")
        for error in errors:
            print(f"   {error}")
        return False

if __name__ == "__main__":
    success = test_freecad_ai_layout()
    sys.exit(0 if success else 1)
