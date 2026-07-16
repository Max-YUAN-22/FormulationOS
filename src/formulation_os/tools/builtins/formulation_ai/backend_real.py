"""Real FormulationAI API adapter.

This adapter replaces the mock backend with actual API calls
to the real FormulationAI service.
"""

from __future__ import annotations

import os
from typing import Any

import httpx


def run(input_data: dict[str, Any]) -> dict[str, Any]:
    """Call real FormulationAI API.

    Args:
        input_data: Expected keys:
            - drug_name: str
            - target_dose_mg: float
            - dosage_form: str

    Returns:
        Formulation recommendation with excipients
    """
    # Get API endpoint from environment
    api_url = os.getenv(
        "FORMULATION_AI_API_URL",
        "https://api.formulation-ai.com/v1/formulate"
    )
    api_key = os.getenv("FORMULATION_AI_API_KEY")

    # If no API key, fall back to mock
    if not api_key:
        return _mock_fallback(input_data)

    # Prepare API request
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "drug_name": input_data.get("drug_name", ""),
        "target_dose_mg": input_data.get("target_dose_mg", 0),
        "dosage_form": input_data.get("dosage_form", "tablet"),
        "indication": input_data.get("indication")
    }

    try:
        # Make API call with timeout
        response = httpx.post(
            api_url,
            json=payload,
            headers=headers,
            timeout=30.0
        )
        response.raise_for_status()

        # Parse and return response
        result = response.json()

        # Ensure consistent output format
        return {
            "drug_name": result.get("drug_name", payload["drug_name"]),
            "dosage_form": result.get("dosage_form", payload["dosage_form"]),
            "excipients": result.get("excipients", []),
            "summary": result.get("summary", ""),
            "warnings": result.get("warnings", [])
        }

    except httpx.HTTPError as e:
        # API call failed, return error with mock fallback
        return _mock_fallback_with_error(input_data, str(e))
    except Exception as e:
        # Unexpected error
        return _mock_fallback_with_error(input_data, f"Unexpected error: {e}")


def _mock_fallback(input_data: dict[str, Any]) -> dict[str, Any]:
    """Fallback to mock when API is not configured."""
    from formulation_os.tools.builtins.formulation_ai import backend as mock_backend

    result = mock_backend.run(input_data)
    result["warnings"] = result.get("warnings", []) + [
        "⚠️ Using mock backend - set FORMULATION_AI_API_KEY to use real API"
    ]
    return result


def _mock_fallback_with_error(input_data: dict[str, Any], error: str) -> dict[str, Any]:
    """Fallback with error message."""
    from formulation_os.tools.builtins.formulation_ai import backend as mock_backend

    result = mock_backend.run(input_data)
    result["warnings"] = result.get("warnings", []) + [
        f"⚠️ API call failed: {error}",
        "⚠️ Falling back to mock backend"
    ]
    return result
