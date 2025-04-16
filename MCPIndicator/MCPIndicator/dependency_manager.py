import os
import sys
import subprocess
import time
import platform
import FreeCAD
from PySide2 import QtWidgets, QtCore

class DependencyManager:
    """Manages installation of Python dependencies for the MCP Indicator."""

    def __init__(self):
        """Initialize the DependencyManager."""
        self.params = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/MCPIndicator")

    def install_dependencies(self):
        """Show a dialog with pip dependency installation UI."""
        dialog = QtWidgets.QDialog()
        dialog.setWindowTitle("Install MCP Server Dependencies")
        dialog.setMinimumWidth(600)
        dialog.setMinimumHeight(400)

        layout = QtWidgets.QVBoxLayout(dialog)

        # Create a group box for MCP server dependencies
        mcp_group = QtWidgets.QGroupBox("MCP Server Dependencies")
        mcp_layout = QtWidgets.QVBoxLayout(mcp_group)

        mcp_info = QtWidgets.QLabel(
            "The MCP server requires Python packages: fastapi, uvicorn, loguru, beautifulsoup4, and more.\n"
            "You can install these automatically using pip, or manually if automatic installation fails."
        )
        mcp_info.setWordWrap(True)
        mcp_layout.addWidget(mcp_info)

        mcp_status = QtWidgets.QLabel("Status: Ready to install")
        mcp_layout.addWidget(mcp_status)

        # Use a monospace font for the log
        log_text = QtWidgets.QTextEdit()
        log_text.setReadOnly(True)
        font = log_text.font()
        font.setFamily("Courier")
        log_text.setFont(font)
        log_text.setMinimumHeight(150)
        mcp_layout.addWidget(log_text)

        # Button for installing dependencies
        mcp_button_layout = QtWidgets.QHBoxLayout()
        install_btn = QtWidgets.QPushButton("Install MCP Dependencies")
        install_btn.clicked.connect(
            lambda: self._run_pip_install(
                ["fastapi", "uvicorn", "loguru", "beautifulsoup4", "openai",
                 "pydantic", "python-multipart", "psutil"],
                log_text,
                mcp_status,
                install_btn,
            )
        )
        mcp_button_layout.addWidget(install_btn)

        # Optional --break-system-packages for newer pip (21+)
        use_break_option = False
        try:
            pip_version = subprocess.check_output([sys.executable, "-m", "pip", "--version"]).decode().strip()
            version_part = pip_version.split()[1]
            major_version = int(version_part.split(".")[0])
            if major_version >= 21:
                use_break_option = True
                break_system_check = QtWidgets.QCheckBox("Use --break-system-packages (for pip 21+)")
                break_system_check.setChecked(False)
                mcp_button_layout.addWidget(break_system_check)

                # Update the install button click handler
                install_btn.clicked.disconnect()
                install_btn.clicked.connect(
                    lambda: self._run_pip_install(
                        ["fastapi", "uvicorn", "loguru", "beautifulsoup4", "openai",
                         "pydantic", "python-multipart", "psutil"],
                        log_text,
                        mcp_status,
                        install_btn,
                        break_system_check.isChecked()
                    )
                )
        except:
            # Couldn't determine pip version, leave as is
            pass

        manual_btn = QtWidgets.QPushButton("Show Manual Install Commands")
        manual_btn.clicked.connect(lambda: self._show_manual_install_instructions(log_text))
        mcp_button_layout.addWidget(manual_btn)

        mcp_layout.addLayout(mcp_button_layout)
        layout.addWidget(mcp_group)

        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        # Show the dialog
        dialog.exec_()

    def _run_pip_install(self, packages, log_text, status_label, install_btn, break_system_packages=False):
        """Run pip install for the given packages."""
        status_label.setText("Status: Installing...")
        log_text.clear()
        install_btn.setEnabled(False)

        # Create a QProcess
        process = QtCore.QProcess()

        # Function to handle output
        def handle_output():
            data = process.readAllStandardOutput().data().decode("utf-8", errors="replace")
            log_text.append(data)
            # Scroll to bottom
            cursor = log_text.textCursor()
            cursor.movePosition(QtWidgets.QTextCursor.End)
            log_text.setTextCursor(cursor)

        # Function to handle error
        def handle_error():
            data = process.readAllStandardError().data().decode("utf-8", errors="replace")
            log_text.append(data)
            # Scroll to bottom
            cursor = log_text.textCursor()
            cursor.movePosition(QtWidgets.QTextCursor.End)
            log_text.setTextCursor(cursor)

        # Function to handle process finished
        def handle_finished(exit_code, exit_status):
            install_btn.setEnabled(True)
            if exit_code == 0:
                status_label.setText("Status: Installation completed successfully")
                log_text.append("\nDependencies installed successfully.\n")
            else:
                status_label.setText("Status: Installation failed")
                log_text.append("\nInstallation failed. Check the log for errors.\n")
                log_text.append("Try using the 'Show Manual Install Commands' option.\n")

        # Connect signals
        process.readyReadStandardOutput.connect(handle_output)
        process.readyReadStandardError.connect(handle_error)
        process.finished.connect(handle_finished)

        # Set up the command
        cmd = [sys.executable, "-m", "pip", "install"]
        if break_system_packages:
            cmd.append("--break-system-packages")
        cmd.extend(packages)

        # Start the process
        log_text.append(f"Running: {' '.join(cmd)}\n")
        log_text.append(f"Python executable: {sys.executable}\n")
        log_text.append(f"Platform: {platform.platform()}\n")
        process.start(cmd[0], cmd[1:])

    def _show_manual_install_instructions(self, log_text):
        """Show manual installation instructions in the log text area."""
        log_text.clear()
        log_text.append("# Manual Installation Instructions:\n\n")
        log_text.append("1. Open a terminal (command prompt on Windows)\n")
        log_text.append("2. Ensure you are using the Python environment associated with FreeCAD, or install globally.\n")
        log_text.append("3. Run the following command:\n\n")

        # Include psutil in manual command
        cmd = f"{sys.executable} -m pip install fastapi uvicorn loguru beautifulsoup4 openai pydantic python-multipart psutil"
        log_text.append(f"{cmd}\n\n")

        log_text.append("4. If you're using pip 21 or later and need to install to system Python, try:\n\n")
        log_text.append(f"{cmd} --break-system-packages\n\n")

        log_text.append("5. If using a virtual environment, activate it first:\n")
        if platform.system() == "Windows":
            log_text.append("   .venv\\Scripts\\activate  # Windows\n")
        else:
            log_text.append("   source .venv/bin/activate  # Linux/Mac\n")
        log_text.append("   Then run the pip install command above.\n")
