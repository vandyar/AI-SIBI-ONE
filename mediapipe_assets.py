"""
Unduh model .task MediaPipe (Tasks API) ke folder Model/mediapipe_tasks/ jika belum ada.
Diperlukan untuk MediaPipe >= 0.10.20 yang tidak lagi menyertakan mp.solutions.
"""
from __future__ import annotations

import urllib.request
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).parent
MODEL_DIR = BASE_DIR / "Model" / "mediapipe_tasks"

HAND_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)
FACE_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/1/face_landmarker.task"
)


def _download(url: str, dest: Path) -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    try:
        urllib.request.urlretrieve(url, tmp)
        tmp.replace(dest)
    except Exception:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        raise


def ensure_hand_landmarker_model() -> Optional[Path]:
    dest = MODEL_DIR / "hand_landmarker.task"
    if not dest.exists():
        try:
            print(f"[MediaPipe] Mengunduh hand_landmarker.task …")
            _download(HAND_URL, dest)
        except Exception as e:
            print(f"[MediaPipe] Gagal unduh hand model: {e}")
            return None
    return dest


def ensure_face_landmarker_model() -> Optional[Path]:
    dest = MODEL_DIR / "face_landmarker.task"
    if not dest.exists():
        try:
            print(f"[MediaPipe] Mengunduh face_landmarker.task …")
            _download(FACE_URL, dest)
        except Exception as e:
            print(f"[MediaPipe] Gagal unduh face model: {e}")
            return None
    return dest
