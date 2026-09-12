PYTHON ?= python3.11

.PHONY: help format-check lint test workflow-check check

help:
	@printf '%s\n' \
		'Targets:' \
		'  make format-check   Check Python formatting' \
		'  make lint           Run Python lint' \
		'  make test           Run focused repository tests' \
		'  make workflow-check Validate GitHub Actions syntax' \
		'  make check          Run every local repository gate'

format-check:
	$(PYTHON) -m ruff format --check packaging tests

lint:
	$(PYTHON) -m ruff check packaging tests

test:
	$(PYTHON) -m unittest discover -s tests

workflow-check:
	actionlint .github/workflows/prototype.yml

check: format-check lint test workflow-check
