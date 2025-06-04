"""Tool Selector - Selects appropriate tools based on natural language input"""

from typing import List, Dict, Optional, Tuple, Any
import re
from dataclasses import dataclass
from .semantic_matcher import SemanticMatcher, Match
from .tool_capabilities import get_capability_registry, CapabilityType


@dataclass
class ToolMatch:
    """Represents a tool match result"""
    tool_name: str
    tool_id: str
    confidence: float
    parameters: Dict[str, Any]
    reason: str
    semantic_score: Optional[float] = None
    capability_match: Optional[bool] = None


class ToolSelector:
    """
    Selects appropriate tools based on natural language input.
    Uses both pattern matching and semantic similarity.
    """

    def __init__(self, tool_registry=None):
        """Initialize the Tool Selector"""
        self.tool_registry = tool_registry
        self.semantic_matcher = SemanticMatcher()
        self.capability_registry = get_capability_registry()

        # Pattern-based tool detection
        self.tool_patterns = self._build_tool_patterns()

        # Tool aliases and synonyms
        self.tool_aliases = self._build_tool_aliases()

        # Parameter extraction patterns
        self.param_patterns = self._build_param_patterns()

        # Initialize semantic matcher with tool data
        self._initialize_semantic_matcher()

    def _build_tool_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Build regex patterns for tool detection"""
        return {
            "primitives.create_box": [
                re.compile(r'\b(create|make|add|build)\s+(a\s+)?(box|cube|rectangular)', re.I),
                re.compile(r'\bbox\s+(with|of)\s+dimensions?', re.I),
            ],
            "primitives.create_cylinder": [
                re.compile(r'\b(create|make|add|build)\s+(a\s+)?(cylinder|pipe|tube)', re.I),
                re.compile(r'\bcylinder\s+(with|of)\s+(radius|diameter)', re.I),
            ],
            "primitives.create_sphere": [
                re.compile(r'\b(create|make|add|build)\s+(a\s+)?(sphere|ball|globe)', re.I),
                re.compile(r'\bsphere\s+(with|of)\s+radius', re.I),
            ],
            "operations.move": [
                re.compile(r'\b(move|translate|shift|position)\s+(the\s+)?(\w+)?', re.I),
                re.compile(r'\b(place|put)\s+(it|the\s+\w+)\s+at', re.I),
            ],
            "operations.rotate": [
                re.compile(r'\b(rotate|turn|spin)\s+(the\s+)?(\w+)?', re.I),
                re.compile(r'\b(rotation|angle)\s+of\s+\d+', re.I),
            ],
            "operations.scale": [
                re.compile(r'\b(scale|resize|size|enlarge|shrink)\s+(the\s+)?(\w+)?', re.I),
                re.compile(r'\b(make|scale)\s+(it|the\s+\w+)\s+(larger|smaller|bigger)', re.I),
            ],
            "operations.delete": [
                re.compile(r'\b(delete|remove|erase|clear)\s+(the\s+)?(\w+)?', re.I),
                re.compile(r'\bget\s+rid\s+of\s+(the\s+)?(\w+)?', re.I),
            ],
            "measurements.distance": [
                re.compile(r'\b(measure|calculate|find)\s+(the\s+)?distance', re.I),
                re.compile(r'\bhow\s+far\s+(is|between)', re.I),
            ],
            "measurements.area": [
                re.compile(r'\b(measure|calculate|find)\s+(the\s+)?area', re.I),
                re.compile(r'\bsurface\s+area\s+of', re.I),
            ],
            "selection.select_all": [
                re.compile(r'\bselect\s+all', re.I),
                re.compile(r'\b(pick|choose|highlight)\s+everything', re.I),
            ],
            "selection.select_by_type": [
                re.compile(r'\bselect\s+all\s+(\w+)s?', re.I),
                re.compile(r'\b(pick|choose)\s+(?:all\s+)?(?:the\s+)?(\w+)s?', re.I),
            ]
        }

    def _build_tool_aliases(self) -> Dict[str, List[str]]:
        """Build tool aliases for flexible matching"""
        return {
            "primitives.create_box": ["box", "cube", "rectangular prism", "block"],
            "primitives.create_cylinder": ["cylinder", "pipe", "tube", "rod"],
            "primitives.create_sphere": ["sphere", "ball", "globe", "orb"],
            "primitives.create_cone": ["cone", "pyramid", "taper"],
            "operations.move": ["move", "translate", "shift", "position", "place"],
            "operations.rotate": ["rotate", "turn", "spin", "revolve", "twist"],
            "operations.scale": ["scale", "resize", "size", "enlarge", "shrink"],
            "operations.delete": ["delete", "remove", "erase", "clear", "destroy"],
            "operations.copy": ["copy", "duplicate", "clone", "replicate"],
            "operations.mirror": ["mirror", "reflect", "flip"],
            "operations.extrude": ["extrude", "extend", "pull", "push"],
            "operations.revolve": ["revolve", "lathe", "spin", "rotate around"],
            "operations.fillet": ["fillet", "round", "smooth", "blend"],
            "operations.chamfer": ["chamfer", "bevel", "angle", "slope"]
        }

    def _build_param_patterns(self) -> Dict[str, re.Pattern]:
        """Build patterns for parameter extraction"""
        return {
            "dimension": re.compile(r'(\d+(?:\.\d+)?)\s*(mm|cm|m|inch|inches)?', re.I),
            "position": re.compile(r'at\s*\(?\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)?', re.I),
            "angle": re.compile(r'(\d+(?:\.\d+)?)\s*(degrees?|deg|radians?|rad|°)', re.I),
            "radius": re.compile(r'radius\s*(?:of\s*)?(\d+(?:\.\d+)?)', re.I),
            "diameter": re.compile(r'diameter\s*(?:of\s*)?(\d+(?:\.\d+)?)', re.I),
            "count": re.compile(r'(\d+)\s+(?:times?|copies|instances?)', re.I),
            "axis": re.compile(r'(?:along|around)\s+(?:the\s+)?(x|y|z)[\s-]?axis', re.I),
            "color": re.compile(r'\b(red|green|blue|yellow|orange|purple|black|white|gray|grey)\b', re.I),
            "percentage": re.compile(r'(\d+(?:\.\d+)?)\s*%', re.I)
        }

    def _initialize_semantic_matcher(self):
        """Initialize semantic matcher with tool data"""
        if not self.tool_registry:
            return

        # Add embeddings for each registered tool
        for tool_id, tool_info in self.tool_registry.get_all_tools().items():
            # Get capability info if available
            capability = self.capability_registry.get(tool_id)

            if capability:
                # Use rich capability data
                description = capability.detailed_description
                keywords = capability.keywords
                examples = [ex.input_text for ex in capability.examples]
            else:
                # Fall back to basic tool info
                description = tool_info.get("description", "")
                keywords = self.tool_aliases.get(tool_id, [])
                examples = []

            self.semantic_matcher.add_tool_embedding(
                tool_id=tool_id,
                description=description,
                keywords=keywords,
                examples=examples
            )

        # Finalize embeddings for TF-IDF
        self.semantic_matcher.finalize_embeddings()

    def select_tool(self, text: str, context: Optional[Dict] = None) -> List[ToolMatch]:
        """
        Select appropriate tools for the given text

        Args:
            text: Natural language input
            context: Optional context information

        Returns:
            List of ToolMatch objects sorted by confidence
        """
        matches = []

        # 1. Pattern-based matching
        pattern_matches = self._pattern_based_matching(text)

        # 2. Semantic matching
        semantic_matches = self._semantic_matching(text)

        # 3. Capability-based matching
        capability_matches = self._capability_based_matching(text, context)

        # 4. Combine and deduplicate matches
        combined_matches = self._combine_matches(
            pattern_matches, semantic_matches, capability_matches
        )

        # 5. Extract parameters for each match
        for match in combined_matches:
            match.parameters = self._extract_parameters(text, match.tool_id)

        # 6. Apply context-based adjustments
        if context:
            combined_matches = self._apply_context_adjustments(combined_matches, context)

        # 7. Sort by confidence
        combined_matches.sort(key=lambda x: x.confidence, reverse=True)

        return combined_matches

    def _pattern_based_matching(self, text: str) -> List[ToolMatch]:
        """Perform pattern-based tool matching"""
        matches = []
        text_lower = text.lower()

        for tool_id, patterns in self.tool_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    # Calculate confidence based on pattern specificity
                    confidence = 0.8

                    # Boost confidence for exact matches
                    if tool_id in self.tool_aliases:
                        for alias in self.tool_aliases[tool_id]:
                            if alias in text_lower:
                                confidence = 0.9
                                break

                    matches.append(ToolMatch(
                        tool_name=self._get_tool_name(tool_id),
                        tool_id=tool_id,
                        confidence=confidence,
                        parameters={},
                        reason="Pattern match"
                    ))
                    break  # Only one match per tool

        return matches

    def _semantic_matching(self, text: str) -> List[ToolMatch]:
        """Perform semantic similarity matching"""
        semantic_results = self.semantic_matcher.match(text, top_k=5, min_score=0.3)

        matches = []
        for result in semantic_results:
            # Convert semantic match to ToolMatch
            match = ToolMatch(
                tool_name=result.tool_name,
                tool_id=result.tool_id,
                confidence=result.similarity_score * 0.9,  # Slightly lower than pattern
                parameters={},
                reason=f"Semantic match: {result.explanation}",
                semantic_score=result.similarity_score
            )
            matches.append(match)

        return matches

    def _capability_based_matching(self, text: str,
                                  context: Optional[Dict]) -> List[ToolMatch]:
        """Match based on tool capabilities"""
        matches = []

        # Extract potential keywords from text
        keywords = self._extract_keywords(text)

        # Query capabilities
        capabilities = self.capability_registry.query(keywords=keywords)

        for capability in capabilities:
            # Check if requirements are met
            reqs_met, _ = self.capability_registry.check_requirements(capability.tool_id)

            confidence = 0.7 if reqs_met else 0.4

            matches.append(ToolMatch(
                tool_name=capability.name,
                tool_id=capability.tool_id,
                confidence=confidence,
                parameters={},
                reason="Capability match",
                capability_match=True
            ))

        return matches

    def _combine_matches(self, *match_lists) -> List[ToolMatch]:
        """Combine and deduplicate matches from different sources"""
        combined = {}

        for matches in match_lists:
            for match in matches:
                if match.tool_id in combined:
                    # Update with higher confidence
                    existing = combined[match.tool_id]
                    if match.confidence > existing.confidence:
                        combined[match.tool_id] = match
                    else:
                        # Combine reasons
                        existing.reason += f"; {match.reason}"
                        # Average semantic scores if both have them
                        if match.semantic_score and existing.semantic_score:
                            existing.semantic_score = (
                                existing.semantic_score + match.semantic_score
                            ) / 2
                else:
                    combined[match.tool_id] = match

        return list(combined.values())

    def _extract_parameters(self, text: str, tool_id: str) -> Dict[str, Any]:
        """Extract parameters from text for a specific tool"""
        params = {}

        # Get capability definition
        capability = self.capability_registry.get(tool_id)

        # Extract dimensions
        dim_matches = self.param_patterns["dimension"].findall(text)
        if dim_matches and capability:
            # Map to appropriate parameter names
            param_names = ["length", "width", "height", "radius", "diameter"]
            expected_params = [p.name for p in capability.parameters
                             if p.name in param_names]

            for i, (value, unit) in enumerate(dim_matches):
                if i < len(expected_params):
                    params[expected_params[i]] = float(value)
                    if unit:
                        params[f"{expected_params[i]}_unit"] = unit

        # Extract position
        pos_match = self.param_patterns["position"].search(text)
        if pos_match:
            params["position"] = [
                float(pos_match.group(1)),
                float(pos_match.group(2)),
                float(pos_match.group(3))
            ]

        # Extract angle
        angle_match = self.param_patterns["angle"].search(text)
        if angle_match:
            angle_value = float(angle_match.group(1))
            angle_unit = angle_match.group(2)

            # Convert to radians if needed
            if angle_unit in ["degrees", "deg", "°"]:
                params["angle"] = angle_value * 3.14159 / 180
            else:
                params["angle"] = angle_value

        # Extract axis
        axis_match = self.param_patterns["axis"].search(text)
        if axis_match:
            axis_map = {"x": [1, 0, 0], "y": [0, 1, 0], "z": [0, 0, 1]}
            params["axis"] = axis_map[axis_match.group(1).lower()]

        # Extract color
        color_match = self.param_patterns["color"].search(text)
        if color_match:
            params["color"] = color_match.group(1)

        # Tool-specific parameter extraction
        if tool_id == "primitives.create_cylinder":
            # Check for radius/diameter
            radius_match = self.param_patterns["radius"].search(text)
            if radius_match:
                params["radius"] = float(radius_match.group(1))
            else:
                diameter_match = self.param_patterns["diameter"].search(text)
                if diameter_match:
                    params["radius"] = float(diameter_match.group(1)) / 2

        return params

    def _apply_context_adjustments(self, matches: List[ToolMatch],
                                  context: Dict) -> List[ToolMatch]:
        """Apply context-based adjustments to matches"""
        # Boost confidence for tools that match current state
        if "selection" in context and context["selection"]["has_selection"]:
            # Boost modification tools when objects are selected
            for match in matches:
                if match.tool_id.startswith("operations."):
                    match.confidence *= 1.1
                    match.reason += " (objects selected)"

        # Adjust based on current workbench
        if "workbench" in context:
            workbench = context["workbench"]
            for match in matches:
                # Boost tools from current workbench
                if match.tool_id.startswith(workbench.lower()):
                    match.confidence *= 1.15

        return matches

    def _get_tool_name(self, tool_id: str) -> str:
        """Get human-readable tool name"""
        if self.tool_registry:
            tool_info = self.tool_registry.get_tool(tool_id)
            if tool_info and "name" in tool_info:
                return tool_info["name"]

        # Fall back to ID-based name
        parts = tool_id.split(".")
        if len(parts) > 1:
            return parts[-1].replace("_", " ").title()
        return tool_id

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Simple keyword extraction
        words = text.lower().split()

        # Filter common words
        stop_words = {"the", "a", "an", "of", "in", "at", "to", "for", "with", "by"}
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        return keywords

    def get_tool_parameters(self, tool_id: str) -> List[Dict[str, Any]]:
        """Get parameter definitions for a tool"""
        capability = self.capability_registry.get(tool_id)

        if capability:
            return [
                {
                    "name": p.name,
                    "type": p.type,
                    "description": p.description,
                    "required": p.required,
                    "default": p.default,
                    "constraints": p.constraints
                }
                for p in capability.parameters
            ]

        # Fall back to tool registry
        if self.tool_registry:
            tool_info = self.tool_registry.get_tool(tool_id)
            if tool_info and "parameters" in tool_info:
                return tool_info["parameters"]

        return []

    def validate_parameters(self, tool_id: str,
                          parameters: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate parameters for a tool"""
        return self.capability_registry.validate_parameters(tool_id, parameters)

    def get_tool_examples(self, tool_id: str) -> List[str]:
        """Get usage examples for a tool"""
        capability = self.capability_registry.get(tool_id)

        if capability:
            return [ex.input_text for ex in capability.examples]

        return []

    def learn_from_execution(self, text: str, tool_id: str,
                           success: bool, feedback: Optional[str] = None):
        """Learn from execution results"""
        # Update semantic matcher
        self.semantic_matcher.record_match_result(text, tool_id, success, feedback)

    def get_statistics(self) -> Dict[str, Any]:
        """Get selection statistics"""
        return self.semantic_matcher.get_match_statistics()
