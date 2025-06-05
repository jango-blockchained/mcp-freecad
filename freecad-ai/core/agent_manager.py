"""Agent Manager - Core orchestration for FreeCAD AI Agent System"""

import enum
import json
import asyncio
import threading
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import FreeCAD

class AgentMode(enum.Enum):
    """Agent operation modes"""
    CHAT = "chat"      # AI provides instructions only
    AGENT = "agent"    # AI executes tools autonomously

class ExecutionState(enum.Enum):
    """Execution state tracking"""
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    PAUSED = "paused"
    ERROR = "error"
    COMPLETED = "completed"

class AgentManager:
    """
    Main agent orchestration class that manages the AI agent's behavior,
    execution modes, and tool interactions.
    """

    def __init__(self):
        """Initialize the Agent Manager"""
        self.current_mode = AgentMode.CHAT
        self.execution_state = ExecutionState.IDLE
        self.tool_registry = None
        self.tool_selector = None
        self.execution_pipeline = None
        self.context_enricher = None
        self.ai_provider = None

        # Execution tracking
        self.current_plan = None
        self.execution_history = []
        self.execution_queue = []
        self.active_execution = None

        # Configuration
        self.config = {
            "max_retries": 3,
            "execution_timeout": 300,  # 5 minutes
            "require_approval": False,
            "safety_checks": True,
            "auto_rollback": True,
            "log_executions": True
        }

        # Callbacks
        self.callbacks = {
            "on_mode_change": [],
            "on_state_change": [],
            "on_execution_start": [],
            "on_execution_complete": [],
            "on_execution_error": [],
            "on_plan_created": []
        }

        # Thread safety
        self.lock = threading.Lock()

        # Initialize components
        self._initialize_components()

    def _initialize_components(self):
        """Initialize agent components"""
        try:
            # Import components with relative imports
            try:
                from ..core.tool_registry import ToolRegistry
                from ..core.tool_selector import ToolSelector
                from ..core.execution_pipeline import ExecutionPipeline
                from ..core.context_enricher import ContextEnricher
            except ImportError:
                # Try alternative import paths
                try:
                    from .tool_registry import ToolRegistry
                    from .tool_selector import ToolSelector
                    from .execution_pipeline import ExecutionPipeline
                    from .context_enricher import ContextEnricher
                except ImportError:
                    # Fallback to create dummy classes if components don't exist
                    FreeCAD.Console.PrintMessage("Agent Manager: Core components not available, using fallback\n")
                    self._initialize_fallback_components()
                    return

            self.tool_registry = ToolRegistry()
            self.tool_selector = ToolSelector(self.tool_registry)
            self.execution_pipeline = ExecutionPipeline(self)
            self.context_enricher = ContextEnricher()

            # Register all available tools
            self._register_all_tools()

            FreeCAD.Console.PrintMessage("Agent Manager: All components initialized\n")
        except ImportError as e:
            FreeCAD.Console.PrintError(f"Agent Manager: Failed to initialize components: {e}\n")
            # Initialize fallback components
            self._initialize_fallback_components()
        except Exception as e:
            FreeCAD.Console.PrintError(f"Agent Manager: Unexpected error during initialization: {e}\n")
            import traceback
            FreeCAD.Console.PrintError(f"Traceback: {traceback.format_exc()}\n")
            self._initialize_fallback_components()

    def _initialize_fallback_components(self):
        """Initialize fallback components when imports fail"""
        try:
            # Create a simple tool registry fallback
            self.tool_registry = self._create_fallback_tool_registry()
            FreeCAD.Console.PrintMessage("Agent Manager: Using fallback components\n")
        except Exception as e:
            FreeCAD.Console.PrintError(f"Agent Manager: Even fallback initialization failed: {e}\n")

    def _create_fallback_tool_registry(self):
        """Create a fallback tool registry with direct tool access"""
        class FallbackToolRegistry:
            def __init__(self):
                self.tools = {}
                self._load_tools_directly()

            def _load_tools_directly(self):
                """Load tools directly from GUI tools widget"""
                try:
                    # Import tools directly using relative imports
                    try:
                        from ..tools.primitives import PrimitivesTool
                        from ..tools.operations import OperationsTool
                        from ..tools.measurements import MeasurementsTool
                        from ..tools.export_import import ExportImportTool
                    except ImportError:
                        # Try alternative import path
                        from tools.primitives import PrimitivesTool
                        from tools.operations import OperationsTool
                        from tools.measurements import MeasurementsTool
                        from tools.export_import import ExportImportTool

                    self.tools = {
                        "primitives": PrimitivesTool(),
                        "operations": OperationsTool(),
                        "measurements": MeasurementsTool(),
                        "export_import": ExportImportTool(),
                    }

                    # Try to load advanced tools
                    try:
                        try:
                            from ..tools.advanced_primitives import AdvancedPrimitivesTool
                            from ..tools.advanced_operations import AdvancedOperationsTool
                            from ..tools.surface_modification import SurfaceModificationTool
                        except ImportError:
                            from tools.advanced_primitives import AdvancedPrimitivesTool
                            from tools.advanced_operations import AdvancedOperationsTool
                            from tools.surface_modification import SurfaceModificationTool

                        self.tools.update({
                            "advanced_primitives": AdvancedPrimitivesTool(),
                            "advanced_operations": AdvancedOperationsTool(),
                            "surface_modification": SurfaceModificationTool(),
                        })
                    except ImportError:
                        pass

                except ImportError as e:
                    FreeCAD.Console.PrintError(f"Failed to load tools directly: {e}\n")

            def get_tool(self, tool_id):
                """Get tool by ID"""
                # Tool ID format: category.method
                if '.' in tool_id:
                    category, method = tool_id.split('.', 1)
                    if category in self.tools:
                        tool = self.tools[category]
                        if hasattr(tool, method):
                            return tool
                return None

            def get_all_tools(self):
                """Get all available tools"""
                return self.tools.copy()

            def get_tool_methods(self, category):
                """Get all methods for a tool category"""
                if category in self.tools:
                    tool = self.tools[category]
                    methods = [method for method in dir(tool)
                             if not method.startswith('_') and callable(getattr(tool, method))]
                    return methods
                return []

        return FallbackToolRegistry()

    def _register_all_tools(self):
        """Register all available tools from the GUI tools widget"""
        if not self.tool_registry:
            return

        try:
            # Get tool categories and methods
            tool_categories = ['primitives', 'operations', 'measurements', 'export_import',
                             'advanced_primitives', 'advanced_operations', 'surface_modification']

            for category in tool_categories:
                if hasattr(self.tool_registry, 'tools') and category in self.tool_registry.tools:
                    tool = self.tool_registry.tools[category]
                    methods = [method for method in dir(tool)
                             if not method.startswith('_') and callable(getattr(tool, method))]

                    for method in methods:
                        tool_id = f"{category}.{method}"
                        FreeCAD.Console.PrintMessage(f"Registered tool: {tool_id}\n")

        except Exception as e:
            FreeCAD.Console.PrintError(f"Error registering tools: {e}\n")

    def set_mode(self, mode: AgentMode):
        """
        Set the agent operation mode

        Args:
            mode: AgentMode.CHAT or AgentMode.AGENT
        """
        with self.lock:
            old_mode = self.current_mode
            self.current_mode = mode

            # Clear execution queue when switching to chat mode
            if mode == AgentMode.CHAT:
                self.execution_queue.clear()
                if self.execution_state == ExecutionState.EXECUTING:
                    self.pause_execution()

            self._trigger_callbacks("on_mode_change", old_mode, mode)
            FreeCAD.Console.PrintMessage(f"Agent Manager: Mode changed from {old_mode.value} to {mode.value}\n")

    def get_mode(self) -> AgentMode:
        """Get current agent mode"""
        return self.current_mode

    def set_ai_provider(self, provider):
        """Set the AI provider for agent operations"""
        self.ai_provider = provider

    def get_available_tools(self) -> Dict[str, List[str]]:
        """Get all available tools organized by category"""
        available_tools = {}

        if self.tool_registry and hasattr(self.tool_registry, 'tools'):
            for category, tool in self.tool_registry.tools.items():
                methods = [method for method in dir(tool)
                         if not method.startswith('_') and callable(getattr(tool, method))]
                available_tools[category] = methods

        return available_tools

    def process_message(self, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Process a user message based on current mode

        Args:
            message: User input message
            context: Optional context information

        Returns:
            Response dictionary with mode-specific content
        """
        # Enrich context
        enriched_context = self._enrich_context(context)

        if self.current_mode == AgentMode.CHAT:
            return self._process_chat_mode(message, enriched_context)
        else:
            return self._process_agent_mode(message, enriched_context)

    def _process_chat_mode(self, message: str, context: Dict) -> Dict[str, Any]:
        """Process message in chat mode - provide instructions only"""
        response = {
            "mode": "chat",
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "response_type": "instructions"
        }

        try:
            # Analyze intent and suggest tools
            intent = self._analyze_intent(message, context)
            suggested_tools = self._select_tools_for_intent(intent, context)

            # Generate instruction response
            instructions = self._generate_instructions(intent, suggested_tools, context)

            response.update({
                "intent": intent,
                "suggested_tools": [self._get_tool_info(tool) for tool in suggested_tools],
                "instructions": instructions,
                "can_execute": True  # Indicate this could be executed in agent mode
            })

        except Exception as e:
            FreeCAD.Console.PrintError(f"Agent Manager: Error in chat mode: {e}\n")
            response["error"] = str(e)

        return response

    def _process_agent_mode(self, message: str, context: Dict) -> Dict[str, Any]:
        """Process message in agent mode - plan and execute autonomously"""
        response = {
            "mode": "agent",
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "response_type": "execution"
        }

        try:
            # Update state
            self._set_state(ExecutionState.PLANNING)

            # Analyze intent
            intent = self._analyze_intent(message, context)

            # Select tools
            selected_tools = self._select_tools_for_intent(intent, context)

            # Create execution plan
            plan = self._create_execution_plan(intent, selected_tools, context)
            self.current_plan = plan

            # Trigger plan created callback
            self._trigger_callbacks("on_plan_created", plan)

            response.update({
                "intent": intent,
                "plan": plan,
                "selected_tools": [self._get_tool_info(tool) for tool in selected_tools]
            })

            # Check if approval required
            if self.config["require_approval"]:
                response["status"] = "awaiting_approval"
                response["approval_required"] = True
            else:
                # Execute plan
                execution_result = self._execute_plan(plan)
                response["execution_result"] = execution_result
                response["status"] = "completed" if execution_result["success"] else "failed"

        except Exception as e:
            FreeCAD.Console.PrintError(f"Agent Manager: Error in agent mode: {e}\n")
            self._set_state(ExecutionState.ERROR)
            response["error"] = str(e)
            response["status"] = "error"

        return response

    def _select_tools_for_intent(self, intent: Dict, context: Dict) -> List[str]:
        """Select appropriate tools based on intent"""
        tools = []

        if not self.tool_registry:
            return tools

        intent_type = intent.get("type", "unknown")
        action = intent.get("action", "")

        # Map intents to tool categories and methods
        if intent_type == "creation":
            if any(word in action.lower() for word in ["box", "cube", "rectangle"]):
                tools.append("primitives.create_box")
            elif any(word in action.lower() for word in ["cylinder", "tube"]):
                tools.append("primitives.create_cylinder")
            elif any(word in action.lower() for word in ["sphere", "ball"]):
                tools.append("primitives.create_sphere")
            elif any(word in action.lower() for word in ["cone"]):
                tools.append("primitives.create_cone")
            else:
                # Default creation tools
                tools.extend(["primitives.create_box", "primitives.create_cylinder"])

        elif intent_type == "modification":
            tools.extend([
                "operations.move_object",
                "operations.rotate_object",
                "operations.scale_object"
            ])

        elif intent_type == "analysis":
            tools.extend([
                "measurements.measure_volume",
                "measurements.measure_area",
                "measurements.measure_distance"
            ])

        elif intent_type == "boolean":
            tools.extend([
                "operations.boolean_union",
                "operations.boolean_cut",
                "operations.boolean_intersection"
            ])

        return tools

    def _get_tool_info(self, tool_id: str) -> Dict:
        """Get information about a tool"""
        return {
            "id": tool_id,
            "name": tool_id.split('.')[-1].replace('_', ' ').title(),
            "category": tool_id.split('.')[0] if '.' in tool_id else "unknown"
        }

    def _enrich_context(self, context: Optional[Dict]) -> Dict:
        """Enrich context with FreeCAD state and history"""
        if not context:
            context = {}

        if self.context_enricher:
            enriched = self.context_enricher.enrich(context)
            return enriched

        # Fallback context enrichment
        try:
            import FreeCAD
            import FreeCADGui

            context["freecad_state"] = {
                "has_active_document": FreeCAD.ActiveDocument is not None,
                "document_objects": [],
                "selected_objects": []
            }

            if FreeCAD.ActiveDocument:
                context["freecad_state"]["document_objects"] = [
                    {"name": obj.Name, "type": obj.TypeId}
                    for obj in FreeCAD.ActiveDocument.Objects
                ]

            if hasattr(FreeCADGui, 'Selection'):
                context["freecad_state"]["selected_objects"] = [
                    {"name": obj.Name, "type": obj.TypeId}
                    for obj in FreeCADGui.Selection.getSelection()
                ]

        except Exception as e:
            context["context_error"] = str(e)

        return context

    def _analyze_intent(self, message: str, context: Dict) -> Dict:
        """Analyze user intent from message"""
        intent = {
            "type": "unknown",
            "confidence": 0.0,
            "entities": [],
            "action": message
        }

        # Enhanced pattern matching
        message_lower = message.lower()

        # Creation patterns
        if any(word in message_lower for word in ["create", "make", "build", "add", "new"]):
            intent["type"] = "creation"
            intent["action"] = "create"
            intent["confidence"] = 0.8

            # Extract shape type
            if any(word in message_lower for word in ["box", "cube", "rectangle"]):
                intent["entities"].append({"type": "shape", "value": "box"})
            elif any(word in message_lower for word in ["cylinder", "tube"]):
                intent["entities"].append({"type": "shape", "value": "cylinder"})
            elif any(word in message_lower for word in ["sphere", "ball"]):
                intent["entities"].append({"type": "shape", "value": "sphere"})

        # Boolean operations
        elif any(word in message_lower for word in ["union", "combine", "merge", "join"]):
            intent["type"] = "boolean"
            intent["action"] = "union"
            intent["confidence"] = 0.9
        elif any(word in message_lower for word in ["cut", "subtract", "difference"]):
            intent["type"] = "boolean"
            intent["action"] = "cut"
            intent["confidence"] = 0.9
        elif any(word in message_lower for word in ["intersect", "intersection"]):
            intent["type"] = "boolean"
            intent["action"] = "intersection"
            intent["confidence"] = 0.9

        # Modification patterns
        elif any(word in message_lower for word in ["modify", "change", "edit", "update", "move", "rotate", "scale"]):
            intent["type"] = "modification"
            intent["action"] = "modify"
            intent["confidence"] = 0.7

        # Analysis patterns
        elif any(word in message_lower for word in ["measure", "calculate", "analyze", "volume", "area", "distance"]):
            intent["type"] = "analysis"
            intent["action"] = "analyze"
            intent["confidence"] = 0.8

        return intent

    def _generate_instructions(self, intent: Dict, tools: List[str], context: Dict) -> List[str]:
        """Generate step-by-step instructions for chat mode"""
        instructions = []

        if intent["type"] == "creation":
            instructions.append("To create the requested object:")
            for i, tool_id in enumerate(tools, 1):
                tool_name = tool_id.split('.')[-1].replace('_', ' ').title()
                instructions.append(f"{i}. Use the {tool_name} tool from the Tools tab")
                instructions.append(f"   - Click the appropriate button in the Tools widget")
                instructions.append(f"   - Configure the parameters as needed")

        elif intent["type"] == "modification":
            instructions.append("To modify the object:")
            instructions.append("1. Select the target object in the FreeCAD tree")
            for i, tool_id in enumerate(tools, 2):
                tool_name = tool_id.split('.')[-1].replace('_', ' ').title()
                instructions.append(f"{i}. Apply {tool_name} from the Tools tab")

        elif intent["type"] == "analysis":
            instructions.append("To analyze the object:")
            instructions.append("1. Select the object(s) you want to measure")
            for i, tool_id in enumerate(tools, 2):
                tool_name = tool_id.split('.')[-1].replace('_', ' ').title()
                instructions.append(f"{i}. Use {tool_name} from the Measurements section")

        # Add safety reminders
        instructions.append("\nRemember to:")
        instructions.append("- Save your work before making changes")
        instructions.append("- Use undo (Ctrl+Z) if needed")
        instructions.append("- Switch to Agent mode for autonomous execution")

        return instructions

    def _create_execution_plan(self, intent: Dict, tools: List[str], context: Dict) -> Dict:
        """Create a detailed execution plan"""
        plan = {
            "id": f"plan_{int(datetime.now().timestamp() * 1000)}",
            "intent": intent,
            "steps": [],
            "estimated_duration": 0,
            "risk_level": "low",
            "rollback_possible": True
        }

        # Create execution steps
        for i, tool_id in enumerate(tools):
            step = {
                "order": i + 1,
                "tool": tool_id.split('.')[-1],
                "tool_id": tool_id,
                "parameters": self._infer_parameters(tool_id, intent, context),
                "description": f"Execute {tool_id.split('.')[-1].replace('_', ' ')}",
                "estimated_duration": 2.0,
                "dependencies": []
            }

            plan["steps"].append(step)
            plan["estimated_duration"] += step["estimated_duration"]

        # Assess risk level
        if any(word in str(intent) for word in ["delete", "remove", "clear"]):
            plan["risk_level"] = "high"
        elif len(tools) > 3:
            plan["risk_level"] = "medium"

        return plan

    def _infer_parameters(self, tool_id: str, intent: Dict, context: Dict) -> Dict:
        """Infer tool parameters from context and intent"""
        params = {}

        # Extract entities from intent
        entities = {entity["type"]: entity["value"] for entity in intent.get("entities", [])}

        # Tool-specific parameter inference
        if "create_box" in tool_id:
            params = {"length": 10.0, "width": 10.0, "height": 10.0}
        elif "create_cylinder" in tool_id:
            params = {"radius": 5.0, "height": 10.0}
        elif "create_sphere" in tool_id:
            params = {"radius": 5.0}
        elif "create_cone" in tool_id:
            params = {"radius1": 5.0, "radius2": 0.0, "height": 10.0}

        # Use selected objects for operations
        if context.get("freecad_state", {}).get("selected_objects"):
            selected = context["freecad_state"]["selected_objects"]
            if len(selected) >= 1 and "move_object" in tool_id:
                params["obj_name"] = selected[0]["name"]
                params["x"] = 5.0
                params["y"] = 0.0
                params["z"] = 0.0
            elif len(selected) >= 2 and "boolean" in tool_id:
                params["obj1_name"] = selected[0]["name"]
                params["obj2_name"] = selected[1]["name"]

        return params

    def _execute_plan(self, plan: Dict) -> Dict:
        """Execute the plan using the execution pipeline or fallback"""
        self._set_state(ExecutionState.EXECUTING)

        result = {
            "success": False,
            "executed_steps": [],
            "failed_step": None,
            "outputs": [],
            "errors": []
        }

        try:
            if self.execution_pipeline:
                pipeline_result = self.execution_pipeline.execute(plan)
                result.update(pipeline_result)
            else:
                # Fallback execution
                for step in plan["steps"]:
                    self._trigger_callbacks("on_execution_start",
                                           step["order"],
                                           len(plan["steps"]),
                                           step)

                    step_result = self._execute_step_fallback(step)
                    result["executed_steps"].append(step_result)

                    self._trigger_callbacks("on_execution_complete",
                                           step["order"],
                                           len(plan["steps"]),
                                           step_result)

                    if not step_result["success"]:
                        result["failed_step"] = step
                        result["errors"].append(step_result.get("error", "Unknown error"))
                        break
                else:
                    result["success"] = True

            self._set_state(ExecutionState.COMPLETED if result["success"] else ExecutionState.ERROR)

        except Exception as e:
            result["errors"].append(str(e))
            self._set_state(ExecutionState.ERROR)

        # Add to history
        self.execution_history.append({
            "timestamp": datetime.now().isoformat(),
            "plan": plan,
            "result": result
        })

        return result

    def _execute_step_fallback(self, step: Dict) -> Dict:
        """Execute a single step using fallback method"""
        step_result = {
            "step": step["order"],
            "tool": step["tool_id"],
            "success": False,
            "output": None,
            "error": None
        }

        try:
            tool_id = step["tool_id"]
            parameters = step.get("parameters", {})

            # Get tool from registry
            if self.tool_registry:
                tool = self.tool_registry.get_tool(tool_id)
                if tool:
                    # Execute the tool method
                    category, method = tool_id.split('.', 1)
                    if hasattr(tool, method):
                        method_func = getattr(tool, method)
                        result = method_func(**parameters)

                        step_result["success"] = result.get("success", True)
                        step_result["output"] = result.get("message", f"Executed {tool_id}")

                        if not step_result["success"]:
                            step_result["error"] = result.get("message", "Execution failed")
                    else:
                        step_result["error"] = f"Method {method} not found on tool"
                else:
                    step_result["error"] = f"Tool {tool_id} not found"
            else:
                step_result["error"] = "Tool registry not available"

        except Exception as e:
            step_result["error"] = str(e)

        return step_result

    def approve_plan(self, plan_id: str) -> Dict:
        """Approve and execute a pending plan"""
        if self.current_plan and self.current_plan["id"] == plan_id:
            return self._execute_plan(self.current_plan)
        else:
            return {"error": "Plan not found or expired"}

    def reject_plan(self, plan_id: str):
        """Reject a pending plan"""
        if self.current_plan and self.current_plan["id"] == plan_id:
            self.current_plan = None
            self._set_state(ExecutionState.IDLE)

    def pause_execution(self):
        """Pause current execution"""
        if self.execution_state == ExecutionState.EXECUTING:
            self._set_state(ExecutionState.PAUSED)
            # Implementation will signal pipeline to pause

    def resume_execution(self):
        """Resume paused execution"""
        if self.execution_state == ExecutionState.PAUSED:
            self._set_state(ExecutionState.EXECUTING)
            # Implementation will signal pipeline to resume

    def cancel_execution(self):
        """Cancel current execution"""
        self._set_state(ExecutionState.IDLE)
        self.current_plan = None
        # Implementation will signal pipeline to stop

    def _set_state(self, state: ExecutionState):
        """Update execution state"""
        old_state = self.execution_state
        self.execution_state = state
        self._trigger_callbacks("on_state_change", old_state, state)

    def register_callback(self, event: str, callback: Callable):
        """Register a callback for agent events"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)

    def _trigger_callbacks(self, event: str, *args, **kwargs):
        """Trigger callbacks for an event"""
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    FreeCAD.Console.PrintError(f"Agent Manager: Callback error: {e}\n")

    def get_execution_history(self) -> List[Dict]:
        """Get execution history"""
        return self.execution_history.copy()

    def get_status(self) -> Dict:
        """Get current agent status"""
        return {
            "mode": self.current_mode.value,
            "state": self.execution_state.value,
            "has_active_plan": self.current_plan is not None,
            "queue_size": len(self.execution_queue),
            "history_size": len(self.execution_history),
            "config": self.config.copy(),
            "available_tools": self.get_available_tools()
        }

    def update_config(self, config: Dict):
        """Update agent configuration"""
        self.config.update(config)
        FreeCAD.Console.PrintMessage(f"Agent Manager: Configuration updated\n")
