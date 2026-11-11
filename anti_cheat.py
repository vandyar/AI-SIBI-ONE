"""
anti_cheat.py - Sistem Anti-Contek untuk AI Interview Platform
Deteksi: multi-face, gaze away, tab switch, copy-paste, jawaban cepat, AI text.
Mendukung MediaPipe Face Mesh (legacy) dan Face Landmarker (Tasks API).
"""
import time
import re
import math
import base64
import io
import numpy as np

try:
    import cv2
    CV2_OK = True
except ImportError:
    cv2 = None
    CV2_OK = False

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

try:
    import mediapipe as mp
    MP_PKG_OK = True
except ImportError:
    mp = None
    MP_PKG_OK = False

_face_backend = None
_legacy_face_mesh = None
_tasks_face_landmarker = None
_opencv_cascade = None

if CV2_OK:
    try:
        _opencv_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
    except Exception:
        _opencv_cascade = None


def get_anticheat_status():
    backend = _face_backend or ("opencv" if _opencv_cascade is not None else "none")
    ready = backend != "none"
    return {
        "ready": ready,
        "backend": backend,
        "mediapipe": _face_backend in ("legacy", "tasks"),
        "opencv_fallback": _face_backend is None and _opencv_cascade is not None,
        "message": "Siap" if ready else "Install mediapipe dan opencv-python",
    }


def _init_face_detector():
    global _face_backend, _legacy_face_mesh, _tasks_face_landmarker
    if _face_backend is not None:
        return _face_backend
    if not MP_PKG_OK:
        return None
    if hasattr(mp, "solutions") and hasattr(mp.solutions, "face_mesh"):
        try:
            _legacy_face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=3,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            _face_backend = "legacy"
            print("[AntiCheat] MediaPipe backend: face_mesh (legacy)")
            return "legacy"
        except Exception as e:
            print(f"[AntiCheat] Legacy FaceMesh gagal: {e}")
    try:
        from mediapipe_assets import ensure_face_landmarker_model

        face_path = ensure_face_landmarker_model()
        if face_path is None or not face_path.exists():
            return None
        from mediapipe.tasks.python import vision

        opts = vision.FaceLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(face_path)),
            running_mode=vision.RunningMode.IMAGE,
            num_faces=3,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5,
            output_face_blendshapes=True,
        )
        _tasks_face_landmarker = vision.FaceLandmarker.create_from_options(opts)
        _face_backend = "tasks"
        print("[AntiCheat] MediaPipe backend: tasks (FaceLandmarker)")
        return "tasks"
    except Exception as e:
        print(f"[AntiCheat] Tasks FaceLandmarker gagal: {e}")
        return None


LEFT_EYE_INNER = 362
LEFT_EYE_OUTER = 263
RIGHT_EYE_INNER = 133
RIGHT_EYE_OUTER = 33
LEFT_PUPIL = 468
RIGHT_PUPIL = 473


class AntiCheatMonitor:
    GAZE_THRESHOLD = 0.35
    MIN_ANSWER_SECONDS = 5
    NO_FACE_TIMEOUT = 25.0
    NO_FACE_WARN_AFTER = 4.0
    VIOLATION_COOLDOWN_SECONDS = {
        "gaze_away": 2.0,
        "multi_face": 1.5,
        "no_face": 8.0,
    }

    def __init__(self):
        self.violations = {
            "tab_switch": [],
            "multi_face": [],
            "gaze_away": [],
            "copy_paste": [],
            "fast_answer": [],
            "ai_text": [],
            "no_face": [],
        }
        self.risk_score = 0
        self._last_face_ts = time.time()
        self._question_start_ts = {}
        self._last_violation_ts = {}

    def _decode_frame(self, data_url):
        try:
            _, encoded = data_url.split(",", 1)
            raw = base64.b64decode(encoded)
        except Exception:
            return None
        if PIL_OK:
            img = np.ascontiguousarray(np.array(Image.open(io.BytesIO(raw)).convert("RGB")))
            return img
        if CV2_OK:
            buf = np.frombuffer(raw, np.uint8)
            img_bgr = cv2.imdecode(buf, cv2.IMREAD_COLOR)
            if img_bgr is None:
                return None
            return np.ascontiguousarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
        return None

    def _estimate_gaze_legacy(self, face_landmarks, frame_shape):
        h, w = frame_shape[:2]
        lm = face_landmarks.landmark
        try:

            def px(idx):
                return int(lm[idx].x * w), int(lm[idx].y * h)

            l_inner = px(LEFT_EYE_INNER)
            l_outer = px(LEFT_EYE_OUTER)
            r_inner = px(RIGHT_EYE_INNER)
            r_outer = px(RIGHT_EYE_OUTER)
            l_pupil = px(LEFT_PUPIL)
            r_pupil = px(RIGHT_PUPIL)

            def ratio(pupil, inner, outer):
                eye_width = abs(outer[0] - inner[0])
                if eye_width < 1:
                    return 0.5
                return (pupil[0] - inner[0]) / eye_width

            avg_ratio = (ratio(l_pupil, l_inner, l_outer) + ratio(r_pupil, r_inner, r_outer)) / 2
            looking = self.GAZE_THRESHOLD <= avg_ratio <= (1 - self.GAZE_THRESHOLD)
            return {"looking_at_screen": looking, "ratio_x": round(avg_ratio, 3)}
        except Exception:
            return {"looking_at_screen": True, "ratio_x": 0.5}

    def _estimate_gaze_tasks(self, blendshape_categories):
        if not blendshape_categories:
            return {"looking_at_screen": True, "ratio_x": 0.5}
        d = {c.category_name: float(c.score) for c in blendshape_categories}
        out_lr = 0.0
        down_lr = 0.0
        for name, val in d.items():
            nl = name.lower()
            if "lookout" in nl and "eye" in nl:
                out_lr = max(out_lr, val)
            if "lookdown" in nl and "eye" in nl:
                down_lr = max(down_lr, val)
        if out_lr == 0.0 and down_lr == 0.0:
            out_lr = max(d.get("eyeLookOutLeft", 0), d.get("eyeLookOutRight", 0))
            down_lr = max(d.get("eyeLookDownLeft", 0), d.get("eyeLookDownRight", 0))
        away = out_lr * 0.85 + down_lr * 0.5
        looking = away < 0.42
        ratio_x = max(0.0, min(1.0, 1.0 - away))
        return {"looking_at_screen": looking, "ratio_x": round(ratio_x, 3)}

    def check_frame(self, data_url):
        violations_this_frame = []
        details = {}
        frame = self._decode_frame(data_url)
        if frame is None:
            return {
                "violations_this_frame": violations_this_frame,
                "total_violations": self._total_violations(),
                "risk_score": self.risk_score,
                "details": {"error": "decode_failed"},
            }

        if _face_backend == "legacy" and _legacy_face_mesh is not None:
            results = _legacy_face_mesh.process(frame)
            if not results.multi_face_landmarks:
                self._handle_no_face(violations_this_frame, details)
                return self._frame_response(violations_this_frame, details)
            self._last_face_ts = time.time()
            num_faces = len(results.multi_face_landmarks)
            details["num_faces"] = num_faces
            details["face_detected"] = True
            details["backend"] = "mediapipe_legacy"
            if num_faces > 1:
                self._record("multi_face", {"count": num_faces})
                violations_this_frame.append("multi_face")
            gaze_result = self._estimate_gaze_legacy(results.multi_face_landmarks[0], frame.shape)
            details["gaze"] = gaze_result
            if not gaze_result["looking_at_screen"]:
                self._record("gaze_away", gaze_result)
                violations_this_frame.append("gaze_away")
            self._update_risk_score()
            return self._frame_response(violations_this_frame, details)

        if _face_backend == "tasks" and _tasks_face_landmarker is not None:
            mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
            result = _tasks_face_landmarker.detect(mp_img)
            n = len(result.face_landmarks) if result.face_landmarks else 0
            if n == 0:
                self._handle_no_face(violations_this_frame, details)
                return self._frame_response(violations_this_frame, details)
            self._last_face_ts = time.time()
            details["num_faces"] = n
            details["face_detected"] = True
            details["backend"] = "mediapipe_tasks"
            if n > 1:
                self._record("multi_face", {"count": n})
                violations_this_frame.append("multi_face")
            blend_list = result.face_blendshapes[0] if result.face_blendshapes else []
            gaze_result = self._estimate_gaze_tasks(blend_list)
            details["gaze"] = gaze_result
            if not gaze_result["looking_at_screen"]:
                self._record("gaze_away", gaze_result)
                violations_this_frame.append("gaze_away")
            self._update_risk_score()
            return self._frame_response(violations_this_frame, details)

        return self._check_opencv_fallback(frame, violations_this_frame, details)

    def _frame_response(self, violations_this_frame, details):
        return {
            "violations_this_frame": violations_this_frame,
            "total_violations": self._total_violations(),
            "risk_score": self.risk_score,
            "details": details,
        }

    def _handle_no_face(self, violations_this_frame, details):
        elapsed_no_face = time.time() - self._last_face_ts
        details["face_detected"] = False
        details["no_face_seconds"] = round(elapsed_no_face, 1)
        if elapsed_no_face > self.NO_FACE_WARN_AFTER:
            violations_this_frame.append("no_face")
        if elapsed_no_face > self.NO_FACE_TIMEOUT:
            self._record("no_face", {"elapsed_seconds": round(elapsed_no_face, 1)})

    def _check_opencv_fallback(self, frame, violations_this_frame, details):
        if _opencv_cascade is None:
            details["backend"] = "none"
            return self._frame_response(violations_this_frame, details)
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        else:
            gray = frame
        faces = _opencv_cascade.detectMultiScale(gray, scaleFactor=1.12, minNeighbors=6, minSize=(48, 48))
        n = len(faces)
        details["backend"] = "opencv"
        if n == 0:
            self._handle_no_face(violations_this_frame, details)
            return self._frame_response(violations_this_frame, details)
        self._last_face_ts = time.time()
        details["num_faces"] = n
        details["face_detected"] = True
        if n > 1:
            self._record("multi_face", {"count": n})
            violations_this_frame.append("multi_face")
        self._update_risk_score()
        return self._frame_response(violations_this_frame, details)

    def record_tab_switch(self):
        self._record("tab_switch", {"timestamp": time.time()})

    def record_copy_paste(self, text_length=0):
        self._record("copy_paste", {"pasted_length": text_length, "timestamp": time.time()})

    def record_question_start(self, question_id):
        self._question_start_ts[question_id] = time.time()

    def check_answer_speed(self, question_id, answer):
        start = self._question_start_ts.get(question_id)
        if start is None:
            return False
        elapsed = time.time() - start
        words = len(answer.split())
        min_expected_seconds = max(self.MIN_ANSWER_SECONDS, words / 3.2)
        if words > 24 and elapsed < min_expected_seconds:
            self._record("fast_answer", {"elapsed_seconds": round(elapsed, 2), "word_count": words})
            return True
        return False

    def analyze_text_for_ai(self, text):
        if not text or len(text) < 50:
            return {"is_likely_ai": False, "confidence": 0.0, "signals": []}
        signals = []
        score = 0.0
        ai_phrases = [
            r"\bcertainly\b",
            r"\bas an ai\b",
            r"\bin conclusion\b",
            r"\bit is worth noting\b",
            r"\bfurthermore\b",
            r"\bin summary\b",
            r"\bmoreover\b",
            r"\bultimately\b",
        ]
        phrase_hits = sum(1 for p in ai_phrases if re.search(p, text.lower()))
        if phrase_hits >= 2:
            signals.append(f"Template AI ditemukan ({phrase_hits}x)")
            score += min(phrase_hits * 0.1, 0.3)
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if len(s) > 5]
        if len(sentences) >= 4:
            lengths = [len(s.split()) for s in sentences]
            avg_len = sum(lengths) / len(lengths)
            variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)
            std_dev = math.sqrt(variance)
            if avg_len > 20:
                signals.append(f"Kalimat rata-rata panjang ({avg_len:.0f} kata)")
                score += 0.15
            if std_dev < 5 and len(sentences) >= 5:
                signals.append(f"Variasi kalimat rendah (std={std_dev:.1f})")
                score += 0.2
        personal = len(re.findall(r"\b(saya|aku|gue|i\b|my\b|me\b)", text.lower()))
        if len(text.split()) > 50 and personal < 2:
            signals.append("Minim kata ganti orang pertama")
            score += 0.15
        repeated_bigrams = len(re.findall(r"\b(\w+\s+\w+)\b(?=.*\b\1\b)", text.lower()))
        if repeated_bigrams >= 3:
            signals.append("Frasa berulang tidak natural")
            score += 0.15
        punctuation_burst = len(re.findall(r"[;:]{2,}|[!?]{2,}", text))
        if punctuation_burst > 0:
            signals.append("Pola tanda baca tidak natural")
            score += 0.08
        is_ai = score >= 0.4
        if is_ai:
            self._record("ai_text", {"confidence": round(score, 3), "signals": signals})
        return {"is_likely_ai": is_ai, "confidence": round(min(score, 1.0), 3), "signals": signals}

    def get_cheat_report(self):
        summary = {k: len(v) for k, v in self.violations.items()}
        total = sum(summary.values())
        if self.risk_score < 20:
            risk_level = "low"
        elif self.risk_score < 45:
            risk_level = "medium"
        elif self.risk_score < 70:
            risk_level = "high"
        else:
            risk_level = "critical"
        recommendation = self._build_recommendation(summary, risk_level)
        return {
            "risk_level": risk_level,
            "risk_score": self.risk_score,
            "total_violations": total,
            "violations_summary": summary,
            "recommendation": recommendation,
        }

    def _build_recommendation(self, summary, level):
        parts = []
        if summary.get("tab_switch", 0) > 2:
            parts.append(f"Berpindah tab {summary['tab_switch']}x")
        if summary.get("multi_face", 0) > 0:
            parts.append(f"Orang lain terdeteksi {summary['multi_face']}x")
        if summary.get("copy_paste", 0) > 0:
            parts.append(f"Copy-paste {summary['copy_paste']}x")
        if summary.get("ai_text", 0) > 0:
            parts.append(f"Jawaban terindikasi AI {summary['ai_text']}x")
        if level == "critical":
            return f"🚨 KECURANGAN TINGGI — {', '.join(parts)}. Harap tinjau rekaman sesi."
        if level == "high":
            return f"⚠️ Risiko tinggi — {', '.join(parts)}. Perlu verifikasi manual."
        if level == "medium":
            return f"ℹ️ Beberapa kejanggalan — {', '.join(parts)}."
        return "✅ Tidak terdeteksi pelanggaran signifikan."

    def _record(self, violation_type, data):
        now = time.time()
        cooldown = self.VIOLATION_COOLDOWN_SECONDS.get(violation_type, 0.0)
        last_ts = self._last_violation_ts.get(violation_type, 0.0)
        if cooldown > 0 and (now - last_ts) < cooldown:
            return
        self._last_violation_ts[violation_type] = now
        self.violations[violation_type].append({"timestamp": time.time(), **data})

    def _total_violations(self):
        return sum(len(v) for v in self.violations.values())

    def _update_risk_score(self):
        weights = {
            "tab_switch": 8,
            "multi_face": 15,
            "gaze_away": 2,
            "copy_paste": 10,
            "fast_answer": 12,
            "ai_text": 18,
            "no_face": 5,
        }
        score = sum(len(events) * weights.get(vtype, 5) for vtype, events in self.violations.items())
        self.risk_score = min(score, 100)


_init_face_detector()

_monitors = {}


def get_monitor(session_id):
    if session_id not in _monitors:
        _monitors[session_id] = AntiCheatMonitor()
    return _monitors[session_id]


def remove_monitor(session_id):
    _monitors.pop(session_id, None)
