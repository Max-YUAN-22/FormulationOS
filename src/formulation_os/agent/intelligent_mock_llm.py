"""Intelligent Mock LLM for FormulationOS

Simulates LLM-based conversational agent with:
- Context-aware responses (not templates)
- Natural language generation
- Tool calling decisions
- Scientific narrative style

This demonstrates correct architecture before integrating real LLM APIs.
"""

from typing import Dict, Any, List, Optional, Tuple
from formulation_os.agent.conversation_memory import ConversationMemory
from formulation_os.planner.intent_parser import IntentParser


class IntelligentMockLLM:
    """Mock LLM that generates contextual, natural responses"""

    def __init__(self, memory: ConversationMemory):
        self.memory = memory
        self.intent_parser = IntentParser()

    def generate_response(self, user_query: str) -> Tuple[str, List[Dict], bool]:
        """Generate contextual response

        Returns:
            (response_text, tool_calls_needed, should_call_tools)
        """
        # Get current context
        context_summary = self.memory.get_context_summary()
        state = self.memory.scientific_state

        # Parse user intent
        intent = self.intent_parser.parse(user_query)
        query_lower = user_query.lower()

        # Contextual understanding
        if self._is_greeting(query_lower):
            return self._generate_greeting(), [], False

        if self._is_asking_about_capabilities(query_lower):
            return self._generate_capabilities_explanation(), [], False

        if self._is_asking_about_drawing(query_lower) and state.drug_name:
            return self._generate_drawing_response(state.drug_name, state.smiles), [], False

        # Structure queries
        if intent.compound_name and self._is_structure_query(query_lower):
            if state.drug_name == intent.compound_name:
                # We already have this structure
                return self._generate_structure_reminder(state.drug_name, state.smiles), [], False
            else:
                # New drug structure
                return self._generate_structure_response(intent.compound_name, intent.compound_smiles), [], False

        # Analysis queries - need tools
        if intent.compound_name and self._is_analysis_query(query_lower):
            if state.drug_name == intent.compound_name and state.physicochemical_props:
                # Already analyzed
                return self._generate_analysis_summary(state), [], False
            else:
                # Need to analyze
                return self._generate_analysis_intent(intent), self._plan_analysis_tools(intent), True

        # Follow-up about formulation challenges
        if self._is_asking_about_challenges(query_lower):
            if state.physicochemical_props:
                return self._generate_challenge_analysis(state), [], False
            else:
                return self._generate_need_analysis_first(), [], False

        # Follow-up about hypotheses
        if self._is_asking_about_hypotheses(query_lower):
            if state.hypotheses:
                return self._generate_hypothesis_elaboration(state), [], False
            elif state.formulation_results:
                return self._generate_hypothesis_summary(state), [], False
            else:
                return self._generate_need_formulation_first(), [], False

        # Follow-up about experiments
        if self._is_asking_about_experiments(query_lower):
            if state.hypotheses or state.formulation_results:
                return self._generate_experiment_suggestions(state), [], False
            else:
                return self._generate_need_context_for_experiments(), [], False

        # General contextual follow-up
        if state.drug_name:
            return self._generate_contextual_followup(user_query, state), [], False

        # Fallback: helpful but not template
        return self._generate_helpful_fallback(user_query), [], False

    # Intent detection helpers
    def _is_greeting(self, query: str) -> bool:
        return any(kw in query for kw in ["hello", "hi", "你好", "您好", "hey"])

    def _is_asking_about_capabilities(self, query: str) -> bool:
        return any(kw in query for kw in ["what can you", "capabilities", "能做什么", "功能"])

    def _is_asking_about_drawing(self, query: str) -> bool:
        return any(kw in query for kw in ["draw", "画", "图", "visualize", "show structure"])

    def _is_structure_query(self, query: str) -> bool:
        return any(kw in query for kw in ["structure", "结构", "smiles", "分子式"])

    def _is_analysis_query(self, query: str) -> bool:
        return any(kw in query for kw in ["analyze", "分析", "design", "设计", "formulation", "制剂"])

    def _is_asking_about_challenges(self, query: str) -> bool:
        return any(kw in query for kw in ["challenge", "挑战", "problem", "问题", "limitation", "difficulty"])

    def _is_asking_about_hypotheses(self, query: str) -> bool:
        return any(kw in query for kw in ["hypothesis", "假设", "strategy", "策略", "approach"])

    def _is_asking_about_experiments(self, query: str) -> bool:
        return any(kw in query for kw in ["experiment", "实验", "validation", "验证", "test", "测试"])

    # Response generators (natural language, not templates)
    def _generate_greeting(self) -> str:
        return ("Hello! I'm a pharmaceutical formulation scientist AI. "
                "I can help you analyze drug properties, identify formulation challenges, "
                "and generate scientific hypotheses for experimental validation.\n\n"
                "Try asking me about a specific drug like Ibuprofen or Aspirin, "
                "or tell me about a formulation challenge you're working on.")

    def _generate_capabilities_explanation(self) -> str:
        return ("I integrate computational pharmaceutics tools to assist with formulation research:\n\n"
                "**Drug Analysis**: I can analyze physicochemical properties (LogP, LogS, solubility) "
                "and predict BCS classification using PreformulationAI.\n\n"
                "**Formulation Screening**: I evaluate candidate strategies (solid dispersion, nanocrystal, "
                "cyclodextrin) using FormulationAI's computational models.\n\n"
                "**Scientific Reasoning**: I generate testable hypotheses based on computational evidence, "
                "highlighting remaining uncertainties and suggesting validation experiments.\n\n"
                "What specific aspect would you like to explore?")

    def _generate_drawing_response(self, drug_name: str, smiles: Optional[str]) -> str:
        if smiles:
            return (f"Yes, I can help visualize {drug_name}!\n\n"
                    f"Here's the structure we're discussing:\n```\nSMILES: {smiles}\n```\n\n"
                    f"I can provide:\n"
                    f"- 2D chemical structure representation\n"
                    f"- Molecular property diagram\n"
                    f"- Formulation decision tree\n\n"
                    f"Which type of visualization would be most helpful for your work?")
        else:
            return (f"I'd like to help visualize {drug_name}, but I need its chemical structure first. "
                    f"Could you provide the SMILES notation?")

    def _generate_structure_response(self, drug_name: str, smiles: Optional[str]) -> str:
        if not smiles:
            return (f"I'd like to help with {drug_name}, but I don't have its structure in my database. "
                    f"If you provide the SMILES notation, I can analyze its properties and suggest formulation strategies.")

        self.memory.update_scientific_state(drug_name=drug_name, smiles=smiles)

        response = f"## {drug_name}\n\n**Chemical Structure**:\n```\nSMILES: {smiles}\n```\n\n"

        if "ibuprofen" in drug_name.lower():
            response += ("Ibuprofen is a typical BCS Class II drug - it has excellent membrane permeability "
                        "but suffers from poor aqueous solubility. This means the primary development challenge "
                        "is dissolution-limited absorption rather than permeability.\n\n")
        elif "aspirin" in drug_name.lower():
            response += ("Aspirin is generally classified as BCS Class I with good solubility and permeability. "
                        "However, its main challenges are chemical instability (hydrolysis) and GI irritation.\n\n")

        response += ("Would you like me to:\n"
                    "- Analyze its physicochemical properties in detail?\n"
                    "- Predict formulation challenges?\n"
                    "- Suggest candidate formulation strategies?")

        return response

    def _generate_structure_reminder(self, drug_name: str, smiles: str) -> str:
        return (f"We're currently discussing {drug_name} with SMILES: `{smiles}`.\n\n"
                f"I've already analyzed some of its properties. "
                f"Would you like me to elaborate on the formulation challenges or generated hypotheses?")

    def _generate_analysis_intent(self, intent) -> str:
        drug_name = intent.compound_name
        dosage_form = intent.dosage_form or "oral formulation"

        response = f"## Analyzing {drug_name} for {dosage_form}\n\n"
        response += ("I'll systematically evaluate this compound using computational tools. "
                    "My approach will be:\n\n"
                    "1. **Physicochemical characterization** - LogP, LogS, molecular descriptors\n"
                    "2. **Developability assessment** - BCS classification, formulatability index\n"
                    "3. **Challenge identification** - Primary limitations for oral delivery\n"
                    "4. **Strategy screening** - Computational evaluation of candidate approaches\n\n"
                    "Let me gather the computational evidence...\n\n")

        return response

    def _generate_analysis_summary(self, state) -> str:
        props = state.physicochemical_props
        drug = state.drug_name

        response = f"I've already analyzed {drug}. Here's what we found:\n\n"

        if props.get("logP"):
            response += f"- **LogP**: {props['logP']:.2f} (lipophilicity)\n"
        if props.get("logS"):
            response += f"- **LogS**: {props['logS']:.2f} (aqueous solubility)\n"
        if props.get("bcs_class"):
            response += f"- **BCS Class**: {props['bcs_class']}\n\n"

        if props.get("bcs_class") == "II":
            response += (f"The key finding is that {drug} is a BCS Class II compound. "
                        f"This means dissolution rate is the primary absorption bottleneck, "
                        f"not membrane permeability.\n\n")

        response += "Would you like me to elaborate on:\n- Formulation challenges?\n- Candidate strategies?\n- Validation experiments?"

        return response

    def _generate_challenge_analysis(self, state) -> str:
        props = state.physicochemical_props
        drug = state.drug_name
        bcs = props.get("bcs_class", "Unknown")

        response = f"## Formulation Challenges for {drug}\n\n"

        if bcs == "II":
            response += ("Based on the BCS Class II profile, the primary challenges are:\n\n"
                        "**1. Poor Dissolution Rate**\n"
                        f"With LogS = {props.get('logS', 'N/A')}, {drug} has low intrinsic solubility. "
                        "This creates a dissolution-limited absorption profile.\n\n"
                        "**2. Solubility-Dissolution Relationship**\n"
                        "Even with good permeability, oral bioavailability will be limited by how fast "
                        "the drug can dissolve in GI fluids.\n\n"
                        "**3. Formulation Strategy Selection**\n"
                        "We need approaches that enhance apparent solubility or increase dissolution kinetics "
                        "without compromising stability.\n\n")

            response += ("Potential strategies to address these challenges:\n"
                        "- Solid dispersion (amorphous conversion)\n"
                        "- Nanocrystal (particle size reduction)\n"
                        "- Cyclodextrin complexation (inclusion complex)\n\n"
                        "Would you like me to evaluate these approaches computationally?")

        else:
            response += f"For BCS Class {bcs} compounds, the challenges differ from typical solubility limitations. "

        return response

    def _generate_need_analysis_first(self) -> str:
        return ("To discuss formulation challenges, I first need to analyze the drug's properties. "
                "Could you tell me which compound you're working with?")

    def _generate_hypothesis_elaboration(self, state) -> str:
        response = "## Generated Hypotheses - Detailed Analysis\n\n"
        for i, hyp in enumerate(state.hypotheses, 1):
            response += f"**Hypothesis {i}**: {hyp.get('strategy', 'Unknown')}\n\n"
            response += f"*Rationale*: {hyp.get('rationale', 'N/A')}\n\n"
            if hyp.get('evidence'):
                response += f"*Computational Evidence*: {hyp['evidence']}\n\n"
            if hyp.get('uncertainty'):
                response += f"*Remaining Uncertainty*: {hyp['uncertainty']}\n\n"
            response += "---\n\n"

        response += "Which hypothesis would you like to explore further?"
        return response

    def _generate_hypothesis_summary(self, state) -> str:
        results = state.formulation_results
        drug = state.drug_name

        response = f"## Computational Formulation Hypotheses for {drug}\n\n"

        if "solid_dispersion" in results:
            sd = results["solid_dispersion"]
            response += ("**Hypothesis 1: Amorphous Solid Dispersion**\n"
                        f"Computational stability prediction: {sd.get('physical_stability', 'N/A')}\n"
                        "Rationale: Amorphous conversion increases apparent solubility\n"
                        "Uncertainty: Polymer selection, long-term stability\n\n")

        if "nanocrystal" in results:
            nc = results["nanocrystal"]
            response += ("**Hypothesis 2: Nanocrystal Formulation**\n"
                        f"Predicted size: {nc.get('predicted_particle_size_nm', 'N/A')} nm\n"
                        "Rationale: Particle size reduction enhances dissolution kinetics\n"
                        "Uncertainty: Manufacturing feasibility, stabilizer selection\n\n")

        if "cyclodextrin" in results:
            cd = results["cyclodextrin"]
            response += ("**Hypothesis 3: Cyclodextrin Complexation**\n"
                        f"Complexation ΔG: {cd.get('complexation_free_energy_kj_mol', 'N/A')} kJ/mol\n"
                        "Rationale: Inclusion complex increases apparent solubility\n"
                        "Uncertainty: CD type optimization, cost-effectiveness\n\n")

        response += ("These are computational hypotheses requiring experimental validation. "
                    "None can be considered definitive without dissolution testing and stability studies.")

        return response

    def _generate_need_formulation_first(self) -> str:
        return ("I haven't evaluated any formulation strategies yet. "
                "Would you like me to analyze your compound and screen candidate approaches?")

    def _generate_experiment_suggestions(self, state) -> str:
        drug = state.drug_name

        response = f"## Experimental Validation Plan for {drug}\n\n"
        response += ("Based on the computational hypotheses, I recommend a staged validation approach:\n\n"
                    "**Phase 1: Feasibility Screening**\n"
                    "- Solid dispersion: Polymer screening (PVP, PVPVA, HPMCAS) + thermal analysis\n"
                    "- Nanocrystal: Wet bead milling feasibility + particle size characterization\n"
                    "- Cyclodextrin: Phase solubility study + complexation constant determination\n\n"
                    "**Phase 2: Performance Comparison**\n"
                    "- Dissolution testing (USP Apparatus II, multiple pH conditions)\n"
                    "- Stability studies (accelerated 40°C/75%RH for 3 months)\n"
                    "- Physical characterization (XRPD, DSC, SEM)\n\n"
                    "**Phase 3: Lead Selection**\n"
                    "- In vitro-in vivo correlation assessment\n"
                    "- Manufacturing scalability evaluation\n"
                    "- Cost-benefit analysis\n\n"
                    "Which experimental aspect would you like me to detail further?")

        return response

    def _generate_need_context_for_experiments(self) -> str:
        return ("To suggest validation experiments, I need to understand the formulation context first. "
                "Which compound are you working with, and have you identified any promising strategies?")

    def _generate_contextual_followup(self, query: str, state) -> str:
        drug = state.drug_name
        return (f"We're currently analyzing {drug}. "
                f"Your question '{query}' is interesting. "
                f"Could you clarify if you're asking about:\n"
                f"- Formulation challenges for {drug}?\n"
                f"- Specific experimental validation?\n"
                f"- Alternative formulation approaches?\n\n"
                f"I want to make sure I address your exact question.")

    def _generate_helpful_fallback(self, query: str) -> str:
        return (f"I understand you're asking about: '{query}'\n\n"
                f"I'm here to help with pharmaceutical formulation research. "
                f"I work best when we focus on:\n"
                f"- A specific drug compound\n"
                f"- Formulation challenges\n"
                f"- Strategy evaluation\n"
                f"- Experimental design\n\n"
                f"Could you tell me which compound you're interested in, or what formulation challenge you're facing?")

    def _plan_analysis_tools(self, intent) -> List[Dict[str, Any]]:
        """Plan which tools to call for analysis"""
        tools = []

        if intent.compound_smiles or intent.compound_name:
            # Need PreformulationAI
            tools.append({
                "tool": "preformulation_ai",
                "module": "fundamentals",
                "params": {
                    "smiles": intent.compound_smiles,
                    "drug_name": intent.compound_name
                }
            })
            tools.append({
                "tool": "preformulation_ai",
                "module": "developability",
                "params": {
                    "smiles": intent.compound_smiles,
                    "drug_name": intent.compound_name
                }
            })

            # If BCS II detected, plan FormulationAI calls
            tools.append({
                "tool": "formulation_ai",
                "module": "solid_dispersion",
                "params": {
                    "smiles": intent.compound_smiles,
                    "drug_name": intent.compound_name
                }
            })
            tools.append({
                "tool": "formulation_ai",
                "module": "nanocrystal",
                "params": {
                    "smiles": intent.compound_smiles,
                    "drug_name": intent.compound_name
                }
            })
            tools.append({
                "tool": "formulation_ai",
                "module": "cd_complex",
                "params": {
                    "smiles": intent.compound_smiles,
                    "drug_name": intent.compound_name
                }
            })

        return tools
