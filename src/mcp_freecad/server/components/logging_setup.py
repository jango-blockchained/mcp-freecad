"""
Logging infrastructure for FreeCAD MCP Server.

Provides structured logging with socket receivers and file handlers.
"""

import logging
import logging.handlers
import os
import socketserver
import struct
import pickle
from typing import Optional


class LogRequestHandler(socketserver.StreamRequestHandler):
    """Handler for incoming log records."""

    def handle(self):
        """Handle multiple requests with 4-byte length prefix + pickled record."""
        while True:
            try:
                chunk = self.request.recv(4)
                if len(chunk) < 4:
                    break
                slen = struct.unpack(">L", chunk)[0]
                chunk = self.request.recv(slen)
                while len(chunk) < slen:
                    chunk = chunk + self.request.recv(slen - len(chunk))
                obj = pickle.loads(chunk)
                record = logging.makeLogRecord(obj)
                self.handle_log_record(record)
            except Exception:
                break

    def handle_log_record(self, record):
        """Process the log record."""
        if self.server.logname:
            name = self.server.logname
        else:
            name = record.name
        logger = logging.getLogger(name)
        logger.handle(record)


class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    """TCP server for receiving log records."""

    allow_reuse_address = True
    abort = 0
    timeout = 1

    def __init__(self, host="localhost", port=9020, handler=LogRequestHandler):
        super().__init__((host, port), handler)
        self.logname = None


def setup_logging(config: dict) -> Optional[LogRecordSocketReceiver]:
    """Setup logging infrastructure based on configuration."""
    log_config = config.get("logging", {})

    # Ensure logs directory exists
    log_file = log_config.get("file", "logs/freecad_mcp_server.log")
    log_dir = os.path.dirname(log_file)
    os.makedirs(log_dir, exist_ok=True)

    # Configure basic logging
    level = getattr(logging, log_config.get("level", "INFO").upper())
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )

    # Setup socket receiver for remote logging
    try:
        port = log_config.get("port", 9020)
        receiver = LogRecordSocketReceiver(port=port)
        return receiver
    except Exception as e:
        logging.warning(f"Could not setup log receiver: {e}")
        return None
