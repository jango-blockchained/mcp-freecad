#!/usr/bin/env python3
"""
Test FreeCAD with the AppImage found in the data directory
"""

import os
import subprocess
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_freecad_appimage():
    """Test if the FreeCAD AppImage works"""
    appimage_path = Path(__file__).parent / "data" / "FreeCAD_1.0.0-conda-Linux-x86_64-py311.AppImage"
    
    if not appimage_path.exists():
        print(f"❌ FreeCAD AppImage not found at: {appimage_path}")
        return False
    
    # Make sure AppImage is executable
    os.chmod(appimage_path, 0o755)
    print(f"✅ Found FreeCAD AppImage: {appimage_path}")
    
    # Test version check
    try:
        result = subprocess.run(
            [str(appimage_path), "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"✅ FreeCAD version check successful:")
            print(f"   {result.stdout.strip()}")
            return True
        else:
            print(f"❌ FreeCAD version check failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ FreeCAD version check timed out")
        return False
    except Exception as e:
        print(f"❌ Error running FreeCAD: {e}")
        return False

def test_bridge_with_appimage():
    """Test the bridge with the AppImage"""
    appimage_path = Path(__file__).parent / "data" / "FreeCAD_1.0.0-conda-Linux-x86_64-py311.AppImage"
    
    try:
        from src.mcp_freecad.server.freecad_bridge import FreeCADBridge
        
        # Create bridge with AppImage path
        bridge = FreeCADBridge(str(appimage_path))
        print("✅ Created bridge with AppImage path")
        
        # Test availability
        if bridge.is_available():
            print("✅ FreeCAD AppImage is available via bridge")
            
            # Test version
            try:
                version_info = bridge.get_version()
                if version_info.get("success"):
                    print(f"✅ Version via bridge: {version_info.get('version')}")
                    return True
                else:
                    print(f"❌ Version check via bridge failed: {version_info.get('error')}")
                    return False
            except Exception as e:
                print(f"❌ Version check via bridge crashed: {e}")
                return False
        else:
            print("❌ FreeCAD AppImage not available via bridge")
            return False
            
    except Exception as e:
        print(f"❌ Bridge test with AppImage failed: {e}")
        return False

def test_simple_operation():
    """Test a simple FreeCAD operation"""
    appimage_path = Path(__file__).parent / "data" / "FreeCAD_1.0.0-conda-Linux-x86_64-py311.AppImage"
    
    try:
        from src.mcp_freecad.server.freecad_bridge import FreeCADBridge
        
        bridge = FreeCADBridge(str(appimage_path))
        
        if not bridge.is_available():
            print("⚠️  Skipping operation test - FreeCAD not available")
            return False
        
        print("Testing document creation...")
        try:
            doc_name = bridge.create_document("TestDoc")
            print(f"✅ Document created: {doc_name}")
            
            print("Testing box creation...")
            box_name = bridge.create_box(10.0, 20.0, 30.0, doc_name)
            print(f"✅ Box created: {box_name}")
            
            return True
            
        except Exception as e:
            print(f"❌ Operation test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ Setup for operation test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing FreeCAD AppImage Integration...")
    print("=" * 50)
    
    # Test 1: Direct AppImage test
    print("\nTEST 1: Direct AppImage Test")
    print("-" * 30)
    appimage_works = test_freecad_appimage()
    
    # Test 2: Bridge with AppImage
    print("\nTEST 2: Bridge with AppImage")
    print("-" * 30)
    bridge_works = test_bridge_with_appimage()
    
    # Test 3: Simple operations
    print("\nTEST 3: Simple Operations")
    print("-" * 30)
    operations_work = test_simple_operation()
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"AppImage direct test: {'✅ PASS' if appimage_works else '❌ FAIL'}")
    print(f"Bridge integration:   {'✅ PASS' if bridge_works else '❌ FAIL'}")
    print(f"Basic operations:     {'✅ PASS' if operations_work else '❌ FAIL'}")
    
    if appimage_works and bridge_works and operations_work:
        print("\n🎉 All tests passed! FreeCAD integration is working!")
        print("The crash fixes should resolve the original issue.")
    elif appimage_works and bridge_works:
        print("\n✅ Basic functionality works but operations may need more work.")
        print("This is a significant improvement over crashing.")
    else:
        print("\n⚠️  Some basic tests failed, but the fixes may still help.")
        print("Check the error messages above for specific issues.")
