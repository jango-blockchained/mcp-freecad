#!/usr/bin/env python3
"""
Test script to verify FreeCAD crash fixes

This script tests the fixed FreeCAD bridge and connection manager
to ensure that creating documents and shapes no longer crashes.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("crash_fix_test")

def test_bridge_directly():
    """Test the FreeCAD bridge directly"""
    logger.info("Testing FreeCAD Bridge directly...")
    
    try:
        from src.mcp_freecad.server.freecad_bridge import FreeCADBridge
        
        # Test bridge initialization
        bridge = FreeCADBridge()
        logger.info("Bridge initialized successfully")
        
        # Test availability check
        if not bridge.is_available():
            logger.warning("FreeCAD not available - skipping bridge tests")
            return False
            
        logger.info("FreeCAD is available")
        
        # Test version check
        try:
            version_info = bridge.get_version()
            if version_info.get("success"):
                logger.info(f"✅ Version check successful: {version_info.get('version')}")
            else:
                logger.error(f"❌ Version check failed: {version_info.get('error')}")
                return False
        except Exception as e:
            logger.error(f"❌ Version check crashed: {e}")
            return False
            
        # Test document creation
        try:
            doc_name = bridge.create_document("TestDoc")
            logger.info(f"✅ Document creation successful: {doc_name}")
        except Exception as e:
            logger.error(f"❌ Document creation crashed: {e}")
            return False
            
        # Test box creation
        try:
            box_name = bridge.create_box(10.0, 20.0, 30.0, doc_name)
            logger.info(f"✅ Box creation successful: {box_name}")
        except Exception as e:
            logger.error(f"❌ Box creation crashed: {e}")
            return False
            
        logger.info("✅ All bridge tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Bridge test setup failed: {e}")
        return False

def test_connection_manager():
    """Test the FreeCAD connection manager"""
    logger.info("Testing FreeCAD Connection Manager...")
    
    try:
        from src.mcp_freecad.client.freecad_connection_manager import FreeCADConnection
        
        # Test connection with bridge method
        fc = FreeCADConnection(auto_connect=False)
        
        # Try to connect using bridge method specifically
        success = fc.connect(prefer_method="bridge")
        if success:
            logger.info("✅ Connection manager bridge connection successful")
            
            # Test version through connection manager
            version_info = fc.get_version()
            if version_info.get("success"):
                logger.info(f"✅ Version through connection manager: {version_info.get('version')}")
            else:
                logger.warning(f"Version check failed: {version_info.get('error')}")
                
            # Test document creation through connection manager
            doc_name = fc.create_document("TestDoc2")
            if doc_name:
                logger.info(f"✅ Document creation through connection manager: {doc_name}")
                
                # Test box creation through connection manager
                box_name = fc.create_box(5.0, 10.0, 15.0, doc_name)
                if box_name:
                    logger.info(f"✅ Box creation through connection manager: {box_name}")
                else:
                    logger.warning("Box creation returned None")
            else:
                logger.warning("Document creation returned None")
                
        else:
            logger.warning("❌ Bridge connection failed, trying other methods...")
            success = fc.connect()  # Try all methods
            if success:
                logger.info(f"✅ Connected using {fc.get_connection_type()} method")
            else:
                logger.error("❌ All connection methods failed")
                return False
                
        fc.close()
        logger.info("✅ Connection manager tests completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Connection manager test failed: {e}")
        return False

async def test_mcp_server_tools():
    """Test the MCP server tools"""
    logger.info("Testing MCP Server Tools...")
    
    try:
        # Import server components
        from src.mcp_freecad.server.freecad_mcp_server import (
            freecad_create_document, 
            freecad_create_box,
            initialize_freecad_connection,
            load_config
        )
        
        # Load config and initialize connection
        config = load_config("config.json")
        initialize_freecad_connection(config)
        
        # Test document creation tool
        try:
            result = await freecad_create_document("TestDoc3")
            if result.get("success"):
                doc_name = result.get("document_name")
                logger.info(f"✅ MCP document creation successful: {doc_name}")
                
                # Test box creation tool
                box_result = await freecad_create_box(
                    length=8.0, width=12.0, height=16.0, name="TestBox"
                )
                if box_result.get("success"):
                    box_name = box_result.get("object_name")
                    logger.info(f"✅ MCP box creation successful: {box_name}")
                else:
                    logger.error(f"❌ MCP box creation failed: {box_result}")
                    
            else:
                logger.error(f"❌ MCP document creation failed: {result}")
                
        except Exception as e:
            logger.error(f"❌ MCP tool execution crashed: {e}")
            return False
            
        logger.info("✅ MCP server tools tests completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ MCP server tools test setup failed: {e}")
        return False

def main():
    """Main test function"""
    logger.info("=" * 60)
    logger.info("FreeCAD Crash Fix Validation Tests")
    logger.info("=" * 60)
    
    results = []
    
    # Test 1: Direct bridge test
    logger.info("\n" + "=" * 40)
    logger.info("TEST 1: Direct Bridge Test")
    logger.info("=" * 40)
    results.append(("Direct Bridge", test_bridge_directly()))
    
    # Test 2: Connection manager test
    logger.info("\n" + "=" * 40)
    logger.info("TEST 2: Connection Manager Test")
    logger.info("=" * 40)
    results.append(("Connection Manager", test_connection_manager()))
    
    # Test 3: MCP server tools test
    logger.info("\n" + "=" * 40)
    logger.info("TEST 3: MCP Server Tools Test")
    logger.info("=" * 40)
    try:
        result = asyncio.run(test_mcp_server_tools())
        results.append(("MCP Server Tools", result))
    except Exception as e:
        logger.error(f"❌ MCP server tools test crashed: {e}")
        results.append(("MCP Server Tools", False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if success:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! The crash fixes appear to be working.")
        return 0
    else:
        logger.error("❌ Some tests failed. Check the logs above for details.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
