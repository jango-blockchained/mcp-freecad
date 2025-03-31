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
from src.mcp_freecad.resources.cad_model import CADModelResourceProvider
from src.mcp_freecad.resources.measurement import MeasurementResourceProvider
from src.mcp_freecad.resources.material import MaterialResourceProvider
from src.mcp_freecad.resources.constraint import ConstraintResourceProvider
from src.mcp_freecad.tools.primitives import PrimitiveToolProvider
from src.mcp_freecad.tools.model_manipulation import ModelManipulationToolProvider
from src.mcp_freecad.tools.measurement import MeasurementToolProvider
from src.mcp_freecad.tools.export_import import ExportImportToolProvider
from src.mcp_freecad.tools.code_generator import CodeGenerationToolProvider
from src.mcp_freecad.events.document_events import DocumentEventProvider
from src.mcp_freecad.events.command_events import CommandExecutionEventProvider
from src.mcp_freecad.events.error_events import ErrorEventProvider
from src.mcp_freecad.api.events import create_event_router
from src.mcp_freecad.api.resources import create_resource_router
from src.mcp_freecad.api.tools import create_tool_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp_freecad")

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

async def create_app():
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
    server.register_resource("cad_model", CADModelResourceProvider())
    server.register_resource("measurements", MeasurementResourceProvider())
    server.register_resource("materials", MaterialResourceProvider())
    server.register_resource("constraints", ConstraintResourceProvider())
    logger.info(f"Registered resource providers: {server.resources.keys()}")
    
    # Register tool providers
    server.register_tool("primitives", PrimitiveToolProvider())
    server.register_tool("model_manipulation", ModelManipulationToolProvider())
    server.register_tool("measurement", MeasurementToolProvider())
    server.register_tool("export_import", ExportImportToolProvider())
    server.register_tool("code_generation", CodeGenerationToolProvider())
    logger.info(f"Registered tool providers: {server.tools.keys()}")
    
    # Create the FastAPI app
    app = server.create_app()
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.get("cors", {}).get("origins", ["*"]),
        allow_credentials=config.get("cors", {}).get("allow_credentials", True),
        allow_methods=config.get("cors", {}).get("methods", ["*"]),
        allow_headers=config.get("cors", {}).get("headers", ["*"]),
    )
    
    # Create event router first so we can pass it to event providers
    event_router = create_event_router(server)
    
    # Register event handlers
    document_event_provider = DocumentEventProvider(event_router=event_router)
    command_event_provider = CommandExecutionEventProvider(event_router=event_router)
    error_event_provider = ErrorEventProvider(event_router=event_router)
    
    server.register_event_handler("document_changed", document_event_provider)
    server.register_event_handler("document_created", document_event_provider)
    server.register_event_handler("document_closed", document_event_provider)
    server.register_event_handler("active_document_changed", document_event_provider)
    server.register_event_handler("selection_changed", document_event_provider)
    
    server.register_event_handler("command_executed", command_event_provider)
    
    server.register_event_handler("error", error_event_provider)
    
    logger.info(f"Registered event handlers: {server.event_handlers.keys()}")
    
    # Mount API routers
    app.include_router(event_router, prefix="/events", tags=["events"])
    
    # Add startup event handler
    app.add_event_handler("startup", startup_event)
    
    # Add API routes directly to the app
    @app.post("/tools/primitives.create_box")
    @server.performance_monitor.track("primitives.create_box")
    async def create_box(tool_request: dict):
        try:
            # Get parameters with default values
            params = tool_request.get("parameters", {})
            length = params.get("length", 10.0)
            width = params.get("width", 10.0)
            height = params.get("height", 10.0)
            
            return {
                "tool_id": "primitives.create_box",
                "status": "success",
                "result": {
                    "message": f"Box created successfully with dimensions: {length}x{width}x{height}",
                    "parameters": {
                        "length": length,
                        "width": width,
                        "height": height
                    }
                }
            }
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

    # Add model manipulation tool endpoints
    @app.post("/tools/model_manipulation.transform")
    @server.performance_monitor.track("model_manipulation.transform")
    async def transform_object(tool_request: dict):
        try:
            if "model_manipulation" not in server.tools:
                return {"status": "error", "message": "Model manipulation tool provider not found"}
                
            tool_provider = server.tools["model_manipulation"]
            params = tool_request.get("parameters", {})
            
            # Use recovery mechanism for executing the tool
            return await server.recovery.with_retry(
                lambda: tool_provider.execute_tool("transform", params),
                "model_manipulation.transform"
            )
        except Exception as e:
            # Report error
            if "error" in server.event_handlers:
                for handler in server.event_handlers["error"]:
                    if hasattr(handler, "report_error"):
                        handler.report_error(str(e), "api_error")
            return {"status": "error", "message": str(e)}
    
    # Add measurement tool endpoints
    @app.post("/tools/measurement.distance")
    @server.performance_monitor.track("measurement.distance")
    async def measure_distance(tool_request: dict):
        try:
            if "measurement" not in server.tools:
                return {"status": "error", "message": "Measurement tool provider not found"}
                
            tool_provider = server.tools["measurement"]
            params = tool_request.get("parameters", {})
            
            # Use recovery mechanism for executing the tool
            return await server.recovery.with_retry(
                lambda: tool_provider.execute_tool("distance", params),
                "measurement.distance"
            )
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # Add export/import tool endpoint example with recovery
    @app.post("/tools/export_import.export")
    @server.performance_monitor.track("export_import.export")
    async def export_file(tool_request: dict):
        try:
            if "export_import" not in server.tools:
                return {"status": "error", "message": "Export/Import tool provider not found"}
                
            tool_provider = server.tools["export_import"]
            params = tool_request.get("parameters", {})
            
            # Use recovery mechanism for executing the tool
            return await server.recovery.with_retry(
                lambda: tool_provider.execute_tool("export", params),
                "export_import.export"
            )
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # Add code generation tool endpoint example with recovery
    @app.post("/tools/code_generation.generate_script")
    @server.performance_monitor.track("code_generation.generate_script")
    async def generate_script(tool_request: dict):
        try:
            if "code_generation" not in server.tools:
                return {"status": "error", "message": "Code generation tool provider not found"}
                
            tool_provider = server.tools["code_generation"]
            params = tool_request.get("parameters", {})
            
            # Use recovery mechanism for executing the tool
            return await server.recovery.with_retry(
                lambda: tool_provider.execute_tool("generate_script", params),
                "code_generation.generate_script"
            )
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # Add new event handler endpoints
    @app.get("/events/command_history")
    @server.performance_monitor.track("events.command_history")
    async def get_command_history(limit: Optional[int] = None):
        """Get the command execution history."""
        if "command_executed" not in server.event_handlers:
            return {"status": "error", "message": "Command execution handler not registered"}
            
        handler = server.event_handlers["command_executed"][0]
        if hasattr(handler, "get_command_history"):
            history = handler.get_command_history(limit)
            return {"status": "success", "command_history": history}
        else:
            return {"status": "error", "message": "Command history not available"}
    
    @app.get("/events/error_history")
    @server.performance_monitor.track("events.error_history")
    async def get_error_history(limit: Optional[int] = None):
        """Get the error history."""
        if "error" not in server.event_handlers:
            return {"status": "error", "message": "Error handler not registered"}
            
        handler = server.event_handlers["error"][0]
        if hasattr(handler, "get_error_history"):
            history = handler.get_error_history(limit)
            return {"status": "success", "error_history": history}
        else:
            return {"status": "error", "message": "Error history not available"}
    
    @app.post("/events/report_error")
    @server.performance_monitor.track("events.report_error")
    async def report_error(error_data: dict):
        """Manually report an error."""
        if "error" not in server.event_handlers:
            return {"status": "error", "message": "Error handler not registered"}
            
        handler = server.event_handlers["error"][0]
        if hasattr(handler, "report_error"):
            message = error_data.get("message", "Unknown error")
            error_type = error_data.get("error_type", "manual")
            details = error_data.get("details", {})
            
            handler.report_error(message, error_type, details)
            return {"status": "success", "message": "Error reported successfully"}
        else:
            return {"status": "error", "message": "Error reporting not available"}
    
    # === Health check and monitoring endpoints ===
    @app.get("/health")
    async def health_check():
        """Basic health check endpoint that returns server status."""
        global server
        return {
            "status": "ok",
            "version": "1.0.0",  # You might want to fetch this from a version file
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
        freecad_status = "connected" if server and server.freecad_connected else "disconnected"
        
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
        if not server or not hasattr(server, "config"):
            raise HTTPException(status_code=500, detail="Server not initialized")
            
        expected_api_key = server.config.get("auth", {}).get("api_key")
        if not expected_api_key:
            return True  # No API key configured, allow all
            
        # Check if API key is provided
        if not authorization:
            raise HTTPException(status_code=401, detail="API key is required")
            
        if authorization != expected_api_key:
            raise HTTPException(status_code=403, detail="Invalid API key")
            
        return True
    
    @app.get("/cache/stats")
    @server.performance_monitor.track("cache.stats")
    async def get_cache_stats(authorized: bool = Depends(verify_api_key)):
        """Get statistics about the cache."""
        if not server or not hasattr(server, "cache"):
            raise HTTPException(status_code=500, detail="Cache system not initialized")
            
        return {
            "size": len(server.cache),
            "max_size": server.cache.max_size,
            "default_ttl": server.cache.default_ttl,
            "hit_count": server.cache.hit_count,
            "miss_count": server.cache.miss_count,
            "hit_rate": server.cache.hit_rate,
            "keys": list(server.cache.keys())[:100]  # Limit to 100 keys for readability
        }
    
    @app.post("/cache/clear")
    @server.performance_monitor.track("cache.clear")
    async def clear_cache(authorized: bool = Depends(verify_api_key)):
        """Clear the cache."""
        if not server or not hasattr(server, "cache"):
            raise HTTPException(status_code=500, detail="Cache system not initialized")
            
        server.cache.clear()
        return {"status": "success", "message": "Cache cleared successfully"}
    
    @app.delete("/cache/item/{key}")
    @server.performance_monitor.track("cache.delete_item")
    async def delete_cache_item(key: str, authorized: bool = Depends(verify_api_key)):
        """Delete a specific item from the cache."""
        if not server or not hasattr(server, "cache"):
            raise HTTPException(status_code=500, detail="Cache system not initialized")
            
        if key in server.cache:
            del server.cache[key]
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
        metrics = server.performance_monitor.get_metrics()
        
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
                "retries": server.recovery.retries if hasattr(server, "recovery") else {},
                "failures": server.recovery.failures if hasattr(server, "recovery") else {}
            },
            "cache": {
                "size": len(server.cache) if hasattr(server, "cache") else 0,
                "hit_rate": server.cache.hit_rate if hasattr(server, "cache") else 0
            }
        }
    
    @app.post("/diagnostics/reset")
    @server.performance_monitor.track("diagnostics.reset")
    async def reset_diagnostics(authorized: bool = Depends(verify_api_key)):
        """Reset performance metrics."""
        if not server or not hasattr(server, "performance_monitor"):
            raise HTTPException(status_code=500, detail="Performance monitoring not initialized")
            
        server.performance_monitor.reset()
        
        if hasattr(server, "recovery"):
            server.recovery.reset_stats()
            
        return {"status": "success", "message": "Diagnostics reset successfully"}
    
    @app.get("/diagnostics/slow_endpoints")
    @server.performance_monitor.track("diagnostics.slow_endpoints")
    async def get_slow_endpoints(limit: int = 10, authorized: bool = Depends(verify_api_key)):
        """Get the slowest endpoints."""
        if not server or not hasattr(server, "performance_monitor"):
            raise HTTPException(status_code=500, detail="Performance monitoring not initialized")
            
        metrics = server.performance_monitor.get_metrics()
        
        # Sort by average duration (descending)
        sorted_metrics = sorted(metrics, key=lambda m: m.get("avg_duration", 0), reverse=True)
        
        return {
            "slow_endpoints": sorted_metrics[:limit]
        }
    
    @app.get("/diagnostics/errors")
    @server.performance_monitor.track("diagnostics.errors")
    async def get_error_diagnostics(limit: int = 50, authorized: bool = Depends(verify_api_key)):
        """Get detailed error information."""
        if "error" not in server.event_handlers:
            raise HTTPException(status_code=404, detail="Error handler not registered")
            
        handler = server.event_handlers["error"][0]
        if hasattr(handler, "get_error_history"):
            history = handler.get_error_history(limit)
            
            # Aggregate errors by type
            error_types = {}
            for error in history:
                error_type = error.get("error_type", "unknown")
                if error_type not in error_types:
                    error_types[error_type] = 0
                error_types[error_type] += 1
                
            return {
                "error_count": server.performance_monitor.error_count if hasattr(server, "performance_monitor") else len(history),
                "error_types": error_types,
                "recent_errors": history
            }
        else:
            raise HTTPException(status_code=501, detail="Error history not available")
    
    return app

def main():
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
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(create_app())
    
    # Start the server
    logger.info(f"Starting FreeCAD MCP Server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    main() 