#!/bin/bash

echo "🗄️ Resume Relevance System - Database Initialization"
echo "============================================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ Python not found! Please install Python first."
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# Run the database initialization script
$PYTHON_CMD init_database.py

echo ""
echo "Press any key to exit..."
read -n 1 -s
