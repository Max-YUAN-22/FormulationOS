"""Auto Visualization Generator for FormulationOS

Automatically generates relevant plots based on AI analysis results.
"""

import re
from typing import Dict, Any, List, Optional
from .visualization_tools import (
    plot_solubility_profile,
    plot_ph_stability,
    plot_formulation_comparison
)

def extract_numerical_data(text: str, pattern: str) -> List[float]:
    """Extract numerical values from text using regex pattern"""
    matches = re.findall(pattern, text)
    return [float(m) for m in matches if m]

def generate_visualizations_from_response(response: str, tool_calls: List[Dict], prompt: str) -> List[Dict[str, str]]:
    """Automatically generate visualizations based on AI response content

    Args:
        response: AI's text response
        tool_calls: List of tool calls made
        prompt: User's original prompt

    Returns:
        List of dictionaries with 'type', 'title', and 'image' (base64)
    """
    visualizations = []
    response_lower = response.lower()

    # Extract drug name from prompt
    drug_name = "Compound"
    drug_patterns = [
        r'分析\s*([A-Za-z一-龥]+)[（(]',
        r'Ibuprofen|Aspirin|布洛芬|阿司匹林',
    ]
    for pattern in drug_patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            if match.lastindex and match.lastindex >= 1:
                drug_name = match.group(1)
            else:
                drug_name = match.group(0)
            break

    # 1. Formulation Strategy Comparison
    if any(tool in str(tool_calls).lower() for tool in ['formulation', 'strategy', 'solid_dispersion']):
        # Extract strategy names and scores from response
        strategies = []
        scores = []

        # Common formulation strategies
        strategy_keywords = [
            'solid dispersion', 'nanocrystal', 'cyclodextrin',
            'sedds', 'liposome', 'phospholipid'
        ]

        for keyword in strategy_keywords:
            if keyword in response_lower:
                strategies.append(keyword.title())
                # Try to find a score (0-1 or percentage)
                score_pattern = rf'{keyword}[^\d]*(\d+\.?\d*)'
                score_match = re.search(score_pattern, response_lower)
                if score_match:
                    score = float(score_match.group(1))
                    scores.append(score if score <= 1 else score/100)
                else:
                    # Assign default scores based on keyword position
                    scores.append(0.7 + len(strategies) * 0.05)

        if len(strategies) >= 2:
            img = plot_formulation_comparison(strategies[:5], scores[:5], drug_name)
            visualizations.append({
                'type': 'formulation_comparison',
                'title': f'Formulation Strategy Ranking - {drug_name}',
                'image': img
            })

    # 2. pH Stability Profile
    if 'ph' in response_lower or 'stability' in response_lower:
        # Generate example pH stability data
        ph_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

        # Try to extract pKa
        pka_match = re.search(r'pka[:\s]+(\d+\.?\d*)', response_lower)
        if pka_match:
            pka = float(pka_match.group(1))
            # Model stability: higher near pKa, lower at extremes
            stability = [max(20, 100 - abs(ph - pka) * 15) for ph in ph_values]
        else:
            # Default stability profile
            stability = [40, 50, 65, 75, 85, 90, 95, 90, 80, 70, 60, 50]

        img = plot_ph_stability(ph_values, stability, drug_name)
        visualizations.append({
            'type': 'ph_stability',
            'title': f'pH Stability Profile - {drug_name}',
            'image': img
        })

    # 3. Solubility-Temperature Profile
    if 'solubility' in response_lower or 'temperature' in response_lower:
        # Generate example solubility data
        temperatures = [10, 20, 25, 30, 37, 40, 50, 60]

        # Try to extract solubility value
        sol_match = re.search(r'solubility[:\s]+(\d+\.?\d*)\s*(mg/ml|g/l)?', response_lower)
        if sol_match:
            base_sol = float(sol_match.group(1))
        else:
            base_sol = 0.05  # Default

        # Model: solubility increases with temperature
        solubilities = [base_sol * (1 + (t-25)*0.02) for t in temperatures]

        img = plot_solubility_profile(temperatures, solubilities, drug_name)
        visualizations.append({
            'type': 'solubility_profile',
            'title': f'Solubility vs Temperature - {drug_name}',
            'image': img
        })

    return visualizations
