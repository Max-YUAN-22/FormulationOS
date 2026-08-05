"""
Pharma Knowledge MCP Layer

Provides knowledge-grounded context for FormulationOS scientific reasoning.

Components:
- Drug Knowledge MCP: External drug databases (PubChem, ChEMBL, DrugBank)
- Formulation Knowledge Graph: Drug property → Challenge → Strategy → Excipient
- Literature Evidence MCP: PubMed/Semantic Scholar integration
- Excipient Knowledge Base: Curated excipient database with compatibility rules
"""

from .drug_knowledge_mcp import DrugKnowledgeMCP

__all__ = ["DrugKnowledgeMCP"]
