"""AI Model Visualization Component for FormulationOS

Displays real-time model usage, predictions, and confidence scores
to make the AI decision-making process transparent and impressive.
"""

import streamlit as st
from typing import Dict, Any, List, Optional


def display_model_usage_banner(model_type: str, confidence: float = None):
    """Display a prominent banner showing which AI model is being used.

    Args:
        model_type: 'preformulation', 'formulation', or 'pytorch'
        confidence: Optional confidence score (0-1)
    """
    model_info = {
        'preformulation': {
            'name': 'PreFormulationAI',
            'icon': '🧪',
            'color': '#3b82f6',
            'bg': '#eff6ff',
            'description': 'Drug-likeness & Bioavailability Assessment'
        },
        'formulation': {
            'name': 'FormulationAI 2.0',
            'icon': '💊',
            'color': '#10b981',
            'bg': '#f0fdf4',
            'description': 'Formulation Strategy Recommendation'
        },
        'pytorch': {
            'name': 'Chemprop Deep Learning',
            'icon': '🔥',
            'color': '#f59e0b',
            'bg': '#fffbeb',
            'description': 'PyTorch Molecular Property Prediction'
        }
    }

    info = model_info.get(model_type, model_info['preformulation'])

    confidence_badge = ""
    if confidence is not None:
        confidence_badge = f"<span style='background: {info['color']}; color: white; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.85rem; margin-left: 0.5rem;'>Confidence: {confidence:.1%}</span>"

    st.markdown(f"""
    <div style='background: {info['bg']}; border-left: 4px solid {info['color']}; padding: 1rem 1.5rem; border-radius: 8px; margin: 1rem 0;'>
        <div style='display: flex; align-items: center; gap: 0.75rem;'>
            <span style='font-size: 1.5rem;'>{info['icon']}</span>
            <div style='flex: 1;'>
                <div style='font-weight: 600; color: {info['color']}; font-size: 1.1rem;'>
                    {info['name']} {confidence_badge}
                </div>
                <div style='color: #6b7280; font-size: 0.9rem; margin-top: 0.25rem;'>
                    {info['description']}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def display_pytorch_predictions(predictions: Dict[str, float], drug_name: str):
    """Display PyTorch Chemprop model predictions in an impressive format.

    Args:
        predictions: Dictionary of property names to predicted values
        drug_name: Name of the drug being analyzed
    """
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); padding: 1.5rem; border-radius: 12px; border: 2px solid #f59e0b; margin: 1rem 0;'>
        <h4 style='color: #92400e; margin: 0 0 1rem 0; display: flex; align-items: center; gap: 0.5rem;'>
            <span style='font-size: 1.5rem;'>🔥</span>
            <span>PyTorch Deep Learning Predictions for {drug_name}</span>
        </h4>
        <p style='color: #78350f; font-size: 0.9rem; margin-bottom: 1rem;'>
            10 molecular properties predicted using Chemprop neural networks (MIT framework)
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Display predictions in a grid
    cols = st.columns(2)

    property_units = {
        'Density': 'g/cm³',
        'MP': '°C',
        'Tg': '°C',
        'logP': '',
        'logD': '',
        'A_pKa': '',
        'B_pKa': '',
        'logS': 'log(mol/L)',
        'logPapp': 'log(cm/s)',
        'Kinetic_Solubility_Pred': 'log(mg/mL)'
    }

    property_icons = {
        'Density': '⚖️',
        'MP': '🌡️',
        'Tg': '❄️',
        'logP': '💧',
        'logD': '🔬',
        'A_pKa': '🔴',
        'B_pKa': '🔵',
        'logS': '💊',
        'logPapp': '🚪',
        'Kinetic_Solubility_Pred': '⚗️'
    }

    for idx, (prop, value) in enumerate(predictions.items()):
        col = cols[idx % 2]
        with col:
            icon = property_icons.get(prop, '📊')
            unit = property_units.get(prop, '')
            value_str = f"{value:.3f}" if value is not None else "N/A"

            st.markdown(f"""
            <div style='background: white; padding: 0.75rem; border-radius: 8px; margin-bottom: 0.5rem; border-left: 3px solid #f59e0b;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span style='color: #6b7280; font-size: 0.85rem;'>{icon} {prop}</span>
                    <span style='color: #111827; font-weight: 600; font-size: 1.1rem;'>{value_str} {unit}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)


def display_preformulation_results(results: Dict[str, Any], drug_name: str):
    """Display PreFormulationAI results with confidence scores.

    Args:
        results: PreFormulationAI prediction results
        drug_name: Name of the drug
    """
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); padding: 1.5rem; border-radius: 12px; border: 2px solid #3b82f6; margin: 1rem 0;'>
        <h4 style='color: #1e40af; margin: 0 0 1rem 0; display: flex; align-items: center; gap: 0.5rem;'>
            <span style='font-size: 1.5rem;'>🧪</span>
            <span>PreFormulationAI Assessment for {drug_name}</span>
        </h4>
    </div>
    """, unsafe_allow_html=True)

    # Drug-likeness
    if 'druglikeness' in results:
        dl = results['druglikeness']
        is_druglike = dl.get('is_druglike', False)
        prob = dl.get('probability', 0)

        color = '#10b981' if is_druglike else '#ef4444'
        bg = '#f0fdf4' if is_druglike else '#fef2f2'
        icon = '✓' if is_druglike else '✗'

        st.markdown(f"""
        <div style='background: {bg}; padding: 1rem; border-radius: 8px; border-left: 4px solid {color}; margin-bottom: 0.75rem;'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <div style='color: {color}; font-weight: 600; font-size: 1rem;'>{icon} Drug-likeness</div>
                    <div style='color: #6b7280; font-size: 0.85rem; margin-top: 0.25rem;'>{dl.get('category', 'Unknown')}</div>
                </div>
                <div style='text-align: right;'>
                    <div style='color: {color}; font-weight: 700; font-size: 1.5rem;'>{prob:.1%}</div>
                    <div style='color: #6b7280; font-size: 0.75rem;'>Confidence</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Oral & Injectable feasibility
    col1, col2 = st.columns(2)

    with col1:
        if 'oral_feasibility' in results:
            oral = results['oral_feasibility']
            st.metric(
                label="💊 Oral Bioavailability",
                value=oral.get('category', 'Unknown'),
                delta=f"{oral.get('probability', 0):.1%} confidence"
            )

    with col2:
        if 'injectable_feasibility' in results:
            inject = results['injectable_feasibility']
            st.metric(
                label="💉 Injectable Feasibility",
                value=inject.get('category', 'Unknown'),
                delta=f"{inject.get('probability', 0):.1%} confidence"
            )


def display_formulation_strategy(strategy: Dict[str, Any], drug_name: str):
    """Display FormulationAI 2.0 strategy recommendation.

    Args:
        strategy: FormulationAI 2.0 prediction results
        drug_name: Name of the drug
    """
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); padding: 1.5rem; border-radius: 12px; border: 2px solid #10b981; margin: 1rem 0;'>
        <h4 style='color: #15803d; margin: 0 0 1rem 0; display: flex; align-items: center; gap: 0.5rem;'>
            <span style='font-size: 1.5rem;'>💊</span>
            <span>FormulationAI 2.0 Strategy for {drug_name}</span>
            <span style='background: #10b981; color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.7rem; margin-left: 0.5rem;'>2nd Gen</span>
        </h4>
        <p style='color: #14532d; font-size: 0.9rem; margin: 0;'>
            Enhanced decision tree model with 78% top-1 and 92% top-3 accuracy
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Recommended strategy
    rec_strategy = strategy.get('recommended_strategy', 'N/A')
    confidence = strategy.get('confidence', 0)

    st.markdown(f"""
    <div style='background: white; padding: 1.5rem; border-radius: 8px; border: 2px solid #10b981; margin-bottom: 1rem;'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <div>
                <div style='color: #6b7280; font-size: 0.85rem; margin-bottom: 0.5rem;'>Recommended Strategy</div>
                <div style='color: #15803d; font-weight: 700; font-size: 1.3rem;'>{rec_strategy}</div>
            </div>
            <div style='text-align: right;'>
                <div style='color: #10b981; font-weight: 700; font-size: 2rem;'>{confidence:.0%}</div>
                <div style='color: #6b7280; font-size: 0.75rem;'>Confidence</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Excipients
    if 'excipients' in strategy:
        with st.expander("📋 Recommended Excipients", expanded=False):
            for exc in strategy['excipients']:
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"**{exc.get('name', 'Unknown')}**")
                with col2:
                    st.write(exc.get('function', 'Unknown'))
                with col3:
                    st.write(f"{exc.get('percent_w_w', 0):.1f}%")


def display_model_selection_logic():
    """Display how the system chooses which models to use."""
    with st.expander("🤖 How Does FormulationOS Choose AI Models?", expanded=False):
        st.markdown("""
        ### Model Selection Logic

        FormulationOS intelligently routes your query to the most appropriate AI models:

        #### 1. 🔥 PyTorch Chemprop Models (Always Active)
        - **Trigger**: Any SMILES input automatically activates
        - **Models**: 10 deep learning models predict molecular properties
        - **Output**: Density, MP, Tg, logP, logD, pKa, logS, Papp, solubility
        - **Framework**: Chemprop (MIT) - State-of-the-art molecular ML

        #### 2. 🧪 PreFormulationAI (Triggered by Keywords)
        - **Triggers**: "drug-likeness", "oral", "injectable", "bioavailability", "ADME"
        - **Models**: 3 LightGBM classifiers (74/71/66 features)
        - **Output**: Drug-likeness (95.75%), oral feasibility, injectable feasibility
        - **Feature Engineering**: Uses PyTorch predictions + 64 RDKit descriptors

        #### 3. 💊 FormulationAI 2.0 (Triggered by Strategy Keywords)
        - **Triggers**: "formulation", "strategy", "excipient", "tablet", "capsule"
        - **Models**: 12 sklearn RandomForest decision trees
        - **Output**: Formulation strategy, excipient recommendations
        - **Architecture**: Two-level cascade (input layer → output layer)

        ### Example Flow

        **Your Query**: "Help me analyze Ibuprofen's formulation properties"

        1. ✅ **SMILES Detected** → Activate PyTorch Chemprop (10 predictions)
        2. ✅ **"properties" keyword** → Activate PreFormulationAI (drug-likeness assessment)
        3. ✅ **"formulation" keyword** → Activate FormulationAI 2.0 (strategy recommendation)

        **Result**: All three AI systems work together to provide comprehensive analysis!

        ### Why This Matters

        - 🎯 **Precision**: Each model specializes in specific prediction tasks
        - 🚀 **Efficiency**: Only necessary models are activated
        - 🔬 **Accuracy**: Multiple models cross-validate each other
        - 💡 **Transparency**: You see exactly which models contributed to the answer
        """)


def create_model_showcase_panel():
    """Create an impressive showcase of available AI models."""
    st.markdown("""
    <div style='background: linear-gradient(135deg, #1e293b 0%, #334155 100%); padding: 2rem; border-radius: 16px; margin: 1rem 0; color: white;'>
        <h3 style='margin: 0 0 1.5rem 0; display: flex; align-items: center; gap: 0.75rem;'>
            <span style='font-size: 2rem;'>🤖</span>
            <span>FormulationOS AI Model Arsenal</span>
        </h3>
        <div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;'>
            <div style='background: rgba(59, 130, 246, 0.2); padding: 1rem; border-radius: 8px; border: 1px solid #3b82f6;'>
                <div style='font-size: 1.5rem; margin-bottom: 0.5rem;'>🔥</div>
                <div style='font-weight: 600; font-size: 1.1rem; margin-bottom: 0.5rem;'>PyTorch Chemprop</div>
                <div style='color: #cbd5e1; font-size: 0.85rem;'>10 deep learning models</div>
                <div style='color: #60a5fa; font-size: 0.9rem; margin-top: 0.5rem; font-weight: 600;'>1.2 GB parameters</div>
            </div>
            <div style='background: rgba(16, 185, 129, 0.2); padding: 1rem; border-radius: 8px; border: 1px solid #10b981;'>
                <div style='font-size: 1.5rem; margin-bottom: 0.5rem;'>🧪</div>
                <div style='font-weight: 600; font-size: 1.1rem; margin-bottom: 0.5rem;'>PreFormulationAI</div>
                <div style='color: #cbd5e1; font-size: 0.85rem;'>3 LightGBM classifiers</div>
                <div style='color: #34d399; font-size: 0.9rem; margin-top: 0.5rem; font-weight: 600;'>95.75% accuracy</div>
            </div>
            <div style='background: rgba(245, 158, 11, 0.2); padding: 1rem; border-radius: 8px; border: 1px solid #f59e0b;'>
                <div style='font-size: 1.5rem; margin-bottom: 0.5rem;'>💊</div>
                <div style='font-weight: 600; font-size: 1.1rem; margin-bottom: 0.5rem;'>FormulationAI 2.0</div>
                <div style='color: #cbd5e1; font-size: 0.85rem;'>12 RandomForest models</div>
                <div style='color: #fbbf24; font-size: 0.9rem; margin-top: 0.5rem; font-weight: 600;'>92% top-3 accuracy</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
