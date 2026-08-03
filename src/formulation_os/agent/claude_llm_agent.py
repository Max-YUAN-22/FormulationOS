"""Real Claude LLM Agent for FormulationOS

Uses Claude API for:
- Natural language understanding
- Context-aware responses
- Tool calling decisions
- Scientific narrative generation
"""

from typing import Dict, Any, List, Tuple, Optional
from anthropic import Anthropic
from formulation_os.agent.conversation_memory import ConversationMemory


class ClaudeLLMAgent:
    """Real LLM agent using Claude API"""

    def __init__(
        self,
        memory: ConversationMemory,
        api_key: str,
        base_url: str = "https://yunqiaoapi.com",
        model: str = "claude-opus-4-6"
    ):
        self.memory = memory
        self.client = Anthropic(api_key=api_key, base_url=base_url)
        self.model = model

        # System prompt defining the scientific reasoner role
        self.system_prompt = self._build_system_prompt()

        # Available tools
        self.tools = self._define_tools()

    def _build_system_prompt(self) -> str:
        """Build system prompt for Claude"""
        return """You are an expert pharmaceutical formulation scientist AI assistant.

Your role:
- Help researchers analyze drug properties and formulation challenges
- Generate scientific hypotheses based on computational evidence
- Explain complex concepts in clear scientific narrative
- Decide when to use computational tools for analysis

Available computational tools:
- PreformulationAI: Analyze physicochemical properties (LogP, LogS, BCS class)
- FormulationAI: Evaluate formulation strategies (solid dispersion, nanocrystal, cyclodextrin)

Important guidelines:
1. Respond naturally in scientific narrative style, NOT templates
2. Use conversation memory to maintain context
3. Call tools when computational evidence is needed
4. Present results as scientific hypotheses, NOT final recommendations
5. Always acknowledge remaining uncertainties
6. Suggest experimental validation when appropriate

Current conversation context will be provided in the messages."""

    def _define_tools(self) -> List[Dict[str, Any]]:
        """Define tools in Claude format"""
        return [
            {
                "name": "preformulation_ai_fundamentals",
                "description": "Analyze basic physicochemical properties of a drug compound including LogP (lipophilicity), LogS (aqueous solubility), molecular weight, pKa, and other fundamental descriptors. Use this when you need to understand the compound's basic properties.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "drug_name": {
                            "type": "string",
                            "description": "Name of the drug compound"
                        },
                        "smiles": {
                            "type": "string",
                            "description": "SMILES notation of the chemical structure"
                        }
                    },
                    "required": ["smiles"]
                }
            },
            {
                "name": "preformulation_ai_developability",
                "description": "Assess drug developability including BCS classification, druglikeness, and formulatability indices. Use this to understand formulation challenges and development feasibility.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "drug_name": {
                            "type": "string",
                            "description": "Name of the drug compound"
                        },
                        "smiles": {
                            "type": "string",
                            "description": "SMILES notation of the chemical structure"
                        }
                    },
                    "required": ["smiles"]
                }
            },
            {
                "name": "formulation_ai_solid_dispersion",
                "description": "Evaluate solid dispersion feasibility by predicting physical stability. Returns stability prediction (stable/unstable) with confidence score. Use when considering amorphous formulation strategies.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "drug_name": {
                            "type": "string",
                            "description": "Name of the drug"
                        },
                        "smiles": {
                            "type": "string",
                            "description": "SMILES notation"
                        }
                    },
                    "required": ["smiles"]
                }
            },
            {
                "name": "formulation_ai_nanocrystal",
                "description": "Predict nanocrystal formulation feasibility including particle size and PDI. Returns predicted particle size in nm. Use when considering particle size reduction strategies.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "drug_name": {
                            "type": "string",
                            "description": "Name of the drug"
                        },
                        "smiles": {
                            "type": "string",
                            "description": "SMILES notation"
                        }
                    },
                    "required": ["smiles"]
                }
            },
            {
                "name": "formulation_ai_cyclodextrin",
                "description": "Evaluate cyclodextrin complexation by calculating complexation free energy (ΔG). Negative values indicate favorable complexation. Use when considering solubilization through inclusion complexes.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "drug_name": {
                            "type": "string",
                            "description": "Name of the drug"
                        },
                        "smiles": {
                            "type": "string",
                            "description": "SMILES notation"
                        }
                    },
                    "required": ["smiles"]
                }
            }
        ]

    def generate_response(self, user_query: str) -> Tuple[str, List[Dict], int, int]:
        """Generate response using Claude API

        Returns:
            (response_text, tool_calls, input_tokens, output_tokens)
        """
        # Get conversation history
        history = self.memory.get_conversation_history(last_n=10)

        # Add scientific context to system prompt
        context_summary = self.memory.get_context_summary()
        enhanced_system = self.system_prompt
        if context_summary != "No active drug compound being discussed.":
            enhanced_system += f"\n\nCurrent scientific context:\n{context_summary}"

        # Add user message
        history.append({"role": "user", "content": user_query})

        # Call Claude API with tool use
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=enhanced_system,
                tools=self.tools,
                messages=history
            )

            # Extract text and tool calls
            text_content = ""
            tool_calls = []

            for block in response.content:
                if block.type == "text":
                    text_content += block.text
                elif block.type == "tool_use":
                    tool_calls.append({
                        "id": block.id,
                        "name": block.name,
                        "input": block.input
                    })

            # Get token usage
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens

            return text_content, tool_calls, input_tokens, output_tokens

        except Exception as e:
            error_msg = f"Claude API error: {str(e)}"
            return error_msg, [], 0, 0

    def execute_tool_call(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call and return results"""
        from formulation_os.tools.builtins.preformulation_ai.adapter import run as preform_run
        from formulation_os.tools.builtins.formulation_ai.adapter import run as formulation_run

        try:
            if tool_name == "preformulation_ai_fundamentals":
                result = preform_run({
                    "smiles": tool_input.get("smiles"),
                    "drug_name": tool_input.get("drug_name", ""),
                    "module": "fundamentals"
                })
                return result

            elif tool_name == "preformulation_ai_developability":
                result = preform_run({
                    "smiles": tool_input.get("smiles"),
                    "drug_name": tool_input.get("drug_name", ""),
                    "module": "developability"
                })
                return result

            elif tool_name == "formulation_ai_solid_dispersion":
                result = formulation_run({
                    "smiles": tool_input.get("smiles"),
                    "drug_name": tool_input.get("drug_name", ""),
                    "module": "solid_dispersion"
                })
                return result

            elif tool_name == "formulation_ai_nanocrystal":
                result = formulation_run({
                    "smiles": tool_input.get("smiles"),
                    "drug_name": tool_input.get("drug_name", ""),
                    "module": "nanocrystal"
                })
                return result

            elif tool_name == "formulation_ai_cyclodextrin":
                result = formulation_run({
                    "smiles": tool_input.get("smiles"),
                    "drug_name": tool_input.get("drug_name", ""),
                    "module": "cd_complex"
                })
                return result

            else:
                return {"error": f"Unknown tool: {tool_name}"}

        except Exception as e:
            return {"error": str(e)}

    def process_with_tools(self, initial_response: str, tool_calls: List[Dict]) -> str:
        """Execute tools and get Claude's synthesis

        This implements the full tool use loop with Claude
        """
        if not tool_calls:
            return initial_response

        # Execute all tool calls
        tool_results = []
        for tool_call in tool_calls:
            result = self.execute_tool_call(tool_call["name"], tool_call["input"])
            tool_results.append({
                "tool_use_id": tool_call["id"],
                "type": "tool_result",
                "content": str(result)
            })

        # Get conversation history
        history = self.memory.get_conversation_history(last_n=10)

        # Reconstruct the assistant's message with tool use
        history.append({
            "role": "assistant",
            "content": [
                {"type": "text", "text": initial_response if initial_response else "Let me analyze this using computational tools."},
                *[{"type": "tool_use", "id": tc["id"], "name": tc["name"], "input": tc["input"]} for tc in tool_calls]
            ]
        })

        # Add tool results as user message (Claude's convention)
        history.append({
            "role": "user",
            "content": tool_results
        })

        # Get Claude's synthesis
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=self.system_prompt + f"\n\nCurrent context: {self.memory.get_context_summary()}",
                messages=history
            )

            # Extract final text
            final_text = ""
            for block in response.content:
                if block.type == "text":
                    final_text += block.text

            return final_text

        except Exception as e:
            return f"Error synthesizing tool results: {str(e)}"
