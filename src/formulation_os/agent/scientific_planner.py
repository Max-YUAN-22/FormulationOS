"""Scientific Planner for FormulationOS

Transforms AI from "report generator" to "research partner" by:
1. Understanding research objectives
2. Actively asking clarifying questions
3. Identifying key constraints
4. Guiding the research process
"""

from typing import Dict, List, Optional, Tuple
import re

class ScientificPlanner:
    """Plans and guides pharmaceutical formulation research"""

    def __init__(self):
        self.research_goals = []
        self.constraints = {}
        self.clarifications_needed = []

    def analyze_user_query(self, query: str) -> Dict[str, any]:
        """Analyze user query to understand research objective

        Returns:
            {
                'goal_type': 'formulation_design' | 'property_analysis' | 'strategy_selection',
                'drug_info': {...},
                'constraints': [...],
                'missing_info': [...],
                'clarifying_questions': [...]
            }
        """
        result = {
            'goal_type': None,
            'drug_info': {},
            'constraints': [],
            'missing_info': [],
            'clarifying_questions': []
        }

        query_lower = query.lower()

        # 1. Identify goal type
        if any(kw in query_lower for kw in ['设计', 'design', 'develop', 'formulation']):
            result['goal_type'] = 'formulation_design'
        elif any(kw in query_lower for kw in ['分析', 'analyze', 'evaluate', 'assess']):
            result['goal_type'] = 'property_analysis'
        elif any(kw in query_lower for kw in ['策略', 'strategy', 'recommend', 'suggest']):
            result['goal_type'] = 'strategy_selection'
        else:
            result['goal_type'] = 'general_inquiry'

        # 2. Extract drug info
        smiles_match = re.search(r'SMILES[：:是]?\s*[\'"]?([A-Za-z0-9@+\-\[\]()=#$]+)[\'"]?', query, re.IGNORECASE)
        if smiles_match:
            result['drug_info']['smiles'] = smiles_match.group(1)

        drug_patterns = [
            r'分析\s*([A-Za-z一-龥]+)[（(]',
            r'Ibuprofen|Aspirin|布洛芬|阿司匹林',
        ]
        for pattern in drug_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                if match.lastindex and match.lastindex >= 1:
                    result['drug_info']['name'] = match.group(1)
                else:
                    result['drug_info']['name'] = match.group(0)
                break

        # 3. Identify constraints
        if 'oral' in query_lower or '口服' in query_lower:
            result['constraints'].append('oral_administration')
        if 'bioavailability' in query_lower or '生物利用度' in query_lower:
            result['constraints'].append('improve_bioavailability')
        if 'tablet' in query_lower or '片剂' in query_lower:
            result['constraints'].append('tablet_form')

        # 4. Identify missing critical information
        if result['goal_type'] == 'formulation_design':
            # For formulation design, we need more info
            if 'dosage_form' not in [c for c in result['constraints']]:
                result['missing_info'].append('dosage_form')
                result['clarifying_questions'].append(
                    "**Dosage Form Clarification**: What is your target dosage form?\n"
                    "A. Immediate Release Tablet\n"
                    "B. Sustained Release Formulation\n"
                    "C. Pediatric Formulation (liquid/suspension)\n"
                    "D. Other (please specify)"
                )

            if not result.get('constraints'):
                result['missing_info'].append('primary_objective')
                result['clarifying_questions'].append(
                    "**Primary Objective**: What is the main challenge you're trying to address?\n"
                    "A. Poor solubility/dissolution\n"
                    "B. Stability issues\n"
                    "C. Manufacturing challenges\n"
                    "D. Patient compliance"
                )

        return result

    def should_ask_clarifying_questions(self, analysis: Dict) -> bool:
        """Determine if AI should ask questions before proceeding"""
        return len(analysis.get('clarifying_questions', [])) > 0

    def generate_clarifying_prompt(self, analysis: Dict) -> str:
        """Generate a natural prompt asking for clarification"""
        questions = analysis.get('clarifying_questions', [])
        if not questions:
            return ""

        prompt = "I'd like to understand your research objective better before diving into analysis. Could you help me clarify:\n\n"

        for i, q in enumerate(questions, 1):
            prompt += f"{q}\n\n"

        prompt += "This will help me provide more targeted recommendations."

        return prompt
