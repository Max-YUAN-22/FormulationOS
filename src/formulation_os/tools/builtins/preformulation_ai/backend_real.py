"""Updated PreformulationAI adapter for real API integration.

Based on the actual project structure:
- FastAPI backend at /api/v1/tasks/create-and-submit
- Async task processing with task_code
- Requires authentication
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx


def run(input_data: dict[str, Any]) -> dict[str, Any]:
    """Call real PreformulationAI API using the actual task-based interface.

    Args:
        input_data: Expected keys:
            - drug_name: str
            - smiles: str (optional)

    Returns:
        Preformulation properties
    """
    # Get API configuration from environment
    base_url = os.getenv(
        "PREFORMULATION_AI_BASE_URL",
        "http://localhost:8000"  # Default to local deployment
    )
    api_token = os.getenv("PREFORMULATION_AI_TOKEN")

    # If no token, fall back to mock
    if not api_token:
        return _mock_fallback(input_data)

    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    # Step 1: Create and submit task
    create_url = f"{base_url}/api/v1/tasks/create-and-submit"

    task_payload = {
        "task_type": "preformulation_prediction",  # Actual task type may vary
        "user_inputs": {
            "drug_name": input_data.get("drug_name", ""),
            "smiles": input_data.get("smiles"),
        }
    }

    try:
        # Create task
        response = httpx.post(
            create_url,
            json=task_payload,
            headers=headers,
            timeout=30.0
        )
        response.raise_for_status()

        task_code = response.json().get("task_code")

        if not task_code:
            return _mock_fallback_with_error(input_data, "No task_code in response")

        # Step 2: Poll for results (simplified - real implementation should handle async better)
        result = _poll_task_result(base_url, task_code, headers, max_wait=60)

        if result:
            return _format_result(result, input_data)
        else:
            return _mock_fallback_with_error(input_data, "Task timeout or failed")

    except httpx.HTTPError as e:
        return _mock_fallback_with_error(input_data, f"HTTP error: {e}")
    except Exception as e:
        return _mock_fallback_with_error(input_data, f"Unexpected error: {e}")


def _poll_task_result(
    base_url: str,
    task_code: str,
    headers: dict[str, str],
    max_wait: int = 60,
    poll_interval: int = 2
) -> dict[str, Any] | None:
    """Poll for task result."""
    result_url = f"{base_url}/api/v1/tasks/{task_code}/result"

    elapsed = 0
    while elapsed < max_wait:
        try:
            response = httpx.get(result_url, headers=headers, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "completed":
                    return data.get("result")

            time.sleep(poll_interval)
            elapsed += poll_interval

        except Exception:
            time.sleep(poll_interval)
            elapsed += poll_interval

    return None


def _format_result(api_result: dict[str, Any], input_data: dict[str, Any]) -> dict[str, Any]:
    """Format API result to match expected output schema."""
    return {
        "drug_name": input_data.get("drug_name", ""),
        "bcs_class": api_result.get("bcs_class"),
        "log_p": api_result.get("log_p"),
        "solubility_mg_ml": api_result.get("solubility"),
        "permeability": api_result.get("permeability"),
        "stability_score": api_result.get("stability"),
        "summary": api_result.get("summary", ""),
        "warnings": api_result.get("warnings", [])
    }


def _mock_fallback(input_data: dict[str, Any]) -> dict[str, Any]:
    """Fallback to mock when API is not configured."""
    from formulation_os.tools.builtins.preformulation_ai import backend as mock_backend

    result = mock_backend.run(input_data)
    result["warnings"] = result.get("warnings", []) + [
        "⚠️ Using mock backend - set PREFORMULATION_AI_TOKEN to use real API"
    ]
    return result


def _mock_fallback_with_error(input_data: dict[str, Any], error: str) -> dict[str, Any]:
    """Fallback with error message."""
    from formulation_os.tools.builtins.preformulation_ai import backend as mock_backend

    result = mock_backend.run(input_data)
    result["warnings"] = result.get("warnings", []) + [
        f"⚠️ API call failed: {error}",
        "⚠️ Falling back to mock backend"
    ]
    return result
