"""Configuration for switching between mock and real backends."""

import os

# Check environment variable to decide which backend to use
USE_REAL_BACKENDS = os.getenv("USE_REAL_FORMULATION_TOOLS", "false").lower() == "true"

# Backend module paths
FORMULATION_AI_BACKEND = (
    "formulation_os.tools.builtins.formulation_ai.backend_real"
    if USE_REAL_BACKENDS
    else "formulation_os.tools.builtins.formulation_ai.backend"
)

PREFORMULATION_AI_BACKEND = (
    "formulation_os.tools.builtins.preformulation_ai.backend_real"
    if USE_REAL_BACKENDS
    else "formulation_os.tools.builtins.preformulation_ai.backend"
)
