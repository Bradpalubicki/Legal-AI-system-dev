#!/bin/bash

# Legal AI System Compliance Validation Runner
# This script runs the comprehensive compliance validation checks

echo "========================================"
echo "Legal AI System Compliance Validation"
echo "========================================"
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "ERROR: Python is not installed or not in PATH"
        echo "Please install Python 3.8+ and try again"
        exit 1
    fi
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi

echo "Using Python: $($PYTHON_CMD --version)"

# Change to the backend directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# Set PYTHONPATH to include the app directory
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Check if virtual environment exists and activate it
if [[ -f "venv/bin/activate" ]]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
elif [[ -f ".venv/bin/activate" ]]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "WARNING: No virtual environment found, using system Python"
fi

# Check dependencies
echo "Checking dependencies..."
$PYTHON_CMD -c "import sqlite3, json, re, logging, asyncio" 2>/dev/null
if [[ $? -ne 0 ]]; then
    echo "Installing required Python packages..."
    pip install asyncio 2>/dev/null || echo "Note: Some packages may already be available"
fi

echo
echo "Starting compliance validation..."
echo "This may take several minutes to complete."
echo

# Run the compliance validation script
$PYTHON_CMD scripts/compliance_validation.py

# Capture exit code
VALIDATION_RESULT=$?

echo
echo "========================================"
if [[ $VALIDATION_RESULT -eq 0 ]]; then
    echo "✅ COMPLIANCE VALIDATION COMPLETED SUCCESSFULLY"
    echo "All systems are compliant with legal requirements"
elif [[ $VALIDATION_RESULT -eq 1 ]]; then
    echo "❌ COMPLIANCE VALIDATION FAILED"
    echo "Critical compliance issues detected"
    echo "Please review the report and address failures immediately"
else
    echo "⚠️  COMPLIANCE VALIDATION ERROR"
    echo "An error occurred during validation"
    echo "Please check the logs and try again"
fi
echo "========================================"

# Exit with the validation result
exit $VALIDATION_RESULT