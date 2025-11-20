.PHONY: help install test lint format clean run

help:
	@echo "WeatherDataTool - Makefile Commands"
	@echo ""
	@echo "  make install     - Install package and dependencies"
	@echo "  make test        - Run test suite"
	@echo "  make test-cov    - Run tests with coverage"
	@echo "  make lint        - Run linters (ruff, mypy)"
	@echo "  make format      - Format code with black"
	@echo "  make clean       - Clean generated files"
	@echo "  make run         - Run example pipeline"
	@echo "  make info        - Show configuration info"
	@echo ""

install:
	pip install -r requirements.txt
	pip install -e .

test:
	pytest -v

test-cov:
	pytest --cov=weather_data_tool --cov-report=html --cov-report=term

lint:
	ruff check src/ tests/
	mypy src/ || true

format:
	black src/ tests/

clean:
	rm -rf build/ dist/ *.egg-info
	rm -rf htmlcov/ .coverage
	rm -rf .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

run:
	./scripts/run_pipeline.sh

info:
	python -m weather_data_tool.cli info
