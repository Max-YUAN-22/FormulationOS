"""Knowledge Base Visualization Component for FormulationOS

Displays literature citations, drug database queries, and knowledge sources
to make the knowledge base more visible and impressive in conversations.
"""

import streamlit as st
from typing import Dict, Any, List, Optional


def display_literature_search_results(papers: List[Dict], query: str):
    """Display PubMed literature search results with expandable cards.

    Args:
        papers: List of paper dictionaries from PubMedSearchEngine
        query: Original search query
    """
    if not papers:
        return

    st.markdown("---")
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1rem 1.5rem; border-radius: 8px; margin: 1rem 0;'>
        <div style='display: flex; align-items: center; gap: 0.75rem;'>
            <span style='font-size: 1.5rem;'>📚</span>
            <div>
                <div style='color: white; font-weight: 600; font-size: 1.1rem;'>
                    Literature Evidence Found
                </div>
                <div style='color: rgba(255,255,255,0.9); font-size: 0.9rem;'>
                    {len(papers)} relevant papers from PubMed
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    for i, paper in enumerate(papers, 1):
        with st.expander(f"📄 [{i}] {paper.get('title', 'Untitled')}", expanded=(i == 1)):
            # Authors and Journal
            st.markdown(f"**Authors:** {paper.get('authors_full', 'N/A')}")
            st.markdown(f"**Journal:** {paper.get('journal', 'N/A')} ({paper.get('year', 'N/A')})")

            # PMID and link
            pmid = paper.get('pmid', '')
            pubmed_url = paper.get('pubmed_url', f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/")
            st.markdown(f"**PMID:** [{pmid}]({pubmed_url})")

            # Abstract
            abstract = paper.get('abstract', 'No abstract available')
            if abstract and len(abstract) > 100:
                st.markdown("**Abstract:**")
                st.markdown(f"<div style='background: #f8f9fa; padding: 1rem; border-radius: 4px; font-size: 0.9rem; line-height: 1.6;'>{abstract}</div>", unsafe_allow_html=True)

            # Relevance indicator
            st.markdown("🎯 **Relevance:** High (selected from top search results)")


def display_drug_database_query(drug_name: str, drug_data: Dict):
    """Display drug database query results with property panel.

    Args:
        drug_name: Name of the drug
        drug_data: Dictionary with drug properties from DrugSearchEngine or ChEMBL
    """
    if not drug_data:
        return

    source = drug_data.get('source', 'Database')
    source_colors = {
        'PubChem': {'bg': '#e0f2fe', 'border': '#0ea5e9', 'icon': '🧪'},
        'ChEMBL': {'bg': '#fef3c7', 'border': '#f59e0b', 'icon': '💊'},
        'Cache': {'bg': '#f3e8ff', 'border': '#a855f7', 'icon': '⚡'}
    }

    colors = source_colors.get(source, {'bg': '#f8f9fa', 'border': '#6b7280', 'icon': '📊'})

    st.markdown("---")
    st.markdown(f"""
    <div style='background: {colors['bg']}; border-left: 4px solid {colors['border']};
                padding: 1rem 1.5rem; border-radius: 8px; margin: 1rem 0;'>
        <div style='display: flex; align-items: center; gap: 0.75rem;'>
            <span style='font-size: 1.5rem;'>{colors['icon']}</span>
            <div>
                <div style='font-weight: 600; font-size: 1.1rem;'>
                    Drug Database Query: {drug_name}
                </div>
                <div style='color: #6b7280; font-size: 0.85rem;'>
                    Source: {source}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Display properties in a clean grid
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Molecular Weight", f"{drug_data.get('molecular_weight', 'N/A'):.2f}" if isinstance(drug_data.get('molecular_weight'), (int, float)) else "N/A")
        st.metric("H-Bond Donors", drug_data.get('hbd', drug_data.get('HBondDonorCount', 'N/A')))

    with col2:
        st.metric("LogP", f"{drug_data.get('logp', drug_data.get('XLogP', 'N/A')):.2f}" if isinstance(drug_data.get('logp') or drug_data.get('XLogP'), (int, float)) else "N/A")
        st.metric("H-Bond Acceptors", drug_data.get('hba', drug_data.get('HBondAcceptorCount', 'N/A')))

    with col3:
        st.metric("TPSA (Ų)", f"{drug_data.get('tpsa', drug_data.get('TPSA', 'N/A')):.2f}" if isinstance(drug_data.get('tpsa') or drug_data.get('TPSA'), (int, float)) else "N/A")
        bcs_class = drug_data.get('bcs_class', 'Calculating...')
        st.metric("BCS Class", bcs_class)

    # SMILES if available
    smiles = drug_data.get('smiles', drug_data.get('CanonicalSMILES'))
    if smiles:
        with st.expander("🔬 SMILES Structure"):
            st.code(smiles, language=None)


def display_knowledge_source_badge(sources: List[str]):
    """Display badges showing which knowledge sources were consulted.

    Args:
        sources: List of source names (e.g., ['PubMed', 'ChEMBL', 'PubChem'])
    """
    if not sources:
        return

    source_icons = {
        'PubMed': '📚',
        'ChEMBL': '💊',
        'PubChem': '🧪',
        'DrugBank': '🏥',
        'Cache': '⚡'
    }

    badges_html = ""
    for source in sources:
        icon = source_icons.get(source, '📊')
        badges_html += f"""
        <span style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                     color: white; padding: 0.25rem 0.75rem; border-radius: 12px;
                     font-size: 0.85rem; margin-right: 0.5rem; display: inline-block;'>
            {icon} {source}
        </span>
        """

    st.markdown(f"""
    <div style='margin: 0.5rem 0;'>
        <div style='color: #6b7280; font-size: 0.85rem; margin-bottom: 0.25rem;'>
            Knowledge Sources Consulted:
        </div>
        {badges_html}
    </div>
    """, unsafe_allow_html=True)


def display_citation_summary(total_papers: int, total_drugs: int):
    """Display a summary of knowledge base usage in the current conversation.

    Args:
        total_papers: Total number of papers cited
        total_drugs: Total number of drug database queries
    """
    if total_papers == 0 and total_drugs == 0:
        return

    st.markdown("---")
    st.markdown("""
    <div style='background: #f8f9fa; border-radius: 8px; padding: 1rem; margin: 1rem 0;'>
        <div style='font-weight: 600; margin-bottom: 0.5rem; color: #374151;'>
            📖 Knowledge Base Summary
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("📚 Papers Cited", total_papers)
    with col2:
        st.metric("💊 Drug Queries", total_drugs)

    st.markdown("</div>", unsafe_allow_html=True)


def display_knowledge_search_status(searching: bool, query: str = ""):
    """Display a loading status when searching knowledge bases.

    Args:
        searching: Whether a search is in progress
        query: Search query being executed
    """
    if not searching:
        return

    st.markdown(f"""
    <div style='background: #eff6ff; border-left: 4px solid #3b82f6;
                padding: 1rem 1.5rem; border-radius: 8px; margin: 1rem 0;'>
        <div style='display: flex; align-items: center; gap: 0.75rem;'>
            <div class='spinner'></div>
            <div>
                <div style='font-weight: 600; color: #1e40af;'>
                    🔍 Searching Knowledge Base...
                </div>
                <div style='color: #6b7280; font-size: 0.9rem;'>
                    {query if query else "Querying PubMed, ChEMBL, and PubChem"}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
