"""Visualization Tools for FormulationOS

Provides plotting and molecular visualization capabilities.
"""

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for Streamlit
import numpy as np
from io import BytesIO
import base64

def plot_solubility_profile(temperatures, solubilities, drug_name="Compound"):
    """Plot solubility vs temperature

    Args:
        temperatures: List of temperatures (°C)
        solubilities: List of solubility values (mg/mL)
        drug_name: Name of the drug

    Returns:
        Base64 encoded image string
    """
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(temperatures, solubilities, 'o-', linewidth=2, markersize=8, color='#3b82f6')
    ax.set_xlabel('Temperature (°C)', fontsize=12)
    ax.set_ylabel('Solubility (mg/mL)', fontsize=12)
    ax.set_title(f'Solubility Profile - {drug_name}', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)

    return img_base64

def plot_ph_stability(ph_values, stability_scores, drug_name="Compound"):
    """Plot pH-dependent stability

    Args:
        ph_values: List of pH values
        stability_scores: List of stability scores (0-100)
        drug_name: Name of the drug

    Returns:
        Base64 encoded image string
    """
    fig, ax = plt.subplots(figsize=(8, 5))

    # Color gradient based on stability
    colors = ['#ef4444' if s < 50 else '#fbbf24' if s < 80 else '#10b981'
              for s in stability_scores]

    ax.bar(ph_values, stability_scores, color=colors, alpha=0.7, edgecolor='black')
    ax.set_xlabel('pH', fontsize=12)
    ax.set_ylabel('Stability Score', fontsize=12)
    ax.set_title(f'pH Stability Profile - {drug_name}', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 100)
    ax.axhline(y=80, color='green', linestyle='--', alpha=0.5, label='Good Stability')
    ax.axhline(y=50, color='orange', linestyle='--', alpha=0.5, label='Moderate Stability')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)

    return img_base64

def plot_formulation_comparison(strategies, scores, drug_name="Compound"):
    """Plot formulation strategy comparison

    Args:
        strategies: List of strategy names
        scores: List of prediction scores
        drug_name: Name of the drug

    Returns:
        Base64 encoded image string
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    y_pos = np.arange(len(strategies))
    colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(strategies)))

    bars = ax.barh(y_pos, scores, color=colors, edgecolor='black', linewidth=1.5)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(strategies)
    ax.set_xlabel('Prediction Score', fontsize=12)
    ax.set_title(f'Formulation Strategy Ranking - {drug_name}', fontsize=14, fontweight='bold')
    ax.set_xlim(0, max(scores) * 1.1)

    # Add value labels
    for i, (bar, score) in enumerate(zip(bars, scores)):
        ax.text(score + 0.02, i, f'{score:.2f}', va='center', fontsize=10, fontweight='bold')

    ax.grid(True, alpha=0.3, axis='x')

    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)

    return img_base64

def visualize_molecule_2d(smiles):
    """Visualize molecular structure from SMILES

    Args:
        smiles: SMILES string

    Returns:
        Base64 encoded image string or None if RDKit not available
    """
    try:
        from rdkit import Chem
        from rdkit.Chem import Draw

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None

        img = Draw.MolToImage(mol, size=(400, 400))

        buf = BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode()

        return img_base64
    except ImportError:
        return None
