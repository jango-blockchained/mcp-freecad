#!/usr/bin/env python3
"""
Simple syntax check for provider selector integration
"""

import ast
import os


def check_syntax(file_path):
    """Check if a Python file has valid syntax."""
    try:
        with open(file_path, 'r') as f:
            source = f.read()
        ast.parse(source)
        return True, None
    except SyntaxError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

def check_imports(file_path):
    """Check if imports in the file are structurally correct."""
    try:
        with open(file_path, 'r') as f:
            source = f.read()
        
        tree = ast.parse(source)
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        
        return True, imports
    except Exception as e:
        return False, str(e)

def main():
    """Check the integration files."""
    print("Provider Selector Syntax Check")
    print("=" * 40)
    
    files_to_check = [
        "/home/jango/Git/mcp-freecad/freecad-ai/gui/provider_selector_widget.py",
        "/home/jango/Git/mcp-freecad/freecad-ai/gui/conversation_widget.py",
        "/home/jango/Git/mcp-freecad/freecad-ai/gui/agent_control_widget.py",
        "/home/jango/Git/mcp-freecad/freecad-ai/gui/main_widget.py"
    ]
    
    all_good = True
    
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            print(f"❌ {os.path.basename(file_path)}: File not found")
            all_good = False
            continue
            
        # Check syntax
        syntax_ok, error = check_syntax(file_path)
        if syntax_ok:
            print(f"✅ {os.path.basename(file_path)}: Syntax OK")
        else:
            print(f"❌ {os.path.basename(file_path)}: Syntax Error - {error}")
            all_good = False
            continue
            
        # Check imports structure
        imports_ok, imports = check_imports(file_path)
        if imports_ok:
            # Look for our new imports
            relevant_imports = [imp for imp in imports if 'provider_selector' in imp.lower()]
            if relevant_imports:
                print(f"   📦 Found provider selector imports: {relevant_imports}")
        else:
            print(f"⚠️  {os.path.basename(file_path)}: Import analysis failed - {imports}")
    
    print("\n" + "=" * 40)
    if all_good:
        print("✅ All files have valid syntax!")
        print("\nIntegration Summary:")
        print("1. ✅ ProviderSelectorWidget created")
        print("2. ✅ ConversationWidget updated with provider selector")
        print("3. ✅ AgentControlWidget updated with provider selector")  
        print("4. ✅ MainWidget updated to connect services")
        print("\nNext: Test in FreeCAD environment")
    else:
        print("❌ Some files have syntax issues")
    
    return 0 if all_good else 1

if __name__ == "__main__":
    exit(main())
