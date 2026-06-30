# FormulationOS — common development tasks
#
# Run `make help` for a summary of targets.

PYTHON ?= python3
PIP    ?= $(PYTHON) -m pip

# Path to the Streamlit entry point.
UI_APP = src/formulation_os/ui/app.py

.PHONY: help install test run-ui run-ui-llm lint clean

help:
	@echo "FormulationOS — common targets:"
	@echo ""
	@echo "  install       install in editable mode with [all,dev] extras"
	@echo "  test          run the full test suite (pytest, quiet)"
	@echo "  run-ui        launch the Streamlit UI (rule-based planner)"
	@echo "  run-ui-llm    launch the Streamlit UI with the LLM planner"
	@echo "                (requires LLM_PLANNER=1 and a MiniMax or Anthropic key)"
	@echo "  lint          run ruff and mypy"
	@echo "  clean         remove caches and build artifacts"

install:
	$(PIP) install -e ".[all,dev]"

test:
	$(PYTHON) -m pytest

run-ui:
	$(PYTHON) -m streamlit run $(UI_APP)

run-ui-llm:
	@if [ -z "$$MINIMAX_API_KEY" ] && [ -z "$$ANTHROPIC_API_KEY" ]; then \
		echo "Error: set MINIMAX_API_KEY (or ANTHROPIC_API_KEY) before running with the LLM planner."; \
		exit 1; \
	fi
	LLM_PLANNER=1 $(PYTHON) -m streamlit run $(UI_APP)

lint:
	@if command -v $(PYTHON) -m ruff >/dev/null 2>&1; then \
		$(PYTHON) -m ruff check src tests; \
	else \
		echo "ruff not installed; skipping. Install with: $(PIP) install ruff"; \
	fi
	$(PYTHON) -m mypy src

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache build dist
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
