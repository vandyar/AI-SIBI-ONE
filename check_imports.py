#!/usr/bin/env python
import sys

print("Checking dependencies...")
print("-" * 50)

modules = [
    ("flask", "Flask"),
    ("flask_socketio", "Flask-SocketIO"),
    ("socketio", "python-socketio"),
    ("engineio", "python-engineio"),
    ("werkzeug", "Werkzeug"),
    ("cv2", "opencv-python"),
    ("PIL", "Pillow"),
    ("numpy", "NumPy"),
    ("mediapipe", "mediapipe"),
]

missing = []
for module, display_name in modules:
    try:
        __import__(module)
        print(f"[OK] {display_name}")
    except ImportError:
        print(f"[MISSING] {display_name}")
        missing.append(display_name)

print("-" * 50)

try:
    import face_recognition
    print("[OK] face_recognition (optional)")
except ImportError:
    print("[--] face_recognition (optional, tidak dipasang)")

print()
if missing:
    print(f"ERROR: {len(missing)} missing dependencies:")
    for m in missing:
        print(f"  - {m}")
    sys.exit(1)
else:
    print("Semua dependensi utama terpasang.")
    print("Jalankan: python run.py")
    sys.exit(0)
