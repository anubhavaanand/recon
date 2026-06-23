#!/bin/bash

set -e

echo "Running Evaluation Validation..."
echo "--------------------------------"

# Check if pytest is available
if ! command -v pytest &> /dev/null; then
    echo "ERR: pytest not found. Please activate the virtual environment."
    exit 1
fi

# Run the test suite
echo "Running pytest suite..."
pytest tests/ -v

echo "--------------------------------"
echo "Evaluation Validation Successful"
exit 0
