"""Execution Pipeline - Manages autonomous tool execution flow"""

import queue
import threading
import time
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import FreeCAD
import FreeCADGui


class StepStatus(Enum):
    """Status of an execution step"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"


class ExecutionPipeline:
    """
    Manages the execution of tool operations in a controlled pipeline
    with support for rollback, validation, and progress tracking.
    """

    def __init__(self, agent_manager):
        """
        Initialize the Execution Pipeline

        Args:
            agent_manager: Reference to the parent AgentManager
        """
        self.agent_manager = agent_manager
        self.current_execution = None
        self.execution_thread = None
        self.should_stop = False
        self.is_paused = False
        self.execution_queue = queue.Queue()

        # Execution tracking
        self.step_results = []
        self.undo_stack = []
        self.execution_log = []

        # Callbacks
        self.step_callbacks = {
            "on_step_start": [],
            "on_step_complete": [],
            "on_step_failed": [],
            "on_progress": [],
        }

        # Safety settings
        self.safety_config = {
            "max_execution_time": 300,  # 5 minutes per step
            "validate_before_execute": True,
            "auto_save_before_execute": True,
            "create_checkpoints": True,
            "rollback_on_failure": True,
        }

    def execute(self, plan: Dict) -> Dict:
        """
        Execute a complete plan

        Args:
            plan: Execution plan with steps

        Returns:
            Execution result dictionary
        """
        # Initialize execution
        self.current_execution = {
            "plan_id": plan["id"],
            "start_time": datetime.now(),
            "status": "running",
            "current_step": 0,
            "total_steps": len(plan["steps"]),
            "results": [],
        }

        # Reset tracking
        self.step_results = []
        self.should_stop = False
        self.is_paused = False

        # Create checkpoint if enabled
        if self.safety_config["create_checkpoints"]:
            self._create_checkpoint()

        # Auto-save if enabled
        if self.safety_config["auto_save_before_execute"]:
            self._auto_save_document()

        # Execute in separate thread
        self.execution_thread = threading.Thread(
            target=self._execute_plan_thread, args=(plan,)
        )
        self.execution_thread.start()
        self.execution_thread.join()  # Wait for completion

        # Prepare final result
        result = {
            "success": self.current_execution["status"] == "completed",
            "executed_steps": self.step_results,
            "failed_step": None,
            "outputs": [],
            "errors": [],
            "duration": (
                datetime.now() - self.current_execution["start_time"]
            ).total_seconds(),
        }

        # Find failed step if any
        for step_result in self.step_results:
            if step_result["status"] == StepStatus.FAILED:
                result["failed_step"] = step_result["step"]
                result["errors"].append(step_result.get("error", "Unknown error"))
                break
            elif step_result["status"] == StepStatus.COMPLETED:
                if "output" in step_result:
                    result["outputs"].append(step_result["output"])

        return result

    def _execute_plan_thread(self, plan: Dict):
        """Execute plan in separate thread"""
        try:
            for i, step in enumerate(plan["steps"]):
                if self.should_stop:
                    self._log("Execution stopped by user")
                    self.current_execution["status"] = "cancelled"
                    break

                while self.is_paused:
                    time.sleep(0.1)
                    if self.should_stop:
                        break

                self.current_execution["current_step"] = i + 1

                # Execute step
                step_result = self._execute_step(step, i + 1, len(plan["steps"]))
                self.step_results.append(step_result)

                # Check if step failed
                if step_result["status"] == StepStatus.FAILED:
                    self._log(
                        f"Step {i + 1} failed: {step_result.get('error', 'Unknown error')}"
                    )

                    # Attempt rollback if enabled
                    if self.safety_config["rollback_on_failure"]:
                        self._rollback_to_checkpoint()

                    self.current_execution["status"] = "failed"
                    break

            else:
                # All steps completed successfully
                self.current_execution["status"] = "completed"
                self._log("Execution completed successfully")

        except Exception as e:
            self._log(f"Execution error: {str(e)}")
            self.current_execution["status"] = "error"

    def _execute_step(self, step: Dict, step_num: int, total_steps: int) -> Dict:
        """Execute a single step"""
        step_result = {
            "step": step,
            "step_number": step_num,
            "status": StepStatus.PENDING,
            "start_time": datetime.now(),
            "duration": 0,
            "output": None,
            "error": None,
        }

        try:
            # Notify step start
            self._trigger_step_callback("on_step_start", step_num, total_steps, step)

            # Validate step if enabled
            if self.safety_config["validate_before_execute"]:
                validation = self._validate_step(step)
                if not validation["valid"]:
                    raise ValueError(f"Step validation failed: {validation['reason']}")

            # Update status
            step_result["status"] = StepStatus.RUNNING

            # Get tool from registry
            tool = self._get_tool(step["tool_id"])
            if not tool:
                raise ValueError(f"Tool not found: {step['tool_id']}")

            # Prepare parameters
            parameters = self._prepare_parameters(step, tool)

            # Execute tool with timeout
            self._log(f"Executing {step['tool']} with parameters: {parameters}")

            # Record state before execution for potential rollback
            before_state = self._capture_state()
            self.undo_stack.append(
                {
                    "step": step_num,
                    "before_state": before_state,
                    "tool": tool,
                    "parameters": parameters,
                }
            )

            # Execute the tool
            if hasattr(tool, "execute"):
                result = self._execute_with_timeout(
                    lambda: tool.execute(**parameters),
                    timeout=self.safety_config["max_execution_time"],
                )
                step_result["output"] = result
            else:
                # Fallback execution method
                result = self._execute_tool_fallback(tool, parameters)
                step_result["output"] = result

            # Update status
            step_result["status"] = StepStatus.COMPLETED
            step_result["duration"] = (
                datetime.now() - step_result["start_time"]
            ).total_seconds()

            # Notify completion
            self._trigger_step_callback(
                "on_step_complete", step_num, total_steps, step_result
            )

            # Update progress
            progress = step_num / total_steps
            self._trigger_step_callback("on_progress", progress, step_num, total_steps)

        except Exception as e:
            step_result["status"] = StepStatus.FAILED
            step_result["error"] = str(e)
            step_result["duration"] = (
                datetime.now() - step_result["start_time"]
            ).total_seconds()

            # Notify failure
            self._trigger_step_callback(
                "on_step_failed", step_num, total_steps, step_result
            )

            self._log(f"Step execution failed: {str(e)}")

        return step_result

    def _validate_step(self, step: Dict) -> Dict[str, Any]:
        """Validate a step before execution"""
        validation = {"valid": True, "reason": ""}

        # Check if tool exists
        if "tool_id" not in step:
            validation["valid"] = False
            validation["reason"] = "No tool_id specified"
            return validation

        tool = self._get_tool(step["tool_id"])
        if not tool:
            validation["valid"] = False
            validation["reason"] = f"Tool not found: {step['tool_id']}"
            return validation

        # Validate parameters
        if hasattr(tool, "validate_parameters"):
            param_validation = tool.validate_parameters(step.get("parameters", {}))
            if not param_validation.get("valid", True):
                validation["valid"] = False
                validation["reason"] = param_validation.get(
                    "reason", "Parameter validation failed"
                )

        # Check dependencies
        if "dependencies" in step and step["dependencies"]:
            for dep_step in step["dependencies"]:
                # Check if dependency was completed successfully
                dep_completed = any(
                    r["step_number"] == dep_step and r["status"] == StepStatus.COMPLETED
                    for r in self.step_results
                )
                if not dep_completed:
                    validation["valid"] = False
                    validation["reason"] = f"Dependency step {dep_step} not completed"
                    break

        return validation

    def _get_tool(self, tool_id: str):
        """Get tool from registry"""
        if self.agent_manager and self.agent_manager.tool_registry:
            return self.agent_manager.tool_registry.get_tool(tool_id)
        return None

    def _prepare_parameters(self, step: Dict, tool) -> Dict[str, Any]:
        """Prepare parameters for tool execution"""
        parameters = step.get("parameters", {}).copy()

        # Apply default parameters if not specified
        if hasattr(tool, "get_default_parameters"):
            defaults = tool.get_default_parameters()
            for key, value in defaults.items():
                if key not in parameters:
                    parameters[key] = value

        # Convert parameter types if needed
        if hasattr(tool, "convert_parameters"):
            parameters = tool.convert_parameters(parameters)

        return parameters

    def _execute_tool_fallback(self, tool, parameters: Dict) -> Any:
        """Fallback execution method for tools without execute method"""
        # Try different execution methods
        if hasattr(tool, "run"):
            return tool.run(**parameters)
        elif hasattr(tool, "apply"):
            return tool.apply(**parameters)
        elif hasattr(tool, "__call__"):
            return tool(**parameters)
        else:
            raise ValueError(f"Tool {tool} has no known execution method")

    def _execute_with_timeout(self, func: Callable, timeout: float) -> Any:
        """Execute function with timeout"""
        result = [None]
        exception = [None]

        def target():
            try:
                result[0] = func()
            except Exception as e:
                exception[0] = e

        thread = threading.Thread(target=target)
        thread.start()
        thread.join(timeout)

        if thread.is_alive():
            # Timeout occurred
            raise TimeoutError(f"Execution timed out after {timeout} seconds")

        if exception[0]:
            raise exception[0]

        return result[0]

    def _create_checkpoint(self):
        """Create a checkpoint for potential rollback"""
        try:
            # Save current document state
            doc = FreeCAD.ActiveDocument
            if doc:
                checkpoint_name = (
                    f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                # Store in memory for now, could save to temp file
                self._checkpoint_data = {
                    "name": checkpoint_name,
                    "timestamp": datetime.now(),
                    "document_state": self._capture_state(),
                }
                self._log(f"Created checkpoint: {checkpoint_name}")
        except Exception as e:
            self._log(f"Failed to create checkpoint: {str(e)}")

    def _rollback_to_checkpoint(self):
        """Rollback to the last checkpoint"""
        try:
            if hasattr(self, "_checkpoint_data") and self._checkpoint_data:
                # In a real implementation, this would restore the document state
                self._log(
                    f"Rolling back to checkpoint: {self._checkpoint_data['name']}"
                )

                # Use undo stack for rollback
                while self.undo_stack:
                    undo_info = self.undo_stack.pop()
                    # Perform undo operation
                    if FreeCADGui:
                        FreeCAD.ActiveDocument.undo()

        except Exception as e:
            self._log(f"Rollback failed: {str(e)}")

    def _capture_state(self) -> Dict:
        """Capture current FreeCAD document state"""
        state = {"timestamp": datetime.now().isoformat(), "objects": []}

        try:
            doc = FreeCAD.ActiveDocument
            if doc:
                for obj in doc.Objects:
                    state["objects"].append(
                        {"name": obj.Name, "type": obj.TypeId, "label": obj.Label}
                    )
        except Exception as e:
            self._log(f"Failed to capture state: {str(e)}")

        return state

    def _auto_save_document(self):
        """Auto-save the document before execution"""
        try:
            doc = FreeCAD.ActiveDocument
            if doc and doc.FileName:
                doc.save()
                self._log("Document auto-saved")
        except Exception as e:
            self._log(f"Auto-save failed: {str(e)}")

    def pause(self):
        """Pause execution"""
        self.is_paused = True
        self._log("Execution paused")

    def resume(self):
        """Resume execution"""
        self.is_paused = False
        self._log("Execution resumed")

    def stop(self):
        """Stop execution"""
        self.should_stop = True
        self._log("Execution stop requested")

    def register_step_callback(self, event: str, callback: Callable):
        """Register a callback for step events"""
        if event in self.step_callbacks:
            self.step_callbacks[event].append(callback)

    def _trigger_step_callback(self, event: str, *args, **kwargs):
        """Trigger callbacks for a step event"""
        if event in self.step_callbacks:
            for callback in self.step_callbacks[event]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    self._log(f"Callback error: {str(e)}")

    def _log(self, message: str):
        """Log execution message"""
        log_entry = {"timestamp": datetime.now().isoformat(), "message": message}
        self.execution_log.append(log_entry)
        FreeCAD.Console.PrintMessage(f"Execution Pipeline: {message}\n")

    def get_execution_log(self) -> List[Dict]:
        """Get execution log"""
        return self.execution_log.copy()

    def update_safety_config(self, config: Dict):
        """Update safety configuration"""
        self.safety_config.update(config)
        self._log(f"Safety config updated: {config}")
