#!/usr/bin/env python3
"""
Minimal MCP-FreeCAD server to test core functionality.
"""

import asyncio
import json
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.mcp_freecad.core.server import MCPServer
from src.mcp_freecad.core.cache import ResourceCache
from src.mcp_freecad.core.recovery import ConnectionRecovery
from src.mcp_freecad.core.diagnostics import PerformanceMonitor

# Create the minimal server
app = FastAPI(title="Minimal MCP-FreeCAD Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create performance monitor for tracking
performance_monitor = PerformanceMonitor()

@app.get("/")
@performance_monitor.track("root")
async def root():
    return {
        "status": "ok",
        "message": "Minimal MCP-FreeCAD server is running"
    }

@app.get("/health")
@performance_monitor.track("health")
async def health():
    return {
        "status": "ok",
        "uptime": performance_monitor.get_server_stats().get("uptime_seconds", 0)
    }

@app.get("/diagnostics")
@performance_monitor.track("diagnostics")
async def diagnostics():
    return performance_monitor.get_diagnostics_report()

@app.post("/cache/test")
@performance_monitor.track("cache_test")
async def test_cache():
    # Create a cache
    cache = ResourceCache(default_ttl=30.0, max_size=100)
    
    # Test setting and getting values
    cache.set("test_key", "test_value")
    value = cache.get("test_key")
    
    # Get cache stats
    stats = cache.get_stats()
    
    return {
        "cache_test": "ok",
        "value": value,
        "stats": stats
    }

@app.post("/recovery/test")
@performance_monitor.track("recovery_test")
async def test_recovery():
    # Create a recovery manager
    recovery = ConnectionRecovery(max_retries=3, retry_delay=1.0)
    
    # Test function that will succeed on the second try
    attempt_count = [0]
    
    async def test_operation():
        attempt_count[0] += 1
        if attempt_count[0] == 1:
            raise Exception("Simulated failure on first attempt")
        return f"Success on attempt {attempt_count[0]}"
    
    # Execute with retry
    try:
        result = await recovery.with_retry(
            test_operation,
            "test operation"
        )
        return {
            "recovery_test": "ok",
            "attempts": attempt_count[0],
            "result": result
        }
    except Exception as e:
        return {
            "recovery_test": "failed",
            "error": str(e),
            "attempts": attempt_count[0]
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 