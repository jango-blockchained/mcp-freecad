"""Instruction Parser - Parses structured instructions from natural language"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional



class InstructionType(Enum):
    """Types of instructions"""

    SINGLE_STEP = "single_step"
    MULTI_STEP = "multi_step"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    COMPOSITE = "composite"


@dataclass
class Parameter:
    """Represents a parameter in an instruction"""

    name: str
    value: Any
    type: str
    unit: Optional[str] = None
    is_variable: bool = False
    constraints: Optional[Dict] = None


@dataclass
class Condition:
    """Represents a condition for conditional instructions"""

    type: str  # "if", "unless", "while", "until"
    expression: str
    parameters: List[Parameter]


@dataclass
class Instruction:
    """Represents a parsed instruction"""

    type: InstructionType
    action: str
    target: Optional[str]
    parameters: List[Parameter]
    conditions: List[Condition]
    sub_instructions: List["Instruction"]
    raw_text: str
    confidence: float


class InstructionParser:
    """
    Parses natural language instructions into structured format
    that can be executed by the agent system.
    """

    def __init__(self):
        """Initialize the Instruction Parser"""
        self.instruction_patterns = self._build_instruction_patterns()
        self.parameter_patterns = self._build_parameter_patterns()
        self.condition_patterns = self._build_condition_patterns()
        self.unit_conversions = self._build_unit_conversions()

        # Instruction templates
        self.templates = self._load_instruction_templates()

        # Common instruction verbs
        self.action_verbs = {
            "create": ["create", "make", "build", "add", "generate"],
            "modify": ["modify", "change", "edit", "update", "alter"],
            "delete": ["delete", "remove", "erase", "clear"],
            "move": ["move", "translate", "shift", "position"],
            "rotate": ["rotate", "turn", "spin", "revolve"],
            "scale": ["scale", "resize", "enlarge", "shrink"],
            "copy": ["copy", "duplicate", "clone", "replicate"],
            "measure": ["measure", "calculate", "compute", "find"],
            "select": ["select", "pick", "choose", "highlight"],
        }

        # Parameter type mappings
        self.parameter_types = {
            "numeric": ["length", "width", "height", "radius", "angle", "distance"],
            "position": ["position", "location", "coordinates", "point"],
            "vector": ["direction", "axis", "normal"],
            "boolean": ["visible", "enabled", "active"],
            "string": ["name", "label", "description"],
            "reference": ["object", "target", "source"],
        }

    def parse(self, text: str, context: Optional[Dict] = None) -> List[Instruction]:
        """
        Parse natural language text into structured instructions

        Args:
            text: Natural language instruction text
            context: Optional context information

        Returns:
            List of parsed instructions
        """
        # Normalize text
        text = self._normalize_text(text)

        # Split into potential instruction segments
        segments = self._split_instructions(text)

        instructions = []
        for segment in segments:
            instruction = self._parse_segment(segment, context)
            if instruction:
                instructions.append(instruction)

        # Link related instructions
        instructions = self._link_instructions(instructions)

        # Optimize instruction sequence
        instructions = self._optimize_instructions(instructions)

        return instructions

    def _build_instruction_patterns(self) -> Dict[str, re.Pattern]:
        """Build regex patterns for instruction parsing"""
        return {
            # Single action pattern: "create a box"
            "single_action": re.compile(
                r"^(\w+)\s+(?:a\s+|an\s+|the\s+)?(.+?)(?:\s+with\s+(.+))?$", re.I
            ),
            # Multi-step pattern: "first create a box, then move it"
            "multi_step": re.compile(
                r"(?:first\s+|then\s+|next\s+|finally\s+)(.+?)(?:,|and|$)", re.I
            ),
            # Conditional pattern: "if selected, rotate 45 degrees"
            "conditional": re.compile(
                r"(?:if|when|unless)\s+(.+?),\s*(?:then\s+)?(.+)", re.I
            ),
            # Iterative pattern: "repeat 5 times: create a box"
            "iterative": re.compile(
                r"(?:repeat|iterate)\s+(\d+)\s+times?:\s*(.+)", re.I
            ),
            # For each pattern: "for each selected object, scale by 2"
            "for_each": re.compile(r"for\s+each\s+(.+?),\s*(.+)", re.I),
        }

    def _build_parameter_patterns(self) -> Dict[str, re.Pattern]:
        """Build patterns for parameter extraction"""
        return {
            # Dimension: "10mm", "5.5 inches"
            "dimension": re.compile(
                r"(\d+(?:\.\d+)?)\s*(mm|cm|m|inch|inches|in|ft|feet)?", re.I
            ),
            # Position: "at (10, 20, 30)" or "at position 10, 20, 30"
            "position": re.compile(
                r"(?:at|to)\s*(?:position\s*)?\(?\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)?",
                re.I,
            ),
            # Angle: "45 degrees", "90°", "1.57 radians"
            "angle": re.compile(
                r"(\d+(?:\.\d+)?)\s*(degrees?|deg|radians?|rad|°)", re.I
            ),
            # Count: "5 times", "3 copies"
            "count": re.compile(r"(\d+)\s+(?:times?|copies|instances?)", re.I),
            # Percentage: "50%", "200 percent"
            "percentage": re.compile(r"(\d+(?:\.\d+)?)\s*(?:%|percent)", re.I),
            # Named parameter: "with radius = 10"
            "named": re.compile(r"(\w+)\s*=\s*([^,\s]+)", re.I),
            # Color: "red", "blue", "#FF0000"
            "color": re.compile(
                r"\b(red|green|blue|yellow|orange|purple|black|white|gray|grey|#[0-9A-Fa-f]{6})\b",
                re.I,
            ),
            # Reference: "the selected object", "all boxes"
            "reference": re.compile(
                r"\b(?:the\s+)?(selected|current|active|all|last|previous)\s*(\w+)?\b",
                re.I,
            ),
        }

    def _build_condition_patterns(self) -> Dict[str, re.Pattern]:
        """Build patterns for condition extraction"""
        return {
            "if_condition": re.compile(r"if\s+(.+?)(?:,|then)", re.I),
            "unless_condition": re.compile(r"unless\s+(.+?)(?:,|then)", re.I),
            "while_condition": re.compile(r"while\s+(.+?)(?:,|do)", re.I),
            "until_condition": re.compile(r"until\s+(.+?)(?:,|do)", re.I),
        }

    def _load_instruction_templates(self) -> Dict[str, Dict]:
        """Load instruction templates for common operations"""
        return {
            "create_box": {
                "action": "create",
                "target": "box",
                "required_params": ["length", "width", "height"],
                "optional_params": ["position", "name"],
            },
            "move_object": {
                "action": "move",
                "target": "object",
                "required_params": ["vector"],
                "optional_params": ["relative", "copy"],
            },
            "rotate_object": {
                "action": "rotate",
                "target": "object",
                "required_params": ["angle", "axis"],
                "optional_params": ["center", "copy"],
            },
        }

    def _normalize_text(self, text: str) -> str:
        """Normalize instruction text"""
        # Remove extra whitespace
        text = " ".join(text.split())

        # Standardize punctuation
        text = text.strip()
        if not text.endswith("."):
            text += "."

        return text

    def _split_instructions(self, text: str) -> List[str]:
        """Split text into individual instruction segments"""
        segments = []

        # Split by common delimiters
        # First split by periods that aren't part of numbers
        parts = re.split(r"\.(?!\d)", text)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Further split by instruction keywords
            if any(
                keyword in part.lower()
                for keyword in ["then", "next", "after that", "finally"]
            ):
                sub_parts = re.split(
                    r"\b(?:then|next|after that|finally)\b", part, flags=re.I
                )
                segments.extend([p.strip() for p in sub_parts if p.strip()])
            else:
                segments.append(part)

        return segments

    def _parse_segment(
        self, segment: str, context: Optional[Dict]
    ) -> Optional[Instruction]:
        """Parse a single instruction segment"""
        # Check for different instruction types

        # Check for iterative pattern
        iterative_match = self.instruction_patterns["iterative"].match(segment)
        if iterative_match:
            return self._parse_iterative_instruction(iterative_match, segment)

        # Check for conditional pattern
        conditional_match = self.instruction_patterns["conditional"].match(segment)
        if conditional_match:
            return self._parse_conditional_instruction(conditional_match, segment)

        # Check for for-each pattern
        for_each_match = self.instruction_patterns["for_each"].match(segment)
        if for_each_match:
            return self._parse_for_each_instruction(for_each_match, segment)

        # Default to single action
        return self._parse_single_action(segment, context)

    def _parse_single_action(
        self, segment: str, context: Optional[Dict]
    ) -> Optional[Instruction]:
        """Parse a single action instruction"""
        # Extract action verb
        action = None
        target = None

        words = segment.lower().split()

        # Find action verb
        for word in words:
            for action_type, verbs in self.action_verbs.items():
                if word in verbs:
                    action = action_type
                    break
            if action:
                break

        if not action:
            return None

        # Extract target
        action_match = self.instruction_patterns["single_action"].match(segment)
        if action_match:
            target = action_match.group(2)

        # Extract parameters
        parameters = self._extract_parameters(segment)

        # Extract conditions
        conditions = self._extract_conditions(segment)

        return Instruction(
            type=InstructionType.SINGLE_STEP,
            action=action,
            target=target,
            parameters=parameters,
            conditions=conditions,
            sub_instructions=[],
            raw_text=segment,
            confidence=0.8,
        )

    def _parse_iterative_instruction(
        self, match: re.Match, segment: str
    ) -> Instruction:
        """Parse an iterative instruction"""
        count = int(match.group(1))
        action_text = match.group(2)

        # Parse the action to repeat
        sub_instruction = self._parse_single_action(action_text, None)

        # Create count parameter
        count_param = Parameter(name="iterations", value=count, type="numeric")

        return Instruction(
            type=InstructionType.LOOP,
            action="repeat",
            target=None,
            parameters=[count_param],
            conditions=[],
            sub_instructions=[sub_instruction] if sub_instruction else [],
            raw_text=segment,
            confidence=0.9,
        )

    def _parse_conditional_instruction(
        self, match: re.Match, segment: str
    ) -> Instruction:
        """Parse a conditional instruction"""
        condition_text = match.group(1)
        action_text = match.group(2)

        # Parse condition
        condition = Condition(
            type="if",
            expression=condition_text,
            parameters=self._extract_parameters(condition_text),
        )

        # Parse action
        sub_instruction = self._parse_single_action(action_text, None)

        return Instruction(
            type=InstructionType.CONDITIONAL,
            action="conditional",
            target=None,
            parameters=[],
            conditions=[condition],
            sub_instructions=[sub_instruction] if sub_instruction else [],
            raw_text=segment,
            confidence=0.85,
        )

    def _parse_for_each_instruction(self, match: re.Match, segment: str) -> Instruction:
        """Parse a for-each instruction"""
        target_text = match.group(1)
        action_text = match.group(2)

        # Parse action
        sub_instruction = self._parse_single_action(action_text, None)

        return Instruction(
            type=InstructionType.LOOP,
            action="for_each",
            target=target_text,
            parameters=[],
            conditions=[],
            sub_instructions=[sub_instruction] if sub_instruction else [],
            raw_text=segment,
            confidence=0.85,
        )

    def _extract_parameters(self, text: str) -> List[Parameter]:
        """Extract parameters from instruction text"""
        parameters = []

        # Extract dimensions
        for match in self.parameter_patterns["dimension"].finditer(text):
            value = float(match.group(1))
            unit = match.group(2) or "mm"

            # Determine parameter name based on context
            param_name = self._infer_dimension_name(text, len(parameters))

            parameters.append(
                Parameter(name=param_name, value=value, type="numeric", unit=unit)
            )

        # Extract position
        pos_match = self.parameter_patterns["position"].search(text)
        if pos_match:
            parameters.append(
                Parameter(
                    name="position",
                    value={
                        "x": float(pos_match.group(1)),
                        "y": float(pos_match.group(2)),
                        "z": float(pos_match.group(3)),
                    },
                    type="position",
                )
            )

        # Extract angles
        for match in self.parameter_patterns["angle"].finditer(text):
            value = float(match.group(1))
            unit = match.group(2)

            # Convert to radians if needed
            if unit in ["degrees", "deg", "°"]:
                value_rad = value * 3.14159 / 180
            else:
                value_rad = value

            parameters.append(
                Parameter(name="angle", value=value_rad, type="numeric", unit="radians")
            )

        # Extract named parameters
        for match in self.parameter_patterns["named"].finditer(text):
            param_name = match.group(1)
            param_value = match.group(2)

            # Try to parse value
            try:
                # Try numeric
                param_value = float(param_value)
                param_type = "numeric"
            except ValueError:
                # Keep as string
                param_type = "string"

            parameters.append(
                Parameter(name=param_name, value=param_value, type=param_type)
            )

        return parameters

    def _extract_conditions(self, text: str) -> List[Condition]:
        """Extract conditions from instruction text"""
        conditions = []

        for cond_type, pattern in self.condition_patterns.items():
            match = pattern.search(text)
            if match:
                condition_text = match.group(1)
                conditions.append(
                    Condition(
                        type=cond_type.replace("_condition", ""),
                        expression=condition_text,
                        parameters=self._extract_parameters(condition_text),
                    )
                )

        return conditions

    def _infer_dimension_name(self, text: str, index: int) -> str:
        """Infer dimension parameter name from context"""
        text_lower = text.lower()

        # Check for explicit dimension names
        if "length" in text_lower:
            return "length"
        elif "width" in text_lower:
            return "width"
        elif "height" in text_lower:
            return "height"
        elif "radius" in text_lower:
            return "radius"
        elif "diameter" in text_lower:
            return "diameter"

        # Default based on index
        dimension_names = ["length", "width", "height"]
        if index < len(dimension_names):
            return dimension_names[index]

        return f"dimension_{index + 1}"

    def _link_instructions(self, instructions: List[Instruction]) -> List[Instruction]:
        """Link related instructions into composite instructions"""
        if len(instructions) <= 1:
            return instructions

        # Look for sequences that should be grouped
        linked = []
        i = 0

        while i < len(instructions):
            current = instructions[i]

            # Check if this starts a multi-step sequence
            if i + 1 < len(instructions):
                next_inst = instructions[i + 1]

                # Check if they're related (e.g., create then move)
                if self._are_related_instructions(current, next_inst):
                    # Create composite instruction
                    composite = Instruction(
                        type=InstructionType.MULTI_STEP,
                        action="composite",
                        target=None,
                        parameters=[],
                        conditions=[],
                        sub_instructions=[current, next_inst],
                        raw_text=f"{current.raw_text} {next_inst.raw_text}",
                        confidence=min(current.confidence, next_inst.confidence),
                    )
                    linked.append(composite)
                    i += 2
                    continue

            linked.append(current)
            i += 1

        return linked

    def _are_related_instructions(self, inst1: Instruction, inst2: Instruction) -> bool:
        """Check if two instructions are related and should be linked"""
        # Instructions are related if the second operates on the result of the first
        creation_actions = ["create", "make", "build", "add"]
        modification_actions = ["move", "rotate", "scale", "modify"]

        if inst1.action in creation_actions and inst2.action in modification_actions:
            # Check if inst2 refers to the created object
            if inst2.target and ("it" in inst2.target or "the" in inst2.target):
                return True

        return False

    def _optimize_instructions(
        self, instructions: List[Instruction]
    ) -> List[Instruction]:
        """Optimize instruction sequence for efficient execution"""
        # This is a placeholder for optimization logic
        # Could include:
        # - Combining similar operations
        # - Reordering for efficiency
        # - Removing redundant operations
        return instructions

    def to_execution_plan(self, instructions: List[Instruction]) -> Dict[str, Any]:
        """Convert parsed instructions to execution plan format"""
        steps = []

        for i, instruction in enumerate(instructions):
            step = {
                "order": i + 1,
                "tool": self._map_action_to_tool(instruction.action),
                "tool_id": f"{instruction.action}.{instruction.target}",
                "parameters": self._convert_parameters(instruction.parameters),
                "description": self._generate_description(instruction),
                "conditions": [
                    {"type": cond.type, "expression": cond.expression}
                    for cond in instruction.conditions
                ],
            }

            # Add sub-steps for composite instructions
            if instruction.sub_instructions:
                sub_plan = self.to_execution_plan(instruction.sub_instructions)
                step["sub_steps"] = sub_plan["steps"]

            steps.append(step)

        return {
            "steps": steps,
            "estimated_duration": len(steps) * 2.0,  # Rough estimate
            "complexity": self._calculate_complexity(instructions),
        }

    def _map_action_to_tool(self, action: str) -> str:
        """Map action to tool name"""
        action_tool_map = {
            "create": "primitives",
            "modify": "operations",
            "delete": "operations",
            "move": "operations",
            "rotate": "operations",
            "scale": "operations",
            "measure": "measurements",
            "select": "selection",
        }
        return action_tool_map.get(action, "unknown")

    def _convert_parameters(self, parameters: List[Parameter]) -> Dict[str, Any]:
        """Convert Parameter objects to dictionary"""
        param_dict = {}

        for param in parameters:
            if param.type == "position":
                param_dict[param.name] = param.value
            elif param.type == "numeric":
                param_dict[param.name] = param.value
                if param.unit:
                    param_dict[f"{param.name}_unit"] = param.unit
            else:
                param_dict[param.name] = param.value

        return param_dict

    def _generate_description(self, instruction: Instruction) -> str:
        """Generate human-readable description of instruction"""
        desc = f"{instruction.action.title()}"

        if instruction.target:
            desc += f" {instruction.target}"

        if instruction.parameters:
            param_strs = []
            for param in instruction.parameters[:3]:  # Limit to first 3
                if param.name == "position":
                    param_strs.append(
                        f"at ({param.value['x']}, {param.value['y']}, {param.value['z']})"
                    )
                else:
                    param_strs.append(f"{param.name}: {param.value}")

            if param_strs:
                desc += f" with {', '.join(param_strs)}"

        return desc

    def _calculate_complexity(self, instructions: List[Instruction]) -> str:
        """Calculate complexity level of instructions"""
        total_steps = len(instructions)
        total_params = sum(len(inst.parameters) for inst in instructions)
        has_conditions = any(inst.conditions for inst in instructions)
        has_iterations = any(inst.type == InstructionType.LOOP for inst in instructions)

        if total_steps > 10 or has_iterations:
            return "high"
        elif total_steps > 5 or has_conditions or total_params > 10:
            return "medium"
        else:
            return "low"
