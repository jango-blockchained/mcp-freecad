#!/usr/bin/env python3
"""
FreeCAD MCP Troubleshooter

This script helps diagnose and fix common issues with the FreeCAD MCP integration.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def log(message, level="INFO"):
    """Print a log message with a level prefix"""
    print(f"[{level}] {message}")


def check_config():
    """Check if the config.json file exists and has valid FreeCAD settings"""
    log("Checking configuration...")

    if not os.path.exists("config.json"):
        log("config.json not found. Creating a default configuration.", "WARNING")
        return False

    try:
        with open("config.json", "r") as f:
            config = json.load(f)
    except json.JSONDecodeError:
        log("config.json is not valid JSON. Please check the file format.", "ERROR")
        return False

    if "freecad" not in config:
        log("FreeCAD configuration not found in config.json", "ERROR")
        return False

    freecad_config = config["freecad"]

    # Check required fields
    required_fields = ["path", "python_path", "module_path", "host", "port"]
    missing_fields = [field for field in required_fields if field not in freecad_config]

    if missing_fields:
        log(
            f"Missing required configuration fields: {', '.join(missing_fields)}",
            "ERROR",
        )
        return False

    # Check if path exists
    path = freecad_config.get("path", "")
    if not os.path.exists(path):
        log(f"FreeCAD path does not exist: {path}", "ERROR")
        return False

    # Check if using AppRun mode
    use_apprun = freecad_config.get("use_apprun", False)
    if use_apprun:
        apprun_path = freecad_config.get("apprun_path", "")
        if not os.path.exists(apprun_path):
            log(f"AppRun path does not exist: {apprun_path}", "ERROR")
            return False
        else:
            log(f"AppRun path exists: {apprun_path}")

    log("Configuration validated successfully")
    return True


def check_freecad_installation():
    """Check if FreeCAD is properly installed and accessible"""
    log("Checking FreeCAD installation...")

    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            freecad_config = config.get("freecad", {})
    except Exception:
        log("Failed to read config.json", "ERROR")
        return False

    # Check FreeCAD executable
    freecad_path = freecad_config.get("path", "")
    if not os.path.exists(freecad_path):
        log(f"FreeCAD executable not found at: {freecad_path}", "ERROR")
        return False

    # Check AppRun if applicable
    use_apprun = freecad_config.get("use_apprun", False)
    if use_apprun:
        apprun_path = freecad_config.get("apprun_path", "")
        if not os.path.exists(apprun_path):
            log(f"AppRun not found at: {apprun_path}", "ERROR")
            return False

        # Try running AppRun with --version
        try:
            result = subprocess.run(
                [apprun_path, "--version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                log(f"AppRun failed to run: {result.stderr}", "ERROR")
                return False
            log(f"AppRun version check successful: {result.stdout.strip()}")
        except subprocess.TimeoutExpired:
            log("AppRun version check timed out", "ERROR")
            return False
        except Exception as e:
            log(f"Failed to run AppRun: {str(e)}", "ERROR")
            return False

    log("FreeCAD installation appears to be valid")
    return True


def check_script_files():
    """Check if the necessary script files exist and are accessible"""
    log("Checking script files...")

    required_files = [
        "freecad_connection.py",
        "freecad_connection_launcher.py",
        "freecad_launcher_script.py",
        "freecad_connection_bridge.py",
    ]

    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)

    if missing_files:
        log(f"Missing required script files: {', '.join(missing_files)}", "ERROR")
        return False

    log("All required script files found")
    return True


def check_backup_files():
    """Check for .bak files that might be causing issues"""
    log("Checking for backup files...")

    backup_files = list(Path(".").glob("**/*.bak"))
    if backup_files:
        log(
            f"Found {len(backup_files)} backup files that might cause issues:",
            "WARNING",
        )
        for file in backup_files[:10]:  # Show first 10 only if there are many
            log(f"  - {file}", "WARNING")

        if len(backup_files) > 10:
            log(f"  (and {len(backup_files) - 10} more...)", "WARNING")

        print("\nWould you like to delete these backup files? (y/n): ", end="")
        choice = input().strip().lower()
        if choice == "y":
            for file in backup_files:
                try:
                    os.remove(file)
                    log(f"Deleted: {file}")
                except Exception as e:
                    log(f"Failed to delete {file}: {e}", "ERROR")
    else:
        log("No backup files found")

    return True


def check_launcher_script():
    """Test the launcher script directly"""
    log("Testing launcher script...")

    try:
        with open("config.json", "r") as f:
            config = json.load(f)
            freecad_config = config.get("freecad", {})
    except Exception:
        log("Failed to read config.json", "ERROR")
        return False

    use_apprun = freecad_config.get("use_apprun", False)
    freecad_path = freecad_config.get("path", "")
    apprun_path = freecad_config.get("apprun_path", "")
    script_path = os.path.abspath("freecad_launcher_script.py")

    if not os.path.exists(script_path):
        log(f"Launcher script not found at: {script_path}", "ERROR")
        return False

    # Set up the command
    if use_apprun and os.path.exists(apprun_path):
        cmd = [apprun_path, script_path, "--", "get_version", "{}"]
    elif os.path.exists(freecad_path):
        cmd = [freecad_path, "--console", script_path, "--", "get_version", "{}"]
    else:
        log("No valid FreeCAD path found for testing", "ERROR")
        return False

    log(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            log(f"Launcher script failed with code {result.returncode}", "ERROR")
            log(f"STDERR: {result.stderr}")
            return False

        log(f"STDOUT: {result.stdout}")

        # Try to extract JSON from output
        for line in reversed(result.stdout.strip().split("\n")):
            if line.strip().startswith("{") and line.strip().endswith("}"):
                try:
                    version_info = json.loads(line)
                    log(f"Successfully retrieved version: {version_info}")
                    return True
                except json.JSONDecodeError:
                    continue

        log("No valid JSON found in output", "ERROR")
        return False
    except subprocess.TimeoutExpired:
        log("Launcher script execution timed out", "ERROR")
        return False
    except Exception as e:
        log(f"Error running launcher script: {e}", "ERROR")
        return False


def fix_permissions():
    """Fix permissions on script files"""
    log("Fixing script file permissions...")

    script_files = [
        "freecad_connection_launcher.py",
        "freecad_launcher_script.py",
        "scripts/troubleshoot_freecad.py",
    ]

    for file in script_files:
        if os.path.exists(file):
            try:
                os.chmod(file, 0o755)  # rwxr-xr-x
                log(f"Fixed permissions for {file}")
            except Exception as e:
                log(f"Failed to fix permissions for {file}: {e}", "ERROR")

    return True


def main():
    """Main function"""
    log("FreeCAD MCP Troubleshooter")
    log(f"System: {platform.system()} {platform.release()}")
    log(f"Python: {sys.version}")
    print()

    # Run checks
    config_ok = check_config()
    freecad_ok = check_freecad_installation()
    scripts_ok = check_script_files()
    fix_permissions()
    backup_ok = check_backup_files()

    # Only run launcher test if other checks pass
    if config_ok and freecad_ok and scripts_ok:
        launcher_ok = check_launcher_script()
    else:
        launcher_ok = False
        log("Skipping launcher test due to previous failures", "WARNING")

    # Print summary
    print("\n" + "=" * 60)
    log("Troubleshooting Summary:")
    log(f"Configuration: {'✅ OK' if config_ok else '❌ FAILED'}")
    log(f"FreeCAD Installation: {'✅ OK' if freecad_ok else '❌ FAILED'}")
    log(f"Script Files: {'✅ OK' if scripts_ok else '❌ FAILED'}")
    log(f"Backup Files: {'✅ CHECKED' if backup_ok else '❌ FAILED'}")
    log(f"Launcher Test: {'✅ OK' if launcher_ok else '❌ FAILED'}")
    print("=" * 60)

    if all([config_ok, freecad_ok, scripts_ok, launcher_ok]):
        log("All checks passed. The system should be functioning correctly.")
    else:
        log(
            "Some checks failed. Please review the errors above and fix them.",
            "WARNING",
        )


if __name__ == "__main__":
    main()
