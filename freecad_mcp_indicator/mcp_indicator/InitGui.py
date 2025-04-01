import os
import FreeCAD
import FreeCADGui
from PySide2 import QtCore, QtGui, QtWidgets
import subprocess
import sys
import inspect
import socket
import time

# Remove global path calculations and move to __init__
PYTHON_EXECUTABLE = sys.executable

class MCPIndicatorWorkbench(FreeCADGui.Workbench):
    """MCP Connection Indicator Workbench"""
    
    MenuText = "MCP Indicator"
    ToolTip = "Shows MCP connection status and controls server"
    Icon = """
/* XPM */
static char * mcp_icon_xpm[] = {
"16 16 3 1",
" 	c None",
".	c #000000",
"+	c #FFFFFF",
"                ",
"     ......     ",
"   ..++++++..   ",
"  .+++++++++++. ",
" .+++++..+++++. ",
".++++.  ..++++. ",
".+++.    .++++. ",
".+++.    .++++. ",
".+++.    .++++. ",
".++++.  ..++++. ",
" .+++++..+++++. ",
"  .+++++++++++. ",
"   ..++++++..   ",
"     ......     ",
"                ",
"                "};
"""
    
    def __init__(self):
        # Get stored path from FreeCAD parameters, or start with empty string
        self.params = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/MCPIndicator")
        self.SERVER_SCRIPT_PATH = self.params.GetString("ServerScriptPath", "")
        
        # If not already set, try to determine a default path
        if not self.SERVER_SCRIPT_PATH:
            try:
                # Try to find the freecad_server.py in the parent directory of the addon
                current_file_path = inspect.getfile(inspect.currentframe())
                current_dir = os.path.dirname(current_file_path)
                # Go up two levels to get to potential project root
                indicator_root = os.path.dirname(current_dir)
                project_root = os.path.dirname(indicator_root)
                
                # Try common locations for the server script
                possible_paths = [
                    os.path.join(project_root, "freecad_server.py"),
                    # Add more potential paths here, like:
                    os.path.join(os.path.expanduser("~"), "Git", "mcp-freecad", "freecad_server.py"),
                    "/usr/local/bin/freecad_server.py"
                ]
                
                # Use the first one that exists
                for path in possible_paths:
                    if os.path.exists(path):
                        self.SERVER_SCRIPT_PATH = path
                        # Store this discovered path
                        self.params.SetString("ServerScriptPath", path)
                        break
                        
            except Exception as e:
                FreeCAD.Console.PrintError(f"Error determining server path: {str(e)}\n")
                
        # Log server path (whether found, set by user, or empty)
        if self.SERVER_SCRIPT_PATH:
            FreeCAD.Console.PrintMessage(f"Server script path: {self.SERVER_SCRIPT_PATH}\n")
        else:
            FreeCAD.Console.PrintWarning("Server script path not set. Use Settings to configure.\n")
            
        self._control_button = None
        self._server_process = None
        self._timer = None
        self._connection_status = False
        self._server_running = False # Track server running separately from process
        
    def Initialize(self):
        """Initialize the workbench"""
        # Import necessary PySide modules locally for this scope
        from PySide2 import QtWidgets, QtCore # Add QtCore here
        
        # Create the control button
        self._control_button = QtWidgets.QToolButton()
        self._control_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self._control_button.setFixedSize(24, 24)
        self._control_button.setToolTip("Server: Stopped\nMCP: Disconnected")
        self._control_button.setAutoRaise(True)

        # Create menu and actions
        self._control_menu = QtWidgets.QMenu(self._control_button)
        
        # Add settings action first
        self._settings_action = QtWidgets.QAction("Settings...", self._control_menu)
        self._settings_action.triggered.connect(self._show_settings)
        self._control_menu.addAction(self._settings_action)
        
        # Add install dependencies action
        self._install_deps_action = QtWidgets.QAction("Install Dependencies...", self._control_menu)
        self._install_deps_action.triggered.connect(self._install_dependencies)
        self._control_menu.addAction(self._install_deps_action)
        
        # Add separator
        self._control_menu.addSeparator()
        
        # Create server control actions
        self._start_action = QtWidgets.QAction("Start Server (Standalone)", self._control_menu)
        self._start_action.triggered.connect(lambda: self._start_server(connect_mode=False))
        self._control_menu.addAction(self._start_action)

        # Add start with connect mode
        self._start_connect_action = QtWidgets.QAction("Start Server (Connect to FreeCAD)", self._control_menu)
        self._start_connect_action.triggered.connect(lambda: self._start_server(connect_mode=True))
        self._control_menu.addAction(self._start_connect_action)

        self._stop_action = QtWidgets.QAction("Stop Server", self._control_menu)
        self._stop_action.triggered.connect(self._stop_server)
        self._stop_action.setEnabled(False)
        self._control_menu.addAction(self._stop_action)

        self._restart_action = QtWidgets.QAction("Restart Server", self._control_menu)
        self._restart_action.triggered.connect(self._restart_server)
        self._restart_action.setEnabled(False)
        self._control_menu.addAction(self._restart_action)

        self._control_button.setMenu(self._control_menu)
        
        # Update both server and MCP indicator states
        self._update_indicator_icon()
        
        # Add button to status bar
        mw = FreeCADGui.getMainWindow()
        if mw:
            statusbar = mw.statusBar()
            statusbar.addPermanentWidget(self._control_button)
            
        # Setup timer for periodic connection check
        self._timer = QtCore.QTimer() # Now QtCore should be defined
        self._timer.timeout.connect(self._check_status)
        self._timer.start(5000)

        # Initial check
        self._check_status()
        self._update_action_states()
        
    def _show_settings(self):
        """Show settings dialog to configure server path"""
        # Import locally to ensure Qt modules are available
        from PySide2 import QtWidgets, QtCore, QtGui
        
        # Create dialog
        dialog = QtWidgets.QDialog(FreeCADGui.getMainWindow())
        dialog.setWindowTitle("MCP Indicator Settings")
        dialog.setMinimumWidth(400)
        
        # Create layout
        layout = QtWidgets.QVBoxLayout()
        dialog.setLayout(layout)
        
        # Add path field with browse button
        path_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(path_layout)
        
        # Label for server path
        path_label = QtWidgets.QLabel("Server Script Path:")
        path_layout.addWidget(path_label)
        
        # Text field for path
        self.path_field = QtWidgets.QLineEdit()
        self.path_field.setText(self.SERVER_SCRIPT_PATH)
        path_layout.addWidget(self.path_field)
        
        # Browse button
        browse_button = QtWidgets.QPushButton("Browse...")
        browse_button.clicked.connect(self._browse_server_path)
        path_layout.addWidget(browse_button)
        
        # Add button box
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        # Show dialog and process result
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            # Save the path
            new_path = self.path_field.text()
            self.SERVER_SCRIPT_PATH = new_path
            # Store in FreeCAD parameters
            self.params.SetString("ServerScriptPath", new_path)
            FreeCAD.Console.PrintMessage(f"Server script path set to: {new_path}\n")
            
            # Update UI based on new path
            self._update_action_states()

    def _browse_server_path(self):
        """Open file dialog to select server script"""
        from PySide2 import QtWidgets
        
        # Start in the directory of the current path, or home dir if empty
        start_dir = os.path.dirname(self.SERVER_SCRIPT_PATH) if self.SERVER_SCRIPT_PATH else os.path.expanduser("~")
        
        # Open file dialog
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            FreeCADGui.getMainWindow(),
            "Select FreeCAD Server Script",
            start_dir,
            "Python Scripts (*.py);;All Files (*.*)"
        )
        
        if file_path:
            self.path_field.setText(file_path)
        
    def Activated(self):
        """Called when workbench is activated"""
        pass
        
    def Deactivated(self):
        """Called when workbench is deactivated"""
        if self._server_process:
             FreeCAD.Console.PrintMessage("MCPIndicatorWorkbench deactivated, consider stopping the server manually if needed.\n")
        pass

    def _is_server_running(self):
        """Check if the server process is running."""
        try:
            return bool(self._server_process is not None and self._server_process.poll() is None)
        except Exception:
            return False

    def _update_action_states(self):
        """Enable/disable actions based on server state."""
        try:
            running = bool(self._server_running)  # Ensure boolean
            
            # Check if path is set
            path_exists = bool(self.SERVER_SCRIPT_PATH)
            
            if self._start_action:  # Check if actions exist
                # Only enable start if path is set and server not running
                self._start_action.setEnabled(not running and path_exists)
                
            if self._start_connect_action:
                # Only enable connect start if path is set and server not running
                self._start_connect_action.setEnabled(not running and path_exists)
                
            if self._stop_action:
                # Enable stop if server is running
                self._stop_action.setEnabled(running)
                
            if self._restart_action:
                # Only enable restart if path is set and server is running
                self._restart_action.setEnabled(running and path_exists)
                
            self._update_tooltip()
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"Error updating action states: {str(e)}\n")

    def _update_tooltip(self):
        """Update the button's tooltip based on server status."""
        server_status = "Running" if self._server_running else "Stopped"
        path_status = "Path Set" if self.SERVER_SCRIPT_PATH else "Path Not Set"
        self._control_button.setToolTip(f"Server: {server_status}\n{path_status}")

    def _start_server(self, connect_mode=False):
        """Start the freecad_server.py script."""
        # Local imports to ensure modules are available in this scope
        import subprocess
        import os
        import sys
        import socket
        import time
        from PySide2 import QtCore, QtWidgets
        
        if self._is_server_running():
            FreeCAD.Console.PrintMessage("Server is already running.\n")
            return

        if not self.SERVER_SCRIPT_PATH or not os.path.exists(self.SERVER_SCRIPT_PATH):
             FreeCAD.Console.PrintError(f"Server script not found: {self.SERVER_SCRIPT_PATH}\n")
             return
        
        # Check for wrapper script existence
        server_dir = os.path.dirname(self.SERVER_SCRIPT_PATH)
        wrapper_script = os.path.join(server_dir, "run_freecad_server.sh")
        use_wrapper = os.path.exists(wrapper_script) and os.access(wrapper_script, os.X_OK)
        
        if use_wrapper:
            FreeCAD.Console.PrintMessage(f"Found wrapper script: {wrapper_script}\n")
        else:
            # Find a proper Python executable, not FreeCAD itself
            # Try common Python executable locations
            python_candidates = [
                '/usr/bin/python3',
                '/usr/local/bin/python3',
                '/usr/bin/python',
                os.path.join(os.path.dirname(sys.executable), 'python3'),
                os.path.join(sys.prefix, 'bin', 'python3'),
            ]
            
            python_exec = None
            for candidate in python_candidates:
                if os.path.exists(candidate):
                    python_exec = candidate
                    break
            
            if not python_exec:
                FreeCAD.Console.PrintError("Could not find Python executable. Please install Python.\n")
                return
             
        try:
            # Check if port is already in use (default port 12345)
            port_in_use = False
            try:
                # Try to bind to the port to see if it's available
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind(('localhost', 12345))
                s.close()
            except socket.error:
                port_in_use = True
            
            # If port is in use, ask user what to do
            if port_in_use:
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Warning)
                msg.setText("The server port (12345) is already in use.")
                msg.setInformativeText("There may be another server running. What would you like to do?")
                killButton = msg.addButton("Kill Existing && Start New", QtWidgets.QMessageBox.ActionRole)
                cancelButton = msg.addButton(QtWidgets.QMessageBox.Cancel)
                msg.setDefaultButton(killButton)
                msg.exec_()
                
                if msg.clickedButton() == killButton:
                    # Try to kill existing processes
                    try:
                        # Find processes using the freecad_server.py script
                        cmd = f"pkill -f \"python.*{os.path.basename(self.SERVER_SCRIPT_PATH)}\""
                        subprocess.run(cmd, shell=True)
                        FreeCAD.Console.PrintMessage("Killed existing server processes.\n")
                        # Wait a moment for the process to die and port to be freed
                        time.sleep(1)
                    except Exception as e:
                        FreeCAD.Console.PrintError(f"Failed to kill existing processes: {str(e)}\n")
                        return
                else:
                    # User cancelled
                    return
            
            # Determine if we should run in connect mode
            mode_text = "connect mode" if connect_mode else "standalone mode"
            
            # Create log files in the same directory as the server script
            log_dir = os.path.dirname(self.SERVER_SCRIPT_PATH)
            stdout_log = os.path.join(log_dir, "freecad_server_stdout.log")
            stderr_log = os.path.join(log_dir, "freecad_server_stderr.log")
            
            # Create a modified environment with a variable to prevent GUI
            env = dict(os.environ)
            env['FREECAD_NO_GUI'] = '1'  # Custom environment variable to signal no GUI
            env['PYTHONUNBUFFERED'] = '1'  # Ensure Python output is unbuffered
            
            # Set up command with appropriate arguments
            if use_wrapper:
                FreeCAD.Console.PrintMessage(f"Starting server using wrapper script: {wrapper_script}\n")
                server_cmd = [wrapper_script]
                # The wrapper script already includes --connect, so only add it if not in connect mode
                if not connect_mode:
                    server_cmd.append("--no-connect")
            else:
                FreeCAD.Console.PrintMessage(f"Starting server in {mode_text}: {self.SERVER_SCRIPT_PATH} with Python: {python_exec}...\n")
                server_cmd = [python_exec, self.SERVER_SCRIPT_PATH]
                # Add connect flag if requested
                if connect_mode:
                    server_cmd.append("--connect")
            
            # Open log files
            with open(stdout_log, 'w') as out, open(stderr_log, 'w') as err:
                # Start the server process
                self._server_process = subprocess.Popen(
                    server_cmd,
                    stdout=out,
                    stderr=err,
                    bufsize=1,
                    env=env,
                    cwd=os.path.dirname(self.SERVER_SCRIPT_PATH)
                )
            
            FreeCAD.Console.PrintMessage(f"Server started with PID: {self._server_process.pid}\n")
            FreeCAD.Console.PrintMessage(f"Stdout log: {stdout_log}\n")
            FreeCAD.Console.PrintMessage(f"Stderr log: {stderr_log}\n")
            
            # Give the server a moment to start up
            QtCore.QTimer.singleShot(1000, self._check_server_status)
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"Failed to start server: {str(e)}\n")
            self._server_process = None
        
        self._update_action_states()

    def _check_server_status(self):
        """Check if the server started successfully by checking its process status."""
        if not self._server_process:
            return
            
        # Check if process is still running
        if self._server_process.poll() is not None:
            # Process has terminated
            FreeCAD.Console.PrintError(f"Server process terminated unexpectedly with code: {self._server_process.poll()}\n")
            self._server_process = None
            self._update_action_states()
            return
            
        # If we get here, the process is still running
        FreeCAD.Console.PrintMessage("Server startup completed.\n")

    def _stop_server(self):
        """Stop the running freecad_server.py script."""
        # Local import to ensure module is available in this scope
        import subprocess
        
        if not self._is_server_running():
            FreeCAD.Console.PrintMessage("Server is not running.\n")
            return
            
        try:
            FreeCAD.Console.PrintMessage(f"Stopping server (PID: {self._server_process.pid})...\n")
            self._server_process.terminate()
            try:
                self._server_process.wait(timeout=2)
                FreeCAD.Console.PrintMessage("Server stopped.\n")
            except subprocess.TimeoutExpired:
                FreeCAD.Console.PrintWarning("Server did not terminate gracefully, killing...\n")
                self._server_process.kill()
                self._server_process.wait()
                FreeCAD.Console.PrintMessage("Server killed.\n")
        except Exception as e:
            FreeCAD.Console.PrintError(f"Failed to stop server: {str(e)}\n")
            
        self._server_process = None
        self._update_action_states()

    def _restart_server(self):
        """Restart the freecad_server.py script."""
        # Local import to ensure Qt module is available in this scope
        from PySide2 import QtCore
        
        FreeCAD.Console.PrintMessage("Restarting server...\n")
        if self._is_server_running():
            self._stop_server()
            QtCore.QTimer.singleShot(500, self._start_server)
        else:
            self._start_server()

    def _update_indicator_icon(self):
        """Update the button's icon to show only server status."""
        from PySide2 import QtGui, QtCore
        
        # Color for server status
        server_color = QtGui.QColor(QtCore.Qt.blue) if self._server_running else QtGui.QColor(QtCore.Qt.gray)
        
        # Create a pixmap for our status icon
        icon_size = QtCore.QSize(16, 16)
        pixmap = QtGui.QPixmap(icon_size)
        pixmap.fill(QtCore.Qt.transparent)
        
        # Paint the status icon
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Draw circle indicator for server status
        painter.setBrush(QtGui.QBrush(server_color))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawEllipse(2, 2, icon_size.width()-4, icon_size.height()-4)
        
        # Finish painting
        painter.end()
        
        # Set the icon
        self._control_button.setIcon(QtGui.QIcon(pixmap))
        self._update_tooltip()
        
    def _check_status(self):
        """Check server running status"""
        # Check if server is running
        self._server_running = self._is_server_running()
        # Update the indicator and tooltip
        self._update_indicator_icon()
        # Update button states
        self._update_action_states()

    def _check_connection(self):
        """Check MCP connection status - now just a stub method"""
        # This method is kept as a placeholder but not used anymore
        pass

    def _install_dependencies(self):
        """Install required dependencies for the MCP modules."""
        from PySide2 import QtWidgets
        import subprocess
        import sys
        
        # Create dialog
        dialog = QtWidgets.QDialog(FreeCADGui.getMainWindow())
        dialog.setWindowTitle("Installing Dependencies")
        dialog.setMinimumWidth(500)
        
        # Layout
        layout = QtWidgets.QVBoxLayout()
        dialog.setLayout(layout)
        
        # Status message
        status_label = QtWidgets.QLabel("Select installation method")
        layout.addWidget(status_label)
        
        # Installation options
        options_group = QtWidgets.QGroupBox("Installation Options")
        options_layout = QtWidgets.QVBoxLayout()
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Normal install option
        normal_radio = QtWidgets.QRadioButton("Standard installation")
        normal_radio.setChecked(True)
        options_layout.addWidget(normal_radio)
        
        # Break system packages option
        break_system_radio = QtWidgets.QRadioButton("Use --break-system-packages flag (may be required on Debian/Ubuntu)")
        options_layout.addWidget(break_system_radio)
        
        # Required packages
        packages = ["fastapi", "uvicorn", "websockets", "aiofiles", "pydantic"]
        packages_label = QtWidgets.QLabel(f"Packages to install: {', '.join(packages)}")
        layout.addWidget(packages_label)
        
        # Log area
        log_text = QtWidgets.QTextEdit()
        log_text.setReadOnly(True)
        log_text.setMinimumHeight(200)
        layout.addWidget(log_text)
        
        # Instructions for manual installation
        instructions = (
            "<b>Alternative Installation Methods:</b><br>"
            "<ol>"
            "<li>Create a virtual environment:<br>"
            "<code>python3 -m venv ~/venv-freecad</code><br>"
            "<code>~/venv-freecad/bin/pip install fastapi uvicorn websockets aiofiles pydantic</code><br>"
            "Then run your server with: <code>~/venv-freecad/bin/python /path/to/freecad_server.py</code></li>"
            "<li>Use system packages:<br>"
            "<code>sudo apt install python3-fastapi python3-uvicorn python3-websockets python3-aiofiles python3-pydantic</code></li>"
            "</ol>"
        )
        help_label = QtWidgets.QLabel(instructions)
        help_label.setWordWrap(True)
        help_label.setOpenExternalLinks(True)  # Allow links to open
        layout.addWidget(help_label)
        
        # Button box
        button_box = QtWidgets.QDialogButtonBox()
        install_btn = button_box.addButton("Install Packages", QtWidgets.QDialogButtonBox.AcceptRole)
        cancel_btn = button_box.addButton(QtWidgets.QDialogButtonBox.Cancel)
        layout.addWidget(button_box)
        
        # Connect signals
        cancel_btn.clicked.connect(dialog.reject)
        
        # Connect install button with the options
        install_btn.clicked.connect(lambda: self._run_pip_install(
            packages, 
            log_text, 
            status_label, 
            install_btn,
            break_system_packages=break_system_radio.isChecked()
        ))
        
        # Show dialog
        dialog.exec_()
    
    def _run_pip_install(self, packages, log_text, status_label, install_btn, break_system_packages=False):
        """Run pip install with appropriate flags"""
        import subprocess
        import sys
        import os
        
        # Disable the install button to prevent multiple clicks
        install_btn.setEnabled(False)
        status_label.setText("Installing packages... (this may take a while)")
        
        # Find the actual Python executable, not FreeCAD
        # Check for FreeCAD's Python first
        freecad_python = None
        freecad_bin_dir = os.path.dirname(sys.executable)
        
        # Try to find Python in FreeCAD's directory
        for name in ['python3', 'python']:
            potential_path = os.path.join(freecad_bin_dir, name)
            if os.path.exists(potential_path):
                freecad_python = potential_path
                break
                
        # System Python executable locations
        python_candidates = [
            freecad_python,  # Try FreeCAD's Python first if found
            '/usr/bin/python3',
            '/usr/local/bin/python3',
            '/usr/bin/python',
            os.path.join(sys.prefix, 'bin', 'python3'),
            # Add more if needed
        ]
        
        # Filter out None entries
        python_candidates = [p for p in python_candidates if p]
        
        python_exec = None
        for candidate in python_candidates:
            if os.path.exists(candidate):
                python_exec = candidate
                break
                
        if not python_exec:
            log_text.append("❌ Error: Could not find Python executable. Please install packages manually.")
            status_label.setText("Installation failed - Python not found")
            install_btn.setEnabled(True)
            return
        
        # Log info
        log_text.append(f"Using Python: {python_exec}\n")
        log_text.append("Starting installation...\n")
        
        try:
            # Prepare installation command
            cmd = [python_exec, "-m", "pip", "install", "--user"]
            
            # Add break-system-packages flag if requested
            if break_system_packages:
                cmd.append("--break-system-packages")
                log_text.append("⚠️ Using --break-system-packages flag\n")
                
            # Add packages
            cmd.extend(packages)
            
            log_text.append(f"Running command: {' '.join(cmd)}\n")
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False
            )
            
            # Show the output
            log_text.append(result.stdout)
            
            if result.returncode == 0:
                status_label.setText("Packages installed successfully! Please restart FreeCAD.")
                log_text.append("\n✅ Installation successful!")
                log_text.append("\nPlease restart FreeCAD for changes to take effect.")
            else:
                # Check if this is an externally managed environment error
                if "externally-managed-environment" in result.stdout:
                    status_label.setText("Externally managed Python detected")
                    log_text.append("\n⚠️ Your Python is externally managed by your OS package manager.")
                    log_text.append("\nPlease use a virtual environment or system packages.")
                    
                    # Try direct pip if not tried yet and not using break-system-packages
                    if not break_system_packages:
                        log_text.append("\n➡️ Try using the --break-system-packages option in the dialog.")
                        log_text.append("\nOr follow the manual installation instructions below.")
                    else:
                        log_text.append("\n❌ Installation with --break-system-packages also failed.")
                        log_text.append("\nPlease follow the manual installation instructions below.")
                else:
                    # Generic failure
                    status_label.setText("Installation failed. See log for details.")
                    log_text.append("\n❌ Installation failed for an unknown reason.")
                    
                # Provide instructions for manual installation
                self._show_manual_install_instructions(log_text)
                
        except Exception as e:
            log_text.append(f"\nError during installation: {str(e)}")
            status_label.setText("Installation failed due to an error.")
            self._show_manual_install_instructions(log_text)
        
        # Re-enable the install button
        install_btn.setEnabled(True)
        
    def _show_manual_install_instructions(self, log_text):
        """Show instructions for manual installation"""
        log_text.append("\n\n--- MANUAL INSTALLATION INSTRUCTIONS ---")
        log_text.append("\nOption 1: Create a virtual environment:")
        log_text.append("python3 -m venv ~/venv-freecad")
        log_text.append("source ~/venv-freecad/bin/activate")
        log_text.append("pip install fastapi uvicorn websockets aiofiles pydantic")
        log_text.append("\nThen update your server path to point to:")
        log_text.append("~/venv-freecad/bin/python /path/to/freecad_server.py")
        
        log_text.append("\n\nOption 2: Install system packages (Ubuntu/Debian):")
        log_text.append("sudo apt install python3-fastapi python3-uvicorn python3-websockets python3-aiofiles python3-pydantic")

FreeCADGui.addWorkbench(MCPIndicatorWorkbench()) 