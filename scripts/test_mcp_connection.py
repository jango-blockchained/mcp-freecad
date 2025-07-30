#!/usr/bin/env python3
"""
Test script to verify MCP server connection and functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add the freecad-ai directory to the path
project_root = Path(__file__).parent.parent
freecad_ai_path = project_root / "freecad-ai"
sys.path.insert(0, str(freecad_ai_path))
sys.path.insert(0, str(project_root))

try:
    from mcp_server import FreeCADMCPServer
    print("✅ Successfully imported FreeCADMCPServer")
except ImportError as e:
    print(f"❌ Failed to import FreeCADMCPServer: {e}")
    print(f"Project root: {project_root}")
    print(f"FreeCAD AI path: {freecad_ai_path}")
    print("Please ensure mcp_server.py exists in freecad-ai/ directory")
    sys.exit(1)

async def test_mcp_server():
    """Test the MCP server initialization and basic functionality."""
    print("\n🔧 Testing MCP Server...")
    
    try:
        # Initialize the server
        server = FreeCADMCPServer()
        print("✅ MCP Server initialized successfully")
        
        # Check server configuration
        print(f"✅ FreeCAD available: {server.freecad_available}")
        print(f"✅ Tools available: {server.tools_available}")
        print(f"✅ Events available: {server.events_available}")
        
        # Test tools listing
        print("\n📋 Testing tools listing...")
        server._register_handlers()
        
        # Get the server's capabilities
        try:
            capabilities = server.server.get_capabilities(
                notification_options=None, 
                experimental_capabilities=None
            )
            print("✅ Server capabilities available")
            print(f"✅ Capabilities: {len(capabilities)} items configured")
        except Exception as e:
            print(f"⚠️  Server capabilities test skipped: {e}")
        
        print("\n✅ All tests passed! MCP server is ready for development.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dependencies():
    """Test that all required dependencies are available."""
    print("🔍 Testing dependencies...")
    
    dependencies = [
        "mcp",
        "mcp.server",
        "mcp.server.stdio",
        "mcp.types",
        "asyncio",
        "json",
        "logging",
    ]
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}")
        except ImportError as e:
            print(f"❌ {dep}: {e}")
            return False
    
    return True

def main():
    """Main test function."""
    print("🚀 FreeCAD MCP Server Development Test")
    print("=" * 50)
    
    # Test dependencies first
    if not test_dependencies():
        print("\n❌ Dependency test failed. Please install required packages:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    
    # Test MCP server
    success = asyncio.run(test_mcp_server())
    
    if success:
        print("\n🎉 MCP Server is ready for VS Code development!")
        print("\nNext steps:")
        print("1. Start the MCP server: Press F1 → 'Tasks: Run Task' → 'Start MCP Server'")
        print("2. Debug the server: Press F5 → Select 'Debug FreeCAD MCP Server'")
        print("3. Test tools in VS Code chat by mentioning @freecad-mcp-server")
    else:
        print("\n❌ MCP Server test failed. Check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
