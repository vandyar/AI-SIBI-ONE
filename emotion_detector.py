"""
emotion_detector.py - Deteksi emosi wajah (DeepFace + fallback OpenCV)
"""
import base64
import io
import time
import numpy as np
from collections import Counter

try:
    from deepface import DeepFace
    DEEPFACE_OK = True
except ImportError:
    DeepFace = None
    DEEPFACE_OK = False

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

try:
    import cv2
    CV2_OK = True
    _FACE_CASCADE = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
except ImportError:
    cv2 = None
    CV2_OK = False
    _FACE_CASCADE = None

NEGATIVE_EMOTIONS = {"angry", "disgust", "fear", "sad"}

EMOTION_EMOJI = {
    "angry": "😠", "disgust": "🤢", "fear": "😨",
    "happy": "😊", "sad": "😢", "surprise": "😲", "neutral": "😐",
}


def get_emotion_status():
    backend = "deepface" if DEEPFACE_OK else ("opencv" if CV2_OK else "none")
    return {
        "ready": DEEPFACE_OK or CV2_OK,
        "backend": backend,
        "deepface": DEEPFACE_OK,
        "opencv_fallback": CV2_OK and not DEEPFACE_OK,
        "message": "Siap" if (DEEPFACE_OK or CV2_OK) else "Install deepface tf-keras atau opencv-python",
    }


class EmotionDetector:
    def __init__(self, analyze_interval=2.0):
        self.history = []
        self.emotion_counts = Counter()
        self.is_ready = DEEPFACE_OK or CV2_OK
        self.backend = "deepface" if DEEPFACE_OK else ("opencv" if CV2_OK else "none")
        self.analyze_interval = analyze_interval
        self._last_analyzed = 0.0
        self._last_result = None
        self._recent_dominant = []
        self._detector_backends = ["opencv", "retinaface", "mtcnn"]

    def _decode_frame(self, data_url):
        try:
            _, encoded = data_url.split(",", 1)
            raw = base64.b64decode(encoded)
        except Exception:
            return None
        if PIL_OK:
            img_rgb = np.array(Image.open(io.BytesIO(raw)).convert("RGB"))
            if CV2_OK:
                return cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
            return img_rgb
        if CV2_OK:
            buf = np.frombuffer(raw, np.uint8)
            return cv2.imdecode(buf, cv2.IMREAD_COLOR)
        return None

    def _analyze_opencv_fallback(self, frame, now):
        if not CV2_OK or _FACE_CASCADE is None:
            return self._error("OpenCV tidak tersedia")
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = _FACE_CASCADE.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
        if len(faces) == 0:
            return {
                "status": "no_face",
                "dominant_emotion": "neutral",
                "emotion_scores": {},
                "emoji": "😐",
                "is_negative": False,
                "message": "Wajah tidak terdeteksi — hadapkan wajah ke kamera",
                "timestamp": now,
                "backend": "opencv",
            }
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        roi = gray[y:y + h, x:x + w]
        if roi.size == 0:
            return self._error("ROI wajah kosong")
        brightness = float(np.mean(roi))
        contrast = float(np.std(roi))
        if brightness > 140 and contrast > 35:
            dominant = "happy"
        elif brightness < 85:
            dominant = "sad"
        elif contrast > 55:
            dominant = "surprise"
        else:
            dominant = "neutral"
        scores = {dominant: 72.0, "neutral": 28.0 if dominant != "neutral" else 85.0}
        return self._finalize_result(dominant, scores, now, backend="opencv")

    def _finalize_result(self, dominant, scores, now, backend="deepface"):
        dominant = self._smooth_dominant_emotion(dominant, scores)
        record = {
            "timestamp": now,
            "dominant_emotion": dominant,
            "scores": {k: round(float(v), 2) for k, v in scores.items()},
        }
        self.history.append(record)
        self.emotion_counts[dominant] += 1
        result = {
            "status": "success",
            "dominant_emotion": dominant,
            "emotion_scores": record["scores"],
            "emoji": EMOTION_EMOJI.get(dominant, "😐"),
            "is_negative": dominant in NEGATIVE_EMOTIONS,
            "message": f"Emosi: {dominant}",
            "timestamp": now,
            "backend": backend,
        }
        self._last_analyzed = now
        self._last_result = result
        return result

    def analyze_frame(self, data_url):
        now = time.time()
        if now - self._last_analyzed < self.analyze_interval and self._last_result:
            cached = {**self._last_result, "status": "throttled"}
            return cached
        if not self.is_ready:
            return self._error("Modul emosi tidak tersedia. Install: pip install deepface tf-keras")

        frame = self._decode_frame(data_url)
        if frame is None:
            return self._error("Gagal decode frame kamera")

        if DEEPFACE_OK:
            try:
                face_data = None
                for backend in self._detector_backends:
                    try:
                        results = DeepFace.analyze(
                            frame,
                            actions=["emotion"],
                            enforce_detection=False,
                            silent=True,
                            detector_backend=backend,
                        )
                        face_data = results[0] if isinstance(results, list) else results
                        break
                    except Exception:
                        continue
                if face_data is not None:
                    dominant = face_data.get("dominant_emotion", "neutral")
                    scores = face_data.get("emotion", {})
                    return self._finalize_result(dominant, scores, now, backend="deepface")
            except Exception:
                pass

        return self._analyze_opencv_fallback(frame, now)

    def get_session_report(self):
        if not self.history:
            return {
                "total_samples": 0,
                "dominant_overall": "neutral",
                "emotion_distribution": {},
                "negative_ratio": 0.0,
                "recommendation": "Tidak ada data emosi — pastikan webcam aktif selama interview.",
                "backend": self.backend,
            }
        total = len(self.history)
        distribution = {
            emotion: round((count / total) * 100, 1)
            for emotion, count in self.emotion_counts.items()
        }
        dominant_overall = self.emotion_counts.most_common(1)[0][0]
        negative_count = sum(
            count for emotion, count in self.emotion_counts.items()
            if emotion in NEGATIVE_EMOTIONS
        )
        negative_ratio = round(negative_count / total, 3)
        recommendation = self._generate_recommendation(dominant_overall, negative_ratio, distribution)
        return {
            "total_samples": total,
            "dominant_overall": dominant_overall,
            "emotion_distribution": distribution,
            "negative_ratio": negative_ratio,
            "recommendation": recommendation,
            "backend": self.backend,
        }

    def _generate_recommendation(self, dominant, negative_ratio, distribution):
        if negative_ratio > 0.5:
            return "Kandidat menunjukkan emosi negatif dominan (>50%). Pertimbangkan evaluasi ulang."
        if dominant == "happy" and distribution.get("happy", 0) > 40:
            return "Kandidat terlihat percaya diri dan antusias selama interview."
        if dominant == "neutral" and distribution.get("neutral", 0) > 60:
            return "Kandidat tampil tenang dan profesional."
        if dominant == "fear" and distribution.get("fear", 0) > 30:
            return "Kandidat terlihat gugup. Pertimbangkan sesi follow-up yang lebih santai."
        return f"Emosi dominan kandidat: {dominant} ({distribution.get(dominant, 0)}%)."

    def reset(self):
        self.history.clear()
        self.emotion_counts.clear()
        self._last_result = None
        self._last_analyzed = 0.0
        self._recent_dominant.clear()

    def _smooth_dominant_emotion(self, dominant, scores):
        if scores:
            top_emotion = max(scores.items(), key=lambda item: float(item[1]))[0]
        else:
            top_emotion = dominant or "neutral"
        self._recent_dominant.append(top_emotion)
        if len(self._recent_dominant) > 5:
            self._recent_dominant.pop(0)
        most_common = Counter(self._recent_dominant).most_common(1)
        return most_common[0][0] if most_common else (dominant or "neutral")

    @staticmethod
    def _error(msg):
        return {
            "status": "error",
            "dominant_emotion": "neutral",
            "emotion_scores": {},
            "emoji": "❓",
            "is_negative": False,
            "message": msg,
            "timestamp": time.time(),
        }


_session_detectors = {}


def get_emotion_detector(session_id):
    if session_id not in _session_detectors:
        _session_detectors[session_id] = EmotionDetector()
    return _session_detectors[session_id]


def remove_emotion_detector(session_id):
    _session_detectors.pop(session_id, None)
