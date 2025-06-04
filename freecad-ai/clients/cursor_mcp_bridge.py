#!/usr/bin/env python3
"""
Cursor MCP Bridge for FreeCAD

This script launches the FreeCAD MCP server in stdio mode for Cursor integration.
All debugging/info messages are redirected to stderr, keeping stdout clean for JSON-only communication.
"""

import os
import sys
import subprocess
import logging
import atexit

# Configure logging to stderr only (keep stdout clean for JSON)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,  # Send all logging to stderr, not stdout
)
logger = logging.getLogger("cursor_mcp_bridge")

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Try to find the MCP server script in the parent project directory
ADDON_DIR = os.path.dirname(SCRIPT_DIR)
PROJECT_DIR = os.path.dirname(ADDON_DIR)
MCP_SERVER_SCRIPT = os.path.join(
    PROJECT_DIR, "src", "mcp_freecad", "server", "freecad_mcp_server.py"
)

# Fallback to a local server script if the main one doesn't exist
if not os.path.exists(MCP_SERVER_SCRIPT):
    MCP_SERVER_SCRIPT = os.path.join(ADDON_DIR, "mcp_server.py")

# Track processes for cleanup
processes = []


def cleanup():
    """Clean up processes on exit"""
    for proc in processes:
        if proc.poll() is None:  # Still running
            try:
                logger.info(f"Terminating process {proc.pid}")
                proc.terminate()
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                logger.warning(f"Process {proc.pid} did not terminate, killing")
                proc.kill()
            except Exception as e:
                logger.error(f"Error terminating process {proc.pid}: {e}")


# Register cleanup function
atexit.register(cleanup)


def start_mcp_server():
    """Start the MCP server in stdio mode, properly connecting stdin/stdout"""
    logger.info("Starting MCP server in stdio mode...")

    # Ensure logs directory exists
    logs_dir = os.path.join(SCRIPT_DIR, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    # CORRECTION: We must connect our stdin/stdout to the MCP server process
    # for proper communication, but send stderr to a log file
    with open(
        os.path.join(logs_dir, "mcp_server_stderr.log"), "w"
    ) as stderr_log:
        proc = subprocess.Popen(
            [sys.executable, MCP_SERVER_SCRIPT],
            stdin=sys.stdin,  # Connect our stdin to the MCP server
            stdout=sys.stdout,  # Connect MCP server's output directly to our stdout
            stderr=stderr_log,  # Redirect stderr to a log file
            bufsize=0,  # Unbuffered communication
        )
        processes.append(proc)
        logger.info(f"MCP server started with PID: {proc.pid}")
        return proc


def main():
    """Start the servers and handle graceful shutdown"""
    try:
        # Start MCP server - this connects stdin/stdout directly
        mcp_proc = start_mcp_server()

        # Now simply wait for the MCP server to exit
        # Since we've connected stdin/stdout directly to the MCP server,
        # it will read from Cursor and write to Cursor without our interference
        exit_code = mcp_proc.wait()
        logger.info(f"MCP server exited with code: {exit_code}")
        return exit_code

    except KeyboardInterrupt:
        logger.info("Interrupted, shutting down servers...")
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
    finally:
        # Clean up all processes
        cleanup()

    return 0


if __name__ == "__main__":
    sys.exit(main())
