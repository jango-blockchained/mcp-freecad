# Refactoring Plan for InitGui.py

This plan outlines the steps to break down the large mcp-freecad/freecad_mcp_indicator/mcp_indicator/InitGui.py file into smaller, more manageable components based on functionality.

1. Analyze InitGui.py

- [x] The current MCPIndicatorWorkbench class mixes responsibilities including:
  - [x] Configuration loading/saving/UI.
  - [x] Server process management (start, stop, status checks for FreeCAD legacy server and MCP server).
  - [x] UI element creation and updates (status bar buttons, menus, dialogs, log viewer).
  - [x] Periodic status checking logic.
  - [x] Dependency installation logic.
  - [x] Flow visualization launching.
  - [x] Path utility functions.

2. Identify Components & Existing Modules

Based on the analysis and existing files (process_manager.py, path_finder.py, config_manager.py, flow_visualization.py), the following logical components are identified:

- [x] Configuration Management: Handles loading, saving, and UI for settings.
  - [x] Likely covered by: config_manager.py
- [x] Process Management: Logic for starting, stopping, restarting, and checking server status.
  - [x] Likely covered by: process_manager.py
- [x] Path Utilities: Finding script paths, Python executables, etc.
  - [x] Likely covered by: path_finder.py
- [x] UI Management: Creation and updating of status bar icons, menus, dialogs (settings, info), and the log viewer.
  - [x] Implemented in new module: ui_manager.py
- [x] Status Checking: Core logic for periodically checking connection and server status via timer.
  - [x] Implemented in new module: status_checker.py
- [x] Dependency Management: Logic for installing pip dependencies.
  - [x] Implemented in new module: dependency_manager.py
- [x] Flow Visualization: Launching the visualization dialog.
  - [x] Covered by: flow_visualization.py

3. Refactoring Structure

- [x] Create the following new Python files within the mcp-freecad/freecad_mcp_indicator/mcp_indicator/ directory:
  - [x] ui_manager.py
  - [x] dependency_manager.py
  - [x] status_checker.py
  - [x] process_manager.py (fixed from empty file)

4. Extraction Plan (Order of Operations)

- [x] Step 4.1: Dependency Management
  - [x] Move _install_dependencies, _run_pip_install, _show_manual_install_instructions from InitGui.py to dependency_manager.py. Create a DependencyManager class.
  - [x] Update InitGui.py to import and use the new module/class.
- [x] Step 4.2: UI Management (Largest Task)
  - [x] Create a UIManager class in ui_manager.py.
  - [x] Move UI-related parts of Initialize (widget creation, menu setup, dock widget) to the UIManager.
  - [x] Move UI update methods (_update_*_icon, _update_tooltip, _update_action_states) to UIManager.
  - [x] Move dialog methods (_show_*_info, _get_*_info_html, _show_settings, _browse_*_path, _apply_repo_path) to UIManager.
  - [x] Move log viewer methods (_load_mcp_log_content, _toggle_mcp_log_viewer, _handle_log_*_change) to UIManager.
  - [x] Update InitGui.py to instantiate and interact with UIManager.
- [x] Step 4.3: Status Checking
  - [x] Create a StatusChecker class in status_checker.py.
  - [x] Move _check_status, _check_connection, _update_connection_details to this class/module.
  - [x] Adjust the timer setup in InitGui.py to use the StatusChecker.
- [x] Step 4.4: Review Existing Modules & Remove Redundancy
  - [x] Examine config_manager.py, process_manager.py, path_finder.py.
  - [x] Ensure they cover all intended logic (e.g., server start/stop, path finding).
  - [x] Remove the corresponding now-redundant methods from InitGui.py (e.g., _start_*_server, _stop_*_server, _is_*_server_running, _get_python_executable, _update_script_paths_from_repo, etc.).
  - [x] Update InitGui.py to use these modules correctly.

5. Refine MCPIndicatorWorkbench in InitGui.py

- [x] The main MCPIndicatorWorkbench class will become a coordinator.
- [x] It will instantiate the manager classes (UIManager, ProcessManager, ConfigManager, etc.).
- [x] It will delegate UI setup to the UIManager.
- [x] It will likely manage the main QTimer, triggering the StatusChecker.
- [x] It will route actions (like menu triggers) to the appropriate managers.

6. Finalize and Test

- [x] Thoroughly check all imports across the refactored modules and InitGui.py.
- [x] Verify that all workbench functionality (status icons, menus, server controls, settings, log viewer) works as it did before the refactoring.

## Summary of Changes

The InitGui.py file has been successfully refactored into modular components:

1. The original ~2600 line file has been split into multiple focused modules:
   - config_manager.py - Configuration management
   - path_finder.py - Path utility functions
   - process_manager.py - Server process management
   - status_checker.py - Connection status checking
   - ui_manager.py - UI management and event handling
   - dependency_manager.py - Package installation
   - flow_visualization.py - Message flow visualization

2. The InitGui.py file now:
   - Is much smaller (~100 lines)
   - Acts as a coordinator between modules
   - Has clearer separation of concerns
   - Is easier to maintain and extend

3. Benefits of this refactoring:
   - Improved code organization
   - Easier to locate and fix bugs
   - Facilitates adding new features
   - Better code reuse
   - Easier to test individual components