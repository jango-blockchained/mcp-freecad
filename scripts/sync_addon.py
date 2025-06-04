#!/usr/bin/env python3
"""
Sync FreeCAD addon using symlink for seamless development.

This script creates a symlink from the FreeCAD installation directory
to the development directory, ensuring changes are immediately available.
"""

import os
import shutil
import sys
from pathlib import Path

def create_symlink():
    """Create symlink from installation to development directory."""

    # Define paths
    dev_addon_dir = Path(__file__).parent.parent / "freecad-ai"
    install_addon_dir = Path.home() / ".local/share/FreeCAD/Mod/freecad-ai"
    backup_dir = Path.home() / ".freecad-ai/freecad-ai-backup"

    print(f"Development addon: {dev_addon_dir}")
    print(f"Installation target: {install_addon_dir}")

    if not dev_addon_dir.exists():
        print("❌ Development addon directory not found!")
        return False

    # Ensure parent directory exists
    install_addon_dir.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Handle existing installation
        if install_addon_dir.exists():
            if install_addon_dir.is_symlink():
                current_target = install_addon_dir.readlink()
                if current_target == dev_addon_dir:
                    print("✅ Symlink already exists and points to correct location")
                    return True
                else:
                    print(f"🔄 Updating symlink from {current_target} to {dev_addon_dir}")
                    install_addon_dir.unlink()
            else:
                # Backup existing directory
                if backup_dir.exists():
                    shutil.rmtree(backup_dir)
                shutil.move(str(install_addon_dir), str(backup_dir))
                print(f"✅ Backed up existing installation to {backup_dir}")

        # Create symlink
        install_addon_dir.symlink_to(dev_addon_dir)
        print(f"✅ Created symlink: {install_addon_dir} -> {dev_addon_dir}")

        # Verify symlink works
        if install_addon_dir.exists() and install_addon_dir.is_symlink():
            print("✅ Symlink verification successful")

            # Test Python syntax
            test_file = install_addon_dir / "freecad_ai_workbench.py"
            if test_file.exists():
                result = os.system(f"cd {install_addon_dir} && python -m py_compile freecad_ai_workbench.py")
                if result == 0:
                    print("✅ Python syntax validation passed")
                    return True
                else:
                    print("❌ Python syntax validation failed")
                    return False
            else:
                print("⚠️ Main workbench file not found, but symlink created")
                return True
        else:
            print("❌ Symlink creation failed")
            return False

    except Exception as e:
        print(f"❌ Error during symlink creation: {e}")
        return False

def main():
    """Main function."""
    print("🔗 Creating symlink for FreeCAD addon development...")

    if create_symlink():
        print("\n🎉 Symlink setup completed successfully!")
        print("✨ Benefits:")
        print("  • Changes in development directory are immediately available")
        print("  • No need to sync files manually")
        print("  • Always uses latest development version")
        print("\n📋 Next steps:")
        print("  1. Restart FreeCAD to load any changes")
        print("  2. Select 'FreeCAD AI' workbench")
        print("  3. Develop directly in the Git repository")
    else:
        print("\n💥 Symlink setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
