#!/usr/bin/env python3
"""
Test script to diagnose FastAPI/Pydantic compatibility issue in FreeCAD AI context
"""

import sys
import traceback


def test_basic_imports():
    """Test basic FastAPI/Pydantic imports"""
    print(f"Python version: {sys.version}")
    print(f"Python version info: {sys.version_info}")

    try:
        import fastapi

        print(f"✅ FastAPI imported successfully: {fastapi.__version__}")
    except Exception as e:
        print(f"❌ FastAPI import failed: {e}")
        return False

    try:
        import pydantic

        print(f"✅ Pydantic imported successfully: {pydantic.__version__}")
    except Exception as e:
        print(f"❌ Pydantic import failed: {e}")
        return False

    return True


def test_fastapi_pydantic_integration():
    """Test FastAPI/Pydantic integration"""
    try:
        from fastapi import APIRouter, HTTPException
        from pydantic import BaseModel

        print("✅ FastAPI/Pydantic specific imports successful")

        # Test creating a Pydantic model
        class TestModel(BaseModel):
            test_field: str = "test"
            number_field: int = 42

        print("✅ Pydantic model creation successful")

        # Test model instantiation
        test_instance = TestModel()
        print(f"✅ Pydantic model instantiation successful: {test_instance}")

        # Test router creation
        router = APIRouter()
        print("✅ FastAPI router creation successful")

        return True

    except TypeError as e:
        print(f"❌ TypeError in FastAPI/Pydantic integration: {e}")
        if "Protocols with non-method members" in str(e):
            print("   This is the known Python 3.13+ compatibility issue")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Error in FastAPI/Pydantic integration: {e}")
        traceback.print_exc()
        return False


def main():
    print("=== FastAPI/Pydantic Compatibility Test ===")

    if not test_basic_imports():
        print("❌ Basic imports failed, skipping integration test")
        return False

    if not test_fastapi_pydantic_integration():
        print("❌ Integration test failed")
        return False

    print("✅ All tests passed! FastAPI/Pydantic should work correctly")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
