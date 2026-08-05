"""
AI Prediction Validation Framework
Multi-layer validation to verify AI predictions and recommendations
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import numpy as np

@dataclass
class ValidationResult:
    """验证结果"""
    passed: bool
    confidence: float  # 0-1
    evidence: List[str]
    warnings: List[str]
    method: str

class PredictionValidator:
    """AI预测验证器"""

    def __init__(self):
        self.validation_history = []

    def validate_bcs_prediction(self,
                                 predicted_class: str,
                                 molecular_properties: Dict,
                                 literature_support: List[Dict] = None) -> Dict:
        """
        验证BCS分类预测

        返回多层验证结果：
        1. 规则验证（FDA指南）
        2. 文献验证（已知药物对比）
        3. 不确定性评估
        """
        validation_report = {
            'prediction': predicted_class,
            'confidence_score': 0.0,
            'validation_layers': [],
            'overall_status': 'pending',
            'warnings': [],
            'evidence': []
        }

        # Layer 1: FDA规则验证
        rule_validation = self._validate_by_fda_rules(predicted_class, molecular_properties)
        validation_report['validation_layers'].append(rule_validation)

        if rule_validation.passed:
            validation_report['confidence_score'] += 0.4
            validation_report['evidence'].extend(rule_validation.evidence)
        else:
            validation_report['warnings'].extend(rule_validation.warnings)

        # Layer 2: Lipinski规则检查
        lipinski_validation = self._validate_lipinski(molecular_properties)
        validation_report['validation_layers'].append(lipinski_validation)

        if lipinski_validation.passed:
            validation_report['confidence_score'] += 0.2
            validation_report['evidence'].extend(lipinski_validation.evidence)
        else:
            validation_report['warnings'].extend(lipinski_validation.warnings)

        # Layer 3: 文献支持验证
        if literature_support:
            lit_validation = self._validate_by_literature(predicted_class, literature_support)
            validation_report['validation_layers'].append(lit_validation)
            validation_report['confidence_score'] += lit_validation.confidence * 0.4

        # 最终判断
        if validation_report['confidence_score'] >= 0.7:
            validation_report['overall_status'] = 'high_confidence'
        elif validation_report['confidence_score'] >= 0.5:
            validation_report['overall_status'] = 'moderate_confidence'
        else:
            validation_report['overall_status'] = 'low_confidence'

        return validation_report

    def _validate_by_fda_rules(self, bcs_class: str, props: Dict) -> ValidationResult:
        """基于FDA BCS指南验证"""
        evidence = []
        warnings = []
        passed = True

        mw = props.get('molecular_weight', 0)
        logp = props.get('logp', 0)
        tpsa = props.get('tpsa', 0)

        # BCS I: 高溶解度 + 高渗透性
        if bcs_class == "BCS I":
            if logp > -1 and logp < 3:
                evidence.append(f"✅ LogP={logp:.2f} suggests good solubility (FDA: -1 to 3)")
            else:
                warnings.append(f"⚠️ LogP={logp:.2f} may indicate solubility issues")
                passed = False

            if tpsa < 140:
                evidence.append(f"✅ TPSA={tpsa:.1f} Ų suggests good permeability (FDA: <140)")
            else:
                warnings.append(f"⚠️ TPSA={tpsa:.1f} Ų may limit permeability")
                passed = False

        # BCS II: 低溶解度 + 高渗透性
        elif bcs_class == "BCS II":
            if logp > 3:
                evidence.append(f"✅ LogP={logp:.2f} consistent with low solubility (FDA: >3)")
            else:
                warnings.append(f"⚠️ LogP={logp:.2f} suggests solubility may not be limiting")

            if tpsa < 140:
                evidence.append(f"✅ TPSA={tpsa:.1f} Ų confirms good permeability (FDA: <140)")
            else:
                warnings.append(f"⚠️ TPSA={tpsa:.1f} Ų conflicts with BCS II classification")
                passed = False

        # BCS III: 高溶解度 + 低渗透性
        elif bcs_class == "BCS III":
            if logp < 0:
                evidence.append(f"✅ LogP={logp:.2f} suggests high solubility (FDA: <0)")

            if tpsa > 140:
                evidence.append(f"✅ TPSA={tpsa:.1f} Ų consistent with low permeability (FDA: >140)")
            else:
                warnings.append(f"⚠️ TPSA={tpsa:.1f} Ų suggests permeability may not be limiting")

        # BCS IV: 低溶解度 + 低渗透性
        elif bcs_class == "BCS IV":
            if logp > 5 or logp < -2:
                evidence.append(f"✅ LogP={logp:.2f} suggests solubility challenges")

            if tpsa > 140 or mw > 500:
                evidence.append(f"✅ TPSA={tpsa:.1f}/MW={mw:.1f} consistent with permeability issues")

        return ValidationResult(
            passed=passed,
            confidence=0.8 if passed else 0.3,
            evidence=evidence,
            warnings=warnings,
            method="FDA BCS Guidelines"
        )

    def _validate_lipinski(self, props: Dict) -> ValidationResult:
        """Lipinski五规则验证"""
        evidence = []
        warnings = []
        violations = 0

        mw = props.get('molecular_weight', 0)
        logp = props.get('logp', 0)
        hbd = props.get('hbd', 0)
        hba = props.get('hba', 0)

        if mw <= 500:
            evidence.append(f"✅ MW={mw:.1f} Da (Lipinski: ≤500)")
        else:
            warnings.append(f"⚠️ MW={mw:.1f} Da exceeds Lipinski limit (>500)")
            violations += 1

        if logp <= 5:
            evidence.append(f"✅ LogP={logp:.2f} (Lipinski: ≤5)")
        else:
            warnings.append(f"⚠️ LogP={logp:.2f} exceeds Lipinski limit (>5)")
            violations += 1

        if hbd <= 5:
            evidence.append(f"✅ HBD={hbd} (Lipinski: ≤5)")
        else:
            warnings.append(f"⚠️ HBD={hbd} exceeds Lipinski limit (>5)")
            violations += 1

        if hba <= 10:
            evidence.append(f"✅ HBA={hba} (Lipinski: ≤10)")
        else:
            warnings.append(f"⚠️ HBA={hba} exceeds Lipinski limit (>10)")
            violations += 1

        passed = violations <= 1  # Lipinski允许1个违反

        return ValidationResult(
            passed=passed,
            confidence=1.0 - (violations * 0.2),
            evidence=evidence,
            warnings=warnings,
            method="Lipinski Rule of Five"
        )

    def _validate_by_literature(self, predicted_class: str, papers: List[Dict]) -> ValidationResult:
        """文献支持验证"""
        evidence = []
        warnings = []

        # 检查文献中是否提到BCS分类
        supporting_papers = 0
        for paper in papers[:5]:  # 只检查前5篇
            abstract = paper.get('abstract', '').lower()
            title = paper.get('title', '').lower()

            if predicted_class.lower() in abstract or predicted_class.lower() in title:
                supporting_papers += 1
                evidence.append(f"📚 Literature support: {paper.get('title', 'Unknown')[:50]}... (PMID: {paper.get('pmid')})")

        confidence = min(supporting_papers / 3.0, 1.0)  # 3篇文献 = 100%置信度

        if supporting_papers == 0:
            warnings.append("⚠️ No direct literature support found for this BCS classification")

        return ValidationResult(
            passed=supporting_papers > 0,
            confidence=confidence,
            evidence=evidence,
            warnings=warnings,
            method="Literature Evidence"
        )

    def validate_formulation_strategy(self,
                                      strategy: str,
                                      drug_properties: Dict,
                                      bcs_class: str) -> Dict:
        """验证制剂策略推荐"""
        validation_report = {
            'strategy': strategy,
            'suitability_score': 0.0,
            'evidence': [],
            'warnings': [],
            'success_cases': [],
            'failure_risks': []
        }

        # 策略适用性规则库
        strategy_rules = {
            'ASD': {
                'suitable_bcs': ['BCS II', 'BCS IV'],
                'mw_range': (200, 600),
                'logp_range': (2, 5),
                'success_rate': 0.75
            },
            'Nanocrystal': {
                'suitable_bcs': ['BCS II', 'BCS IV'],
                'mw_range': (200, 800),
                'logp_range': (3, 7),
                'success_rate': 0.70
            },
            'SEDDS': {
                'suitable_bcs': ['BCS II', 'BCS IV'],
                'logp_range': (3, 8),
                'success_rate': 0.65
            },
            'Cyclodextrin': {
                'suitable_bcs': ['BCS II'],
                'mw_range': (150, 400),
                'success_rate': 0.60
            }
        }

        if strategy in strategy_rules:
            rules = strategy_rules[strategy]

            # BCS适用性
            if bcs_class in rules.get('suitable_bcs', []):
                validation_report['evidence'].append(f"✅ {strategy} is suitable for {bcs_class}")
                validation_report['suitability_score'] += 0.4
            else:
                validation_report['warnings'].append(f"⚠️ {strategy} typically not recommended for {bcs_class}")

            # MW检查
            if 'mw_range' in rules:
                mw = drug_properties.get('molecular_weight', 0)
                min_mw, max_mw = rules['mw_range']
                if min_mw <= mw <= max_mw:
                    validation_report['evidence'].append(f"✅ MW={mw:.1f} Da within optimal range ({min_mw}-{max_mw})")
                    validation_report['suitability_score'] += 0.3
                else:
                    validation_report['warnings'].append(f"⚠️ MW={mw:.1f} Da outside typical range ({min_mw}-{max_mw})")

            # LogP检查
            if 'logp_range' in rules:
                logp = drug_properties.get('logp', 0)
                min_logp, max_logp = rules['logp_range']
                if min_logp <= logp <= max_logp:
                    validation_report['evidence'].append(f"✅ LogP={logp:.2f} within optimal range ({min_logp}-{max_logp})")
                    validation_report['suitability_score'] += 0.3
                else:
                    validation_report['warnings'].append(f"⚠️ LogP={logp:.2f} outside typical range ({min_logp}-{max_logp})")

            # 成功率
            success_rate = rules.get('success_rate', 0.5)
            validation_report['evidence'].append(f"📊 Historical success rate: {success_rate*100:.0f}%")

        return validation_report

    def generate_validation_summary(self, validation_results: List[Dict]) -> str:
        """生成验证摘要"""
        summary = "## 🔍 Prediction Validation Summary\n\n"

        for result in validation_results:
            if 'prediction' in result:  # BCS验证
                summary += f"**BCS Classification: {result['prediction']}**\n"
                summary += f"- Confidence: {result['confidence_score']*100:.0f}%\n"
                summary += f"- Status: {result['overall_status'].replace('_', ' ').title()}\n\n"

                summary += "**Evidence:**\n"
                for ev in result['evidence'][:3]:
                    summary += f"{ev}\n"

                if result['warnings']:
                    summary += "\n**Warnings:**\n"
                    for warn in result['warnings'][:2]:
                        summary += f"{warn}\n"

            elif 'strategy' in result:  # 策略验证
                summary += f"\n**Strategy: {result['strategy']}**\n"
                summary += f"- Suitability: {result['suitability_score']*100:.0f}%\n"
                for ev in result['evidence'][:2]:
                    summary += f"{ev}\n"

        return summary
