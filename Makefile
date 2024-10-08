.PHONY: fmt
fmt:
	uvx ruff format viz.py

.PHONY: run
run:
	uvx --with-requirements requirements.txt streamlit run viz.py

.PHONY: lint
lint:
	uvx ruff check viz.py
