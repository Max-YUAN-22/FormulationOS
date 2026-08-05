"""
Populate FormulationOS Knowledge Base with Demo Data

This script pre-loads the knowledge base with example analyses
to make the demo more impressive for presentations.
"""

import sys
sys.path.insert(0, 'src')

from formulation_os.knowledge_base.database import KnowledgeBaseDB
import uuid
from datetime import datetime, timedelta

def populate_demo_data():
    """Fill knowledge base with demo analyses"""

    kb = KnowledgeBaseDB()

    print("=" * 80)
    print("Populating FormulationOS Demo Data")
    print("=" * 80)
    print()

    # Demo session
    demo_session_id = "demo_session_001"
    kb.create_session(demo_session_id)

    # ========================================================================
    # Case 1: Ibuprofen (BCS II, Classic solid dispersion case)
    # ========================================================================
    print("Adding Case 1: Ibuprofen...")

    kb.save_message(
        demo_session_id,
        "user",
        "帮我分析Ibuprofen的制剂挑战，推荐合适的增溶策略",
        None
    )

    ibuprofen_id = kb.save_drug_analysis(
        demo_session_id,
        "Ibuprofen",
        "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
        "Oral tablet"
    )

    # Save properties
    kb.save_property(ibuprofen_id, "molecular_weight", 206.28, 0.99, "RDKit")
    kb.save_property(ibuprofen_id, "logP", 3.5, 0.95, "PreformulationAI")
    kb.save_property(ibuprofen_id, "logS", -3.97, 0.90, "PreformulationAI")
    kb.save_property(ibuprofen_id, "BCS_class", "II", 0.95, "Literature")
    kb.save_property(ibuprofen_id, "dose", 400, 1.0, "DrugBank")

    # Save formulation strategy
    kb.save_formulation_strategy(
        ibuprofen_id,
        "Solid Dispersion",
        {
            "feasibility_score": 0.77,
            "recommended_polymer": "HPMC-AS",
            "process": "Spray drying",
            "challenges": ["Physical stability", "Polymer selection"]
        },
        "推荐固体分散体技术。Ibuprofen为BCS II类药物，溶出度限制吸收。通过与HPMC-AS形成固体分散体可提高溶解度。"
    )

    # Save hypothesis
    kb.save_hypothesis(
        ibuprofen_id,
        "Ibuprofen固体分散体制剂可显著提高溶出速率，改善生物利用度",
        [
            "BCS II类药物，溶出度为限速步骤",
            "MW=206 Da适合聚合物分散",
            "LogP=3.5显示中等亲脂性，适合无定形化",
            "文献证实固体分散体有效性"
        ],
        0.85
    )

    kb.save_message(
        demo_session_id,
        "assistant",
        """# Ibuprofen制剂分析报告

## 药物基本信息
- **分子量**: 206.28 Da
- **LogP**: 3.5 (中等亲脂性)
- **LogS**: -3.97 (溶解度差)
- **BCS分类**: II类 (低溶解度，高渗透性)

## 制剂挑战
主要挑战是**溶解度差**导致的溶出限制。虽然渗透性良好，但药物在胃肠道的溶出速率成为吸收的限速步骤。

## 推荐策略：固体分散体

**选择理由:**
1. ✅ BCS II类药物的经典策略
2. ✅ MW=206 Da适合聚合物基质
3. ✅ 无定形化可显著提高溶解度
4. ✅ 文献证实临床有效性

**辅料选择:**
- **HPMC-AS**: 沉淀抑制剂，维持过饱和状态
- **PVP-VA**: 无定形稳定剂

**工艺选项:**
- 喷雾干燥（推荐）
- 热熔挤出

**验证计划:**
1. 固态表征 (DSC, XRPD, FTIR)
2. 溶出度测试 (pH 1.2, 4.5, 6.8)
3. 稳定性研究 (40°C/75% RH, 6个月)

**置信度**: 85%""",
        "gpt-4o"
    )

    # ========================================================================
    # Case 2: Paclitaxel (BCS IV, High MW)
    # ========================================================================
    print("Adding Case 2: Paclitaxel...")

    kb.save_message(
        demo_session_id,
        "user",
        "Paclitaxel的溶解度极差，有什么好的制剂方案？",
        None
    )

    paclitaxel_id = kb.save_drug_analysis(
        demo_session_id,
        "Paclitaxel",
        "CC1=C2[C@@]([C@]([C@H]([C@@H]3[C@]4([C@H](OC4)C[C@@H]([C@]3(C(=O)[C@@H]2OC(=O)C)C)O)OC(=O)C)OC(=O)c5ccccc5)(C[C@@H]1OC(=O)[C@H](O)[C@@H](NC(=O)c6ccccc6)c7ccccc7)O)(C)C",
        "Injectable"
    )

    kb.save_property(paclitaxel_id, "molecular_weight", 853.91, 0.99, "RDKit")
    kb.save_property(paclitaxel_id, "logP", 3.0, 0.90, "PreformulationAI")
    kb.save_property(paclitaxel_id, "logS", -6.5, 0.85, "PreformulationAI")
    kb.save_property(paclitaxel_id, "BCS_class", "IV", 0.90, "Literature")

    kb.save_formulation_strategy(
        paclitaxel_id,
        "Nanocrystal",
        {
            "feasibility_score": 0.82,
            "particle_size_target": "200-500 nm",
            "stabilizer": "Poloxamer 188",
            "advantages": ["Minimal carrier", "High drug loading", "IV compatible"]
        },
        "推荐纳米晶体技术。Paclitaxel高MW限制了环糊精和聚合物策略，粒径减小是最有效的方法。"
    )

    kb.save_hypothesis(
        paclitaxel_id,
        "Paclitaxel纳米晶体制剂可显著提高溶出速率，同时避免高MW带来的载体限制",
        [
            "MW=854 Da超过环糊精空腔容量",
            "BCS IV类，溶解度和渗透性双重挑战",
            "纳米粒径减小有效提高溶出",
            "Abraxane临床成功先例"
        ],
        0.82
    )

    kb.save_message(
        demo_session_id,
        "assistant",
        """# Paclitaxel制剂分析

## 关键挑战
- **极差溶解度**: LogS=-6.5
- **高分子量**: 853.91 Da (限制载体选择)
- **BCS IV类**: 溶解度+渗透性双重问题

## 推荐：纳米晶体技术

**为什么不用环糊精？**
❌ MW=854 Da远超β-环糊精空腔容量（~400 Da）

**为什么不用固体分散体？**
❌ 高MW药物在聚合物中分散困难，药物载量低

**纳米晶体优势：**
✅ 不依赖载体，药物载量高
✅ 粒径减小直接提高溶出
✅ 临床验证：Abraxane (白蛋白纳米粒)

**制备参数:**
- 目标粒径: 200-500 nm
- 稳定剂: Poloxamer 188
- 工艺: 湿法研磨或高压均质

**置信度**: 82%""",
        "gpt-4o"
    )

    # ========================================================================
    # Case 3: Celecoxib (BCS II, moderate dose)
    # ========================================================================
    print("Adding Case 3: Celecoxib...")

    celecoxib_id = kb.save_drug_analysis(
        demo_session_id,
        "Celecoxib",
        "Cc1ccc(cc1)c2cc(nn2c3ccc(cc3)S(=O)(=O)N)C(F)(F)F",
        "Oral capsule"
    )

    kb.save_property(celecoxib_id, "molecular_weight", 381.37, 0.99, "RDKit")
    kb.save_property(celecoxib_id, "logP", 3.5, 0.92, "PreformulationAI")
    kb.save_property(celecoxib_id, "logS", -4.3, 0.88, "PreformulationAI")
    kb.save_property(celecoxib_id, "BCS_class", "II", 0.95, "Literature")
    kb.save_property(celecoxib_id, "dose", 200, 1.0, "DrugBank")

    kb.save_formulation_strategy(
        celecoxib_id,
        "Solid Dispersion",
        {
            "feasibility_score": 0.80,
            "recommended_polymer": "PVP K30",
            "drug_polymer_ratio": "1:3",
            "process": "Spray drying"
        },
        "Celecoxib固体分散体技术成熟，临床已有成功产品（Celebrex）。"
    )

    # ========================================================================
    # Case 4: Aspirin (BCS I, control case)
    # ========================================================================
    print("Adding Case 4: Aspirin (Control)...")

    aspirin_id = kb.save_drug_analysis(
        demo_session_id,
        "Aspirin",
        "CC(=O)Oc1ccccc1C(=O)O",
        "Oral tablet"
    )

    kb.save_property(aspirin_id, "molecular_weight", 180.16, 0.99, "RDKit")
    kb.save_property(aspirin_id, "logP", 1.19, 0.95, "PreformulationAI")
    kb.save_property(aspirin_id, "BCS_class", "I", 0.98, "Literature")

    kb.save_formulation_strategy(
        aspirin_id,
        "Conventional",
        {
            "feasibility_score": 0.95,
            "complexity": "Low",
            "note": "No advanced formulation needed"
        },
        "Aspirin为BCS I类药物，溶解度和渗透性均良好，常规片剂即可满足要求。"
    )

    # Get statistics
    print()
    print("=" * 80)
    print("Demo Data Population Complete")
    print("=" * 80)
    stats = kb.get_statistics()
    print(f"Total sessions: {stats['total_sessions']}")
    print(f"Total analyses: {stats['total_drug_analyses']}")
    print(f"Unique drugs: {stats['unique_drugs']}")
    print(f"Total messages: {stats['total_messages']}")
    print()
    print("✅ Knowledge Base is now populated with demo cases!")
    print("🌐 Start Streamlit: streamlit run FormulationOS_Enterprise.py")

    kb.close()


if __name__ == "__main__":
    populate_demo_data()
