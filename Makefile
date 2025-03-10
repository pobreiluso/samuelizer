.PHONY: setup test lint format docs run clean docs-md docs-view

setup:
	poetry install

test:
	poetry run pytest

test-cov:
	poetry run pytest --cov=src --cov-report=term-missing

lint:
	poetry run flake8 src/

format:
	poetry run black src/ tests/
	poetry run isort src/ tests/

type-check:
	poetry run mypy src/

docs:
	mkdir -p docs/_build
	poetry run sphinx-build -b html docs/ docs/_build

docs-md:
	@echo "Markdown documentation is available in the docs/ directory"
	@echo "- docs/architecture.md: Architecture overview"
	@echo "- docs/api.md: API documentation"
	@echo "- docs/examples.md: Usage examples"

docs-view:
	open README.md

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
	rm -rf recordings/*.mp3
	rm -rf recordings/*.wav

.DEFAULT_GOAL := help

help:
	@echo "Available commands:"
	@echo "  setup      - Install dependencies with Poetry"
	@echo "  test       - Run tests with pytest"
	@echo "  test-cov   - Run tests with coverage report"
	@echo "  lint       - Run linting with flake8"
	@echo "  format     - Format code with black and isort"
	@echo "  type-check - Run type checking with mypy"
	@echo "  docs       - Generate HTML documentation with Sphinx"
	@echo "  docs-md    - List available markdown documentation"
	@echo "  docs-view  - Open README.md in default viewer"
	@echo "  run        - Run the application"
	@echo "  clean      - Remove temporary files and directories"
	@echo ""
	@echo "CLI Commands:"
	@echo "  poetry run samuelize media FILE_PATH  - Transcribe and analyze media files"
	@echo "  poetry run samuelize text \"TEXT\"      - Analyze and summarize text"
	@echo "  poetry run samuelize slack CHANNEL_ID - Analyze Slack channel messages"
	@echo "  poetry run samuelize listen           - Record and analyze system audio"
	@echo "  poetry run samuelize version          - Display version information"
	@echo "  poetry run samuelize providers        - List available AI providers and models"
	@echo ""
	@echo "For more details on each command, run:"
	@echo "  poetry run samuelize COMMAND --help"
