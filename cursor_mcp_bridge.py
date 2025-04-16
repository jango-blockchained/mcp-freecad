#!/usr/bin/env python3
"""
Cursor MCP Bridge for FreeCAD

This script launches the FreeCAD MCP server in stdio mode for Cursor integration.
All debugging/info messages are redirected to stderr, keeping stdout clean for JSON-only communication.
"""

import os
import sys
import subprocess
import threading
import time
import signal
import logging
import atexit

# Configure logging to stderr only (keep stdout clean for JSON)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr  # Send all logging to stderr, not stdout
)
logger = logging.getLogger("cursor_mcp_bridge")

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FREECAD_SERVER_SCRIPT = os.path.join(SCRIPT_DIR, "freecad_socket_server.py")
MCP_SERVER_SCRIPT = os.path.join(SCRIPT_DIR, "src", "mcp_freecad", "server", "freecad_mcp_server.py")

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

def start_freecad_server():
    """Start the FreeCAD socket server, redirecting output to stderr and log files"""
    logger.info("Starting FreeCAD server...")

    # Prepare log files
    with open(os.path.join(SCRIPT_DIR, "freecad_server_stdout.log"), "w") as stdout_log, \
         open(os.path.join(SCRIPT_DIR, "freecad_server_stderr.log"), "w") as stderr_log:

        # Start the process, redirecting stdout and stderr to log files and stderr
        proc = subprocess.Popen(
            [sys.executable, FREECAD_SERVER_SCRIPT, "--debug"],
            stdout=subprocess.PIPE,  # Capture stdout
            stderr=subprocess.PIPE,  # Capture stderr
            text=True
        )
        processes.append(proc)

        # Redirect outputs to logs and stderr (not stdout)
        def process_output(stream, logfile, prefix):
            for line in iter(stream.readline, ''):
                logger.info(f"{prefix}: {line.strip()}")
                logfile.write(line)
                logfile.flush()

        # Start threads to handle outputs
        threading.Thread(
            target=process_output,
            args=(proc.stdout, stdout_log, "FreeCAD stdout"),
            daemon=True
        ).start()

        threading.Thread(
            target=process_output,
            args=(proc.stderr, stderr_log, "FreeCAD stderr"),
            daemon=True
        ).start()

        logger.info(f"FreeCAD server started with PID: {proc.pid}")
        return proc

def start_mcp_server():
    """Start the MCP server in stdio mode, properly connecting stdin/stdout"""
    logger.info("Starting MCP server in stdio mode...")

    # CORRECTION: We must connect our stdin/stdout to the MCP server process
    # for proper communication, but send stderr to a log file
    with open(os.path.join(SCRIPT_DIR, "mcp_server_stderr.log"), "w") as stderr_log:
        proc = subprocess.Popen(
            [sys.executable, MCP_SERVER_SCRIPT],
            stdin=sys.stdin,     # Connect our stdin to the MCP server
            stdout=sys.stdout,   # Connect MCP server's output directly to our stdout
            stderr=stderr_log,   # Redirect stderr to a log file
            bufsize=0,           # Unbuffered communication
        )
        processes.append(proc)
        logger.info(f"MCP server started with PID: {proc.pid}")
        return proc

def main():
    """Start the servers and handle graceful shutdown"""
    # Start FreeCAD server first
    try:
        freecad_proc = start_freecad_server()

        # Wait for FreeCAD server to initialize
        logger.info("Waiting for FreeCAD server to initialize...")
        time.sleep(2)

        # Check if FreeCAD server started successfully
        if freecad_proc.poll() is not None:
            logger.error(f"FreeCAD server failed to start (exit code: {freecad_proc.returncode})")
            return 1

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
