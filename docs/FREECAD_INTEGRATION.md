# FreeCAD Integration Guide

## Understanding FreeCAD Integration

When integrating with FreeCAD, it's important to understand that FreeCAD has its own embedded Python interpreter. This means that:

1. FreeCAD's Python modules (like `FreeCAD.so`) **cannot be directly imported** into a standard Python environment
2. The proper way to interact with FreeCAD is through one of these approaches:

## Recommended Integration Approaches

### 1. FreeCAD as a Subprocess

The most reliable approach is to run FreeCAD as a subprocess and communicate with it via standard input/output or a specific protocol.

```python
import subprocess
import json

def run_freecad_command(script_content):
    # Create a temporary script
    with open("temp_script.py", "w") as f:
        f.write(script_content)
    
    # Run FreeCAD with the script
    process = subprocess.run(
        ["freecad", "-c", "temp_script.py"],
        capture_output=True,
        text=True
    )
    
    return process.stdout, process.stderr
```

### 2. Socket-Based Communication

Another approach is to run FreeCAD in server mode and communicate with it via sockets:

```python
import socket
import json

def send_command_to_freecad(command, host='localhost', port=12345):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(json.dumps(command).encode())
        response = s.recv(4096)
        return json.loads(response.decode())
```

This approach requires starting FreeCAD with a server script that listens for connections.

### 3. Python Extension for FreeCAD

You can create a Python extension that runs inside FreeCAD and provides an API for external applications:

1. Create a FreeCAD extension/workbench
2. Implement a server that listens for commands
3. Communicate with it from your application

## Modifications to the MCP-FreeCAD Integration

Based on the above understanding, our MCP-FreeCAD integration should be modified to:

1. Run FreeCAD as a separate process
2. Implement a communication protocol between our MCP server and FreeCAD
3. Use a message-based architecture to send commands and receive responses

## Implementation Steps

1. Modify the `FreeCADConnectionManager` to use subprocess or sockets instead of direct imports
2. Create a FreeCAD server script that will run inside FreeCAD
3. Implement serialization/deserialization of commands and responses
4. Update all resource and tool providers to use this communication channel

## Example Implementation

A basic implementation of the FreeCAD server script (to run inside FreeCAD):

```python
# freecad_server.py - Run this inside FreeCAD
import FreeCAD
import socket
import json
import threading
import sys

def handle_client(conn, addr):
    try:
        data = conn.recv(4096)
        if not data:
            return
            
        command = json.loads(data.decode())
        
        # Execute the command
        result = execute_command(command)
        
        # Send back the result
        conn.sendall(json.dumps(result).encode())
    except Exception as e:
        conn.sendall(json.dumps({"error": str(e)}).encode())
    finally:
        conn.close()

def execute_command(command):
    cmd_type = command.get("type")
    params = command.get("params", {})
    
    if cmd_type == "get_model_info":
        return get_model_info()
    elif cmd_type == "create_object":
        return create_object(params)
    # Add more commands as needed
    
    return {"error": f"Unknown command: {cmd_type}"}
    
def get_model_info():
    if not FreeCAD.ActiveDocument:
        return {"error": "No active document"}
        
    objects = []
    for obj in FreeCAD.ActiveDocument.Objects:
        objects.append({
            "name": obj.Name,
            "label": obj.Label,
            "type": obj.TypeId
        })
        
    return {
        "document": FreeCAD.ActiveDocument.Name,
        "objects": objects
    }
    
def create_object(params):
    if not FreeCAD.ActiveDocument:
        FreeCAD.newDocument("Unnamed")
        
    obj_type = params.get("type")
    
    if obj_type == "box":
        box = FreeCAD.ActiveDocument.addObject("Part::Box", "Box")
        box.Length = params.get("length", 10)
        box.Width = params.get("width", 10)
        box.Height = params.get("height", 10)
        FreeCAD.ActiveDocument.recompute()
        return {"success": True, "object": box.Name}
    
    return {"error": f"Unknown object type: {obj_type}"}

def start_server(host='localhost', port=12345):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"FreeCAD server listening on {host}:{port}")
        
        while True:
            conn, addr = s.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.daemon = True
            thread.start()

if __name__ == "__main__":
    start_server()
```

This approach requires updating your MCP server to communicate with this FreeCAD server. 