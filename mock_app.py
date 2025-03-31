#!/usr/bin/env python3
"""
Mock MCP-FreeCAD server for testing optimization features.
"""

import uvicorn
import json
import logging
import asyncio
import time
import platform
import psutil
import datetime
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.mcp_freecad.core.server import MCPServer
from src.mcp_freecad.core.cache import ResourceCache
from src.mcp_freecad.core.recovery import ConnectionRecovery
from src.mcp_freecad.core.diagnostics import PerformanceMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp_freecad")

# Mock resource provider
class MockResourceProvider:
    def __init__(self):
        self.cache = None
        self.resources = {
            "Box001": {"type": "Box", "length": 10, "width": 10, "height": 10},
            "Cylinder001": {"type": "Cylinder", "radius": 5, "height": 20}
        }
    
    def set_cache(self, cache):
        self.cache = cache
    
    def set_connection_manager(self, manager):
        pass
    
    async def initialize(self):
        logger.info("Initialized mock resource provider")

# Mock tool provider
class MockToolProvider:
    def __init__(self):
        self.tools = {
            "create_box": self.create_box,
            "create_cylinder": self.create_cylinder
        }
    
    def set_connection_manager(self, manager):
        pass
    
    def set_performance_monitor(self, monitor):
        pass
    
    async def initialize(self):
        logger.info("Initialized mock tool provider")
    
    def execute_tool(self, tool_name, params):
        if tool_name in self.tools:
            return self.tools[tool_name](params)
        return {"status": "error", "message": f"Tool {tool_name} not found"}
    
    def create_box(self, params):
        length = params.get("length", 10)
        width = params.get("width", 10)
        height = params.get("height", 10)
        return {
            "status": "success",
            "result": {
                "message": f"Box created with dimensions {length}x{width}x{height}",
                "object": {"type": "Box", "length": length, "width": width, "height": height}
            }
        }
    
    def create_cylinder(self, params):
        radius = params.get("radius", 5)
        height = params.get("height", 20)
        return {
            "status": "success",
            "result": {
                "message": f"Cylinder created with radius {radius} and height {height}",
                "object": {"type": "Cylinder", "radius": radius, "height": height}
            }
        }

# Mock event handler
class MockEventHandler:
    def __init__(self):
        self.events = []
        self.listeners = set()
    
    def set_connection_manager(self, manager):
        pass
    
    def add_listener(self, client_id):
        self.listeners.add(client_id)
    
    def remove_listener(self, client_id):
        if client_id in self.listeners:
            self.listeners.remove(client_id)
    
    async def handle_event(self, event_type, data):
        self.events.append({
            "type": event_type,
            "data": data,
            "timestamp": time.time()
        })
        return True

# Global server instance for use in the initialization function
server = None

async def startup_event():
    """Startup event handler for initializing the server components."""
    global server
    if server:
        try:
            logger.info("Initializing server components...")
            await server.initialize()
            logger.info("Server initialization completed")
        except Exception as e:
            logger.error(f"Error during server initialization: {e}")

async def main():
    """Create and configure the MCP server application."""
    global server
    
    # Load configuration
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load config from config.json: {e}")
        config = {
            "server": {
                "host": "localhost",
                "port": 8000
            },
            "auth": {
                "api_key": "development"
            },
            "cache": {
                "default_ttl": 30.0,
                "max_size": 100
            },
            "recovery": {
                "max_retries": 5,
                "retry_delay": 2.0,
                "backoff_factor": 1.5,
                "max_delay": 30.0
            },
            "freecad": {
                "auto_connect": True
            }
        }
    
    # Create the MCP server
    server = MCPServer(config_path="config.json")
    
    # Register resource providers
    server.register_resource("cad_model", MockResourceProvider())
    logger.info(f"Registered mock resource providers: {server.resources.keys()}")
    
    # Register tool providers
    server.register_tool("primitives", MockToolProvider())
    logger.info(f"Registered mock tool providers: {server.tools.keys()}")
    
    # Create the FastAPI app
    app = FastAPI()
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.get("cors", {}).get("origins", ["*"]),
        allow_credentials=config.get("cors", {}).get("allow_credentials", True),
        allow_methods=config.get("cors", {}).get("methods", ["*"]),
        allow_headers=config.get("cors", {}).get("headers", ["*"]),
    )
    
    # Register event handlers
    document_event_handler = MockEventHandler()
    command_event_handler = MockEventHandler()
    error_event_handler = MockEventHandler()
    
    server.register_event_handler("document_changed", document_event_handler)
    server.register_event_handler("command_executed", command_event_handler)
    server.register_event_handler("error", error_event_handler)
    
    logger.info(f"Registered mock event handlers: {server.event_handlers.keys()}")
    
    # Add startup event handler
    app.add_event_handler("startup", startup_event)
    
    # Add API routes directly to the app
    @app.get("/")
    async def root():
        return {"message": "MCP-FreeCAD Server"}
    
    @app.post("/tools/primitives.create_box")
    @server.performance_monitor.track("primitives.create_box")
    async def create_box(tool_request: dict):
        try:
            if "primitives" not in server.tools:
                return {"status": "error", "message": "Primitives tool provider not found"}
                
            tool_provider = server.tools["primitives"]
            params = tool_request.get("parameters", {})
            
            return await server.recovery.with_retry(
                lambda: tool_provider.execute_tool("create_box", params),
                "primitives.create_box"
            )
        except Exception as e:
            # Report error to error handler
            if "error" in server.event_handlers:
                for handler in server.event_handlers["error"]:
                    if hasattr(handler, "report_error"):
                        handler.report_error(str(e), "api_error", {
                            "endpoint": "/tools/primitives.create_box",
                            "parameters": tool_request.get("parameters", {})
                        })
            return {"status": "error", "message": str(e)}
    
    # === Health check and monitoring endpoints ===
    @app.get("/health")
    async def health_check():
        """Basic health check endpoint that returns server status."""
        global server
        return {
            "status": "ok",
            "version": "1.0.0",  
            "server_initialized": server is not None and hasattr(server, "initialized") and server.initialized,
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    @app.get("/health/detailed")
    @server.performance_monitor.track("health.detailed")
    async def detailed_health_check():
        """Detailed health check that includes system information."""
        global server
        
        # Get system stats
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get server uptime
        uptime = time.time() - server.performance_monitor.start_time if server and hasattr(server, "performance_monitor") else 0
        
        # Format uptime
        uptime_formatted = str(datetime.timedelta(seconds=int(uptime)))
        
        # Check FreeCAD connection
        freecad_status = "mock mode"
        
        return {
            "status": "ok",
            "version": "1.0.0",
            "timestamp": datetime.datetime.now().isoformat(),
            "system": {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": psutil.cpu_percent(),
                "memory": {
                    "total": round(mem.total / (1024 * 1024), 2),  # MB
                    "available": round(mem.available / (1024 * 1024), 2),  # MB
                    "percent": mem.percent
                },
                "disk": {
                    "total": round(disk.total / (1024 * 1024 * 1024), 2),  # GB
                    "free": round(disk.free / (1024 * 1024 * 1024), 2),  # GB
                    "percent": disk.percent
                }
            },
            "server": {
                "uptime_seconds": uptime,
                "uptime_formatted": uptime_formatted,
                "freecad_status": freecad_status,
                "initialized": server is not None and hasattr(server, "initialized") and server.initialized,
                "event_handlers": list(server.event_handlers.keys()) if server else [],
                "resource_providers": list(server.resources.keys()) if server else [],
                "tool_providers": list(server.tools.keys()) if server else []
            }
        }
    
    # === Cache management endpoints ===
    def verify_api_key(authorization: Optional[str] = Header(None)):
        """Verify the API key middleware."""
        return True  # In mock mode, allow all
    
    @app.get("/cache/stats")
    @server.performance_monitor.track("cache.stats")
    async def get_cache_stats(authorized: bool = Depends(verify_api_key)):
        """Get statistics about the cache."""
        if not server or not hasattr(server, "resource_cache"):
            raise HTTPException(status_code=500, detail="Cache system not initialized")
            
        # Create sample stats
        cache_stats = {
            "size": len(server.resource_cache),
            "max_size": server.resource_cache.max_size,
            "default_ttl": server.resource_cache.default_ttl,
            "hit_count": 0,
            "miss_count": 0,
            "hit_rate": 0,
            "keys": list(server.resource_cache.cache.keys())[:100]  # Limit to 100 keys for readability
        }
        
        return cache_stats
    
    @app.post("/cache/clear")
    @server.performance_monitor.track("cache.clear")
    async def clear_cache(authorized: bool = Depends(verify_api_key)):
        """Clear the cache."""
        if not server or not hasattr(server, "resource_cache"):
            raise HTTPException(status_code=500, detail="Cache system not initialized")
            
        server.resource_cache.clear()
        return {"status": "success", "message": "Cache cleared successfully"}
    
    @app.delete("/cache/item/{key}")
    @server.performance_monitor.track("cache.delete_item")
    async def delete_cache_item(key: str, authorized: bool = Depends(verify_api_key)):
        """Delete a specific item from the cache."""
        if not server or not hasattr(server, "resource_cache"):
            raise HTTPException(status_code=500, detail="Cache system not initialized")
            
        if key in server.resource_cache.cache:
            del server.resource_cache.cache[key]
            return {"status": "success", "message": f"Cache item '{key}' deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"Cache item '{key}' not found")
    
    # === Performance monitoring endpoints ===
    @app.get("/diagnostics")
    @server.performance_monitor.track("diagnostics")
    async def get_diagnostics(authorized: bool = Depends(verify_api_key)):
        """Get diagnostics about server performance."""
        if not server or not hasattr(server, "performance_monitor"):
            raise HTTPException(status_code=500, detail="Performance monitoring not initialized")
            
        # Get basic server info
        uptime = time.time() - server.performance_monitor.start_time
        uptime_formatted = str(datetime.timedelta(seconds=int(uptime)))
        
        # Get system stats
        process = psutil.Process()
        sys_metrics = {
            "cpu_percent": process.cpu_percent(),
            "memory_usage": {
                "rss": process.memory_info().rss / (1024 * 1024),  # MB
                "vms": process.memory_info().vms / (1024 * 1024)   # MB
            },
            "thread_count": process.num_threads(),
            "open_files": len(process.open_files()),
            "connections": len(process.connections())
        }
        
        # Get metrics
        try:
            metrics = [m.get_stats() for m in server.performance_monitor.metrics.values()]
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            metrics = []
        
        return {
            "server": {
                "uptime_seconds": uptime,
                "uptime_formatted": uptime_formatted,
                "start_time": datetime.datetime.fromtimestamp(server.performance_monitor.start_time).isoformat(),
                "current_time": datetime.datetime.now().isoformat(),
                "request_count": server.performance_monitor.request_count,
                "error_count": server.performance_monitor.error_count,
                "metric_count": len(metrics)
            },
            "system": sys_metrics,
            "metrics": metrics,
            "recovery": {
                "retries": {},
                "failures": {}
            },
            "cache": {
                "size": len(server.resource_cache.cache) if hasattr(server, "resource_cache") else 0,
                "hit_rate": 0
            }
        }
    
    @app.post("/diagnostics/reset")
    @server.performance_monitor.track("diagnostics.reset")
    async def reset_diagnostics(authorized: bool = Depends(verify_api_key)):
        """Reset performance metrics."""
        if not server or not hasattr(server, "performance_monitor"):
            raise HTTPException(status_code=500, detail="Performance monitoring not initialized")
            
        try:
            server.performance_monitor.reset()
        except Exception as e:
            logger.error(f"Error resetting metrics: {e}")
            
        return {"status": "success", "message": "Diagnostics reset successfully"}
    
    @app.get("/diagnostics/slow_endpoints")
    @server.performance_monitor.track("diagnostics.slow_endpoints")
    async def get_slow_endpoints(limit: int = 10, authorized: bool = Depends(verify_api_key)):
        """Get the slowest endpoints."""
        if not server or not hasattr(server, "performance_monitor"):
            raise HTTPException(status_code=500, detail="Performance monitoring not initialized")
            
        try:
            metrics = [m.get_stats() for m in server.performance_monitor.metrics.values()]
            
            # Sort by average duration (descending)
            sorted_metrics = sorted(metrics, key=lambda m: m.get("avg_duration", 0), reverse=True)
            
            return {
                "slow_endpoints": sorted_metrics[:limit]
            }
        except Exception as e:
            logger.error(f"Error getting slow endpoints: {e}")
            return {"slow_endpoints": []}
    
    return app

if __name__ == "__main__":
    # Get server configuration
    try:
        with open("config.json", "r") as f:
            config = json.load(f)
    except Exception as e:
        logger.warning(f"Could not load config from config.json: {e}")
        config = {
            "server": {
                "host": "0.0.0.0",
                "port": 8000
            }
        }
    
    # Get server host and port
    host = config.get("server", {}).get("host", "0.0.0.0")
    port = config.get("server", {}).get("port", 8000)
    
    # Since we're using async initialization, we need to create the app in an event loop
    app = asyncio.run(main())
    
    # Start the server
    logger.info(f"Starting Mock MCP-FreeCAD Server on {host}:{port}")
    uvicorn.run(app, host=host, port=port) 