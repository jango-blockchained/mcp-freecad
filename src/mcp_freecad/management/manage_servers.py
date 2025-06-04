#!/usr/bin/env python3
"""
Server Management Script for FreeCAD MCP Integration

This script helps to start, stop, and check the status of:
- FreeCAD Server (freecad_socket_server.py)
- MCP Server (freecad_mcp_server.py)

Usage:
  python manage_servers.py start [freecad|mcp|all]
  python manage_servers.py stop [freecad|mcp|all]
  python manage_servers.py status
  python manage_servers.py restart [freecad|mcp|all]
"""

import os
import sys
import subprocess
import argparse
import json
import socket
import time
import signal
import psutil

# Configuration
DEFAULT_CONFIG_PATH = "config.json"
FREECAD_SERVER_SCRIPT = "freecad_socket_server.py"
MCP_SERVER_SCRIPT = "src/mcp_freecad/server/freecad_mcp_server.py"
FREECAD_SERVER_LOG = "freecad_server_stdout.log"
FREECAD_SERVER_ERR_LOG = "freecad_server_stderr.log"
MCP_SERVER_LOG = "freecad_mcp_server_stdout.log"
MCP_SERVER_ERR_LOG = "freecad_mcp_server_stderr.log"


def load_config(config_path=DEFAULT_CONFIG_PATH):
    """Load configuration from file"""
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading config from {config_path}: {e}")
        return {
            "freecad": {"host": "localhost", "port": 12345},
            "server": {"host": "0.0.0.0", "port": 8000},
        }


def check_port(host, port):
    """Check if a port is in use"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        result = s.connect_ex((host, port))
        s.close()
        return result == 0
    except Exception as e:
        print(f"Error checking port {host}:{port}: {e}")
        return False


def find_pid_by_name(name):
    """Find process ID by name"""
    pids = []
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmdline = proc.info["cmdline"]
            if cmdline:
                if name in " ".join(cmdline):
                    pids.append(proc.info["pid"])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return pids


def start_freecad_server(config):
    """Start the FreeCAD server"""
    freecad_config = config.get("freecad", {})
    host = freecad_config.get("host", "localhost")
    port = freecad_config.get("port", 12345)

    # Check if already running
    if check_port(host, port):
        print(f"FreeCAD server already running on {host}:{port}")
        return True

    # Start server
    try:
        with open(FREECAD_SERVER_LOG, "w") as stdout_log, open(
            FREECAD_SERVER_ERR_LOG, "w"
        ) as stderr_log:
            process = subprocess.Popen(
                [
                    sys.executable,
                    FREECAD_SERVER_SCRIPT,
                    "--host",
                    host,
                    "--port",
                    str(port),
                    "--debug",
                ],
                stdout=stdout_log,
                stderr=stderr_log,
            )

        print(f"Started FreeCAD server (PID: {process.pid}) on {host}:{port}")

        # Wait for server to start
        time.sleep(2)
        if check_port(host, port):
            print("FreeCAD server is now accessible")
            return True
        else:
            print("Warning: FreeCAD server may not have started correctly")
            print(f"Check logs: {FREECAD_SERVER_LOG} and {FREECAD_SERVER_ERR_LOG}")
            return False

    except Exception as e:
        print(f"Error starting FreeCAD server: {e}")
        return False


def start_mcp_server(config):
    """Start the MCP server"""
    server_config = config.get("server", {})
    freecad_config = config.get("freecad", {})
    debug_flag = ["--debug"] if server_config.get("debug", False) else []

    # Start server
    try:
        with open(MCP_SERVER_LOG, "w") as stdout_log, open(
            MCP_SERVER_ERR_LOG, "w"
        ) as stderr_log:
            process = subprocess.Popen(
                [sys.executable, MCP_SERVER_SCRIPT, "--config", DEFAULT_CONFIG_PATH]
                + debug_flag,
                stdout=stdout_log,
                stderr=stderr_log,
            )

        print(f"Started MCP server (PID: {process.pid})")
        time.sleep(2)

        # Check if process is still running
        if psutil.pid_exists(process.pid):
            print("MCP server started successfully")
            return True
        else:
            print("Warning: MCP server may have failed to start")
            print(f"Check logs: {MCP_SERVER_LOG} and {MCP_SERVER_ERR_LOG}")
            return False

    except Exception as e:
        print(f"Error starting MCP server: {e}")
        return False


def stop_freecad_server():
    """Stop the FreeCAD server"""
    pids = find_pid_by_name(FREECAD_SERVER_SCRIPT)

    if not pids:
        print("FreeCAD server is not running")
        return True

    success = True
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"Stopped FreeCAD server (PID: {pid})")
        except Exception as e:
            print(f"Error stopping FreeCAD server (PID: {pid}): {e}")
            success = False

    return success


def stop_mcp_server():
    """Stop the MCP server"""
    pids = find_pid_by_name(MCP_SERVER_SCRIPT)

    if not pids:
        print("MCP server is not running")
        return True

    success = True
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"Stopped MCP server (PID: {pid})")
        except Exception as e:
            print(f"Error stopping MCP server (PID: {pid}): {e}")
            success = False

    return success


def check_status(config):
    """Check status of both servers"""
    freecad_config = config.get("freecad", {})
    server_config = config.get("server", {})

    # Check FreeCAD server
    host = freecad_config.get("host", "localhost")
    port = freecad_config.get("port", 12345)
    freecad_running = check_port(host, port)
    freecad_pids = find_pid_by_name(FREECAD_SERVER_SCRIPT)

    # Check MCP server
    mcp_pids = find_pid_by_name(MCP_SERVER_SCRIPT)

    print("\nServer Status:")
    print("--------------")
    print(f"FreeCAD Server: {'RUNNING' if freecad_running else 'NOT RUNNING'}")
    if freecad_pids:
        print(f"  - Process IDs: {', '.join(map(str, freecad_pids))}")
        print(f"  - Address: {host}:{port}")

    print(f"MCP Server: {'RUNNING' if mcp_pids else 'NOT RUNNING'}")
    if mcp_pids:
        print(f"  - Process IDs: {', '.join(map(str, mcp_pids))}")

    return freecad_running, bool(mcp_pids)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Manage FreeCAD MCP servers")
    parser.add_argument(
        "action",
        choices=["start", "stop", "status", "restart"],
        help="Action to perform",
    )
    parser.add_argument(
        "target",
        nargs="?",
        choices=["freecad", "mcp", "all"],
        default="all",
        help="Target server (default: all)",
    )
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG_PATH,
        help=f"Path to config file (default: {DEFAULT_CONFIG_PATH})",
    )

    args = parser.parse_args()
    config = load_config(args.config)

    if args.action == "status":
        check_status(config)

    elif args.action == "start":
        if args.target in ["freecad", "all"]:
            start_freecad_server(config)

        if args.target in ["mcp", "all"]:
            start_mcp_server(config)

    elif args.action == "stop":
        if args.target in ["freecad", "all"]:
            stop_freecad_server()

        if args.target in ["mcp", "all"]:
            stop_mcp_server()

    elif args.action == "restart":
        if args.target in ["freecad", "all"]:
            stop_freecad_server()
            time.sleep(1)
            start_freecad_server(config)

        if args.target in ["mcp", "all"]:
            stop_mcp_server()
            time.sleep(1)
            start_mcp_server(config)


if __name__ == "__main__":
    main()
