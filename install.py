#!/usr/bin/env python3
"""
Comprehensive Installer for MCP-FreeCAD Integration

This installer handles:
1. Installing FreeCAD addon to the correct location
2. Installing MCP server dependencies
3. Configuring VS Code to use the MCP server

Author: jango-blockchained
"""

import argparse
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional


class MCPInstaller:
    """Main installer class for MCP-FreeCAD integration"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.script_dir = Path(__file__).parent.resolve()
        self.addon_source = self.script_dir / "freecad-ai"
        self.os_name = platform.system()
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.success_messages: list[str] = []

    def log(self, message: str, level: str = "INFO"):
        """Log messages with formatting"""
        prefix = {
            "INFO": "ℹ️  ",
            "SUCCESS": "✅ ",
            "WARNING": "⚠️  ",
            "ERROR": "❌ ",
        }.get(level, "")

        print(f"{prefix}{message}")

        if level == "SUCCESS":
            self.success_messages.append(message)
        elif level == "WARNING":
            self.warnings.append(message)
        elif level == "ERROR":
            self.errors.append(message)

    # ==================== FreeCAD Addon Installation ====================

    def get_freecad_mod_path(self) -> Optional[Path]:
        """Get the FreeCAD user modules directory"""
        home = Path.home()

        if self.os_name == "Windows":
            return home / "AppData" / "Roaming" / "FreeCAD" / "Mod"
        elif self.os_name == "Darwin":
            return home / "Library" / "Preferences" / "FreeCAD" / "Mod"
        elif self.os_name == "Linux":
            # Try common Linux FreeCAD paths
            linux_paths = [
                home / ".local" / "share" / "FreeCAD" / "Mod",
                home / ".FreeCAD" / "Mod",
            ]
            for path in linux_paths:
                if path.exists() or path.parent.exists():
                    return path
            # Return first path as default
            return linux_paths[0]

        return None

    def install_freecad_addon(self) -> bool:
        """Install FreeCAD addon to the correct location"""
        self.log("Installing FreeCAD Addon...", "INFO")

        if not self.addon_source.exists():
            self.log(
                f"Addon source directory not found: {self.addon_source}", "ERROR"
            )
            return False

        freecad_mod_path = self.get_freecad_mod_path()
        if not freecad_mod_path:
            self.log(
                "Could not determine FreeCAD modules directory. "
                "Please install FreeCAD first.",
                "ERROR",
            )
            return False

        freecad_mod_path.mkdir(parents=True, exist_ok=True)
        addon_dest = freecad_mod_path / "MCPIntegration"

        try:
            # Remove existing addon if present
            if addon_dest.exists():
                self.log(f"Removing existing addon at {addon_dest}", "WARNING")
                if addon_dest.is_dir():
                    shutil.rmtree(addon_dest)
                else:
                    addon_dest.unlink()

            # Copy addon
            self.log(f"Copying addon from {self.addon_source} to {addon_dest}")
            shutil.copytree(self.addon_source, addon_dest)

            self.log(
                f"✓ FreeCAD addon installed successfully at {addon_dest}", "SUCCESS"
            )
            return True

        except (OSError, shutil.Error) as e:
            self.log(f"Failed to install FreeCAD addon: {e}", "ERROR")
            return False

    # ==================== MCP Server Dependencies ====================

    def install_mcp_dependencies(self) -> bool:
        """Install MCP server dependencies"""
        self.log("Installing MCP Server Dependencies...", "INFO")

        requirements_file = self.script_dir / "requirements.txt"

        if not requirements_file.exists():
            self.log(f"Requirements file not found: {requirements_file}", "ERROR")
            return False

        try:
            self.log("Installing Python packages from requirements.txt")
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
            )
            self.log("✓ MCP dependencies installed successfully", "SUCCESS")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"Failed to install MCP dependencies: {e}", "ERROR")
            return False

    # ==================== VS Code Configuration ====================

    def get_vscode_config_path(self) -> Optional[Path]:
        """Get the VS Code user configuration directory"""
        home = Path.home()

        paths = {
            "Windows": home / "AppData" / "Roaming" / "Code" / "User",
            "Darwin": home / "Library" / "Application Support" / "Code" / "User",
            "Linux": home / ".config" / "Code" / "User",
        }

        vscode_config = paths.get(self.os_name)
        if vscode_config and vscode_config.exists():
            return vscode_config

        return None

    def get_mcp_json_path(self) -> Optional[Path]:
        """Get the mcp.json configuration path"""
        vscode_config = self.get_vscode_config_path()
        if not vscode_config:
            return None

        return vscode_config / "mcp.json"

    def create_mcp_config(self) -> Dict:
        """Create the MCP server configuration for VS Code"""
        mcp_server_script = self.script_dir / "freecad-ai" / "mcp_server.py"

        config = {
            "mcpServers": {
                "freecad-mcp": {
                    "command": sys.executable,
                    "args": [str(mcp_server_script)],
                    "env": {
                        "PYTHONPATH": str(self.addon_source)
                        + ":"
                        + str(self.script_dir),
                        "MCP_DEBUG": "1",
                    },
                }
            }
        }

        return config

    def add_vscode_mcp_config(self) -> bool:
        """Add MCP configuration to VS Code mcp.json"""
        self.log("Configuring VS Code MCP...", "INFO")

        mcp_json_path = self.get_mcp_json_path()
        if not mcp_json_path:
            self.log(
                "Could not find VS Code configuration directory. "
                "VS Code may not be installed.",
                "WARNING",
            )
            return False

        try:
            # Load existing config if it exists
            if mcp_json_path.exists():
                with open(mcp_json_path, "r", encoding="utf-8") as f:
                    existing_config = json.load(f)
                self.log(f"Found existing mcp.json at {mcp_json_path}")
            else:
                existing_config = {}
                self.log(f"Creating new mcp.json at {mcp_json_path}")

            # Ensure mcpServers key exists
            if "mcpServers" not in existing_config:
                existing_config["mcpServers"] = {}

            # Create new MCP config
            new_mcp_config = self.create_mcp_config()
            new_servers = new_mcp_config.get("mcpServers", {})

            # Merge configurations
            for server_name, server_config in new_servers.items():
                existing_config["mcpServers"][server_name] = server_config
                self.log(
                    f"Added MCP server configuration: {server_name}",
                    "INFO",
                )

            # Write updated config
            mcp_json_path.parent.mkdir(parents=True, exist_ok=True)
            with open(mcp_json_path, "w", encoding="utf-8") as f:
                json.dump(existing_config, f, indent=2)

            self.log(
                f"✓ VS Code MCP configuration added successfully at "
                f"{mcp_json_path}",
                "SUCCESS",
            )
            return True

        except (OSError, json.JSONDecodeError) as e:
            self.log(f"Failed to configure VS Code: {e}", "ERROR")
            return False

    # ==================== Test & Verification ====================

    def test_mcp_server(self) -> bool:
        """Test if MCP server can be imported"""
        self.log("Testing MCP server...", "INFO")

        try:
            sys.path.insert(0, str(self.addon_source))
            __import__("mcp_server")

            self.log("✓ MCP server can be initialized successfully", "SUCCESS")
            return True
        except (ImportError, ModuleNotFoundError) as e:
            self.log(f"MCP server test failed: {e}", "WARNING")
            return False

    def test_addon_installation(self) -> bool:
        """Verify addon installation"""
        self.log("Verifying addon installation...", "INFO")

        freecad_mod_path = self.get_freecad_mod_path()
        if not freecad_mod_path:
            self.log("Could not verify FreeCAD addon installation", "WARNING")
            return False

        addon_path = freecad_mod_path / "MCPIntegration"
        if addon_path.exists():
            self.log(f"✓ Addon installation verified at {addon_path}", "SUCCESS")
            return True
        else:
            self.log(f"Addon not found at {addon_path}", "WARNING")
            return False

    # ==================== Main Installation Flow ====================

    def install(
        self,
        install_addon: bool = True,
        install_server: bool = True,
        configure_vscode: bool = True,
        test: bool = True,
    ) -> bool:
        """Run the complete installation"""
        self.log("=" * 60)
        self.log("MCP-FreeCAD Integration Installer", "INFO")
        self.log("=" * 60)

        results = {}

        if install_addon:
            results["addon"] = self.install_freecad_addon()

        if install_server:
            results["server"] = self.install_mcp_dependencies()

        if configure_vscode:
            results["vscode"] = self.add_vscode_mcp_config()

        if test:
            self.log("\n" + "=" * 60)
            self.log("Running Tests...", "INFO")
            self.log("=" * 60)
            results["mcp_test"] = self.test_mcp_server()
            results["addon_test"] = self.test_addon_installation()

        # Print summary
        self.print_summary(results)

        return all(results.values())

    def print_summary(self, results: Dict[str, bool]):
        """Print installation summary"""
        self.log("\n" + "=" * 60)
        self.log("Installation Summary", "INFO")
        self.log("=" * 60)

        for step, success in results.items():
            status = "✓ PASSED" if success else "✗ FAILED"
            self.log(f"{step}: {status}")

        if self.warnings:
            self.log("\nWarnings:", "WARNING")
            for warning in self.warnings:
                self.log(f"  - {warning}")

        if self.errors:
            self.log("\nErrors:", "ERROR")
            for error in self.errors:
                self.log(f"  - {error}")

        if self.success_messages:
            self.log("\nSuccess:", "SUCCESS")
            for msg in self.success_messages:
                self.log(f"  - {msg}")

        self.log("\n" + "=" * 60)
        if not self.errors:
            self.log("Installation completed successfully! 🎉", "SUCCESS")
            self.log("\nNext steps:")
            self.log("1. Restart FreeCAD to load the addon")
            self.log("2. Restart VS Code to activate the MCP server")
            self.log("3. Start using FreeCAD with AI assistance!")
        else:
            self.log(
                "Installation completed with errors. Please review above.",
                "ERROR",
            )
        self.log("=" * 60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Install MCP-FreeCAD Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python install.py                    # Full installation with tests
  python install.py --no-test          # Skip tests
  python install.py --addon-only       # Install FreeCAD addon only
  python install.py --server-only      # Install MCP server only
  python install.py --vscode-only      # Configure VS Code only
        """,
    )

    parser.add_argument(
        "--addon-only",
        action="store_true",
        help="Install FreeCAD addon only",
    )
    parser.add_argument(
        "--server-only",
        action="store_true",
        help="Install MCP server dependencies only",
    )
    parser.add_argument(
        "--vscode-only",
        action="store_true",
        help="Configure VS Code only",
    )
    parser.add_argument(
        "--no-test",
        action="store_true",
        help="Skip tests",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    args = parser.parse_args()

    # Determine what to install
    install_addon = not args.server_only and not args.vscode_only
    install_server = not args.addon_only and not args.vscode_only
    configure_vscode = not args.addon_only and not args.server_only
    run_tests = not args.no_test

    # Create installer and run
    installer = MCPInstaller(verbose=args.verbose)
    success = installer.install(
        install_addon=install_addon,
        install_server=install_server,
        configure_vscode=configure_vscode,
        test=run_tests,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
