import json
import logging
import time
from typing import Dict, List, Any, Optional, Callable, TypeVar, Generic

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from loguru import logger

from .cache import ResourceCache
from .recovery import FreeCADConnectionManager, ConnectionRecovery
from .diagnostics import PerformanceMonitor

T = TypeVar('T')

class AuthManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        logger.info("Initializing authentication manager")

    async def authenticate(self, token: str) -> bool:
        # Simple token authentication for now
        return token == self.config.get("api_key", "")

class MCPServer:
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.resources = {}
        self.tools = {}
        self.event_handlers = {}
        self.auth_manager = AuthManager(self.config.get("auth", {}))
        
        # Initialize optimization components
        self.resource_cache = ResourceCache(
            default_ttl=self.config.get("cache", {}).get("default_ttl", 30.0),
            max_size=self.config.get("cache", {}).get("max_size", 100)
        )
        
        self.recovery = ConnectionRecovery(
            max_retries=self.config.get("recovery", {}).get("max_retries", 5),
            retry_delay=self.config.get("recovery", {}).get("retry_delay", 2.0),
            backoff_factor=self.config.get("recovery", {}).get("backoff_factor", 1.5),
            max_delay=self.config.get("recovery", {}).get("max_delay", 30.0)
        )
        
        self.connection_manager = FreeCADConnectionManager(
            self.config.get("freecad", {}),
            self.recovery
        )
        
        self.performance_monitor = PerformanceMonitor()
        
        logger.info("MCP Server initialized with optimization components")
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load config from {config_path}: {e}")
            return {
                "auth": {"api_key": "development"},
                "cache": {"default_ttl": 30.0, "max_size": 100},
                "recovery": {
                    "max_retries": 5,
                    "retry_delay": 2.0,
                    "backoff_factor": 1.5,
                    "max_delay": 30.0
                },
                "freecad": {"auto_connect": True}
            }
    
    def register_resource(self, resource_id: str, resource_provider: Any) -> None:
        """
        Register a resource provider with the server.
        
        Args:
            resource_id: Identifier for the resource
            resource_provider: Resource provider instance
        """
        # Attach the cache to the resource provider if it has an expected attribute
        if hasattr(resource_provider, "set_cache"):
            resource_provider.set_cache(self.resource_cache)
            logger.info(f"Attached cache to resource provider {resource_id}")
            
        # Attach the connection manager if provider expects it
        if hasattr(resource_provider, "set_connection_manager"):
            resource_provider.set_connection_manager(self.connection_manager)
            logger.info(f"Attached connection manager to resource provider {resource_id}")
            
        self.resources[resource_id] = resource_provider
        logger.info(f"Registered resource provider for {resource_id}")
        
    def register_tool(self, tool_id: str, tool_provider: Any) -> None:
        """
        Register a tool provider with the server.
        
        Args:
            tool_id: Identifier for the tool
            tool_provider: Tool provider instance
        """
        # Attach the connection manager if provider expects it
        if hasattr(tool_provider, "set_connection_manager"):
            tool_provider.set_connection_manager(self.connection_manager)
            logger.info(f"Attached connection manager to tool provider {tool_id}")
            
        # Attach performance monitor if provider expects it
        if hasattr(tool_provider, "set_performance_monitor"):
            tool_provider.set_performance_monitor(self.performance_monitor)
            logger.info(f"Attached performance monitor to tool provider {tool_id}")
            
        self.tools[tool_id] = tool_provider
        logger.info(f"Registered tool provider for {tool_id}")
        
    def register_event_handler(self, event_type: str, handler: Any) -> None:
        """
        Register an event handler with the server.
        
        Args:
            event_type: Type of event to handle
            handler: Event handler instance
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
            
        # Attach the connection manager if handler expects it
        if hasattr(handler, "set_connection_manager"):
            handler.set_connection_manager(self.connection_manager)
            logger.info(f"Attached connection manager to event handler for {event_type}")
            
        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered event handler for {event_type}")
        
    async def initialize(self) -> None:
        """
        Initialize the server components.
        
        This should be called during startup to connect to FreeCAD
        and prepare the server.
        """
        try:
            # Connect to FreeCAD
            if self.config.get("freecad", {}).get("auto_connect", True):
                logger.info("Auto-connecting to FreeCAD...")
                await self.connection_manager.connect()
                
            # Initialize resource providers that need it
            for resource_id, provider in self.resources.items():
                if hasattr(provider, "initialize"):
                    try:
                        await provider.initialize()
                        logger.info(f"Initialized resource provider {resource_id}")
                    except Exception as e:
                        logger.error(f"Error initializing resource provider {resource_id}: {e}")
                        
            # Initialize tool providers that need it
            for tool_id, provider in self.tools.items():
                if hasattr(provider, "initialize"):
                    try:
                        await provider.initialize()
                        logger.info(f"Initialized tool provider {tool_id}")
                    except Exception as e:
                        logger.error(f"Error initializing tool provider {tool_id}: {e}")
                        
            logger.info("Server initialization completed")
            
        except Exception as e:
            logger.error(f"Error during server initialization: {e}")
            
    def create_app(self) -> FastAPI:
        """
        Create the FastAPI application.
        
        Returns:
            FastAPI application instance
        """
        app = FastAPI(
            title="FreeCAD MCP Server",
            description="Model Context Protocol server for FreeCAD",
            version="0.1.0"
        )
        
        # Add middleware for performance monitoring
        @app.middleware("http")
        async def performance_middleware(request: Request, call_next):
            # Skip monitoring for static files
            if request.url.path.startswith("/static"):
                return await call_next(request)
                
            start_time = time.time()
            path = request.url.path
            method = request.method
            metric_name = f"{method} {path}"
            success = True
            error = None
            
            try:
                response = await call_next(request)
                return response
            except Exception as e:
                success = False
                error = e
                raise
            finally:
                duration = time.time() - start_time
                
                # Record the performance metric
                if metric_name not in self.performance_monitor.metrics:
                    self.performance_monitor.metrics[metric_name] = self.performance_monitor.track(metric_name)
                    
                self.performance_monitor.metrics[metric_name].record_sample(duration, success, error)
                
        # Add health check endpoints
        @app.get("/health")
        async def health_check():
            """Basic health check endpoint."""
            return {
                "status": "ok",
                "timestamp": time.time(),
                "freecad_connected": self.connection_manager.connected
            }
            
        @app.get("/health/detailed")
        async def detailed_health():
            """Detailed health check with connection status."""
            return {
                "status": "ok",
                "timestamp": time.time(),
                "freecad_connection": self.connection_manager.get_connection_status(),
                "cache": self.resource_cache.get_stats() if hasattr(self.resource_cache, "get_stats") else None,
                "server_uptime": time.time() - self.performance_monitor.start_time
            }
            
        @app.get("/diagnostics")
        async def diagnostics():
            """Get server diagnostics information."""
            return self.performance_monitor.get_diagnostics_report()
            
        @app.post("/diagnostics/reset")
        async def reset_diagnostics():
            """Reset performance metrics."""
            self.performance_monitor.reset_metrics()
            return {"status": "ok", "message": "Performance metrics reset"}
            
        @app.post("/cache/clear")
        async def clear_cache():
            """Clear the resource cache."""
            self.resource_cache.clear()
            return {"status": "ok", "message": "Cache cleared"}
            
        @app.get("/cache/stats")
        async def cache_stats():
            """Get cache statistics."""
            return self.resource_cache.get_stats()
            
        @app.get("/")
        async def root():
            """Server root endpoint."""
            return {
                "message": "FreeCAD MCP Server is running",
                "version": "0.1.0",
                "freecad_connected": self.connection_manager.connected
            }
        
        return app 