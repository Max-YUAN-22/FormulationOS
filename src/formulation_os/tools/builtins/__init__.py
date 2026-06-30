"""Built-in mock scientific tools (v0.1).

Five representative tools spanning computational pharmaceutics:

* :mod:`formulation_os.tools.builtins.formulation_ai` — excipient design
* :mod:`formulation_os.tools.builtins.preformulation_ai` — solubility / permeability
* :mod:`formulation_os.tools.builtins.pbpk_ai` — PK parameter estimation
* :mod:`formulation_os.tools.builtins.formulation_dt` — dissolution / particle
* :mod:`formulation_os.tools.builtins.literature` — literature search

All five return deterministic placeholder data with ``warnings`` fields
clearly labeled as ``MOCK``. They exist to validate the architecture
end-to-end before real models are wired in.
"""