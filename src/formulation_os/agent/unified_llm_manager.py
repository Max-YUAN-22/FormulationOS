"""Unified LLM Manager for FormulationOS

Supports multiple LLM providers:
- Claude (Anthropic API)
- GPT (OpenAI API)
- DeepSeek (OpenAI-compatible API)
"""

from typing import Dict, Any, List, Tuple, Optional
from anthropic import Anthropic
from openai import OpenAI
from formulation_os.agent.conversation_memory import ConversationMemory


class UnifiedLLMManager:
    """Manages multiple LLM providers with unified interface"""

    # Model configurations
    MODELS = {
        # MiniMax models
        "MiniMax-M3": {
            "provider": "minimax",
            "display_name": "MiniMax M3",
            "description": "原生多模态、1M上下文的Frontier Coding模型",
            "pricing": "查看官网"
        },
        "MiniMax-M2.7": {
            "provider": "minimax",
            "display_name": "MiniMax M2.7",
            "description": "开启模型的自我迭代",
            "pricing": "查看官网"
        },
        "MiniMax-M2.7-highspeed": {
            "provider": "minimax",
            "display_name": "MiniMax M2.7 高速版",
            "description": "与M2.7效果不变，速度大幅提升",
            "pricing": "查看官网"
        },

        # GPT models (OpenAI官方)
        "gpt-4o": {
            "provider": "openai",
            "display_name": "GPT-4o",
            "description": "OpenAI最新多模态模型",
            "pricing": "OpenAI官方"
        },
        "gpt-4o-mini": {
            "provider": "openai",
            "display_name": "GPT-4o Mini",
            "description": "经济高效的GPT-4o版本",
            "pricing": "OpenAI官方"
        },
        "gpt-4-turbo": {
            "provider": "openai",
            "display_name": "GPT-4 Turbo",
            "description": "快速的GPT-4变体",
            "pricing": "OpenAI官方"
        }
    }

    def __init__(
        self,
        memory: ConversationMemory,
        anthropic_api_key: str,
        openai_api_key: str,
        minimax_api_key: str,
        anthropic_base_url: str = "http://localhost:3000",
        openai_base_url: str = "http://localhost:3000",
        minimax_base_url: str = "https://api.minimaxi.com/v1",
        evidence_manager = None
    ):
        self.memory = memory
        self.anthropic_api_key = anthropic_api_key
        self.openai_api_key = openai_api_key
        self.minimax_api_key = minimax_api_key
        self.anthropic_base_url = anthropic_base_url
        self.openai_base_url = openai_base_url
        self.minimax_base_url = minimax_base_url
        self.evidence_manager = evidence_manager

        # Initialize clients with separate API keys
        self.anthropic_client = Anthropic(
            api_key=anthropic_api_key,
            base_url=anthropic_base_url
        )
        self.openai_client = OpenAI(
            api_key=openai_api_key,
            base_url=openai_base_url
        )
        self.minimax_client = OpenAI(
            api_key=minimax_api_key,
            base_url=minimax_base_url
        )

        # System prompt
        self.system_prompt = self._build_system_prompt()

        # Tools
        self.anthropic_tools = self._define_anthropic_tools()
        self.openai_tools = self._define_openai_tools()

    def _build_system_prompt(self) -> str:
        """Build system prompt for AI Scientist"""
        return """You are an AI Scientist specializing in pharmaceutical formulation research.

CRITICAL RULE: When the user provides a SMILES string, you MUST IMMEDIATELY call analysis tools in your FIRST response. DO NOT ask clarifying questions before calling tools.

Correct workflow:
1. User provides SMILES → 2. IMMEDIATELY call tools (no questions) → 3. Analyze results → 4. Present hypotheses → 5. Then ask follow-up questions if needed

MANDATORY TOOLS TO CALL (when SMILES is provided):
- preformulation_ai_fundamentals (ALWAYS call first)
- preformulation_ai_developability (ALWAYS call for BCS)
- formulation_ai_solid_dispersion (if low solubility expected)
- formulation_ai_nanocrystal (if BCS II/IV)
- formulation_ai_cyclodextrin (if small molecule)

Example of WRONG behavior:
User: "Analyze Ibuprofen, SMILES: CC(C)..."
You: "Before I analyze, can you tell me..." ❌ WRONG - call tools first!

Example of CORRECT behavior:
User: "Analyze Ibuprofen, SMILES: CC(C)..."
You: [Immediately calls preformulation_ai_fundamentals, preformulation_ai_developability, etc.]
Then after receiving results: "Based on the analysis: LogP=3.5, LogS=-3.97, BCS Class II..."

Present results as evidence-based hypotheses:
Format: "Hypothesis: [strategy] | Evidence: [data from tools] | Uncertainty: [gaps] | Validation: [experiments]"

Remember: TOOLS FIRST, QUESTIONS LATER."""

    def _define_anthropic_tools(self) -> List[Dict[str, Any]]:
        """Define tools in Anthropic format"""
        return [
            {
                "name": "preformulation_ai_fundamentals",
                "description": "Analyze physicochemical properties: LogP, LogS, MW, pKa. Use when you need basic drug properties.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "drug_name": {"type": "string", "description": "Drug name"},
                        "smiles": {"type": "string", "description": "SMILES notation"}
                    },
                    "required": ["smiles"]
                }
            },
            {
                "name": "preformulation_ai_developability",
                "description": "Assess developability: BCS class, druglikeness, formulatability. Use to understand formulation challenges.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "drug_name": {"type": "string"},
                        "smiles": {"type": "string"}
                    },
                    "required": ["smiles"]
                }
            },
            {
                "name": "formulation_ai_solid_dispersion",
                "description": "Predict solid dispersion physical stability. Returns stable/unstable with confidence.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "drug_name": {"type": "string"},
                        "smiles": {"type": "string"}
                    },
                    "required": ["smiles"]
                }
            },
            {
                "name": "formulation_ai_nanocrystal",
                "description": "Predict nanocrystal particle size and PDI.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "drug_name": {"type": "string"},
                        "smiles": {"type": "string"}
                    },
                    "required": ["smiles"]
                }
            },
            {
                "name": "formulation_ai_cyclodextrin",
                "description": "Calculate cyclodextrin complexation free energy (ΔG). Negative = favorable.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "drug_name": {"type": "string"},
                        "smiles": {"type": "string"}
                    },
                    "required": ["smiles"]
                }
            },
            {
                "name": "preformulation_ai_solubility",
                "description": "Predict temperature and solvent-dependent solubility.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "drug_name": {"type": "string"},
                        "smiles": {"type": "string"},
                        "temperature": {"type": "number", "description": "Temperature in Celsius (default: 25.0)"},
                        "solvent": {"type": "string", "description": "Solvent type (default: water)"}
                    },
                    "required": ["smiles"]
                }
            },
            {
                "name": "preformulation_ai_ph_profile",
                "description": "Predict pH-dependent behavior and stability.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "drug_name": {"type": "string"},
                        "smiles": {"type": "string"}
                    },
                    "required": ["smiles"]
                }
            },
            {
                "name": "preformulation_ai_if_descriptors",
                "description": "Calculate interpretable formulation descriptors.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "drug_name": {"type": "string"},
                        "smiles": {"type": "string"}
                    },
                    "required": ["smiles"]
                }
            },
            {
                "name": "formulation_ai_phospholipid_complex",
                "description": "Design phospholipid complex for enhanced permeability.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "drug_name": {"type": "string"},
                        "smiles": {"type": "string"}
                    },
                    "required": ["smiles"]
                }
            },
            {
                "name": "formulation_ai_sedds",
                "description": "Design SEDDS (Self-Emulsifying Drug Delivery System) formulation.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "drug_name": {"type": "string"},
                        "smiles": {"type": "string"}
                    },
                    "required": ["smiles"]
                }
            },
            {
                "name": "formulation_ai_liposome",
                "description": "Design liposome formulation for targeted delivery.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "drug_name": {"type": "string"},
                        "smiles": {"type": "string"}
                    },
                    "required": ["smiles"]
                }
            },
            {
                "name": "formulation_ai_strategy_recommendation",
                "description": "Recommend optimal formulation strategies based on drug properties.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "drug_name": {"type": "string"},
                        "smiles": {"type": "string"}
                    },
                    "required": ["smiles"]
                }
            }
        ]

    def _define_openai_tools(self) -> List[Dict[str, Any]]:
        """Define tools in OpenAI format"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "preformulation_ai_fundamentals",
                    "description": "Analyze physicochemical properties: LogP, LogS, MW, pKa",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "drug_name": {"type": "string"},
                            "smiles": {"type": "string"}
                        },
                        "required": ["smiles"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "preformulation_ai_developability",
                    "description": "Assess BCS class and formulatability",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "drug_name": {"type": "string"},
                            "smiles": {"type": "string"}
                        },
                        "required": ["smiles"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "formulation_ai_solid_dispersion",
                    "description": "Predict solid dispersion stability",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "drug_name": {"type": "string"},
                            "smiles": {"type": "string"}
                        },
                        "required": ["smiles"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "formulation_ai_nanocrystal",
                    "description": "Predict nanocrystal particle size",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "drug_name": {"type": "string"},
                            "smiles": {"type": "string"}
                        },
                        "required": ["smiles"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "formulation_ai_cyclodextrin",
                    "description": "Calculate cyclodextrin complexation energy",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "drug_name": {"type": "string"},
                            "smiles": {"type": "string"}
                        },
                        "required": ["smiles"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "preformulation_ai_solubility",
                    "description": "Predict temperature and solvent-dependent solubility",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "drug_name": {"type": "string"},
                            "smiles": {"type": "string"},
                            "temperature": {"type": "number"},
                            "solvent": {"type": "string"}
                        },
                        "required": ["smiles"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "preformulation_ai_ph_profile",
                    "description": "Predict pH-dependent behavior",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "drug_name": {"type": "string"},
                            "smiles": {"type": "string"}
                        },
                        "required": ["smiles"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "preformulation_ai_if_descriptors",
                    "description": "Calculate interpretable formulation descriptors",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "drug_name": {"type": "string"},
                            "smiles": {"type": "string"}
                        },
                        "required": ["smiles"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "formulation_ai_phospholipid_complex",
                    "description": "Design phospholipid complex formulation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "drug_name": {"type": "string"},
                            "smiles": {"type": "string"}
                        },
                        "required": ["smiles"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "formulation_ai_sedds",
                    "description": "Design SEDDS formulation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "drug_name": {"type": "string"},
                            "smiles": {"type": "string"}
                        },
                        "required": ["smiles"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "formulation_ai_liposome",
                    "description": "Design liposome formulation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "drug_name": {"type": "string"},
                            "smiles": {"type": "string"}
                        },
                        "required": ["smiles"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "formulation_ai_strategy_recommendation",
                    "description": "Recommend optimal formulation strategies",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "drug_name": {"type": "string"},
                            "smiles": {"type": "string"}
                        },
                        "required": ["smiles"]
                    }
                }
            }
        ]

    def generate_response(
        self,
        user_query: str,
        model: str
    ) -> Tuple[str, List[Dict], int, int]:
        """Generate response using specified model

        Returns:
            (response_text, tool_calls, input_tokens, output_tokens)
        """
        if model not in self.MODELS:
            return f"Unknown model: {model}", [], 0, 0

        provider = self.MODELS[model]["provider"]

        if provider == "anthropic":
            return self._generate_anthropic(user_query, model)
        elif provider == "openai":
            return self._generate_openai(user_query, model)
        elif provider == "minimax":
            return self._generate_minimax(user_query, model)
        else:
            return f"Unknown provider: {provider}", [], 0, 0

    def _generate_anthropic(
        self,
        user_query: str,
        model: str
    ) -> Tuple[str, List[Dict], int, int]:
        """Generate using Anthropic API"""
        history = self.memory.get_conversation_history(last_n=10)
        context = self.memory.get_context_summary()

        system_with_context = self.system_prompt
        if context != "No active drug compound being discussed.":
            system_with_context += f"\n\nCurrent context:\n{context}"

        history.append({"role": "user", "content": user_query})

        try:
            response = self.anthropic_client.messages.create(
                model=model,
                max_tokens=2048,
                system=system_with_context,
                tools=self.anthropic_tools,
                messages=history
            )

            text = ""
            tool_calls = []

            for block in response.content:
                if block.type == "text":
                    text += block.text
                elif block.type == "tool_use":
                    tool_calls.append({
                        "id": block.id,
                        "name": block.name,
                        "input": block.input
                    })

            return text, tool_calls, response.usage.input_tokens, response.usage.output_tokens

        except Exception as e:
            return f"API Error: {str(e)}", [], 0, 0

    def _generate_openai(
        self,
        user_query: str,
        model: str
    ) -> Tuple[str, List[Dict], int, int]:
        """Generate using OpenAI-compatible API - Using requests instead of OpenAI SDK to avoid proxy blocking"""
        import requests
        import json

        history = self.memory.get_conversation_history(last_n=10)
        context = self.memory.get_context_summary()

        system_msg = self.system_prompt
        if context != "No active drug compound being discussed.":
            system_msg += f"\n\nCurrent context:\n{context}"

        messages = [{"role": "system", "content": system_msg}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_query})

        try:
            # Use raw HTTP requests instead of OpenAI SDK to avoid being blocked by cun.ai
            url = f"{self.openai_base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": model,
                "max_tokens": 2048,
                "messages": messages,
                "tools": self.openai_tools  # Add tools to enable PreformulationAI and FormulationAI
            }

            response = requests.post(url, headers=headers, json=data, timeout=60)

            if response.status_code != 200:
                return f"API Error: {response.status_code} - {response.text}", [], 0, 0

            result = response.json()
            message = result['choices'][0]['message']
            text = message.get('content', '')

            tool_calls = []
            if 'tool_calls' in message and message['tool_calls']:
                for tc in message['tool_calls']:
                    tool_calls.append({
                        "id": tc['id'],
                        "name": tc['function']['name'],
                        "input": json.loads(tc['function']['arguments'])
                    })

            input_tokens = result.get('usage', {}).get('prompt_tokens', 0)
            output_tokens = result.get('usage', {}).get('completion_tokens', 0)

            return text, tool_calls, input_tokens, output_tokens

        except Exception as e:
            return f"API Error: {str(e)}", [], 0, 0

    def _generate_minimax(
        self,
        user_query: str,
        model: str
    ) -> Tuple[str, List[Dict], int, int]:
        """Generate using MiniMax API (OpenAI-compatible)"""
        history = self.memory.get_conversation_history(last_n=10)
        context = self.memory.get_context_summary()

        system_msg = self.system_prompt
        if context != "No active drug compound being discussed.":
            system_msg += f"\n\nCurrent context:\n{context}"

        messages = [{"role": "system", "content": system_msg}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_query})

        try:
            response = self.minimax_client.chat.completions.create(
                model=model,
                max_tokens=2048,
                messages=messages,
                tools=self.openai_tools
            )

            message = response.choices[0].message
            text = message.content or ""

            tool_calls = []
            if message.tool_calls:
                for tc in message.tool_calls:
                    import json
                    tool_calls.append({
                        "id": tc.id,
                        "name": tc.function.name,
                        "input": json.loads(tc.function.arguments)
                    })

            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0

            return text, tool_calls, input_tokens, output_tokens

        except Exception as e:
            return f"API Error: {str(e)}", [], 0, 0

    def execute_tool_call(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool call"""
        from formulation_os.tools.builtins.preformulation_ai.adapter import run as preform_run
        from formulation_os.tools.builtins.formulation_ai.adapter import run as formulation_run

        try:
            if "preformulation_ai" in tool_name:
                # Map tool name to module
                if "fundamentals" in tool_name:
                    module = "fundamentals"
                elif "developability" in tool_name:
                    module = "developability"
                elif "solubility" in tool_name:
                    module = "solubility"
                elif "ph_profile" in tool_name:
                    module = "ph_profile"
                elif "if_descriptors" in tool_name:
                    module = "if_descriptors"
                else:
                    module = "fundamentals"  # default

                return preform_run({
                    "smiles": tool_input.get("smiles"),
                    "drug_name": tool_input.get("drug_name", ""),
                    "module": module,
                    "temperature": tool_input.get("temperature", 25.0),
                    "solvent": tool_input.get("solvent", "water")
                })

            elif "formulation_ai" in tool_name:
                # Map tool name to module
                if "solid_dispersion" in tool_name:
                    module = "solid_dispersion"
                elif "nanocrystal" in tool_name:
                    module = "nanocrystal"
                elif "cyclodextrin" in tool_name:
                    module = "cd_complex"
                elif "phospholipid_complex" in tool_name:
                    module = "phospholipid_complex"
                elif "sedds" in tool_name:
                    module = "sedds"
                elif "liposome" in tool_name:
                    module = "liposome"
                elif "strategy_recommendation" in tool_name:
                    module = "strategy_recommendation"
                else:
                    module = "solid_dispersion"  # default

                return formulation_run({
                    "smiles": tool_input.get("smiles"),
                    "drug_name": tool_input.get("drug_name", ""),
                    "module": module
                })
            else:
                return {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"error": str(e)}

    def generate_with_tools_loop(
        self,
        user_query: str,
        model: str,
        max_iterations: int = 5
    ) -> Tuple[str, List[Dict], int, int]:
        """Generate response with full tool-use loop

        Implements complete agentic cycle:
        1. User query → AI generates (may include tool_calls)
        2. Execute all tools and collect results
        3. Send tool results back to AI
        4. AI generates comprehensive final analysis
        5. Return complete response

        Args:
            user_query: User's question
            model: Model ID to use
            max_iterations: Maximum tool-use iterations (default: 5)

        Returns:
            (final_response, all_tool_calls, total_input_tokens, total_output_tokens)
        """
        all_tool_calls = []
        total_input_tokens = 0
        total_output_tokens = 0

        # Add user message to memory
        self.memory.add_message("user", user_query)

        current_query = user_query

        for iteration in range(max_iterations):
            # Generate response
            resp, tool_calls, in_tok, out_tok = self.generate_response(current_query, model)
            total_input_tokens += in_tok
            total_output_tokens += out_tok

            # If no tool calls, we're done
            if not tool_calls:
                return resp, all_tool_calls, total_input_tokens, total_output_tokens

            # Execute all tool calls
            all_tool_calls.extend(tool_calls)
            tool_results = []

            for tool_call in tool_calls:
                result = self.execute_tool_call(tool_call["name"], tool_call["input"])
                tool_results.append({
                    "tool_name": tool_call["name"],
                    "result": result
                })

                # Capture evidence if evidence_manager is available
                if self.evidence_manager:
                    self.evidence_manager.capture_from_tool_call(tool_call["name"], result)

            # Add assistant message with tool calls to memory
            # Ensure content is not None/empty for API compatibility
            assistant_content = resp if resp else "[Tool calls executed]"
            self.memory.add_message("assistant", assistant_content)

            # Format tool results for next iteration
            import json
            results_text = "Tool execution results:\n\n"
            for tr in tool_results:
                results_text += f"**{tr['tool_name']}**:\n```json\n{json.dumps(tr['result'], indent=2)}\n```\n\n"
            results_text += "Based on these results, please provide a comprehensive analysis including:\n"
            results_text += "1. BCS classification and reasoning\n"
            results_text += "2. Key physicochemical properties interpretation\n"
            results_text += "3. Developability assessment\n"
            results_text += "4. Formulation strategy recommendations\n"

            current_query = results_text

        # If we hit max iterations, return what we have
        return resp, all_tool_calls, total_input_tokens, total_output_tokens

    @classmethod
    def get_available_models(cls) -> List[Dict[str, Any]]:
        """Get list of available models"""
        return [
            {
                "id": model_id,
                **config
            }
            for model_id, config in cls.MODELS.items()
        ]
