"""
MCP Integrated AI Provider

This provider wraps any AI provider (Claude, Gemini, etc.) and gives it access to
MCP tools internally, allowing the AI to execute FreeCAD operations during conversations.

Author: jango-blockchained
"""

import json
import re
from typing import Dict, List, Optional, Any, Tuple

from ai.providers.base_provider import BaseAIProvider, AIResponse, AIMessage, MessageRole


class MCPIntegratedProvider(BaseAIProvider):
    """AI provider with integrated MCP tool access."""

    def __init__(self, base_provider: BaseAIProvider):
        """Initialize MCP integrated provider.

        Args:
            base_provider: The underlying AI provider (Claude, Gemini, etc.)
        """
        # Copy settings from base provider
        super().__init__(api_key=base_provider.api_key, model=base_provider.model)

        self.base_provider = base_provider
        self.tools_registry = {}
        self.resources_registry = {}

        # Initialize available tools and resources
        self._initialize_tools()
        self._initialize_resources()

        # Update system prompt to include tool usage instructions
        self._update_system_prompt()

    @property
    def name(self) -> str:
        """Return provider name."""
        return f"{self.base_provider.name} (MCP Integrated)"

    @property
    def supported_models(self) -> List[str]:
        """Return supported models from base provider."""
        return self.base_provider.supported_models

    def _initialize_tools(self):
        """Initialize available MCP tools."""
        try:
            # Import tools
            from tools.primitives import PrimitivesTool
            from tools.operations import OperationsTool
            from tools.measurements import MeasurementsTool
            from tools.export_import import ExportImportTool

            # Initialize tool instances
            primitives = PrimitivesTool()
            operations = OperationsTool()
            measurements = MeasurementsTool()
            export_import = ExportImportTool()

            # Register tools with descriptions
            self.tools_registry = {
                # Primitive tools
                "create_box": {
                    "tool": primitives,
                    "method": "create_box",
                    "description": "Create a box/cube primitive",
                    "parameters": ["length", "width", "height", "name?"],
                },
                "create_cylinder": {
                    "tool": primitives,
                    "method": "create_cylinder",
                    "description": "Create a cylinder primitive",
                    "parameters": ["radius", "height", "name?"],
                },
                "create_sphere": {
                    "tool": primitives,
                    "method": "create_sphere",
                    "description": "Create a sphere primitive",
                    "parameters": ["radius", "name?"],
                },
                "create_cone": {
                    "tool": primitives,
                    "method": "create_cone",
                    "description": "Create a cone primitive",
                    "parameters": ["radius1", "radius2", "height", "name?"],
                },
                # Boolean operations
                "boolean_union": {
                    "tool": operations,
                    "method": "boolean_union",
                    "description": "Perform boolean union of two objects",
                    "parameters": ["obj1_name", "obj2_name", "keep_originals?"],
                },
                "boolean_cut": {
                    "tool": operations,
                    "method": "boolean_cut",
                    "description": "Perform boolean cut (subtraction)",
                    "parameters": ["obj1_name", "obj2_name", "keep_originals?"],
                },
                # Measurements
                "measure_distance": {
                    "tool": measurements,
                    "method": "measure_distance",
                    "description": "Measure distance between points/objects",
                    "parameters": ["point1", "point2"],
                },
                "measure_volume": {
                    "tool": measurements,
                    "method": "measure_volume",
                    "description": "Measure volume of an object",
                    "parameters": ["obj_name"],
                },
                # Export
                "export_stl": {
                    "tool": export_import,
                    "method": "export_stl",
                    "description": "Export objects to STL file",
                    "parameters": ["filepath", "object_names?", "ascii?"],
                },
            }

            # Try to add advanced tools if available
            try:
                from tools.advanced import (
                    AssemblyToolProvider,
                    CAMToolProvider,
                    RenderingToolProvider,
                    SmitheryToolProvider,
                )

                assembly = AssemblyToolProvider()
                cam = CAMToolProvider()

                # Add assembly tools
                self.tools_registry["create_assembly"] = {
                    "tool": assembly,
                    "method": "execute_tool",
                    "description": "Create a new assembly",
                    "parameters": ["action='create_assembly'", "assembly_name"],
                }

                # Add CAM tools
                self.tools_registry["create_cam_job"] = {
                    "tool": cam,
                    "method": "execute_tool",
                    "description": "Create a CAM job",
                    "parameters": ["action='create_job'", "job_name", "base_object"],
                }

            except ImportError:
                pass  # Advanced tools not available

        except Exception as e:
            import FreeCAD

            FreeCAD.Console.PrintWarning(f"Failed to initialize MCP tools: {e}\n")

    def _initialize_resources(self):
        """Initialize available MCP resources."""
        try:
            from resources import (
                MaterialResourceProvider,
                ConstraintResourceProvider,
                MeasurementResourceProvider,
                CADModelResourceProvider,
            )

            # Initialize resource providers
            self.resources_registry = {
                "materials": MaterialResourceProvider(),
                "constraints": ConstraintResourceProvider(),
                "measurements": MeasurementResourceProvider(),
                "cad_model": CADModelResourceProvider(),
            }

        except Exception as e:
            import FreeCAD

            FreeCAD.Console.PrintWarning(f"Failed to initialize resources: {e}\n")

    def _update_system_prompt(self):
        """Update system prompt to include tool usage instructions."""
        tools_list = "\n".join(
            [
                f"- {name}: {info['description']} (params: {', '.join(info['parameters'])})"
                for name, info in self.tools_registry.items()
            ]
        )

        enhanced_prompt = f"""{self.base_provider.system_prompt}

You have access to the following MCP tools that you can use to execute FreeCAD operations:

{tools_list}

To use a tool, format your response with tool calls in this exact format:
<tool_use>
<tool_name>create_box</tool_name>
<parameters>
{{"length": 10, "width": 5, "height": 3}}
</parameters>
</tool_use>

You can use multiple tools in a single response. Always explain what you're doing before and after tool calls.

When users ask you to create objects, perform operations, or analyze models, use these tools to actually execute the operations in FreeCAD, don't just describe what to do.
"""

        self.base_provider.system_prompt = enhanced_prompt

    async def send_message(self, message: str, **kwargs) -> AIResponse:
        """Send message to AI and process any tool calls."""
        # Get response from base provider
        ai_response = await self.base_provider.send_message(message, **kwargs)

        # Check for tool calls in the response
        tool_calls = self._extract_tool_calls(ai_response.content)

        if tool_calls:
            # Execute tools and enhance response
            enhanced_content = await self._execute_tools_and_enhance(
                ai_response.content, tool_calls
            )

            # Create enhanced response
            return AIResponse(
                content=enhanced_content,
                thinking_process=ai_response.thinking_process,
                model=ai_response.model,
                usage=ai_response.usage,
                metadata={**ai_response.metadata, "tools_executed": len(tool_calls)},
            )

        return ai_response

    def _extract_tool_calls(self, content: str) -> List[Dict[str, Any]]:
        """Extract tool calls from AI response."""
        tool_calls = []

        # Find all tool_use blocks
        pattern = r"<tool_use>\s*<tool_name>(.*?)</tool_name>\s*<parameters>(.*?)</parameters>\s*</tool_use>"
        matches = re.findall(pattern, content, re.DOTALL)

        for tool_name, params_str in matches:
            try:
                tool_name = tool_name.strip()
                parameters = json.loads(params_str.strip())

                if tool_name in self.tools_registry:
                    tool_calls.append({"name": tool_name, "parameters": parameters})
            except json.JSONDecodeError:
                pass  # Invalid JSON, skip this tool call

        return tool_calls

    async def _execute_tools_and_enhance(
        self, original_content: str, tool_calls: List[Dict[str, Any]]
    ) -> str:
        """Execute tools and enhance the response with results."""
        enhanced_content = original_content

        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            parameters = tool_call["parameters"]

            # Execute the tool
            result = await self._execute_single_tool(tool_name, parameters)

            # Create result block
            result_block = f"""
<tool_result>
<tool_name>{tool_name}</tool_name>
<status>{'success' if result.get('success') else 'error'}</status>
<result>{json.dumps(result, indent=2)}</result>
</tool_result>"""

            # Replace the tool_use block with tool_result
            pattern = rf"<tool_use>\s*<tool_name>{re.escape(tool_name)}</tool_name>.*?</tool_use>"
            enhanced_content = re.sub(
                pattern, result_block, enhanced_content, count=1, flags=re.DOTALL
            )

        return enhanced_content

    async def _execute_single_tool(
        self, tool_name: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single tool and return the result."""
        try:
            if tool_name not in self.tools_registry:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}

            tool_info = self.tools_registry[tool_name]
            tool_instance = tool_info["tool"]
            method_name = tool_info["method"]

            # Get the method
            method = getattr(tool_instance, method_name)

            # Execute the tool
            if method_name == "execute_tool":
                # For advanced tools that use execute_tool pattern
                result = await method(tool_name, parameters)
            else:
                # For regular tools
                result = method(**parameters)

            return result

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def test_connection(self) -> bool:
        """Test connection using base provider."""
        return await self.base_provider.test_connection()

    def enable_thinking_mode(self, budget: int = 2000):
        """Enable thinking mode on base provider."""
        self.base_provider.enable_thinking_mode(budget)

    def disable_thinking_mode(self):
        """Disable thinking mode on base provider."""
        self.base_provider.disable_thinking_mode()

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        return [
            {
                "name": name,
                "description": info["description"],
                "parameters": info["parameters"],
            }
            for name, info in self.tools_registry.items()
        ]

    def get_available_resources(self) -> List[str]:
        """Get list of available resources."""
        return list(self.resources_registry.keys())
