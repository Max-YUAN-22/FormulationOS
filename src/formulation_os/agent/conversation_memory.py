"""Conversation Memory System for FormulationOS

Maintains:
1. Dialogue history (all user-assistant exchanges)
2. Scientific state (current drug, analyzed properties, hypotheses)
3. Tool usage history
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class Message:
    """Single message in conversation"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ScientificState:
    """Current scientific context"""
    # Current compound
    drug_name: Optional[str] = None
    smiles: Optional[str] = None
    dosage_form: Optional[str] = None

    # Analyzed properties
    physicochemical_props: Dict[str, Any] = field(default_factory=dict)
    # e.g., {"logP": 3.97, "logS": -3.97, "bcs_class": "II"}

    # Formulation analysis
    formulation_results: Dict[str, Any] = field(default_factory=dict)
    # e.g., {"solid_dispersion": {...}, "nanocrystal": {...}}

    # Generated hypotheses
    hypotheses: List[Dict[str, Any]] = field(default_factory=list)

    # User preferences/context
    focus_areas: List[str] = field(default_factory=list)
    # e.g., ["dissolution", "stability", "manufacturing"]


class ConversationMemory:
    """Manages conversation history and scientific state"""

    def __init__(self):
        self.messages: List[Message] = []
        self.scientific_state = ScientificState()

    def add_message(self, role: str, content: str, tool_calls: List[Dict] = None):
        """Add a message to history"""
        msg = Message(
            role=role,
            content=content,
            tool_calls=tool_calls or []
        )
        self.messages.append(msg)

    def get_conversation_history(self, last_n: int = None) -> List[Dict[str, str]]:
        """Get conversation history in LLM format

        Args:
            last_n: Return only last N messages (None = all)

        Returns:
            List of {"role": "user/assistant", "content": "..."}
        """
        messages = self.messages[-last_n:] if last_n else self.messages
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

    def update_scientific_state(self, **kwargs):
        """Update scientific state with new information

        Example:
            memory.update_scientific_state(
                drug_name="Ibuprofen",
                physicochemical_props={"logP": 3.97, "logS": -3.97}
            )
        """
        for key, value in kwargs.items():
            if hasattr(self.scientific_state, key):
                if isinstance(getattr(self.scientific_state, key), dict):
                    # Merge dictionaries
                    getattr(self.scientific_state, key).update(value)
                elif isinstance(getattr(self.scientific_state, key), list):
                    # Extend lists
                    if isinstance(value, list):
                        getattr(self.scientific_state, key).extend(value)
                    else:
                        getattr(self.scientific_state, key).append(value)
                else:
                    # Direct assignment
                    setattr(self.scientific_state, key, value)

    def get_context_summary(self) -> str:
        """Get a summary of current scientific context

        This is used to provide context to the LLM
        """
        state = self.scientific_state

        if not state.drug_name:
            return "No active drug compound being discussed."

        summary = f"Currently discussing: {state.drug_name}"

        if state.smiles:
            summary += f"\nSMILES: {state.smiles}"

        if state.dosage_form:
            summary += f"\nTarget dosage form: {state.dosage_form}"

        if state.physicochemical_props:
            summary += "\n\nAnalyzed properties:"
            for key, value in state.physicochemical_props.items():
                summary += f"\n  - {key}: {value}"

        if state.formulation_results:
            summary += f"\n\nFormulation strategies evaluated: {', '.join(state.formulation_results.keys())}"

        if state.hypotheses:
            summary += f"\n\n{len(state.hypotheses)} scientific hypotheses generated"

        if state.focus_areas:
            summary += f"\n\nUser focus areas: {', '.join(state.focus_areas)}"

        return summary

    def clear(self):
        """Clear all conversation history and state"""
        self.messages.clear()
        self.scientific_state = ScientificState()

    def has_analyzed_drug(self, drug_name: str = None) -> bool:
        """Check if a drug has been analyzed

        Args:
            drug_name: Specific drug to check (None = check current drug)
        """
        if drug_name:
            return (self.scientific_state.drug_name and
                   self.scientific_state.drug_name.lower() == drug_name.lower())
        return bool(self.scientific_state.drug_name and
                   self.scientific_state.physicochemical_props)
