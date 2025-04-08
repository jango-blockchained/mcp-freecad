# FreeCAD MCP/Client/Server Interaction Flowchart

This document outlines the different ways the provided Python scripts interact to control FreeCAD using the `FreeCADConnection` interface.

## Components

1.  **User/Client Application (`freecad_client.py` / `freecad_mcp_server.py`)**: The application that wants to perform actions in FreeCAD.
2.  **Connection Layer (`freecad_connection.py`)**: A smart layer that determines the best way to talk to FreeCAD.
3.  **Execution Backends**:
    *   **Launcher (`freecad_launcher.py`)**: (Recommended) Launches FreeCAD (often via AppRun) and runs `freecad_script.py` inside it.
    *   **Wrapper (`freecad_wrapper.py`)**: Runs `freecad_subprocess.py` which imports FreeCAD modules.
    *   **Socket Server (`freecad_server.py`)**: Runs inside or connects to FreeCAD, listens on a socket.
    *   **CLI Bridge (`freecad_bridge.py`)**: Executes FreeCAD commands via the command-line executable.
    *   **Mock**: A fallback simulation if no real FreeCAD connection is available.
4.  **FreeCAD Instance/Environment**: The actual FreeCAD application, its Python modules, or the AppRun environment.
5.  **GUI Indicator (`InitGui.py`)**: (Optional) A FreeCAD Addon to manage `freecad_server.py` for the `server` method.

## Use Cases & Connection Modes

The `FreeCADConnection` class determines the connection method based on availability and preference (`prefer_method` argument):

1.  **`launcher` Mode (Recommended)**:
    *   Uses `freecad_launcher.py` to start FreeCAD, often via `AppRun` from an extracted AppImage.
    *   Runs `freecad_script.py` within the launched FreeCAD environment.
    *   Considered the most reliable method, especially with AppImages.
    *   Setup is often automated by `extract_appimage.py`.

2.  **`wrapper` Mode**:
    *   Uses `freecad_wrapper.py` which starts `freecad_subprocess.py`.
    *   `freecad_subprocess.py` attempts to `import FreeCAD` directly.
    *   Requires a Python environment where FreeCAD modules can be imported (e.g., system install or correctly configured AppImage Python).

3.  **`server` Mode**:
    *   `freecad_connection.py` attempts to connect to `freecad_server.py` running on the specified host/port.
    *   Requires `freecad_server.py` to be running independently inside FreeCAD.
    *   Can interact with `FreeCADGui` if the server is started with `--connect`.

4.  **`bridge` Mode (Legacy)**:
    *   Uses `FreeCADBridge` which calls the `freecad` command-line executable.
    *   Does *not* require `freecad_server.py`.
    *   Generally slower and less reliable.

5.  **`mock` Mode (Fallback)**:
    *   If all other methods fail or `use_mock` is true.
    *   Simulates FreeCAD operations.

6.  **`auto` Mode (Default Behavior)**:
    *   `freecad_connection.py` tries methods in order: `launcher`, `wrapper`, `server`, `bridge`, then `mock`. It uses the first one that succeeds.

## Mermaid Flowchart

```mermaid
graph TD
    subgraph "Initiator (Client)"
        UC["User Command (e.g., create_box)"]
        Client["freecad_client.py / freecad_mcp_server.py"]
    end

    subgraph "Connection Layer"
        FCConn["freecad_connection.py"]
        FCConn_Auto{"Auto-Detect Mode?"}
        FCConn_Pref{"Preference Set?"}
        FCConn_Launcher["Try Launcher Mode"]
        FCConn_Wrapper["Try Wrapper Mode"]
        FCConn_Server["Try Server Mode"]
        FCConn_Bridge["Try Bridge Mode"]
        FCConn_Mock["Use Mock Mode"]
    end

    subgraph "Execution Backends"
        direction LR
        subgraph "Launcher Backend"
            FCLauncher["freecad_launcher.py"]
            AppRun["AppRun (from AppImage)"]
            FCScript["freecad_script.py"]
        end
        subgraph "Wrapper Backend"
            FCWrapper["freecad_wrapper.py"]
            FCSubprocess["freecad_subprocess.py"]
        end
        subgraph "Server Backend"
            FCServer["freecad_server.py"]
            FCServer_Mode{"--connect Mode?"}
            FCServer_Standalone["Standalone / Mock"]
            FCServer_Connect["Connect to Running GUI"]
        end
        subgraph "Bridge Backend"
             FCBridge["freecad_bridge.py"]
             FCExt["FreeCAD Executable (CLI)"]
        end
        Mock["Mock Implementation"]
    end

    subgraph "FreeCAD Environment"
        direction LR
        FreeCADApp["Running FreeCAD GUI Instance"]
        FreeCADEnv["FreeCAD Modules / Environment"]
    end

    subgraph "GUI Management Addon (Server Mode)"
        direction LR
        GUIIndicator["InitGui.py (in FreeCAD GUI)"]
        StartStop["Start/Stop Server Buttons"]
    end

    %% Client Flow
    UC --> Client
    Client --> FCConn

    %% Connection Logic
    FCConn --> FCConn_Auto
    FCConn_Auto -- Yes --> FCConn_Launcher
    FCConn_Auto -- No --> FCConn_Pref

    FCConn_Pref -- Mode=Launcher --> FCConn_Launcher
    FCConn_Pref -- Mode=Wrapper --> FCConn_Wrapper
    FCConn_Pref -- Mode=Server --> FCConn_Server
    FCConn_Pref -- Mode=Bridge --> FCConn_Bridge
    FCConn_Pref -- Mode=Mock --> FCConn_Mock
    FCConn_Pref -- Mode=Auto/None --> FCConn_Launcher

    FCConn_Launcher -- Success --> FCLauncher
    FCConn_Launcher -- Failure --> FCConn_Wrapper
    FCConn_Wrapper -- Success & Available --> FCWrapper
    FCConn_Wrapper -- Failure --> FCConn_Server
    FCConn_Server -- Success --> FCServer
    FCConn_Server -- Failure --> FCConn_Bridge
    FCConn_Bridge -- Success & Available --> FCBridge
    FCConn_Bridge -- Failure / Unavailable --> FCConn_Mock
    FCConn_Mock --> Mock

    %% Launcher Backend Flow
    FCLauncher --> AppRun
    AppRun --> FCScript
    FCScript --> FreeCADEnv

    %% Wrapper Backend Flow
    FCWrapper --> FCSubprocess
    FCSubprocess --> FreeCADEnv

    %% Server Backend Flow
    FCServer --> FCServer_Mode
    FCServer_Mode -- Yes --> FCServer_Connect
    FCServer_Mode -- No --> FCServer_Standalone
    FCServer_Connect --> FreeCADApp
    FCServer_Standalone --> FreeCADEnv
    FCServer --> FreeCADEnv

    %% Bridge Backend Flow
    FCBridge --> FCExt
    FCExt --> FreeCADEnv

    %% GUI Indicator Flow (Server Mode)
    GUIIndicator --> StartStop
    StartStop -- Start --> FCServer
    StartStop -- Stop --> FCServer

    %% Style
    classDef client fill:#cde4ff,stroke:#333,stroke-width:2px;
    classDef conn fill:#ccffcc,stroke:#333,stroke-width:2px;
    classDef backend fill:#fff0cc,stroke:#333,stroke-width:2px;
    classDef freecad fill:#ffcccc,stroke:#333,stroke-width:2px;
    classDef gui fill:#e6ccff,stroke:#333,stroke-width:2px;

    class UC,Client client;
    class FCConn,FCConn_Auto,FCConn_Pref,FCConn_Launcher,FCConn_Wrapper,FCConn_Server,FCConn_Bridge,FCConn_Mock conn;
    class FCLauncher,AppRun,FCScript,FCWrapper,FCSubprocess,FCServer,FCServer_Mode,FCServer_Standalone,FCServer_Connect,FCBridge,FCExt,Mock backend;
    class FreeCADApp,FreeCADEnv freecad;
    class GUIIndicator,StartStop gui;
```

This flowchart illustrates the decision-making process within `freecad_connection.py`, showing the priority order (Launcher > Wrapper > Server > Bridge > Mock) and how different backends interact with the FreeCAD environment.

---

**Running the Examples:**

The `
