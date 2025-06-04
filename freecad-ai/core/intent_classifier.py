"""Intent Classifier - Classifies user intent from natural language input"""

import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import FreeCAD


class IntentType(Enum):
    """Types of user intents"""
    CREATE = "create"
    MODIFY = "modify"
    DELETE = "delete"
    QUERY = "query"
    MEASURE = "measure"
    EXPORT = "export"
    IMPORT = "import"
    VIEW = "view"
    ANALYZE = "analyze"
    HELP = "help"
    CONFIGURE = "configure"
    UNKNOWN = "unknown"


class ActionType(Enum):
    """Types of actions within intents"""
    # Creation actions
    PRIMITIVE = "primitive"
    SKETCH = "sketch"
    FEATURE = "feature"
    ASSEMBLY = "assembly"

    # Modification actions
    TRANSFORM = "transform"
    BOOLEAN = "boolean"
    FILLET_CHAMFER = "fillet_chamfer"
    PATTERN = "pattern"

    # Query actions
    PROPERTIES = "properties"
    SELECTION = "selection"
    DOCUMENT = "document"

    # Analysis actions
    GEOMETRY = "geometry"
    PHYSICS = "physics"
    INTERFERENCE = "interference"


@dataclass
class Intent:
    """Represents a classified intent"""
    type: IntentType
    action: Optional[ActionType]
    confidence: float
    entities: List[Dict[str, Any]]
    parameters: Dict[str, Any]
    original_text: str
    keywords_matched: List[str]


class IntentClassifier:
    """
    Classifies user intent from natural language input
    to determine what action the user wants to perform.
    """

    def __init__(self):
        """Initialize the Intent Classifier"""
        self.intent_patterns = self._build_intent_patterns()
        self.entity_patterns = self._build_entity_patterns()
        self.parameter_extractors = self._build_parameter_extractors()

        # Intent keywords mapping
        self.intent_keywords = {
            IntentType.CREATE: [
                "create", "make", "build", "add", "new", "generate", "construct",
                "draw", "design", "model", "produce"
            ],
            IntentType.MODIFY: [
                "modify", "change", "edit", "update", "alter", "adjust", "transform",
                "move", "rotate", "scale", "resize", "extend", "trim"
            ],
            IntentType.DELETE: [
                "delete", "remove", "erase", "clear", "destroy", "eliminate",
                "cut", "subtract"
            ],
            IntentType.QUERY: [
                "what", "which", "where", "show", "find", "get", "list",
                "display", "tell", "info", "information"
            ],
            IntentType.MEASURE: [
                "measure", "calculate", "compute", "distance", "length", "area",
                "volume", "angle", "dimension", "size"
            ],
            IntentType.EXPORT: [
                "export", "save", "output", "write", "generate file", "convert to"
            ],
            IntentType.IMPORT: [
                "import", "load", "open", "read", "bring in"
            ],
            IntentType.VIEW: [
                "view", "look", "zoom", "pan", "orbit", "fit", "focus", "center"
            ],
            IntentType.ANALYZE: [
                "analyze", "check", "verify", "validate", "inspect", "evaluate",
                "test", "examine"
            ],
            IntentType.HELP: [
                "help", "how", "explain", "guide", "tutorial", "documentation",
                "what is", "how to"
            ],
            IntentType.CONFIGURE: [
                "configure", "settings", "preferences", "setup", "options",
                "customize", "config"
            ]
        }

        # Action keywords
        self.action_keywords = {
            ActionType.PRIMITIVE: ["box", "cube", "cylinder", "sphere", "cone", "torus"],
            ActionType.SKETCH: ["sketch", "2d", "profile", "drawing"],
            ActionType.TRANSFORM: ["move", "translate", "rotate", "scale", "mirror"],
            ActionType.BOOLEAN: ["union", "difference", "intersection", "combine", "subtract"],
            ActionType.FILLET_CHAMFER: ["fillet", "round", "chamfer", "bevel"],
            ActionType.PATTERN: ["pattern", "array", "duplicate", "copy", "repeat"]
        }

    def classify(self, text: str, context: Optional[Dict] = None) -> Intent:
        """
        Classify intent from user input text

        Args:
            text: User input text
            context: Optional context information

        Returns:
            Intent object with classification results
        """
        text_lower = text.lower()

        # Extract entities first
        entities = self._extract_entities(text)

        # Determine intent type
        intent_type, intent_confidence, intent_keywords = self._classify_intent_type(text_lower)

        # Determine action type
        action_type = self._classify_action_type(text_lower, intent_type)

        # Extract parameters
        parameters = self._extract_parameters(text, intent_type, action_type)

        # Enhance with context
        if context:
            self._enhance_with_context(intent_type, action_type, parameters, context)

        # Adjust confidence based on clarity
        confidence = self._calculate_confidence(
            text_lower, intent_type, action_type, entities, parameters
        )

        return Intent(
            type=intent_type,
            action=action_type,
            confidence=confidence,
            entities=entities,
            parameters=parameters,
            original_text=text,
            keywords_matched=intent_keywords
        )

    def _build_intent_patterns(self) -> Dict[IntentType, List[re.Pattern]]:
        """Build regex patterns for intent detection"""
        patterns = {}

        # Create patterns
        patterns[IntentType.CREATE] = [
            re.compile(r'\b(create|make|build|add)\s+(a\s+)?(\w+)', re.I),
            re.compile(r'\b(new|generate)\s+(\w+)', re.I),
            re.compile(r'\b(draw|design)\s+(a\s+)?(\w+)', re.I)
        ]

        patterns[IntentType.MODIFY] = [
            re.compile(r'\b(modify|change|edit|update)\s+(\w+)', re.I),
            re.compile(r'\b(move|rotate|scale)\s+(the\s+)?(\w+)?', re.I),
            re.compile(r'\b(extend|trim|offset)\s+(\w+)', re.I)
        ]

        patterns[IntentType.DELETE] = [
            re.compile(r'\b(delete|remove|erase)\s+(the\s+)?(\w+)?', re.I),
            re.compile(r'\b(clear|destroy)\s+(all\s+)?(\w+)?', re.I)
        ]

        patterns[IntentType.QUERY] = [
            re.compile(r'\b(what|which|where)\s+(is|are)\s+(\w+)', re.I),
            re.compile(r'\b(show|display|list)\s+(me\s+)?(the\s+)?(\w+)?', re.I),
            re.compile(r'\b(get|find)\s+(the\s+)?(\w+)', re.I)
        ]

        patterns[IntentType.MEASURE] = [
            re.compile(r'\b(measure|calculate)\s+(the\s+)?(distance|length|area|volume)', re.I),
            re.compile(r'\b(what\s+is\s+the)\s+(distance|length|area|volume)', re.I),
            re.compile(r'\b(compute|find)\s+(the\s+)?(dimension|size)', re.I)
        ]

        return patterns

    def _build_entity_patterns(self) -> Dict[str, re.Pattern]:
        """Build patterns for entity extraction"""
        return {
            "object_type": re.compile(r'\b(box|cube|cylinder|sphere|cone|torus|sketch|part|assembly|body)\b', re.I),
            "dimension": re.compile(r'(\d+(?:\.\d+)?)\s*(mm|cm|m|inch|in|ft)?', re.I),
            "color": re.compile(r'\b(red|green|blue|yellow|orange|purple|black|white|gray|grey)\b', re.I),
            "position": re.compile(r'at\s*\(?\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)?', re.I),
            "angle": re.compile(r'(\d+(?:\.\d+)?)\s*(degrees?|deg|radians?|rad|°)', re.I),
            "count": re.compile(r'\b(\d+)\s+(times?|copies|instances?)\b', re.I),
            "axis": re.compile(r'\b(x|y|z)[\s-]?axis\b', re.I),
            "direction": re.compile(r'\b(up|down|left|right|forward|backward|north|south|east|west)\b', re.I),
            "reference": re.compile(r'\b(selected|current|active|last|previous|all)\b', re.I)
        }

    def _build_parameter_extractors(self) -> Dict[str, callable]:
        """Build parameter extraction functions"""
        def extract_dimensions(text):
            """Extract dimensional parameters"""
            dims = []
            pattern = re.compile(r'(\d+(?:\.\d+)?)\s*(mm|cm|m|inch|in)?', re.I)
            for match in pattern.findall(text):
                value = float(match[0])
                unit = match[1] if match[1] else "mm"
                dims.append({"value": value, "unit": unit})
            return dims

        def extract_position(text):
            """Extract position parameters"""
            pattern = re.compile(r'at\s*\(?\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)?', re.I)
            match = pattern.search(text)
            if match:
                return {
                    "x": float(match.group(1)),
                    "y": float(match.group(2)),
                    "z": float(match.group(3))
                }
            return None

        return {
            "dimensions": extract_dimensions,
            "position": extract_position
        }

    def _classify_intent_type(self, text: str) -> Tuple[IntentType, float, List[str]]:
        """Classify the intent type from text"""
        intent_scores = {}
        matched_keywords = {}

        # Check keywords
        for intent_type, keywords in self.intent_keywords.items():
            score = 0
            matches = []
            for keyword in keywords:
                if keyword in text:
                    score += 1
                    matches.append(keyword)
            if score > 0:
                intent_scores[intent_type] = score
                matched_keywords[intent_type] = matches

        # Check patterns
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    intent_scores[intent_type] = intent_scores.get(intent_type, 0) + 2

        # Determine best match
        if intent_scores:
            best_intent = max(intent_scores.items(), key=lambda x: x[1])
            confidence = min(best_intent[1] / 5.0, 1.0)  # Normalize confidence
            keywords = matched_keywords.get(best_intent[0], [])
            return best_intent[0], confidence, keywords

        return IntentType.UNKNOWN, 0.0, []

    def _classify_action_type(self, text: str, intent_type: IntentType) -> Optional[ActionType]:
        """Classify the action type based on intent and text"""
        if intent_type == IntentType.CREATE:
            # Check for primitive shapes
            for keyword in self.action_keywords[ActionType.PRIMITIVE]:
                if keyword in text:
                    return ActionType.PRIMITIVE

            # Check for sketch
            if "sketch" in text or "2d" in text:
                return ActionType.SKETCH

        elif intent_type == IntentType.MODIFY:
            # Check for transformations
            if any(word in text for word in ["move", "translate", "rotate", "scale"]):
                return ActionType.TRANSFORM

            # Check for boolean
            if any(word in text for word in ["union", "difference", "intersection", "subtract"]):
                return ActionType.BOOLEAN

            # Check for fillet/chamfer
            if any(word in text for word in ["fillet", "round", "chamfer", "bevel"]):
                return ActionType.FILLET_CHAMFER

        return None

    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from text"""
        entities = []

        for entity_type, pattern in self.entity_patterns.items():
            matches = pattern.findall(text)
            for match in matches:
                entity = {
                    "type": entity_type,
                    "value": match,
                    "start": text.find(str(match)),
                    "end": text.find(str(match)) + len(str(match))
                }
                entities.append(entity)

        return entities

    def _extract_parameters(self, text: str, intent_type: IntentType,
                           action_type: Optional[ActionType]) -> Dict[str, Any]:
        """Extract parameters based on intent and action"""
        parameters = {}

        # Extract dimensions
        if "dimensions" in self.parameter_extractors:
            dims = self.parameter_extractors["dimensions"](text)
            if dims:
                if len(dims) >= 3:
                    parameters["length"] = dims[0]["value"]
                    parameters["width"] = dims[1]["value"]
                    parameters["height"] = dims[2]["value"]
                elif len(dims) == 2:
                    parameters["length"] = dims[0]["value"]
                    parameters["width"] = dims[1]["value"]
                elif len(dims) == 1:
                    parameters["size"] = dims[0]["value"]

        # Extract position
        if "position" in self.parameter_extractors:
            pos = self.parameter_extractors["position"](text)
            if pos:
                parameters["position"] = pos

        # Extract specific parameters based on intent
        if intent_type == IntentType.CREATE and action_type == ActionType.PRIMITIVE:
            # Check for specific shape parameters
            if "radius" in text:
                radius_match = re.search(r'radius\s*(?:of\s*)?(\d+(?:\.\d+)?)', text, re.I)
                if radius_match:
                    parameters["radius"] = float(radius_match.group(1))

        elif intent_type == IntentType.MODIFY and action_type == ActionType.TRANSFORM:
            # Extract transformation parameters
            angle_match = re.search(r'(\d+(?:\.\d+)?)\s*degrees?', text, re.I)
            if angle_match:
                parameters["angle"] = float(angle_match.group(1))

        return parameters

    def _enhance_with_context(self, intent_type: IntentType, action_type: Optional[ActionType],
                            parameters: Dict[str, Any], context: Dict):
        """Enhance classification with context information"""
        # If there's a selection and intent is modify/delete, assume operation on selection
        if context.get("selection", {}).get("has_selection"):
            if intent_type in [IntentType.MODIFY, IntentType.DELETE, IntentType.MEASURE]:
                parameters["target"] = "selection"

        # If no object specified but there's only one object, assume that's the target
        if context.get("objects", {}).get("total_count") == 1:
            if "target" not in parameters:
                parameters["target"] = "current_object"

    def _calculate_confidence(self, text: str, intent_type: IntentType,
                            action_type: Optional[ActionType],
                            entities: List[Dict], parameters: Dict) -> float:
        """Calculate overall confidence score"""
        confidence = 0.5  # Base confidence

        # Boost confidence for clear intent
        if intent_type != IntentType.UNKNOWN:
            confidence += 0.2

        # Boost for specific action
        if action_type is not None:
            confidence += 0.1

        # Boost for entities found
        if entities:
            confidence += min(len(entities) * 0.05, 0.15)

        # Boost for parameters extracted
        if parameters:
            confidence += min(len(parameters) * 0.05, 0.15)

        # Penalty for very short or very long text
        text_length = len(text.split())
        if text_length < 3 or text_length > 50:
            confidence *= 0.8

        return min(confidence, 1.0)

    def explain_classification(self, intent: Intent) -> str:
        """Generate human-readable explanation of the classification"""
        explanation = f"I understood that you want to {intent.type.value}"

        if intent.action:
            explanation += f" (specifically: {intent.action.value})"

        if intent.entities:
            objects = [e["value"] for e in intent.entities if e["type"] == "object_type"]
            if objects:
                explanation += f" involving {', '.join(objects)}"

        if intent.parameters:
            param_strs = []
            for key, value in intent.parameters.items():
                if key == "position":
                    param_strs.append(f"at position ({value['x']}, {value['y']}, {value['z']})")
                elif key in ["length", "width", "height", "radius"]:
                    param_strs.append(f"{key}: {value}")

            if param_strs:
                explanation += f" with {', '.join(param_strs)}"

        explanation += f" (confidence: {intent.confidence:.0%})"

        return explanation

    def get_intent_suggestions(self, partial_text: str) -> List[str]:
        """Get intent suggestions for partial input"""
        suggestions = []

        for intent_type, keywords in self.intent_keywords.items():
            for keyword in keywords:
                if keyword.startswith(partial_text.lower()):
                    suggestions.append(keyword)

        return list(set(suggestions))[:10]
