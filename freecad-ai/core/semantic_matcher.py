"""Semantic Matcher - Advanced semantic similarity for tool matching"""

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set


@dataclass
class Match:
    """Represents a semantic match result"""

    tool_id: str
    tool_name: str
    similarity_score: float
    keyword_matches: List[str]
    semantic_features: Dict[str, float]
    explanation: str
    confidence: float


class SemanticMatcher:
    """
    Advanced semantic matching system for tool selection
    using multiple similarity measures and learning capabilities.
    """

    def __init__(self):
        """Initialize the Semantic Matcher"""
        # Tool embeddings (simplified word vectors)
        self.tool_embeddings = {}

        # Word importance weights
        self.word_weights = defaultdict(float)

        # Synonym mapping
        self.synonyms = self._build_synonym_map()

        # Domain-specific terms
        self.domain_terms = self._build_domain_terms()

        # Match history for learning
        self.match_history = []

        # Precomputed term frequencies
        self.term_frequencies = {}
        self.document_frequencies = {}

        # Initialize with base weights
        self._initialize_weights()

    def _build_synonym_map(self) -> Dict[str, Set[str]]:
        """Build synonym mapping for common terms"""
        return {
            # Geometric shapes
            "box": {"cube", "rectangular", "prism", "block"},
            "cylinder": {"pipe", "tube", "rod", "barrel"},
            "sphere": {"ball", "globe", "orb"},
            "cone": {"pyramid", "taper", "funnel"},
            # Actions
            "create": {"make", "build", "generate", "construct", "add", "new"},
            "modify": {"edit", "change", "alter", "update", "adjust"},
            "delete": {"remove", "erase", "eliminate", "destroy", "clear"},
            "move": {"translate", "shift", "relocate", "position", "displace"},
            "rotate": {"turn", "spin", "revolve", "pivot", "twist"},
            "scale": {"resize", "size", "enlarge", "shrink", "zoom"},
            # Operations
            "extrude": {"extend", "pull", "push", "elongate"},
            "revolve": {"lathe", "spin", "rotate around"},
            "fillet": {"round", "smooth", "curve", "blend"},
            "chamfer": {"bevel", "angle", "slope"},
            "pattern": {"array", "repeat", "duplicate", "copy"},
            # Measurements
            "measure": {"calculate", "compute", "find", "determine"},
            "distance": {"length", "span", "gap", "separation"},
            "area": {"surface", "region", "space"},
            "volume": {"capacity", "content", "size"},
            # Selection
            "select": {"pick", "choose", "highlight", "mark"},
            "all": {"everything", "entire", "whole", "complete"},
            "none": {"nothing", "deselect", "clear"},
        }

    def _build_domain_terms(self) -> Set[str]:
        """Build set of domain-specific technical terms"""
        return {
            # CAD terms
            "sketch",
            "constraint",
            "dimension",
            "feature",
            "body",
            "part",
            "assembly",
            "workbench",
            "document",
            "view",
            # Geometry terms
            "vertex",
            "edge",
            "face",
            "solid",
            "shell",
            "wire",
            "point",
            "line",
            "curve",
            "surface",
            "plane",
            # Operations
            "boolean",
            "union",
            "intersection",
            "difference",
            "mirror",
            "offset",
            "transform",
            "projection",
            # Properties
            "material",
            "color",
            "transparency",
            "texture",
            "mass",
            "density",
            "inertia",
            "center",
        }

    def _initialize_weights(self):
        """Initialize word importance weights"""
        # Action words have higher weight
        for action in ["create", "modify", "delete", "measure", "select"]:
            self.word_weights[action] = 2.0

        # Object types have high weight
        for obj in ["box", "cylinder", "sphere", "sketch", "part"]:
            self.word_weights[obj] = 1.8

        # Domain terms have moderate weight
        for term in self.domain_terms:
            self.word_weights[term] = 1.5

        # Common words have lower weight
        for word in ["the", "a", "an", "of", "in", "at", "to", "for"]:
            self.word_weights[word] = 0.2

    def add_tool_embedding(
        self, tool_id: str, description: str, keywords: List[str], examples: List[str]
    ):
        """Add tool embedding for matching"""
        # Create document from all text
        document = f"{description} {' '.join(keywords)} {' '.join(examples)}"

        # Tokenize and create term frequency
        tokens = self._tokenize(document.lower())
        term_freq = Counter(tokens)

        # Calculate TF-IDF weights
        embedding = {}
        for term, freq in term_freq.items():
            tf = freq / len(tokens)  # Term frequency
            # IDF will be calculated when we have all documents
            embedding[term] = tf

        self.tool_embeddings[tool_id] = {
            "description": description,
            "keywords": keywords,
            "examples": examples,
            "tokens": tokens,
            "term_freq": term_freq,
            "embedding": embedding,
        }

        # Update document frequencies
        for term in set(tokens):
            self.document_frequencies[term] = self.document_frequencies.get(term, 0) + 1

    def finalize_embeddings(self):
        """Finalize embeddings by calculating IDF values"""
        num_tools = len(self.tool_embeddings)

        # Calculate IDF for each term
        idf_values = {}
        for term, doc_freq in self.document_frequencies.items():
            idf = math.log(num_tools / (1 + doc_freq))
            idf_values[term] = idf

        # Update embeddings with TF-IDF
        for tool_id, tool_data in self.tool_embeddings.items():
            embedding = tool_data["embedding"]
            for term in embedding:
                tf = embedding[term]
                idf = idf_values.get(term, 0)
                embedding[term] = tf * idf

    def match(self, query: str, top_k: int = 5, min_score: float = 0.1) -> List[Match]:
        """
        Find best matching tools for query

        Args:
            query: Natural language query
            top_k: Number of top matches to return
            min_score: Minimum similarity score threshold

        Returns:
            List of Match objects sorted by score
        """
        # Tokenize and process query
        query_tokens = self._tokenize(query.lower())
        query_expanded = self._expand_query(query_tokens)

        matches = []

        for tool_id, tool_data in self.tool_embeddings.items():
            # Calculate multiple similarity measures
            keyword_sim = self._keyword_similarity(
                query_expanded, tool_data["keywords"]
            )
            description_sim = self._description_similarity(
                query_expanded, tool_data["description"]
            )
            example_sim = self._example_similarity(
                query_expanded, tool_data["examples"]
            )
            embedding_sim = self._embedding_similarity(
                query_expanded, tool_data["embedding"]
            )

            # Find matched keywords
            keyword_matches = self._find_keyword_matches(query_tokens, tool_data)

            # Combine scores with weights
            semantic_features = {
                "keyword": keyword_sim,
                "description": description_sim,
                "example": example_sim,
                "embedding": embedding_sim,
            }

            # Weighted combination
            combined_score = (
                0.35 * keyword_sim
                + 0.25 * description_sim
                + 0.15 * example_sim
                + 0.25 * embedding_sim
            )

            # Adjust score based on match history
            adjusted_score = self._adjust_score_from_history(
                query, tool_id, combined_score
            )

            if adjusted_score >= min_score:
                # Generate explanation
                explanation = self._generate_explanation(
                    query_tokens, tool_data, semantic_features
                )

                # Calculate confidence
                confidence = self._calculate_confidence(
                    semantic_features, keyword_matches
                )

                matches.append(
                    Match(
                        tool_id=tool_id,
                        tool_name=tool_data["description"].split(":")[0],
                        similarity_score=adjusted_score,
                        keyword_matches=keyword_matches,
                        semantic_features=semantic_features,
                        explanation=explanation,
                        confidence=confidence,
                    )
                )

        # Sort by score and return top k
        matches.sort(key=lambda x: x.similarity_score, reverse=True)
        return matches[:top_k]

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words"""
        # Simple tokenization - could be enhanced with NLP library
        tokens = re.findall(r"\b\w+\b", text.lower())
        return [t for t in tokens if len(t) > 1]

    def _expand_query(self, tokens: List[str]) -> Set[str]:
        """Expand query with synonyms"""
        expanded = set(tokens)

        for token in tokens:
            # Add synonyms
            if token in self.synonyms:
                expanded.update(self.synonyms[token])

            # Check if token is a synonym of something else
            for base_word, syns in self.synonyms.items():
                if token in syns:
                    expanded.add(base_word)
                    expanded.update(syns)

        return expanded

    def _keyword_similarity(self, query_terms: Set[str], keywords: List[str]) -> float:
        """Calculate keyword-based similarity"""
        if not keywords:
            return 0.0

        keyword_set = set(
            word.lower() for keyword in keywords for word in self._tokenize(keyword)
        )

        # Calculate Jaccard similarity
        intersection = query_terms & keyword_set
        union = query_terms | keyword_set

        if not union:
            return 0.0

        jaccard = len(intersection) / len(union)

        # Boost score if important words match
        boost = sum(self.word_weights.get(word, 1.0) for word in intersection)
        boost_factor = boost / len(intersection) if intersection else 1.0

        return min(jaccard * boost_factor, 1.0)

    def _description_similarity(self, query_terms: Set[str], description: str) -> float:
        """Calculate description-based similarity"""
        desc_tokens = set(self._tokenize(description.lower()))

        # Count matching terms with weights
        score = 0.0
        matches = 0

        for term in query_terms:
            if term in desc_tokens:
                score += self.word_weights.get(term, 1.0)
                matches += 1

        # Normalize by query length
        if len(query_terms) > 0:
            return min(score / (len(query_terms) * 1.5), 1.0)
        return 0.0

    def _example_similarity(self, query_terms: Set[str], examples: List[str]) -> float:
        """Calculate example-based similarity"""
        if not examples:
            return 0.0

        # Check each example
        max_similarity = 0.0

        for example in examples:
            example_tokens = set(self._tokenize(example.lower()))

            # Calculate similarity
            intersection = query_terms & example_tokens
            if len(query_terms) > 0:
                similarity = len(intersection) / len(query_terms)
                max_similarity = max(max_similarity, similarity)

        return max_similarity

    def _embedding_similarity(
        self, query_terms: Set[str], embedding: Dict[str, float]
    ) -> float:
        """Calculate embedding-based similarity (cosine similarity)"""
        # Create query embedding
        query_embedding = {}
        for term in query_terms:
            query_embedding[term] = self.word_weights.get(term, 1.0)

        # Calculate cosine similarity
        dot_product = 0.0
        query_norm = 0.0
        tool_norm = 0.0

        all_terms = set(query_embedding.keys()) | set(embedding.keys())

        for term in all_terms:
            q_val = query_embedding.get(term, 0.0)
            t_val = embedding.get(term, 0.0)

            dot_product += q_val * t_val
            query_norm += q_val**2
            tool_norm += t_val**2

        if query_norm > 0 and tool_norm > 0:
            return dot_product / (math.sqrt(query_norm) * math.sqrt(tool_norm))

        return 0.0

    def _find_keyword_matches(
        self, query_tokens: List[str], tool_data: Dict
    ) -> List[str]:
        """Find which keywords matched"""
        matches = []

        # Check in keywords
        for keyword in tool_data["keywords"]:
            keyword_tokens = set(self._tokenize(keyword.lower()))
            if any(token in keyword_tokens for token in query_tokens):
                matches.append(keyword)

        # Check in description
        desc_tokens = set(self._tokenize(tool_data["description"].lower()))
        for token in query_tokens:
            if token in desc_tokens and token in self.domain_terms:
                matches.append(token)

        return list(set(matches))  # Remove duplicates

    def _generate_explanation(
        self, query_tokens: List[str], tool_data: Dict, features: Dict[str, float]
    ) -> str:
        """Generate explanation for why tool was matched"""
        explanations = []

        # High keyword similarity
        if features["keyword"] > 0.7:
            explanations.append("strong keyword match")

        # Good description match
        if features["description"] > 0.5:
            explanations.append("matches tool description")

        # Example match
        if features["example"] > 0.6:
            explanations.append("similar to tool examples")

        # Semantic similarity
        if features["embedding"] > 0.6:
            explanations.append("high semantic similarity")

        # Domain terms
        domain_matches = [t for t in query_tokens if t in self.domain_terms]
        if domain_matches:
            explanations.append(f"domain terms: {', '.join(domain_matches[:3])}")

        if not explanations:
            explanations.append("partial match")

        return "; ".join(explanations)

    def _calculate_confidence(
        self, features: Dict[str, float], keyword_matches: List[str]
    ) -> float:
        """Calculate confidence in the match"""
        # Base confidence from feature scores
        avg_score = sum(features.values()) / len(features)
        confidence = avg_score

        # Boost for multiple feature agreement
        high_features = sum(1 for score in features.values() if score > 0.6)
        if high_features >= 3:
            confidence *= 1.2
        elif high_features >= 2:
            confidence *= 1.1

        # Boost for keyword matches
        if len(keyword_matches) >= 3:
            confidence *= 1.15
        elif len(keyword_matches) >= 2:
            confidence *= 1.08

        return min(confidence, 1.0)

    def _adjust_score_from_history(
        self, query: str, tool_id: str, base_score: float
    ) -> float:
        """Adjust score based on match history"""
        # Simple implementation - could be enhanced with ML
        adjusted_score = base_score

        # Check recent history
        recent_matches = [
            h for h in self.match_history[-20:] if h["tool_id"] == tool_id
        ]

        if recent_matches:
            # Calculate success rate
            successes = sum(1 for m in recent_matches if m.get("successful", True))
            success_rate = successes / len(recent_matches)

            # Adjust score based on success rate
            if success_rate > 0.8:
                adjusted_score *= 1.1
            elif success_rate < 0.3:
                adjusted_score *= 0.9

        return min(adjusted_score, 1.0)

    def record_match_result(
        self,
        query: str,
        tool_id: str,
        successful: bool,
        user_feedback: Optional[str] = None,
    ):
        """Record match result for learning"""
        self.match_history.append(
            {
                "query": query,
                "tool_id": tool_id,
                "successful": successful,
                "feedback": user_feedback,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Update word weights based on feedback
        if successful:
            tokens = self._tokenize(query.lower())
            tool_tokens = self.tool_embeddings[tool_id]["tokens"]

            # Increase weight of matching terms
            for token in tokens:
                if token in tool_tokens:
                    self.word_weights[token] *= 1.05

        # Keep history size manageable
        if len(self.match_history) > 1000:
            self.match_history = self.match_history[-500:]

    def get_match_statistics(self) -> Dict[str, Any]:
        """Get statistics about matching performance"""
        if not self.match_history:
            return {"total_matches": 0}

        total = len(self.match_history)
        successful = sum(1 for m in self.match_history if m.get("successful", True))

        # Tool-specific stats
        tool_stats = defaultdict(lambda: {"total": 0, "successful": 0})
        for match in self.match_history:
            tool_id = match["tool_id"]
            tool_stats[tool_id]["total"] += 1
            if match.get("successful", True):
                tool_stats[tool_id]["successful"] += 1

        return {
            "total_matches": total,
            "successful_matches": successful,
            "success_rate": successful / total if total > 0 else 0,
            "tool_statistics": dict(tool_stats),
        }

    def export_learning_data(self) -> Dict[str, Any]:
        """Export learning data for persistence"""
        return {
            "word_weights": dict(self.word_weights),
            "match_history": self.match_history[-100:],  # Last 100 matches
            "statistics": self.get_match_statistics(),
        }

    def import_learning_data(self, data: Dict[str, Any]):
        """Import learning data"""
        if "word_weights" in data:
            self.word_weights.update(data["word_weights"])

        if "match_history" in data:
            self.match_history.extend(data["match_history"])


from datetime import datetime
