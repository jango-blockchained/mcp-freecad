#!/usr/bin/env python3
"""
Example script demonstrating FastMCP server usage with MCP-FreeCAD.

This script shows how to interact with the FastMCP-based server programmatically.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from cursor_mcp_server import (
    mcp,
    test_connection,
    create_box,
    create_document,
    create_cylinder,
    create_sphere,
    get_server_status
)


def demonstrate_tools():
    """Demonstrate all available tools."""
    print("=" * 80)
    print("FastMCP Server - Tool Demonstration")
    print("=" * 80)
    print()
    
    # 1. Get server status
    print("1. Server Status:")
    print("-" * 40)
    status = get_server_status.fn()
    for key, value in status.items():
        print(f"   {key}: {value}")
    print()
    
    # 2. Test connection
    print("2. Testing FreeCAD Connection:")
    print("-" * 40)
    result = test_connection.fn()
    print(f"   {result}")
    print()
    
    # 3. Create document
    print("3. Creating FreeCAD Document:")
    print("-" * 40)
    result = create_document.fn(name="DemoDocument")
    print(f"   {result}")
    print()
    
    # 4. Create box
    print("4. Creating Box (10x20x30):")
    print("-" * 40)
    result = create_box.fn(length=10.0, width=20.0, height=30.0)
    print(f"   {result}")
    print()
    
    # 5. Create cylinder
    print("5. Creating Cylinder (radius=5, height=15):")
    print("-" * 40)
    result = create_cylinder.fn(radius=5.0, height=15.0)
    print(f"   {result}")
    print()
    
    # 6. Create sphere
    print("6. Creating Sphere (radius=7.5):")
    print("-" * 40)
    result = create_sphere.fn(radius=7.5)
    print(f"   {result}")
    print()
    
    print("=" * 80)
    print("Tool Demonstration Complete!")
    print("=" * 80)


def show_available_tools():
    """Show all available tools and their descriptions."""
    print("=" * 80)
    print("Available FastMCP Tools")
    print("=" * 80)
    print()
    
    tools = [
        test_connection,
        create_box,
        create_document,
        create_cylinder,
        create_sphere
    ]
    
    for i, tool in enumerate(tools, 1):
        print(f"{i}. {tool.name}")
        print(f"   Description: {tool.description}")
        
        # Get function signature for better parameter info
        import inspect
        sig = inspect.signature(tool.fn)
        if sig.parameters:
            print("   Parameters:")
            for param_name, param in sig.parameters.items():
                param_type = param.annotation.__name__ if param.annotation != inspect.Parameter.empty else 'any'
                print(f"      - {param_name} ({param_type})")
        print()
    
    print("=" * 80)


def show_server_info():
    """Show server information."""
    print("=" * 80)
    print("FastMCP Server Information")
    print("=" * 80)
    print()
    print(f"Server Name: {mcp.name}")
    print(f"FastMCP Version: Available")
    print(f"MCP Version: Available")
    print()
    print("Features:")
    print("  - Declarative tool definitions with @mcp.tool()")
    print("  - Resource endpoints with @mcp.resource()")
    print("  - Type-safe parameters with automatic validation")
    print("  - Comprehensive error handling")
    print("  - STDIO transport for MCP clients")
    print()
    print("=" * 80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="FastMCP Server Demonstration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python example_fastmcp_usage.py --info          # Show server information
  python example_fastmcp_usage.py --tools         # List available tools
  python example_fastmcp_usage.py --demo          # Run tool demonstration
  python example_fastmcp_usage.py --all           # Show everything
        """
    )
    
    parser.add_argument("--info", action="store_true", help="Show server information")
    parser.add_argument("--tools", action="store_true", help="List available tools")
    parser.add_argument("--demo", action="store_true", help="Run tool demonstration")
    parser.add_argument("--all", action="store_true", help="Show all information")
    
    args = parser.parse_args()
    
    # If no arguments, show help
    if not any([args.info, args.tools, args.demo, args.all]):
        parser.print_help()
        sys.exit(0)
    
    # Show requested information
    if args.all or args.info:
        show_server_info()
        if args.all:
            print()
    
    if args.all or args.tools:
        show_available_tools()
        if args.all:
            print()
    
    if args.all or args.demo:
        demonstrate_tools()
