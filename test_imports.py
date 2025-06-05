#!/usr/bin/env python3
"""Test script to verify FreeCAD AI addon imports are working correctly."""

import sys
import os

# Add freecad-ai directory to path
freecad_ai_dir = os.path.join(os.path.dirname(__file__), 'freecad-ai')
if freecad_ai_dir not in sys.path:
    sys.path.insert(0, freecad_ai_dir)

print("Testing FreeCAD AI addon imports...")
print(f"Python path includes: {freecad_ai_dir}")
print("-" * 50)

# Test 1: Import AI providers
print("\n1. Testing AI provider imports...")
try:
    from ai.providers.base_provider import BaseAIProvider
    from ai.providers.claude_provider import ClaudeProvider
    from ai.providers.gemini_provider import GeminiProvider
    from ai.providers.openrouter_provider import OpenRouterProvider
    print("✅ AI providers imported successfully")
except ImportError as e:
    print(f"❌ Failed to import AI providers: {e}")

# Test 2: Import AI manager
print("\n2. Testing AI manager import...")
try:
    from ai.ai_manager import AIManager
    print("✅ AI manager imported successfully")
except ImportError as e:
    print(f"❌ Failed to import AI manager: {e}")

# Test 3: Import provider integration service
print("\n3. Testing provider integration service import...")
try:
    from ai.provider_integration_service import get_provider_service
    service = get_provider_service()
    print(f"✅ Provider integration service imported successfully")
    print(f"   Service instance created: {service is not None}")
except ImportError as e:
    print(f"❌ Failed to import provider integration service: {e}")
except Exception as e:
    print(f"❌ Error creating service instance: {e}")

# Test 4: Import config manager
print("\n4. Testing config manager import...")
try:
    from config.config_manager import ConfigManager
    config = ConfigManager()
    print("✅ Config manager imported successfully")
except ImportError as e:
    print(f"❌ Failed to import config manager: {e}")

# Test 5: Import GUI widgets
print("\n5. Testing GUI widget imports...")
try:
    from gui.main_widget import MCPMainWidget
    from gui.conversation_widget import ConversationWidget
    from gui.providers_widget import ProvidersWidget
    print("✅ GUI widgets imported successfully")
except ImportError as e:
    print(f"❌ Failed to import GUI widgets: {e}")

# Test 6: Check for duplicate files
print("\n6. Checking for duplicate provider files...")
ai_dir = os.path.join(freecad_ai_dir, 'ai')
duplicates = []
for file in ['base_provider.py', 'claude_provider.py', 'gemini_provider.py', 'openrouter_provider.py']:
    if os.path.exists(os.path.join(ai_dir, file)):
        duplicates.append(file)

if duplicates:
    print(f"⚠️  Found duplicate files in ai/ directory: {duplicates}")
    print("   These should be removed to avoid import conflicts")
else:
    print("✅ No duplicate provider files found")

print("\n" + "-" * 50)
print("Import test completed!")