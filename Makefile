.PHONY: setup test lint format docs run clean

setup:
	poetry install

test:
	poetry run pytest

lint:
	poetry run flake8 src/

format:
	poetry run black src/

docs:
	mkdir -p docs/_build
	poetry run sphinx-build -b html docs/ docs/_build

run:
	poetry run samuelize

clean:
	rm -rf __pycache__/ 
	rm -rf **/__pycache__/
	rm -rf *.pyc
	rm -rf **/*.pyc
	rm -rf docs/_build
	rm -rf .pytest_cache
	rm -rf .coverage

.DEFAULT_GOAL := help

help:
	@echo "Available commands:"
	@echo "  setup   - Install dependencies with Poetry"
	@echo "  test    - Run tests with pytest"
	@echo "  lint    - Run linting with flake8"
	@echo "  format  - Format code with black"
	@echo "  docs    - Generate documentation with Sphinx"
	@echo "  run     - Run the application"
	@echo "  clean   - Remove temporary files and directories"
