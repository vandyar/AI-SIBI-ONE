#!/usr/bin/env python3
"""Entry point untuk AI Interview Platform Enhanced"""
import sys
import os

def check_dependencies():
    missing = []
    required = ['flask', 'flask_socketio', 'numpy']
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"❌ Package hilang: {', '.join(missing)}")
        print("Jalankan: pip install -r requirements.txt")
        sys.exit(1)

if __name__ == '__main__':
    check_dependencies()
    from app import app, socketio
    print("=" * 60)
    print("🤖 AI Interview Platform Enhanced")
    print("=" * 60)
    print("📱 Buka browser: http://127.0.0.1:8000")
    print("🤟 SIBI | 😊 Emosi | 🛡 Anti-Cheat | 🔍 Portfolio")
    print("=" * 60)
    socketio.run(app, host='127.0.0.1', port=8000, debug=False)
