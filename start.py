#!/usr/bin/env python
"""
AI Interview Platform - Startup Script
"""
import os
import sys
import subprocess

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("=" * 60)
print("AI Interview Platform")
print("=" * 60)
print()

# Check imports
print("[1/3] Checking dependencies...")
try:
    import flask
    import flask_socketio
    import numpy
    import cv2
    from PIL import Image
    print("✓ All required dependencies loaded")
except ImportError as e:
    print(f"✗ Missing dependency: {e}")
    sys.exit(1)

print()
print("[2/3] Checking application modules...")
try:
    from ai_engine import AIInterviewer, CVAnalyzer, JobMatcher, JobDatabase
    print("✓ Application modules loaded")
except Exception as e:
    print(f"✗ Error loading app modules: {e}")
    sys.exit(1)

print()
print("[3/3] Starting Flask server...")
print("-" * 60)
print()
print("Server starting on http://127.0.0.1:8000")
print("Press Ctrl+C to stop")
print()
print("-" * 60)
print()

# Import and run app
try:
    from app import app, socketio
    socketio.run(app, host='127.0.0.1', port=8000, debug=True)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
