import json
import logging
from typing import Dict, List, Any, Optional

from fastapi import FastAPI
from loguru import logger

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
        logger.info("MCP Server initialized")
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load config from {config_path}: {e}")
            return {"auth": {"api_key": "development"}}
    
    def register_resource(self, resource_id: str, resource_provider: Any) -> None:
        self.resources[resource_id] = resource_provider
        logger.info(f"Registered resource provider for {resource_id}")
        
    def register_tool(self, tool_id: str, tool_provider: Any) -> None:
        self.tools[tool_id] = tool_provider
        logger.info(f"Registered tool provider for {tool_id}")
        
    def register_event_handler(self, event_type: str, handler: Any) -> None:
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered event handler for {event_type}")
        
    def create_app(self) -> FastAPI:
        app = FastAPI(title="FreeCAD MCP Server")
        
        @app.get("/")
        async def root():
            return {"message": "FreeCAD MCP Server is running"}
        
        # We'll now let the router registration be handled in the app.py file
        # This avoids duplicate route definitions and allows for better control
        # over how routes are registered
        
        return app 