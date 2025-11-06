"""
FreeCAD AI In-Application Comprehensive Diagnostic

This script should be run within FreeCAD to test all components and generate 
a detailed diagnostic report similar to the enhanced_agent_control_widget.
"""

import os
import sys
from datetime import datetime
import traceback

def generate_freecad_ai_diagnostic_report():
    """Generate a comprehensive diagnostic report from within FreeCAD."""
    
    print("=" * 50)
    print("FreeCAD AI Diagnostic Report")
    print(f"Generated: {datetime.now().isoformat()}")
    print("=" * 50)
    
    # Add the freecad-ai directory to Python path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    freecad_ai_dir = os.path.join(script_dir, 'freecad-ai')
    
    if freecad_ai_dir not in sys.path:
        sys.path.insert(0, freecad_ai_dir)
    
    agent_manager = None
    provider_service = None
    
    # Test agent manager initialization
    print("\n=== AGENT MANAGER DIAGNOSTICS ===\n")
    
    try:
        # Method 1: Try the main widget approach
        from gui.main_widget import MCPMainWidget
        widget = MCPMainWidget()
        
        if hasattr(widget, 'agent_manager') and widget.agent_manager is not None:
            agent_manager = widget.agent_manager
            print("✅ Agent Manager: AVAILABLE")
            print(f"   └─ Source: Main widget initialization")
            print(f"   └─ Type: {type(agent_manager)}")
            print(f"   └─ Mode: {agent_manager.get_mode()}")
            print(f"   └─ State: {agent_manager.execution_state}")
        else:
            # Method 2: Try direct wrapper approach
            try:
                from core.agent_manager_wrapper import get_agent_manager, is_agent_manager_available
                if is_agent_manager_available():
                    agent_manager = get_agent_manager()
                    print("✅ Agent Manager: AVAILABLE")
                    print(f"   └─ Source: Agent manager wrapper")
                    print(f"   └─ Type: {type(agent_manager)}")
                else:
                    print("❌ Agent Manager: NOT AVAILABLE")
                    print("   └─ Agent manager wrapper reports unavailable")
            except Exception as e:
                print("❌ Agent Manager: NOT AVAILABLE")
                print("   └─ Agent manager wrapper import failed")
                print(f"   └─ Error: {e}")
        
        if agent_manager is None:
            # Method 3: Try direct core agent manager
            try:
                from core.agent_manager import AgentManager
                agent_manager = AgentManager()
                print("✅ Agent Manager: AVAILABLE")
                print(f"   └─ Source: Direct core agent manager")
                print(f"   └─ Type: {type(agent_manager)}")
            except Exception as e:
                print("❌ Agent Manager: NOT AVAILABLE")
                print("   └─ Agent manager instance is None")
                print("   └─ This usually indicates import failure")
                print("   └─ Check FreeCAD console for import errors")
                print(f"   └─ Direct creation error: {e}")
    
    except Exception as e:
        print("❌ Agent Manager: NOT AVAILABLE")
        print(f"   └─ Initialization failed: {e}")
        print(f"   └─ Traceback: {traceback.format_exc()}")
    
    # Test provider service initialization
    print("\n=== PROVIDER SERVICE DIAGNOSTICS ===\n")
    
    try:
        # Method 1: From main widget
        if hasattr(widget, 'provider_service') and widget.provider_service is not None:
            provider_service = widget.provider_service
            print("✅ Provider Service: AVAILABLE")
            print(f"   └─ Source: Main widget initialization")
            print(f"   └─ Type: {type(provider_service)}")
        else:
            # Method 2: Try wrapper approach
            try:
                from ai.provider_service_wrapper import get_provider_service, is_provider_service_available
                if is_provider_service_available():
                    provider_service = get_provider_service()
                    print("✅ Provider Service: AVAILABLE")
                    print(f"   └─ Source: Provider service wrapper")
                    print(f"   └─ Type: {type(provider_service)}")
                else:
                    print("❌ Provider Service: NOT AVAILABLE")
                    print("   └─ Provider service wrapper reports unavailable")
            except Exception as e:
                print("❌ Provider Service: NOT AVAILABLE")
                print("   └─ Provider service wrapper import failed")
                print(f"   └─ Error: {e}")
        
        if provider_service is None:
            # Method 3: Try direct approach
            try:
                from ai.provider_integration_service import get_provider_service
                provider_service = get_provider_service()
                if provider_service is not None:
                    print("✅ Provider Service: AVAILABLE")
                    print(f"   └─ Source: Direct provider integration service")
                    print(f"   └─ Type: {type(provider_service)}")
                else:
                    print("❌ Provider Service: NOT AVAILABLE")
                    print("   └─ Provider service instance is None")
            except Exception as e:
                print("❌ Provider Service: NOT AVAILABLE")
                print("   └─ Provider service instance is None")
                print(f"   └─ Direct creation error: {e}")
    
    except Exception as e:
        print("❌ Provider Service: NOT AVAILABLE")
        print(f"   └─ Initialization failed: {e}")
    
    # Test tools registry
    print("\n=== TOOLS REGISTRY DIAGNOSTICS ===\n")
    
    if agent_manager is not None:
        try:
            if hasattr(agent_manager, 'tool_registry') and agent_manager.tool_registry is not None:
                tools = agent_manager.get_available_tools() if hasattr(agent_manager, 'get_available_tools') else []
                print("✅ Tools Registry: AVAILABLE")
                print(f"   └─ Total tools: {len(tools)}")
                if tools:
                    print("   └─ Available tools:")
                    for tool in tools[:5]:  # Show first 5 tools
                        print(f"      • {tool}")
                    if len(tools) > 5:
                        print(f"      ... and {len(tools) - 5} more")
            else:
                print("⚠️ Tools Registry: Agent Manager available but no tools registry")
        except Exception as e:
            print("⚠️ Tools Registry: Error accessing tools")
            print(f"   └─ Error: {e}")
    else:
        print("❌ Tools Registry: Agent Manager Not Available")
    
    # System information
    print("\n=== SYSTEM INFORMATION ===\n")
    
    try:
        import FreeCAD
        print(f"Python Version: {sys.version}")
        print(f"Platform: {sys.platform}")
        print(f"FreeCAD Version: {'.'.join(map(str, FreeCAD.Version()))}")
        print(f"FreeCAD Build: {FreeCAD.Version()[3] if len(FreeCAD.Version()) > 3 else ''}")
        
        # Qt information
        try:
            from PySide2 import QtCore
            print(f"Qt Version: {QtCore.qVersion()}")
            print(f"PySide2 Version: {QtCore.__version__}")
        except ImportError:
            try:
                from PySide import QtCore
                print(f"Qt Version: {QtCore.qVersion()}")
                print("PySide2 Version: Not available (using PySide)")
            except ImportError:
                print("Qt Version: Not available")
                print("PySide2 Version: Not available")
        
        # Memory usage
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            print(f"Memory Usage: {memory_mb:.1f} MB")
        except ImportError:
            print("Memory Usage: Not available (psutil not installed)")
        
        # Working directory and environment
        print(f"Working Directory: {os.getcwd()}")
        print(f"FREECAD_USER_HOME: {os.environ.get('FREECAD_USER_HOME', 'Not set')}")
        print(f"FREECAD_USER_DATA: {os.environ.get('FREECAD_USER_DATA', 'Not set')}")
        print(f"FREECADPATH: {os.environ.get('FREECADPATH', 'Not set')}")
        
    except Exception as e:
        print(f"System information error: {e}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    generate_freecad_ai_diagnostic_report()
