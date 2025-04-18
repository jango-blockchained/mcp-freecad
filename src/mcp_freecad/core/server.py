import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Callable, Dict, Generic, List, Optional, TypeVar

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel

from ..tools.base import ToolParams, ToolProvider, ToolResult
from ..tools.resource import ResourceParams, ResourceProvider, ResourceResult
from .cache import ResourceCache
from .diagnostics import PerformanceMonitor
from .recovery import ConnectionRecovery, FreeCADConnectionManager, RecoveryConfig

T = TypeVar("T")


class AuthManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        logger.info("Initializing authentication manager")

    async def authenticate(self, token: str) -> bool:
        # Simple token authentication for now
        return token == self.config.get("api_key", "")


class ToolExecutionParams(BaseModel):
    params: Dict[str, Any]


class ResourceAccessParams(BaseModel):
    params: Dict[str, Any]


class MCPServer:
    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.resources = {}
        self.tools = {}
        self.event_handlers = {}
        self.auth_manager = AuthManager(self.config.get("auth", {}))
        self.recovery = ConnectionRecovery(
            config=RecoveryConfig(
                max_retries=self.config.get("recovery", {}).get("max_retries", 5),
                retry_delay=self.config.get("recovery", {}).get("retry_delay", 2.0),
                backoff_factor=self.config.get("recovery", {}).get(
                    "backoff_factor", 1.5
                ),
                max_delay=self.config.get("recovery", {}).get("max_delay", 30.0),
            )
        )
        self.start_time = time.time()

        # Initialize optimization components
        self.resource_cache = ResourceCache(
            default_ttl=self.config.get("cache", {}).get("default_ttl", 30.0),
            max_size=self.config.get("cache", {}).get("max_size", 100),
        )

        self.connection_manager = FreeCADConnectionManager(
            config=self.recovery.config, recovery=self.recovery
        )

        self.performance_monitor = PerformanceMonitor()

        # Initialize FastAPI app
        self.app = FastAPI()
        self._setup_routes()
        self._setup_middleware()

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
                    "max_delay": 30.0,
                },
                "freecad": {"auto_connect": True},
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
            logger.info(
                f"Attached connection manager to resource provider {resource_id}"
            )

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
            logger.info(
                f"Attached connection manager to event handler for {event_type}"
            )

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
                        logger.error(
                            f"Error initializing resource provider {resource_id}: {e}"
                        )

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

    async def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit an event to all registered handlers."""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    await handler.handle_event(event_type, data)
                except Exception as e:
                    logger.error(f"Error in event handler for {event_type}: {e}")

    async def handle_tool_execution(
        self, tool_id: str, params: Dict[str, Any]
    ) -> ToolResult:
        """Handle tool execution with proper event emission and error handling."""
        try:
            # Validate tool exists
            if tool_id not in self.tools:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tool {tool_id} not found",
                )

            # Emit pre-execution event
            await self._emit_event(
                "tool.pre_execute", {"tool_id": tool_id, "params": params}
            )

            # Execute tool
            result = await self.tools[tool_id].execute_tool(tool_id, params)

            # Emit post-execution event
            await self._emit_event(
                "tool.post_execute", {"tool_id": tool_id, "result": result}
            )

            return result
        except Exception as e:
            # Emit error event
            await self._emit_event("tool.error", {"tool_id": tool_id, "error": str(e)})
            raise

    async def handle_resource_access(
        self, resource_id: str, params: Dict[str, Any]
    ) -> ResourceResult:
        """Handle resource access with proper event emission and error handling."""
        try:
            # Validate resource exists
            if resource_id not in self.resources:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Resource {resource_id} not found",
                )

            # Emit pre-access event
            await self._emit_event(
                "resource.pre_access", {"resource_id": resource_id, "params": params}
            )

            # Access resource
            result = await self.resources[resource_id].get_resource(resource_id, params)

            # Emit post-access event
            await self._emit_event(
                "resource.post_access", {"resource_id": resource_id, "result": result}
            )

            return result
        except Exception as e:
            # Emit error event
            await self._emit_event(
                "resource.error", {"resource_id": resource_id, "error": str(e)}
            )
            raise

    def _setup_routes(self):
        """Set up FastAPI routes."""

        @self.app.get("/health")
        async def health_check():
            """Basic health check endpoint."""
            return {
                "status": "ok",
                "timestamp": time.time(),
                "freecad_connected": self.connection_manager.connected,
            }

        @self.app.get("/health/detailed")
        async def detailed_health():
            """Detailed health check endpoint."""
            return {
                "status": "ok",
                "timestamp": time.time(),
                "freecad_connection": self.connection_manager.get_status(),
                "cache": self.resource_cache.get_stats(),
                "server_uptime": time.time() - self.start_time,
            }

        @self.app.post("/tools/{tool_id}/execute")
        async def execute_tool(tool_id: str, request: ToolExecutionParams):
            """Execute a tool."""
            return await self.handle_tool_execution(tool_id, request.params)

        @self.app.post("/resources/{resource_id}/access")
        async def access_resource(resource_id: str, request: ResourceAccessParams):
            """Access a resource."""
            if resource_id not in self.resources:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Resource {resource_id} not found",
                )
            return await self.resources[resource_id].get_resource(params=request.params)

        @self.app.get("/diagnostics")
        async def get_diagnostics():
            """Get server diagnostics."""
            return self.performance_monitor.get_diagnostics_report()

        @self.app.post("/cache/clear")
        async def clear_cache():
            """Clear the resource cache."""
            self.resource_cache.clear()
            return {"status": "success"}

    def _setup_middleware(self):
        """Set up FastAPI middleware."""

        @self.app.middleware("http")
        async def auth_middleware(request: Request, call_next):
            if request.url.path.startswith("/health"):
                return await call_next(request)

            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            if not await self.auth_manager.authenticate(token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication token",
                )
            return await call_next(request)

        @self.app.middleware("http")
        async def performance_middleware(request: Request, call_next):
            start_time = time.time()
            try:
                response = await call_next(request)
                duration = time.time() - start_time
                self.performance_monitor.track(
                    f"endpoint.{request.url.path}", duration, success=True
                )
                return response
            except Exception as e:
                duration = time.time() - start_time
                self.performance_monitor.track(
                    f"endpoint.{request.url.path}",
                    duration,
                    success=False,
                    error=str(e),
                )
                raise
