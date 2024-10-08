.PHONY: fmt
fmt:
	uvx ruff format vix.py

.PHONY: run
run:
	uvx --with-requirements requirements.txt streamlit run viz.py