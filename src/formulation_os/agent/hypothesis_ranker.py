"""Hypothesis Ranking System for FormulationOS

Ranks formulation strategies with:
1. Confidence scores
2. Supporting evidence
3. Risk factors
4. Validation methods
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Evidence:
    """Single piece of supporting or contradicting evidence"""
    type: str  # 'supporting' or 'risk'
    description: str
    source: str  # 'literature' | 'model_prediction' | 'physicochemical'
    strength: float  # 0-1

@dataclass
class Hypothesis:
    """Scientific hypothesis with ranking"""
    strategy_name: str
    description: str
    confidence: float  # 0-1
    supporting_evidence: List[Evidence] = field(default_factory=list)
    risks: List[Evidence] = field(default_factory=list)
    validation_methods: List[str] = field(default_factory=list)
    rationale: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    def calculate_confidence(self) -> float:
        """Calculate confidence based on evidence"""
        if not self.supporting_evidence:
            return 0.3  # Default low confidence

        # Weight by evidence strength
        support_score = sum(e.strength for e in self.supporting_evidence) / len(self.supporting_evidence)

        # Penalty for risks
        risk_penalty = sum(e.strength for e in self.risks) * 0.2 if self.risks else 0

        confidence = min(1.0, max(0.0, support_score - risk_penalty))
        return round(confidence, 2)

    def to_markdown(self, rank: int) -> str:
        """Format hypothesis as markdown for display"""
        md = f"### Hypothesis {rank}: {self.strategy_name}\n\n"
        md += f"**Confidence Score**: {self.confidence:.2f}/1.00\n\n"

        if self.rationale:
            md += f"**Rationale**: {self.rationale}\n\n"

        if self.supporting_evidence:
            md += "**Supporting Evidence**:\n"
            for ev in self.supporting_evidence:
                md += f"- ✅ {ev.description} ({ev.source}, strength: {ev.strength:.2f})\n"
            md += "\n"

        if self.risks:
            md += "**Risks & Challenges**:\n"
            for risk in self.risks:
                md += f"- ⚠️ {risk.description} ({risk.source})\n"
            md += "\n"

        if self.validation_methods:
            md += "**Validation Methods**:\n"
            for method in self.validation_methods:
                md += f"- 🔬 {method}\n"
            md += "\n"

        return md


class HypothesisRanker:
    """Ranks and manages formulation hypotheses"""

    def __init__(self):
        self.hypotheses: List[Hypothesis] = []

    def add_hypothesis(self, hypothesis: Hypothesis):
        """Add a hypothesis to the ranking system"""
        # Recalculate confidence
        hypothesis.confidence = hypothesis.calculate_confidence()
        self.hypotheses.append(hypothesis)

    def rank_hypotheses(self) -> List[Hypothesis]:
        """Return hypotheses sorted by confidence"""
        return sorted(self.hypotheses, key=lambda h: h.confidence, reverse=True)

    def generate_ranking_report(self) -> str:
        """Generate comprehensive ranking report"""
        ranked = self.rank_hypotheses()

        if not ranked:
            return "No hypotheses generated yet."

        report = "## 🎯 Formulation Strategy Ranking\n\n"
        report += f"*Based on analysis of {len(ranked)} candidate strategies*\n\n"
        report += "---\n\n"

        for i, hyp in enumerate(ranked, 1):
            report += hyp.to_markdown(i)
            report += "---\n\n"

        # Summary recommendation
        top_hyp = ranked[0]
        report += "## 💡 Recommendation\n\n"
        report += f"Based on current evidence, I would **prioritize Hypothesis 1 ({top_hyp.strategy_name})** "
        report += f"with a confidence score of {top_hyp.confidence:.2f}.\n\n"

        if len(ranked) > 1:
            alt_hyp = ranked[1]
            report += f"However, I recommend keeping **Hypothesis 2 ({alt_hyp.strategy_name})** "
            report += f"as an alternative approach, especially if initial validation reveals challenges with the primary strategy.\n\n"

        return report

    def extract_hypotheses_from_response(self, response: str, tool_calls: List[Dict]) -> None:
        """Extract hypotheses from AI response text"""
        # Look for common formulation strategies
        strategies = {
            'solid dispersion': {
                'description': 'Amorphous solid dispersion to enhance dissolution',
                'validation': ['DSC', 'XRPD', 'Dissolution testing'],
            },
            'nanocrystal': {
                'description': 'Particle size reduction to increase surface area',
                'validation': ['DLS', 'PDI measurement', 'Dissolution testing'],
            },
            'cyclodextrin': {
                'description': 'Cyclodextrin complexation to improve solubility',
                'validation': ['NMR', 'Phase solubility', 'Binding studies'],
            },
            'sedds': {
                'description': 'Self-emulsifying drug delivery system',
                'validation': ['Emulsification test', 'Droplet size', 'In vitro dissolution'],
            },
            'liposome': {
                'description': 'Liposomal formulation for targeted delivery',
                'validation': ['Particle size', 'Encapsulation efficiency', 'Release kinetics'],
            },
        }

        response_lower = response.lower()

        for strategy_key, strategy_info in strategies.items():
            if strategy_key in response_lower:
                # Create hypothesis
                hyp = Hypothesis(
                    strategy_name=strategy_key.replace('_', ' ').title(),
                    description=strategy_info['description'],
                    confidence=0.5,  # Will be recalculated
                    validation_methods=strategy_info['validation']
                )

                # Extract evidence from response
                # Look for positive indicators
                if 'suitable' in response_lower or 'recommend' in response_lower:
                    hyp.supporting_evidence.append(Evidence(
                        type='supporting',
                        description='AI model recommendation',
                        source='model_prediction',
                        strength=0.7
                    ))

                # Look for BCS class mention
                if 'bcs ii' in response_lower or 'bcs class ii' in response_lower:
                    hyp.supporting_evidence.append(Evidence(
                        type='supporting',
                        description='Appropriate for BCS Class II compounds',
                        source='physicochemical',
                        strength=0.8
                    ))

                # Look for risks
                if 'stability' in response_lower and strategy_key == 'solid dispersion':
                    hyp.risks.append(Evidence(
                        type='risk',
                        description='Physical stability challenges (recrystallization)',
                        source='literature',
                        strength=0.6
                    ))

                if 'complexity' in response_lower or 'difficult' in response_lower:
                    hyp.risks.append(Evidence(
                        type='risk',
                        description='Manufacturing complexity',
                        source='model_prediction',
                        strength=0.5
                    ))

                self.add_hypothesis(hyp)
