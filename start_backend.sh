#!/bin/bash

# Quick start script for Hogwarts Mystery Backend

echo "🧙 Starting Hogwarts Mystery Backend..."
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies if needed
if [ ! -f ".venv/bin/uvicorn" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the server
echo ""
echo "Starting FastAPI server on http://127.0.0.1:8000"
echo "Press Ctrl+C to stop the server"
echo ""
uvicorn backend.app:app --reload --port 8000

