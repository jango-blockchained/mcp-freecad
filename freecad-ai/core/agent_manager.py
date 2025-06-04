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
            # Import components with error handling
            from .tool_registry import ToolRegistry
            from .tool_selector import ToolSelector
            from .execution_pipeline import ExecutionPipeline
            from .context_enricher import ContextEnricher

            self.tool_registry = ToolRegistry()
            self.tool_selector = ToolSelector(self.tool_registry)
            self.execution_pipeline = ExecutionPipeline(self)
            self.context_enricher = ContextEnricher()

            FreeCAD.Console.PrintMessage("Agent Manager: All components initialized\n")
        except ImportError as e:
            FreeCAD.Console.PrintError(f"Agent Manager: Failed to initialize components: {e}\n")

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
            suggested_tools = self.tool_selector.select_tools(message, context) if self.tool_selector else []

            # Generate instruction response
            instructions = self._generate_instructions(intent, suggested_tools, context)

            response.update({
                "intent": intent,
                "suggested_tools": [tool.get_info() for tool in suggested_tools],
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
            selected_tools = self.tool_selector.select_tools(message, context) if self.tool_selector else []

            # Create execution plan
            plan = self._create_execution_plan(intent, selected_tools, context)
            self.current_plan = plan

            # Trigger plan created callback
            self._trigger_callbacks("on_plan_created", plan)

            response.update({
                "intent": intent,
                "plan": plan,
                "selected_tools": [tool.get_info() for tool in selected_tools]
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

    def _enrich_context(self, context: Optional[Dict]) -> Dict:
        """Enrich context with FreeCAD state and history"""
        if not context:
            context = {}

        if self.context_enricher:
            enriched = self.context_enricher.enrich(context)
            return enriched

        return context

    def _analyze_intent(self, message: str, context: Dict) -> Dict:
        """Analyze user intent from message"""
        # This will be implemented with the intent classifier
        intent = {
            "type": "unknown",
            "confidence": 0.0,
            "entities": [],
            "action": None
        }

        # Simple pattern matching for now
        message_lower = message.lower()

        if any(word in message_lower for word in ["create", "make", "build", "add"]):
            intent["type"] = "creation"
            intent["action"] = "create"
        elif any(word in message_lower for word in ["modify", "change", "edit", "update"]):
            intent["type"] = "modification"
            intent["action"] = "modify"
        elif any(word in message_lower for word in ["delete", "remove", "clear"]):
            intent["type"] = "deletion"
            intent["action"] = "delete"
        elif any(word in message_lower for word in ["measure", "calculate", "analyze"]):
            intent["type"] = "analysis"
            intent["action"] = "analyze"
        elif any(word in message_lower for word in ["export", "save", "output"]):
            intent["type"] = "export"
            intent["action"] = "export"

        return intent

    def _generate_instructions(self, intent: Dict, tools: List, context: Dict) -> List[str]:
        """Generate step-by-step instructions for chat mode"""
        instructions = []

        if intent["type"] == "creation":
            instructions.append("To create the requested object:")
            for i, tool in enumerate(tools, 1):
                instructions.append(f"{i}. Use {tool.name} tool with the following parameters:")
                if hasattr(tool, 'get_parameters'):
                    for param, desc in tool.get_parameters().items():
                        instructions.append(f"   - {param}: {desc}")

        elif intent["type"] == "modification":
            instructions.append("To modify the object:")
            instructions.append("1. Select the target object")
            for i, tool in enumerate(tools, 2):
                instructions.append(f"{i}. Apply {tool.name} with appropriate parameters")

        # Add safety reminders
        instructions.append("\nRemember to:")
        instructions.append("- Save your work before making changes")
        instructions.append("- Use undo (Ctrl+Z) if needed")

        return instructions

    def _create_execution_plan(self, intent: Dict, tools: List, context: Dict) -> Dict:
        """Create a detailed execution plan"""
        plan = {
            "id": f"plan_{datetime.now().timestamp()}",
            "intent": intent,
            "steps": [],
            "estimated_duration": 0,
            "risk_level": "low",
            "rollback_possible": True
        }

        # Create execution steps
        for i, tool in enumerate(tools):
            step = {
                "order": i + 1,
                "tool": tool.name,
                "tool_id": getattr(tool, 'id', tool.name),
                "parameters": {},
                "description": f"Execute {tool.name}",
                "estimated_duration": 1.0,
                "dependencies": []
            }

            # Add parameters based on tool requirements
            if hasattr(tool, 'get_required_parameters'):
                step["parameters"] = self._infer_parameters(tool, context)

            plan["steps"].append(step)
            plan["estimated_duration"] += step["estimated_duration"]

        # Assess risk level
        if any(word in str(intent) for word in ["delete", "remove", "clear"]):
            plan["risk_level"] = "high"
        elif len(tools) > 3:
            plan["risk_level"] = "medium"

        return plan

    def _infer_parameters(self, tool, context: Dict) -> Dict:
        """Infer tool parameters from context"""
        # This will be enhanced with AI-based parameter inference
        params = {}

        # Get default parameters if available
        if hasattr(tool, 'get_default_parameters'):
            params = tool.get_default_parameters()

        return params

    def _execute_plan(self, plan: Dict) -> Dict:
        """Execute the plan using the execution pipeline"""
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
                    step_result = self._execute_step(step)
                    result["executed_steps"].append(step_result)
                    if not step_result["success"]:
                        result["failed_step"] = step
                        break
                else:
                    result["success"] = True

            self._set_state(ExecutionState.COMPLETED)

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

    def _execute_step(self, step: Dict) -> Dict:
        """Execute a single step of the plan"""
        # This is a placeholder - actual implementation will use tool registry
        return {
            "step": step["order"],
            "tool": step["tool"],
            "success": True,
            "output": f"Executed {step['tool']} successfully"
        }

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
            "config": self.config.copy()
        }

    def update_config(self, config: Dict):
        """Update agent configuration"""
        self.config.update(config)
        FreeCAD.Console.PrintMessage(f"Agent Manager: Configuration updated\n")
