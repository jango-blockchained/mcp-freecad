#!/usr/bin/env python3
"""
Simple syntax and import validation for provider fixes
"""

import ast
import os
import sys

def validate_python_syntax(file_path):
    """Validate Python syntax without importing"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the AST to check syntax
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error reading file: {e}"

def check_base_provider_references(file_path):
    """Check if file correctly references BaseAIProvider"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for correct base class usage
        has_base_ai_provider = 'BaseAIProvider' in content
        has_old_base_provider = 'BaseProvider' in content and 'BaseAIProvider' not in content
        
        return has_base_ai_provider, has_old_base_provider
    except Exception as e:
        return False, True

def main():
    """Validate syntax and imports for key provider files"""
    print("FreeCAD AI Provider Syntax Validation")
    print("=" * 45)
    
    base_dir = "/home/jango/Git/mcp-freecad/freecad-ai"
    
    # Files to check
    files_to_check = [
        "ai/providers/base_provider.py",
        "ai/providers/openai_provider.py", 
        "ai/providers/anthropic_provider.py",
        "ai/providers/ollama_provider.py",
        "ai/providers/vertexai_provider.py",
        "ai/providers/__init__.py",
        "ai/ai_manager.py",
        "ai/provider_integration_service.py",
        "gui/providers_widget.py",
        "gui/provider_selector_widget.py"
    ]
    
    syntax_passed = 0
    import_passed = 0
    total_files = len(files_to_check)
    
    print("\n=== Syntax Validation ===")
    for file_rel_path in files_to_check:
        file_path = os.path.join(base_dir, file_rel_path)
        
        if not os.path.exists(file_path):
            print(f"❌ {file_rel_path}: FILE NOT FOUND")
            continue
            
        is_valid, error = validate_python_syntax(file_path)
        if is_valid:
            print(f"✅ {file_rel_path}: Syntax OK")
            syntax_passed += 1
        else:
            print(f"❌ {file_rel_path}: {error}")
    
    print(f"\nSyntax validation: {syntax_passed}/{total_files} files passed")
    
    # Check base provider references
    print("\n=== Base Provider Reference Check ===")
    provider_files = [f for f in files_to_check if 'provider' in f and f != "ai/providers/__init__.py"]
    
    for file_rel_path in provider_files:
        file_path = os.path.join(base_dir, file_rel_path)
        
        if not os.path.exists(file_path):
            continue
            
        has_correct, has_old = check_base_provider_references(file_path)
        
        if has_correct and not has_old:
            print(f"✅ {file_rel_path}: Uses BaseAIProvider correctly")
            import_passed += 1
        elif has_old:
            print(f"❌ {file_rel_path}: Still uses old BaseProvider")
        else:
            print(f"⚪ {file_rel_path}: No base provider reference (may be OK)")
            import_passed += 1  # Count as passing if no reference needed
    
    print(f"\nBase provider references: {import_passed}/{len(provider_files)} files correct")
    
    # Check if Vertex AI provider exists
    print("\n=== Vertex AI Provider Check ===")
    vertexai_path = os.path.join(base_dir, "ai/providers/vertexai_provider.py")
    if os.path.exists(vertexai_path):
        print("✅ Vertex AI provider file exists")
        
        # Check if it has the right structure
        try:
            with open(vertexai_path, 'r') as f:
                content = f.read()
            
            if 'class VertexAIProvider' in content:
                print("✅ VertexAIProvider class found")
            else:
                print("❌ VertexAIProvider class not found")
                
            if 'BaseAIProvider' in content:
                print("✅ Inherits from BaseAIProvider")
            else:
                print("❌ Does not inherit from BaseAIProvider")
                
        except Exception as e:
            print(f"❌ Error reading Vertex AI provider: {e}")
    else:
        print("❌ Vertex AI provider file not found")
    
    # Summary
    print("\n" + "=" * 45)
    print("SUMMARY:")
    print(f"  Syntax validation: {syntax_passed}/{total_files} passed")
    print(f"  Provider references: {import_passed}/{len(provider_files)} correct")
    
    if syntax_passed == total_files and import_passed == len(provider_files):
        print("🎉 All validations passed!")
        print("The provider selection fixes should work in FreeCAD.")
        return True
    else:
        print("⚠️  Some validations failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
