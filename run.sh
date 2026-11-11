#!/bin/bash

echo "🚀 AI Interview Platform"
echo "========================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    echo "Please install Python 3.8+ from https://python.org"
    exit 1
fi

echo "✅ Python 3 detected"
echo

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.8 or higher is required"
    echo "Current version: $python_version"
    exit 1
fi

echo "✅ Python version $python_version is compatible"
echo

echo "Installing/updating dependencies..."
pip3 install -r requirements.txt

echo
echo "🎯 Starting AI Interview Platform..."
echo "📱 Open your browser and go to: http://127.0.0.1:8000"
echo "⏹️  Press Ctrl+C to stop the application"
echo "========================================"
echo

python3 run.py
