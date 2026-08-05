"""
Pharmaceutical Formulation Report Generator
Generate comprehensive PDF reports from conversation history
"""

from datetime import datetime
from typing import Dict, List, Optional
import json
from pathlib import Path

class FormulationReportGenerator:
    """药物制剂报告生成器"""

    def __init__(self):
        self.report_data = {
            'drug_name': '',
            'smiles': '',
            'cas': '',
            'molecular_properties': {},
            'bcs_classification': '',
            'solubility_assessment': {},
            'permeability_assessment': {},
            'formulation_challenges': [],
            'recommended_strategies': [],
            'experimental_suggestions': [],
            'literature_references': [],
            'tool_calls_history': [],
            'conversation_summary': ''
        }

    def collect_from_conversation(self, memory, tool_calls: List[Dict], drug_name: str, smiles: str):
        """从对话历史中收集数据"""
        self.report_data['drug_name'] = drug_name
        self.report_data['smiles'] = smiles
        self.report_data['tool_calls_history'] = tool_calls

        # 从对话中提取信息
        for msg in memory.messages:
            if msg.role == "assistant":
                content = msg.content

                # 提取BCS分类
                if "BCS" in content and "Class" in content:
                    import re
                    bcs_match = re.search(r'BCS Class (I|II|III|IV)', content)
                    if bcs_match:
                        self.report_data['bcs_classification'] = f"BCS Class {bcs_match.group(1)}"

                # 提取制剂策略
                if "strategy" in content.lower() or "formulation" in content.lower():
                    strategies = self._extract_strategies(content)
                    self.report_data['recommended_strategies'].extend(strategies)

    def _extract_strategies(self, text: str) -> List[str]:
        """从文本中提取制剂策略"""
        strategies = []
        strategy_keywords = [
            "Amorphous Solid Dispersion",
            "ASD",
            "Nanocrystal",
            "SEDDS",
            "Liposome",
            "Cyclodextrin",
            "Solid Lipid Nanoparticle",
            "Hot Melt Extrusion",
            "Spray Drying"
        ]

        for keyword in strategy_keywords:
            if keyword.lower() in text.lower():
                strategies.append(keyword)

        return list(set(strategies))

    def add_molecular_properties(self, properties: Dict):
        """添加分子性质"""
        self.report_data['molecular_properties'] = properties

    def add_literature_reference(self, paper: Dict):
        """添加文献引用"""
        self.report_data['literature_references'].append(paper)

    def add_experimental_suggestion(self, suggestion: str):
        """添加实验建议"""
        self.report_data['experimental_suggestions'].append(suggestion)

    def generate_markdown_report(self) -> str:
        """生成Markdown格式报告"""
        report = f"""# Pharmaceutical Formulation Feasibility Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Drug Name:** {self.report_data['drug_name']}
**SMILES:** `{self.report_data['smiles']}`

---

## Executive Summary

This report presents a comprehensive formulation feasibility analysis for **{self.report_data['drug_name']}**,
generated through AI-powered dialogue and literature analysis.

**BCS Classification:** {self.report_data['bcs_classification'] or 'Not determined'}

---

## 1. Molecular Properties

"""
        # 分子性质
        if self.report_data['molecular_properties']:
            props = self.report_data['molecular_properties']
            report += f"""
| Property | Value | Significance |
|----------|-------|--------------|
| Molecular Weight | {props.get('molecular_weight', 'N/A')} Da | {'✅ Within oral range (<500)' if props.get('molecular_weight', 1000) < 500 else '⚠️ High MW may affect absorption'} |
| LogP | {props.get('logp', 'N/A')} | {'✅ Good lipophilicity' if -1 < props.get('logp', -10) < 5 else '⚠️ May affect permeability'} |
| TPSA | {props.get('tpsa', 'N/A')} Ų | {'✅ Good permeability expected' if props.get('tpsa', 1000) < 140 else '⚠️ Poor permeability risk'} |
| H-Bond Donors | {props.get('hbd', 'N/A')} | {'✅ Lipinski compliant' if props.get('hbd', 10) <= 5 else '⚠️ Lipinski violation'} |
| H-Bond Acceptors | {props.get('hba', 'N/A')} | {'✅ Lipinski compliant' if props.get('hba', 20) <= 10 else '⚠️ Lipinski violation'} |

"""

        # BCS分类与制剂挑战
        report += f"""
---

## 2. Biopharmaceutics Classification

**Classification:** {self.report_data['bcs_classification'] or 'Pending analysis'}

"""

        # 推荐策略
        if self.report_data['recommended_strategies']:
            report += """
---

## 3. Recommended Formulation Strategies

"""
            for i, strategy in enumerate(self.report_data['recommended_strategies'], 1):
                report += f"{i}. **{strategy}**\n"

        # 实验建议
        if self.report_data['experimental_suggestions']:
            report += """
---

## 4. Experimental Suggestions

"""
            for i, suggestion in enumerate(self.report_data['experimental_suggestions'], 1):
                report += f"{i}. {suggestion}\n"

        # 文献引用
        if self.report_data['literature_references']:
            report += """
---

## 5. Literature References

"""
            for i, ref in enumerate(self.report_data['literature_references'], 1):
                report += f"{i}. {ref.get('authors_full', 'Unknown')}. *{ref.get('title', 'No title')}*. "
                report += f"{ref.get('journal', 'Unknown')} ({ref.get('year', 'N/A')}). "
                report += f"PMID: [{ref.get('pmid', 'N/A')}](https://pubmed.ncbi.nlm.nih.gov/{ref.get('pmid')}/)\n\n"

        # 工具调用历史
        if self.report_data['tool_calls_history']:
            report += f"""
---

## 6. Analysis Tools Used

Total tool calls: {len(self.report_data['tool_calls_history'])}

"""
            for tc in self.report_data['tool_calls_history'][:5]:
                report += f"- {tc.get('name', 'Unknown tool')}\n"

        # 免责声明
        report += """
---

## Disclaimer

This report is generated by FormulationOS AI system and should be used as a starting point for
formulation development. All recommendations should be validated through experimental studies.

**Generated by:** FormulationOS v3.5 | Powered by GPT-4o + PubMed + ChEMBL
"""

        return report

    def save_report(self, output_path: str = None) -> str:
        """保存报告为Markdown文件"""
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            drug_name = self.report_data['drug_name'].replace(' ', '_')
            output_path = f"reports/{drug_name}_formulation_report_{timestamp}.md"

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        report_content = self.generate_markdown_report()

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        return output_path

    def export_data_json(self, output_path: str = None) -> str:
        """导出原始数据为JSON"""
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            drug_name = self.report_data['drug_name'].replace(' ', '_')
            output_path = f"reports/{drug_name}_data_{timestamp}.json"

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.report_data, f, indent=2, ensure_ascii=False)

        return output_path
