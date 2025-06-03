"""
Debugging Tool

MCP tool for debugging FreeCAD scripts and addons with advanced debugging capabilities.

Author: jango-blockchained
"""

import FreeCAD as App
import sys
import traceback
import pdb
import inspect
from typing import Dict, Any, List, Optional, Union


class DebuggingTool:
    """Tool for debugging FreeCAD scripts and addons."""

    def __init__(self):
        """Initialize the debugging tool."""
        self.name = "debugging"
        self.description = "Advanced debugging tools for FreeCAD development"
        self.breakpoints = {}
        self.debug_session = None

    def set_breakpoint(self, file_path: str, line_number: int, condition: str = None) -> Dict[str, Any]:
        """Set a breakpoint in a file.

        Args:
            file_path: Path to the Python file
            line_number: Line number to set breakpoint
            condition: Optional condition for conditional breakpoint

        Returns:
            Dictionary with breakpoint result
        """
        try:
            breakpoint_id = f"{file_path}:{line_number}"

            self.breakpoints[breakpoint_id] = {
                "file": file_path,
                "line": line_number,
                "condition": condition,
                "enabled": True,
                "hit_count": 0
            }

            return {
                "success": True,
                "breakpoint_id": breakpoint_id,
                "file": file_path,
                "line": line_number,
                "condition": condition,
                "message": f"Breakpoint set at {file_path}:{line_number}"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to set breakpoint: {str(e)}"
            }

    def remove_breakpoint(self, breakpoint_id: str) -> Dict[str, Any]:
        """Remove a breakpoint.

        Args:
            breakpoint_id: ID of breakpoint to remove

        Returns:
            Dictionary with removal result
        """
        try:
            if breakpoint_id in self.breakpoints:
                del self.breakpoints[breakpoint_id]
                return {
                    "success": True,
                    "breakpoint_id": breakpoint_id,
                    "message": f"Breakpoint {breakpoint_id} removed"
                }
            else:
                return {
                    "success": False,
                    "error": "Breakpoint not found",
                    "message": f"Breakpoint {breakpoint_id} not found"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to remove breakpoint: {str(e)}"
            }

    def list_breakpoints(self) -> Dict[str, Any]:
        """List all breakpoints.

        Returns:
            Dictionary with all breakpoints
        """
        try:
            return {
                "success": True,
                "breakpoints": self.breakpoints,
                "count": len(self.breakpoints),
                "message": f"Found {len(self.breakpoints)} breakpoints"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to list breakpoints: {str(e)}"
            }

    def start_debugger(self, script_path: str = None) -> Dict[str, Any]:
        """Start the Python debugger.

        Args:
            script_path: Optional path to script to debug

        Returns:
            Dictionary with debugger start result
        """
        try:
            if script_path:
                # Debug a specific script
                pdb.run(f"exec(open('{script_path}').read())")
            else:
                # Start interactive debugger
                pdb.set_trace()

            return {
                "success": True,
                "script_path": script_path,
                "message": "Debugger started"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to start debugger: {str(e)}"
            }

    def post_mortem_debug(self) -> Dict[str, Any]:
        """Start post-mortem debugging after an exception.

        Returns:
            Dictionary with post-mortem debug result
        """
        try:
            # Get the last exception
            exc_type, exc_value, exc_traceback = sys.exc_info()

            if exc_traceback:
                pdb.post_mortem(exc_traceback)
                return {
                    "success": True,
                    "exception_type": str(exc_type),
                    "exception_value": str(exc_value),
                    "message": "Post-mortem debugging started"
                }
            else:
                return {
                    "success": False,
                    "error": "No exception found",
                    "message": "No recent exception to debug"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to start post-mortem debug: {str(e)}"
            }

    def inspect_object(self, obj_name: str, doc_name: str = None) -> Dict[str, Any]:
        """Inspect a FreeCAD object in detail.

        Args:
            obj_name: Name of the object to inspect
            doc_name: Optional document name (uses active if None)

        Returns:
            Dictionary with object inspection details
        """
        try:
            # Get document
            if doc_name:
                doc = App.getDocument(doc_name)
            else:
                doc = App.ActiveDocument

            if not doc:
                return {
                    "success": False,
                    "error": "No document found",
                    "message": "No active document or specified document not found"
                }

            # Get object
            obj = doc.getObject(obj_name)
            if not obj:
                return {
                    "success": False,
                    "error": f"Object '{obj_name}' not found",
                    "message": f"Object '{obj_name}' not found in document"
                }

            # Inspect object
            inspection = {
                "name": obj.Name,
                "label": obj.Label,
                "type": obj.TypeId,
                "properties": {},
                "methods": [],
                "attributes": []
            }

            # Get properties
            for prop in obj.PropertiesList:
                try:
                    value = getattr(obj, prop)
                    inspection["properties"][prop] = {
                        "value": str(value),
                        "type": type(value).__name__
                    }
                except Exception as e:
                    inspection["properties"][prop] = {
                        "error": str(e),
                        "type": "unknown"
                    }

            # Get methods and attributes
            for attr_name in dir(obj):
                if not attr_name.startswith('_'):
                    try:
                        attr = getattr(obj, attr_name)
                        if callable(attr):
                            inspection["methods"].append({
                                "name": attr_name,
                                "signature": str(inspect.signature(attr)) if hasattr(inspect, 'signature') else "unknown"
                            })
                        else:
                            inspection["attributes"].append({
                                "name": attr_name,
                                "value": str(attr),
                                "type": type(attr).__name__
                            })
                    except Exception:
                        pass

            return {
                "success": True,
                "object_name": obj_name,
                "inspection": inspection,
                "message": f"Object '{obj_name}' inspected successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to inspect object: {str(e)}"
            }

    def trace_execution(self, script_code: str, max_steps: int = 100) -> Dict[str, Any]:
        """Trace execution of a script step by step.

        Args:
            script_code: Python code to trace
            max_steps: Maximum number of steps to trace

        Returns:
            Dictionary with execution trace
        """
        try:
            trace_log = []
            step_count = 0

            def trace_function(frame, event, arg):
                nonlocal step_count
                if step_count >= max_steps:
                    return None

                if event == 'line':
                    step_count += 1
                    trace_log.append({
                        "step": step_count,
                        "file": frame.f_code.co_filename,
                        "line": frame.f_lineno,
                        "function": frame.f_code.co_name,
                        "locals": {k: str(v) for k, v in frame.f_locals.items() if not k.startswith('_')}
                    })

                return trace_function

            # Set trace function
            sys.settrace(trace_function)

            try:
                # Execute code
                exec(script_code)
            finally:
                # Remove trace function
                sys.settrace(None)

            return {
                "success": True,
                "trace_log": trace_log,
                "steps": step_count,
                "max_steps": max_steps,
                "message": f"Execution traced for {step_count} steps"
            }

        except Exception as e:
            sys.settrace(None)  # Make sure to remove trace function
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to trace execution: {str(e)}"
            }

    def profile_performance(self, script_code: str) -> Dict[str, Any]:
        """Profile performance of a script.

        Args:
            script_code: Python code to profile

        Returns:
            Dictionary with performance profile
        """
        try:
            import cProfile
            import io
            import pstats

            # Create profiler
            profiler = cProfile.Profile()

            # Profile the code
            profiler.enable()
            exec(script_code)
            profiler.disable()

            # Get stats
            stats_stream = io.StringIO()
            stats = pstats.Stats(profiler, stream=stats_stream)
            stats.sort_stats('cumulative')
            stats.print_stats(20)  # Top 20 functions

            profile_output = stats_stream.getvalue()

            return {
                "success": True,
                "profile_output": profile_output,
                "message": "Performance profiling completed"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to profile performance: {str(e)}"
            }

    def memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage information.

        Returns:
            Dictionary with memory usage details
        """
        try:
            import psutil
            import gc

            # Get process memory info
            process = psutil.Process()
            memory_info = process.memory_info()

            # Get Python garbage collection stats
            gc_stats = gc.get_stats()

            # Count FreeCAD objects
            doc_count = len(App.listDocuments())
            total_objects = 0
            for doc_name in App.listDocuments():
                doc = App.getDocument(doc_name)
                total_objects += len(doc.Objects)

            return {
                "success": True,
                "memory_usage": {
                    "rss": memory_info.rss,  # Resident Set Size
                    "vms": memory_info.vms,  # Virtual Memory Size
                    "percent": process.memory_percent(),
                    "available": psutil.virtual_memory().available
                },
                "gc_stats": gc_stats,
                "freecad_objects": {
                    "documents": doc_count,
                    "total_objects": total_objects
                },
                "message": "Memory usage information collected"
            }

        except ImportError:
            return {
                "success": False,
                "error": "psutil not available",
                "message": "Install psutil for detailed memory information"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get memory usage: {str(e)}"
            }

    def validate_script(self, script_path: str) -> Dict[str, Any]:
        """Validate a Python script for syntax errors.

        Args:
            script_path: Path to the script to validate

        Returns:
            Dictionary with validation results
        """
        try:
            with open(script_path, 'r') as f:
                script_content = f.read()

            # Try to compile the script
            try:
                compile(script_content, script_path, 'exec')
                return {
                    "success": True,
                    "valid": True,
                    "script_path": script_path,
                    "message": "Script syntax is valid"
                }
            except SyntaxError as e:
                return {
                    "success": True,
                    "valid": False,
                    "script_path": script_path,
                    "syntax_error": {
                        "line": e.lineno,
                        "column": e.offset,
                        "message": e.msg,
                        "text": e.text
                    },
                    "message": f"Syntax error found at line {e.lineno}"
                }

        except FileNotFoundError:
            return {
                "success": False,
                "error": "File not found",
                "message": f"Script file '{script_path}' not found"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to validate script: {str(e)}"
            }

    def get_available_tools(self) -> Dict[str, Any]:
        """Get list of available debugging tools.

        Returns:
            Dictionary with available debugging tools
        """
        return {
            "tools": {
                "set_breakpoint": {
                    "description": "Set a breakpoint in a file",
                    "parameters": ["file_path", "line_number", "condition"]
                },
                "remove_breakpoint": {
                    "description": "Remove a breakpoint",
                    "parameters": ["breakpoint_id"]
                },
                "list_breakpoints": {
                    "description": "List all breakpoints",
                    "parameters": []
                },
                "start_debugger": {
                    "description": "Start the Python debugger",
                    "parameters": ["script_path"]
                },
                "post_mortem_debug": {
                    "description": "Start post-mortem debugging",
                    "parameters": []
                },
                "inspect_object": {
                    "description": "Inspect a FreeCAD object",
                    "parameters": ["obj_name", "doc_name"]
                },
                "trace_execution": {
                    "description": "Trace script execution step by step",
                    "parameters": ["script_code", "max_steps"]
                },
                "profile_performance": {
                    "description": "Profile script performance",
                    "parameters": ["script_code"]
                },
                "memory_usage": {
                    "description": "Get memory usage information",
                    "parameters": []
                },
                "validate_script": {
                    "description": "Validate script syntax",
                    "parameters": ["script_path"]
                }
            }
        }
