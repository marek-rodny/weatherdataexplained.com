#!/bin/bash
# Local CI simulation script - run before pushing to verify everything works

set -e

echo "========================================="
echo "Local CI Simulation"
echo "========================================="
echo ""

# Check we're in the right directory
if [ ! -f "WeatherDataTool/pyproject.toml" ]; then
    echo "ERROR: Run this from the repository root"
    exit 1
fi

cd WeatherDataTool

echo "Step 1/5: Installing dependencies..."
pip install -q -r requirements.txt
pip install -q -e .
echo "✓ Dependencies installed"
echo ""

echo "Step 2/5: Running black format check..."
black --check src/ tests/ || {
    echo "⚠ Formatting issues found. Run: black src/ tests/"
    exit 1
}
echo "✓ Code formatting OK"
echo ""

echo "Step 3/5: Running ruff linter..."
ruff check src/ tests/ || {
    echo "⚠ Linting issues found"
    exit 1
}
echo "✓ Linting passed"
echo ""

echo "Step 4/5: Running type checking..."
mypy src/ || {
    echo "⚠ Type checking found issues (non-fatal)"
}
echo ""

echo "Step 5/5: Running test suite..."
pytest -v --tb=short --color=yes
echo "✓ All tests passed"
echo ""

echo "========================================="
echo "✓ Local CI simulation complete!"
echo "========================================="
echo ""
echo "Your code is ready to push. CI should pass."
echo ""
