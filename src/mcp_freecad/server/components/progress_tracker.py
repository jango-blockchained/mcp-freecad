"""
Progress tracking system for MCP tool execution.

Provides progress reporting capabilities for long-running operations.
"""

import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class ToolContext:
    """Context for tool execution with progress reporting."""

    _instance = None

    def __init__(self):
        self.progress_callback: Optional[Callable] = None

    @classmethod
    def get(cls):
        """Get singleton instance of ToolContext."""
        if cls._instance is None:
            cls._instance = ToolContext()
        return cls._instance

    def set_progress_callback(self, callback: Callable):
        """Set callback function for progress reporting."""
        self.progress_callback = callback

    async def send_progress(self, progress: float, message: str = None):
        """
        Send progress update.

        Args:
            progress: Progress value between 0.0 and 1.0
            message: Optional progress message
        """
        if self.progress_callback and callable(self.progress_callback):
            await self.progress_callback(progress, message)
        else:
            progress_pct = progress * 100
            msg = f"Progress: {progress_pct:.1f}%"
            if message:
                msg += f" - {message}"
            logger.debug(msg)