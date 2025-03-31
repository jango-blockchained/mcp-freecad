class MCPError(Exception):
    """Base exception for all MCP-related errors."""
    def __init__(self, message: str, code: str = None, details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)

class ToolExecutionError(MCPError):
    """Raised when a tool execution fails."""
    def __init__(self, message: str, tool_id: str, details: dict = None):
        super().__init__(
            message=message,
            code="TOOL_EXECUTION_ERROR",
            details={"tool_id": tool_id, **(details or {})}
        )

class ResourceAccessError(MCPError):
    """Raised when a resource cannot be accessed."""
    def __init__(self, message: str, resource_id: str, details: dict = None):
        super().__init__(
            message=message,
            code="RESOURCE_ACCESS_ERROR",
            details={"resource_id": resource_id, **(details or {})}
        )

class ValidationError(MCPError):
    """Raised when input validation fails."""
    def __init__(self, message: str, field: str = None, details: dict = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details={"field": field, **(details or {})}
        )

class AuthenticationError(MCPError):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication failed", details: dict = None):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            details=details
        )

class ConnectionError(MCPError):
    """Raised when connection to FreeCAD fails."""
    def __init__(self, message: str, connection_type: str, details: dict = None):
        super().__init__(
            message=message,
            code="CONNECTION_ERROR",
            details={"connection_type": connection_type, **(details or {})}
        )

class ConfigurationError(MCPError):
    """Raised when there's an error in the configuration."""
    def __init__(self, message: str, config_key: str = None, details: dict = None):
        super().__init__(
            message=message,
            code="CONFIGURATION_ERROR",
            details={"config_key": config_key, **(details or {})}
        )

class CacheError(MCPError):
    """Raised when there's an error with the cache."""
    def __init__(self, message: str, operation: str, details: dict = None):
        super().__init__(
            message=message,
            code="CACHE_ERROR",
            details={"operation": operation, **(details or {})}
        )

class EventError(MCPError):
    """Raised when there's an error handling events."""
    def __init__(self, message: str, event_type: str, details: dict = None):
        super().__init__(
            message=message,
            code="EVENT_ERROR",
            details={"event_type": event_type, **(details or {})}
        ) 