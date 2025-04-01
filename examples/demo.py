#!/usr/bin/env python3
"""
FreeCAD Integration Demo

This script demonstrates all the available FreeCAD integration methods:
1. Socket Server Connection
2. CLI Bridge Connection
3. Mock Implementation

It creates a simple model in each case and exports it to STL.
"""

import os
import sys
import time
import subprocess
import argparse

try:
    from freecad_connection import FreeCADConnection
except ImportError:
    print("Error: freecad_connection.py not found in the current directory")
    sys.exit(1)

def demo_connection(connection_method=None):
    """
    Demonstrate a specific connection method
    
    Args:
        connection_method: The connection method to use (server, bridge, mock, or None for auto)
    """
    method_name = connection_method if connection_method else "auto"
    print(f"\n{'='*50}")
    print(f"TESTING {method_name.upper()} CONNECTION METHOD")
    print(f"{'='*50}")
    
    # Create connection
    fc = FreeCADConnection(
        prefer_method=connection_method,
        auto_connect=True
    )
    
    if not fc.is_connected():
        print(f"❌ Could not connect to FreeCAD using {method_name} method")
        return False
    
    active_method = fc.get_connection_type()
    print(f"✅ Connected to FreeCAD using {active_method} method")
    
    # Get FreeCAD version
    try:
        version_info = fc.get_version()
        version_str = '.'.join(str(v) for v in version_info.get('version', ['Unknown'])) 
        print(f"✅ FreeCAD version: {version_str}")
    except Exception as e:
        print(f"❌ Failed to get FreeCAD version: {e}")
        return False
    
    # Create a document
    try:
        doc_name = f"Demo_{method_name}_{int(time.time())}"
        doc_result = fc.create_document(doc_name)
        print(f"✅ Created document: {doc_name}")
    except Exception as e:
        print(f"❌ Failed to create document: {e}")
        return False
    
    # Create a box
    try:
        box_result = fc.create_box(length=20, width=15, height=10)
        if 'error' in box_result:
            raise Exception(box_result['error'])
        print(f"✅ Created box with dimensions 20x15x10")
    except Exception as e:
        print(f"❌ Failed to create box: {e}")
        return False
    
    # Create a cylinder
    try:
        cylinder_result = fc.create_cylinder(radius=7.5, height=30)
        if 'error' in cylinder_result:
            raise Exception(cylinder_result['error'])
        print(f"✅ Created cylinder with radius 7.5 and height 30")
    except Exception as e:
        print(f"❌ Failed to create cylinder: {e}")
        return False
    
    # Export to STL
    try:
        output_file = f"output_{method_name}.stl"
        export_result = fc.export_document(output_file, file_type="stl")
        if 'error' in export_result:
            raise Exception(export_result['error'])
        
        if export_result.get('mock', False):
            print(f"✅ Mock export to {output_file} (file not actually created)")
        else:
            print(f"✅ Exported to {output_file}")
            
            # Check if file exists and has size
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                print(f"✅ Verified file exists: {output_file} ({os.path.getsize(output_file)} bytes)")
            else:
                print(f"❌ File not found or empty: {output_file}")
    except Exception as e:
        print(f"❌ Failed to export: {e}")
        return False
    
    # Close the connection
    fc.close()
    print(f"✅ Connection closed")
    
    return True

def start_freecad_server():
    """Start the FreeCAD server in the background"""
    print("\nStarting FreeCAD server in background...")
    try:
        freecad_path = "freecad"  # Adjust if needed
        server_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "freecad_server.py")
        
        if not os.path.exists(server_script):
            print(f"❌ Server script not found: {server_script}")
            return None
        
        # Start FreeCAD server in the background
        cmd = [freecad_path, "-c", server_script, "--debug"]
        process = subprocess.Popen(cmd, 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE,
                                  universal_newlines=True)
        
        # Wait for server to start
        print("Waiting for server to start (10 seconds)...")
        time.sleep(10)
        
        # Check if process is still running
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print(f"❌ Server failed to start: {stderr}")
            return None
        
        print("✅ FreeCAD server started")
        return process
    except Exception as e:
        print(f"❌ Failed to start FreeCAD server: {e}")
        return None

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="FreeCAD Integration Demo")
    parser.add_argument("--method", choices=["auto", "server", "bridge", "mock"], 
                       default="auto", help="Connection method to test")
    parser.add_argument("--test-all", action="store_true", 
                       help="Test all connection methods")
    parser.add_argument("--start-server", action="store_true",
                       help="Start the FreeCAD server before testing")
    
    args = parser.parse_args()
    
    # Start server if requested
    server_process = None
    if args.start_server:
        server_process = start_freecad_server()
    
    try:
        if args.test_all:
            # Test all methods
            results = {}
            for method in ["auto", "server", "bridge", "mock"]:
                results[method] = demo_connection(method)
            
            # Print summary
            print("\n" + "="*50)
            print("SUMMARY OF RESULTS")
            print("="*50)
            for method, success in results.items():
                status = "✅ PASSED" if success else "❌ FAILED"
                print(f"{method.ljust(10)}: {status}")
        else:
            # Test only the specified method
            demo_connection(args.method)
    finally:
        # Clean up server process if we started it
        if server_process:
            print("\nStopping FreeCAD server...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
                print("✅ FreeCAD server stopped")
            except subprocess.TimeoutExpired:
                server_process.kill()
                print("❌ Had to forcibly kill FreeCAD server")

if __name__ == "__main__":
    main() 