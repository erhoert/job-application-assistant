.PHONY: install test run clean

install:
	pip install -e ".[dev]"

test:
	pytest -v

run:
	job-assistant --help

clean:
	rm -rf dist/ *.egg-info/ __pycache__/ .pytest_cache/
