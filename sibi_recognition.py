"""
sibi_recognition.py - SIBI (Sistem Isyarat Bahasa Indonesia) Recognition
MediaPipe Hands + model SVM untuk prediksi isyarat.
Mendukung mp.solutions (lama) dan MediaPipe Tasks API (mediapipe >= 0.10.20).
"""
import pickle
import numpy as np
import base64
import io
from pathlib import Path

try:
    import cv2
    CV2_OK = True
except ImportError:
    cv2 = None
    CV2_OK = False

try:
    import mediapipe as mp
    MP_PKG_OK = True
except ImportError:
    mp = None
    MP_PKG_OK = False

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

BASE_DIR = Path(__file__).parent
MODEL_PATH = BASE_DIR / "Model" / "svm_model_v3.sav"

SIBI_LABELS = ["A", "B", "C", "D", "E", "Hai", "Hallo"]

# Backend: "legacy" | "tasks" | None
_mp_backend = None
_legacy_hands = None
_tasks_landmarker = None


def _detect_mediapipe_backend():
    global _mp_backend, _legacy_hands, _tasks_landmarker
    if _mp_backend is not None:
        return _mp_backend
    if not MP_PKG_OK:
        return None
    if hasattr(mp, "solutions") and hasattr(mp.solutions, "hands"):
        try:
            _legacy_hands = mp.solutions.hands.Hands(
                static_image_mode=False,
                model_complexity=0,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
                max_num_hands=1,
            )
            _mp_backend = "legacy"
            print("[SIBI] MediaPipe backend: solutions (legacy)")
            return "legacy"
        except Exception as e:
            print(f"[SIBI] Legacy Hands gagal: {e}")
    try:
        from mediapipe_assets import ensure_hand_landmarker_model

        hand_path = ensure_hand_landmarker_model()
        if hand_path is None or not hand_path.exists():
            return None
        from mediapipe.tasks.python import vision

        opts = vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(hand_path)),
            running_mode=vision.RunningMode.IMAGE,
            num_hands=1,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        _tasks_landmarker = vision.HandLandmarker.create_from_options(opts)
        _mp_backend = "tasks"
        print("[SIBI] MediaPipe backend: tasks (HandLandmarker)")
        return "tasks"
    except Exception as e:
        print(f"[SIBI] Tasks HandLandmarker gagal: {e}")
        return None


class SIBIRecognizer:
    WINDOW_SIZE = 5
    KEYPOINTS_PER_FRAME = 42
    SCALE_FACTOR = 320

    def __init__(self):
        self.model = None
        self.keypoint_buffer = np.array([])
        self.is_ready = False
        self.last_prediction = None
        self.prediction_count = 0
        self._load_model()
        self._init_mediapipe()

    def _load_model(self):
        if not MODEL_PATH.exists():
            print(f"[SIBI] Model tidak ditemukan: {MODEL_PATH}")
            return
        try:
            with open(MODEL_PATH, "rb") as f:
                self.model = pickle.load(f)
            print(f"[SIBI] Model dimuat: {MODEL_PATH.name}")
        except Exception as e:
            print(f"[SIBI] Gagal load model: {e}")

    def _init_mediapipe(self):
        global _mp_backend
        if _mp_backend is None:
            _detect_mediapipe_backend()
        if _mp_backend is None:
            print("[SIBI] MediaPipe tidak tersedia. Install: pip install mediapipe")
            return
        self.is_ready = self.model is not None

    def _decode_frame(self, data_url):
        try:
            _, encoded = data_url.split(",", 1)
            raw = base64.b64decode(encoded)
        except Exception:
            return None
        if PIL_OK:
            img = Image.open(io.BytesIO(raw)).convert("RGB")
            return np.ascontiguousarray(np.array(img))
        if CV2_OK:
            buf = np.frombuffer(raw, np.uint8)
            img_bgr = cv2.imdecode(buf, cv2.IMREAD_COLOR)
            if img_bgr is None:
                return None
            return np.ascontiguousarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
        return None

    def _keypoints_from_landmarks(self, landmarks):
        if len(landmarks) < 21:
            return None
        wrist_x = landmarks[0].x
        wrist_y = landmarks[0].y
        centered_x = np.array([landmarks[i].x - wrist_x for i in range(21)])
        centered_y = np.array([landmarks[i].y - wrist_y for i in range(21)])
        centered = np.vstack([centered_x, centered_y])
        scaled = np.zeros_like(centered)
        for axis in range(2):
            max_abs = np.max(np.abs(centered[axis]))
            if max_abs == 0:
                max_abs = 1e-9
            scaled[axis] = (centered[axis] / max_abs) * self.SCALE_FACTOR
        normalized = scaled.flatten() + self.SCALE_FACTOR
        return normalized

    def _extract_keypoints(self, frame_rgb):
        if _mp_backend == "legacy" and _legacy_hands is not None:
            results = _legacy_hands.process(frame_rgb)
            if not results.multi_hand_landmarks:
                return None
            return self._keypoints_from_landmarks(results.multi_hand_landmarks[0].landmark)

        if _mp_backend == "tasks" and _tasks_landmarker is not None:
            mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
            result = _tasks_landmarker.detect(mp_img)
            if not result.hand_landmarks:
                return None
            return self._keypoints_from_landmarks(result.hand_landmarks[0])

        return None

    def process_frame(self, data_url):
        if not self.is_ready:
            return {"status": "error", "message": "SIBI recognizer belum siap", "prediction": None, "buffer_size": 0}
        frame = self._decode_frame(data_url)
        if frame is None:
            return {"status": "error", "message": "Gagal decode frame", "prediction": None, "buffer_size": 0}
        keypoints = self._extract_keypoints(frame)
        if keypoints is None:
            self.keypoint_buffer = np.array([])
            return {"status": "no_hand", "message": "Tidak ada tangan terdeteksi", "prediction": None, "buffer_size": 0}
        self.keypoint_buffer = np.append(self.keypoint_buffer, keypoints)
        total_needed = self.WINDOW_SIZE * self.KEYPOINTS_PER_FRAME
        if len(self.keypoint_buffer) < total_needed:
            return {
                "status": "collecting",
                "message": f"Mengumpulkan frame {len(self.keypoint_buffer) // self.KEYPOINTS_PER_FRAME}/{self.WINDOW_SIZE}",
                "prediction": self.last_prediction,
                "buffer_size": int(len(self.keypoint_buffer)),
            }
        window = self.keypoint_buffer[:total_needed]
        try:
            pred_idx = self.model.predict([window])[0]
            label = SIBI_LABELS[int(pred_idx)] if 0 <= int(pred_idx) < len(SIBI_LABELS) else str(pred_idx)
            confidence = 0.0
            if hasattr(self.model, "predict_proba"):
                proba = self.model.predict_proba([window])[0]
                confidence = float(np.max(proba))
            elif hasattr(self.model, "decision_function"):
                scores = self.model.decision_function([window])[0]
                confidence = float(min(1.0, max(0.0, 1.0 / (1.0 + np.exp(-np.max(scores))))))
            self.last_prediction = label
            self.prediction_count += 1
        except Exception:
            label = None
            confidence = 0.0
        delete_idx = np.arange(self.KEYPOINTS_PER_FRAME)
        self.keypoint_buffer = np.delete(self.keypoint_buffer, delete_idx)
        return {
            "status": "prediction",
            "prediction": label,
            "confidence": round(confidence, 4),
            "buffer_size": int(len(self.keypoint_buffer)),
            "message": f"Isyarat: {label}",
        }

    def reset_buffer(self):
        self.keypoint_buffer = np.array([])
        self.last_prediction = None

    def get_status(self):
        return {
            "ready": self.is_ready,
            "model_loaded": self.model is not None,
            "mediapipe_available": _mp_backend is not None,
            "backend": _mp_backend or "none",
            "labels": SIBI_LABELS,
            "total_predictions": self.prediction_count,
        }


_sibi_instance = None


def get_sibi_recognizer():
    global _sibi_instance
    if _sibi_instance is None:
        _sibi_instance = SIBIRecognizer()
    return _sibi_instance
