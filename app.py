from flask import Flask, render_template, request, jsonify, Response
from flask_socketio import SocketIO, emit
import json
import csv
from datetime import datetime, date
import time
import threading
import random
import io
import base64
import os
import pickle
import math
from pathlib import Path

# ── Optional: face_recognition ────────────────────────────────────────────────
try:
    import face_recognition
except Exception:
    face_recognition = None

try:
    from PIL import Image
    PIL_OK = True
except Exception:
    Image = None
    PIL_OK = False

import numpy as np
from ai_engine import AIInterviewer, CVAnalyzer, JobMatcher, JobDatabase

# ── Optional: cv2 ─────────────────────────────────────────────────────────────
try:
    import cv2
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    CV2_OK = True
except Exception:
    cv2 = None
    face_cascade = None
    CV2_OK = False

# ── New feature modules ────────────────────────────────────────────────────────
try:
    from sibi_recognition import get_sibi_recognizer
    SIBI_OK = True
except Exception as e:
    SIBI_OK = False
    print(f"[SIBI] Tidak tersedia: {e}")

try:
    from emotion_detector import get_emotion_detector, remove_emotion_detector, get_emotion_status
    EMOTION_OK = True
except Exception as e:
    EMOTION_OK = False
    get_emotion_status = None
    print(f"[Emotion] Tidak tersedia: {e}")

try:
    from anti_cheat import get_monitor, remove_monitor, get_anticheat_status
    ANTICHEAT_OK = True
except Exception as e:
    ANTICHEAT_OK = False
    get_anticheat_status = None
    print(f"[AntiCheat] Tidak tersedia: {e}")

try:
    from portfolio_analyzer import PortfolioAnalyzer
    PORTFOLIO_OK = True
except Exception as e:
    PORTFOLIO_OK = False
    print(f"[Portfolio] Tidak tersedia: {e}")

# ── Flask app ──────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config['SECRET_KEY'] = 'ai-interview-secret-2025'
socketio = SocketIO(app, cors_allowed_origins="*")

# ── Storage ────────────────────────────────────────────────────────────────────
interview_sessions = {}
cv_analyses = {}
candidate_records = {}

CUSTOM_QUESTIONS_FILE = Path(__file__).parent / 'custom_questions.json'

def load_custom_questions():
    global custom_questions
    if CUSTOM_QUESTIONS_FILE.exists():
        try:
            with open(CUSTOM_QUESTIONS_FILE, 'r') as f:
                custom_questions = json.load(f)
        except Exception:
            pass

def save_custom_questions():
    try:
        with open(CUSTOM_QUESTIONS_FILE, 'w') as f:
            json.dump(custom_questions, f, indent=2)
    except Exception as e:
        print(f"Error saving custom questions: {e}")

custom_questions = {'software-developer': [], 'data-scientist': [], 'product-manager': [], 'general': []}
load_custom_questions()

def safe_score(value, default=0.0):
    try:
        parsed = float(value)
        if not math.isfinite(parsed):
            return default
        return parsed
    except (TypeError, ValueError):
        return default

# ── Face recognition storage ───────────────────────────────────────────────────
reference_encodings = {}
FACE_DB_PATH = Path(__file__).parent / 'face_database.pkl'
face_database = {}

def load_image_from_file(file):
    if PIL_OK:
        image = Image.open(file).convert('RGB')
        return np.array(image)
    if CV2_OK:
        raw_bytes = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(raw_bytes, cv2.IMREAD_COLOR)
        if img is None: return None
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return None

def load_image_from_dataurl(data_url):
    try:
        header, encoded = data_url.split(',', 1)
        decoded = base64.b64decode(encoded)
    except Exception:
        return None
    if PIL_OK:
        image = Image.open(io.BytesIO(decoded)).convert('RGB')
        return np.array(image)
    if CV2_OK:
        raw_bytes = np.frombuffer(decoded, np.uint8)
        img = cv2.imdecode(raw_bytes, cv2.IMREAD_COLOR)
        if img is None: return None
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return None

def extract_face_from_image(image_rgb):
    if face_recognition:
        face_locations = face_recognition.face_locations(image_rgb)
        if len(face_locations) == 0: return None
        return face_recognition.face_encodings(image_rgb, known_face_locations=face_locations)[0]
    if CV2_OK and face_cascade is not None:
        gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        if len(faces) == 0: return None
        x, y, w, h = faces[0]
        face_crop = image_rgb[y:y+h, x:x+w]
        return cv2.resize(face_crop, (128, 128))
    return None

def compare_face_data(ref_data, candidate_data):
    if ref_data is None or candidate_data is None: return False
    if face_recognition and isinstance(ref_data, np.ndarray) and ref_data.size == 128:
        try:
            matches = face_recognition.compare_faces([ref_data], candidate_data, tolerance=0.5)
            return matches[0] if matches else False
        except Exception:
            pass
    if CV2_OK:
        try:
            ref_gray = cv2.cvtColor(ref_data, cv2.COLOR_RGB2GRAY)
            cand_gray = cv2.cvtColor(candidate_data, cv2.COLOR_RGB2GRAY)
            orb = cv2.ORB_create()
            kp1, des1 = orb.detectAndCompute(ref_gray, None)
            kp2, des2 = orb.detectAndCompute(cand_gray, None)
            if des1 is not None and des2 is not None and len(des1) > 0 and len(des2) > 0:
                bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                matches = bf.match(des1, des2)
                if len([m for m in matches if m.distance < 60]) >= 10: return True
            ref_small = cv2.resize(ref_gray, (64, 64))
            cand_small = cv2.resize(cand_gray, (64, 64))
            mse = np.mean((ref_small.astype('float') - cand_small.astype('float')) ** 2)
            return mse < 2500
        except Exception:
            return False
    return False

def load_face_database():
    global face_database
    try:
        if FACE_DB_PATH.exists():
            with open(FACE_DB_PATH, 'rb') as f:
                face_database = pickle.load(f)
        else:
            face_database = {}
    except Exception:
        face_database = {}

def save_face_database():
    try:
        with open(FACE_DB_PATH, 'wb') as f:
            pickle.dump(face_database, f)
    except Exception as e:
        print(f"Warning: gagal save face database: {e}")

def match_face_in_database(candidate_data, tolerance=0.6):
    if candidate_data is None or len(face_database) == 0: return None
    for name, ref_data in face_database.items():
        if face_recognition and isinstance(ref_data, np.ndarray) and ref_data.size == 128:
            try:
                distances = face_recognition.face_distance([ref_data], candidate_data)
                if len(distances) > 0 and distances[0] <= tolerance:
                    return {'name': name, 'distance': float(distances[0])}
            except Exception:
                pass
        if compare_face_data(ref_data, candidate_data):
            return {'name': name, 'distance': None}
    return None

load_face_database()

# ── Attendance (absensi) — gaya Face-main ─────────────────────────────────────
ATTENDANCE_PATH = Path(__file__).parent / 'attendance_log.json'
attendance_records = []
_attendance_lock = threading.Lock()
_scan_state = {'cnt': 0, 'just_scanned': False, 'pause_cnt': 0, 'matched_name': None}
_camera_lock = threading.Lock()
_active_camera = None


def load_attendance_log():
    global attendance_records
    try:
        if ATTENDANCE_PATH.exists():
            with open(ATTENDANCE_PATH, 'r', encoding='utf-8') as f:
                attendance_records = json.load(f)
        else:
            attendance_records = []
    except Exception:
        attendance_records = []


def save_attendance_log():
    try:
        with open(ATTENDANCE_PATH, 'w', encoding='utf-8') as f:
            json.dump(attendance_records, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: gagal save attendance: {e}")


def append_attendance(name, role='Kandidat'):
    with _attendance_lock:
        next_id = max([r.get('id', 0) for r in attendance_records], default=0) + 1
        record = {
            'id': next_id,
            'person_id': name,
            'name': name,
            'role': role,
            'date': date.today().isoformat(),
            'time': datetime.now().strftime('%H:%M:%S'),
        }
        attendance_records.append(record)
        save_attendance_log()
        return record


load_attendance_log()


def _encode_face_from_region(image_bgr, x, y, w, h):
    if image_bgr is None or w <= 0 or h <= 0:
        return None
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB) if CV2_OK else image_bgr
    if face_recognition:
        try:
            loc = [(y, x + w, y + h, x)]
            encodings = face_recognition.face_encodings(rgb, known_face_locations=loc)
            if encodings:
                return encodings[0]
        except Exception:
            pass
    if CV2_OK:
        crop = rgb[y:y + h, x:x + w]
        if crop.size:
            return cv2.resize(crop, (128, 128))
    return None


def generate_attendance_frames():
    global _scan_state, _active_camera
    if not CV2_OK or face_cascade is None:
        return

    cap = None
    with _camera_lock:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            cap = None
            return
        _active_camera = cap
        cap.set(3, 640)
        cap.set(4, 480)

    try:
        while True:
            ret, img = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=10, minSize=(80, 80))
            _scan_state['pause_cnt'] += 1

            if len(face_database) == 0:
                cv2.putText(img, 'Database wajah kosong - daftar wajah dulu', (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 165, 255), 2, cv2.LINE_AA)

            for (x, y, w, h) in faces:
                cv2.rectangle(img, (x, y), (x + w, y + h), (255, 255, 0), 2)
                capture_data = _encode_face_from_region(img, x, y, w, h)
                match_result = match_face_in_database(capture_data, tolerance=0.55) if capture_data is not None else None

                if match_result and not _scan_state['just_scanned']:
                    _scan_state['cnt'] += 1
                    pct = min(100, int((_scan_state['cnt'] / 30) * 100))
                    cv2.putText(img, f'{pct} %', (x + 12, y + h + 28), cv2.FONT_HERSHEY_SIMPLEX, 0.75,
                                (153, 255, 255), 2, cv2.LINE_AA)
                    bar_y = y + h + 40
                    cv2.rectangle(img, (x, bar_y), (x + w, bar_y + 10), (255, 255, 0), 2)
                    fill_w = int(( _scan_state['cnt'] / 30) * w)
                    cv2.rectangle(img, (x, bar_y), (x + fill_w, bar_y + 10), (153, 255, 255), cv2.FILLED)
                    cv2.putText(img, match_result['name'], (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75,
                                (153, 255, 255), 2, cv2.LINE_AA)

                    if _scan_state['cnt'] >= 30:
                        _scan_state['cnt'] = 0
                        append_attendance(match_result['name'])
                        cv2.putText(img, 'ABSEN OK', (x, y - 35), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                                    (0, 255, 128), 2, cv2.LINE_AA)
                        _scan_state['just_scanned'] = True
                        _scan_state['pause_cnt'] = 0
                        time.sleep(0.8)
                elif not _scan_state['just_scanned']:
                    _scan_state['cnt'] = 0
                    cv2.putText(img, 'UNKNOWN', (x, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.75,
                                (0, 0, 255), 2, cv2.LINE_AA)
                else:
                    if _scan_state['pause_cnt'] > 80:
                        _scan_state['just_scanned'] = False
                        _scan_state['cnt'] = 0

            ok, frame = cv2.imencode('.jpg', img)
            if not ok:
                continue
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame.tobytes() + b'\r\n\r\n')
    finally:
        with _camera_lock:
            if cap is not None:
                cap.release()
            _active_camera = None


@app.route('/video_feed')
def video_feed():
    if not CV2_OK:
        return jsonify({'success': False, 'message': 'OpenCV tidak tersedia.'}), 503
    return Response(generate_attendance_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/countTodayScan')
def count_today_scan():
    today = date.today().isoformat()
    with _attendance_lock:
        count = sum(1 for r in attendance_records if r.get('date') == today)
    return jsonify({'rowcount': count})


@app.route('/loadData', methods=['GET', 'POST'])
def load_attendance_data():
    today = date.today().isoformat()
    with _attendance_lock:
        rows = [r for r in attendance_records if r.get('date') == today]
    rows.sort(key=lambda r: r.get('id', 0), reverse=True)
    payload = [[r.get('id'), r.get('person_id'), r.get('name'), r.get('role', '-'), r.get('time')] for r in rows]
    return jsonify(response=payload)


# ══════════════════════════════════════════════════════════════════════════════
# ROUTES — Core
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/roles')
def get_roles():
    from ai_engine import AdvancedAIEngine
    ai_engine = AdvancedAIEngine()
    return jsonify(list(ai_engine.knowledge_base.keys()) + ['general'])

# ── Face recognition ──────────────────────────────────────────────────────────

@app.route('/upload_reference', methods=['POST'])
def upload_reference():
    session_id = request.form.get('sessionId', None)
    if 'reference_image' not in request.files:
        return jsonify({'success': False, 'message': 'File referensi tidak ada.'}), 400
    file = request.files['reference_image']
    if file.filename == '' or not session_id:
        return jsonify({'success': False, 'message': 'Data tidak lengkap.'}), 400
    try:
        image_np = load_image_from_file(file)
        if image_np is None:
            return jsonify({'success': False, 'message': 'Gagal memproses gambar.'}), 400
        face_data = extract_face_from_image(image_np)
        if face_data is None:
            return jsonify({'success': False, 'message': 'Tidak terdeteksi wajah.'}), 400
        reference_encodings[session_id] = face_data
        return jsonify({'success': True, 'message': 'Referensi tersimpan.'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {e}'}), 500

@app.route('/verify_face', methods=['POST'])
def verify_face():
    data = request.get_json(force=True)
    session_id = data.get('sessionId', None)
    if not session_id or session_id not in reference_encodings:
        return jsonify({'success': False, 'message': 'Upload foto referensi dulu.'}), 400
    image_data = data.get('captured_image')
    if not image_data:
        return jsonify({'success': False, 'message': 'Data gambar tidak ditemukan.'}), 400
    try:
        image_np = load_image_from_dataurl(image_data)
        if image_np is None:
            return jsonify({'success': False, 'message': 'Gagal memproses gambar.'}), 400
        capture_data = extract_face_from_image(image_np)
        if capture_data is None:
            return jsonify({'success': False, 'match': False, 'message': 'Tidak terdeteksi wajah.'})
        match = compare_face_data(reference_encodings[session_id], capture_data)
        if match:
            return jsonify({'success': True, 'match': True, 'message': 'Verifikasi sukses.'})
        else:
            return jsonify({'success': True, 'match': False, 'message': 'Wajah tidak cocok.'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {e}'}), 500

@app.route('/face_register', methods=['POST'])
def face_register():
    data = request.get_json(force=True)
    name = (data.get('name') or '').strip()
    image_data = data.get('captured_image')
    if not name or not image_data:
        return jsonify({'success': False, 'message': 'Nama dan gambar diperlukan.'}), 400
    image_np = load_image_from_dataurl(image_data)
    if image_np is None:
        return jsonify({'success': False, 'message': 'Gagal memproses gambar.'}), 400
    face_data = extract_face_from_image(image_np)
    if face_data is None:
        return jsonify({'success': False, 'message': 'Tidak terdeteksi wajah.'}), 400
    face_database[name] = face_data
    save_face_database()
    return jsonify({'success': True, 'message': f'Wajah {name} tersimpan.'})

@app.route('/verify_database', methods=['POST'])
def verify_database():
    data = request.get_json(force=True)
    image_data = data.get('captured_image')
    if not image_data:
        return jsonify({'success': False, 'message': 'Data gambar tidak ditemukan.'}), 400
    if len(face_database) == 0:
        return jsonify({'success': False, 'message': 'Database wajah kosong.'}), 400
    image_np = load_image_from_dataurl(image_data)
    if image_np is None:
        return jsonify({'success': False, 'message': 'Gagal memproses gambar.'}), 400
    capture_data = extract_face_from_image(image_np)
    if capture_data is None:
        return jsonify({'success': False, 'match': False, 'message': 'Tidak terdeteksi wajah.'})
    match_result = match_face_in_database(capture_data, tolerance=0.6)
    if match_result:
        return jsonify({'success': True, 'match': True, 'message': f"Wajah cocok dengan {match_result['name']}.", 'name': match_result['name'], 'distance': match_result['distance']})
    return jsonify({'success': True, 'match': False, 'message': 'Wajah tidak dikenali.'})

@app.route('/face_list', methods=['GET'])
def face_list():
    return jsonify({'success': True, 'faces': [{'name': name} for name in sorted(face_database.keys())]})

@app.route('/face_clear', methods=['POST'])
def face_clear():
    face_database.clear()
    save_face_database()
    try:
        if FACE_DB_PATH.exists():
            FACE_DB_PATH.unlink()
    except Exception:
        pass
    return jsonify({'success': True, 'message': 'Database wajah dihapus.'})

# ── CV Workflow ────────────────────────────────────────────────────────────────

@app.route('/api/upload-cv', methods=['POST'])
def upload_cv():
    try:
        data = request.get_json()
        cv_text = data.get('cvText', '')
        candidate_name = data.get('candidateName', 'Unknown')
        position = data.get('position', 'CV Screening')
        session_id = data.get('sessionId') or f'temp_{datetime.now().timestamp()}'
        if not cv_text or len(cv_text.strip()) < 50:
            return jsonify({'status': 'error', 'message': 'CV minimal 50 karakter'}), 400
        analyzer = CVAnalyzer()
        cv_analysis = analyzer.analyze_cv_text(cv_text)
        cv_analyses[session_id] = cv_analysis
        candidate_records[session_id] = {
            'candidateName': candidate_name, 'position': position,
            'cvAnalysis': cv_analysis, 'status': 'Screened', 'score': None,
            'completedInterview': False,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        return jsonify({'status': 'success', 'message': 'CV dianalisis', 'analysis': cv_analysis, 'sessionId': session_id}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error: {str(e)}'}), 500

@app.route('/api/analyze-cv', methods=['POST'])
def analyze_cv():
    try:
        data = request.get_json()
        session_id = data.get('sessionId')
        if session_id and session_id in cv_analyses:
            return jsonify({'status': 'success', 'analysis': cv_analyses[session_id]}), 200
        return jsonify({'status': 'error', 'message': 'Tidak ada CV analysis'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/recommended-jobs', methods=['POST'])
def recommended_jobs():
    try:
        data = request.get_json()
        session_id = data.get('sessionId')
        if not session_id or session_id not in cv_analyses:
            return jsonify({'status': 'error', 'message': 'Upload CV terlebih dahulu.'}), 400
        cv_analysis = cv_analyses[session_id]
        jobs = JobMatcher.get_recommended_jobs(cv_analysis, limit=5)
        return jsonify({'status': 'success', 'recommended_jobs': jobs, 'cv_summary': cv_analysis['summary']}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/get-jobs', methods=['GET'])
def get_jobs():
    try:
        jobs = JobDatabase.get_all_jobs()
        return jsonify({'status': 'success', 'jobs': jobs}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/job-details/<int:job_id>', methods=['GET'])
def job_details(job_id):
    try:
        jobs = JobDatabase.get_all_jobs()
        job = next((j for j in jobs if j['id'] == job_id), None)
        if job: return jsonify({'status': 'success', 'job': job}), 200
        return jsonify({'status': 'error', 'message': 'Job not found'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/hr-stats', methods=['GET'])
def hr_stats():
    try:
        all_candidates = list(candidate_records.values())
        unique_candidates = {}
        for c in all_candidates:
            name = c.get('candidateName') or 'Unknown'
            if name not in unique_candidates:
                unique_candidates[name] = c
            else:
                if c.get('completedInterview') and not unique_candidates[name].get('completedInterview'):
                    unique_candidates[name] = c
        filtered_candidates = list(unique_candidates.values())
        total_applicants = len(filtered_candidates)
        passed = sum(1 for c in filtered_candidates if c.get('status') in ['Lulus', 'pass', 'Passed'])
        failed = sum(1 for c in filtered_candidates if c.get('status') in ['Gagal', 'fail', 'Failed'])
        completed = sum(1 for c in filtered_candidates if c.get('completedInterview'))
        completed_scores = [
            safe_score(c.get('score', 0), 0.0)
            for c in filtered_candidates
            if c.get('completedInterview')
        ]
        total_score = sum(completed_scores)
        average_score = round(total_score / completed, 1) if completed > 0 else 0
        position_stats = {}
        for candidate in all_candidates:
            pos = candidate.get('position', 'Unknown') or 'Unknown'
            if pos not in position_stats:
                position_stats[pos] = {'total': 0, 'completed': 0, 'passed': 0, 'failed': 0}
            position_stats[pos]['total'] += 1
            if candidate.get('completedInterview'): position_stats[pos]['completed'] += 1
            if candidate.get('status') in ['Lulus', 'pass', 'Passed']: position_stats[pos]['passed'] += 1
            if candidate.get('status') in ['Gagal', 'fail', 'Failed']: position_stats[pos]['failed'] += 1
        return jsonify({
            'status': 'success', 'totalApplicants': total_applicants,
            'passedCandidates': passed, 'failedCandidates': failed,
            'completedInterviews': completed, 'averageScore': average_score,
            'positionStats': position_stats, 'candidates': filtered_candidates
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

def build_public_recruitment_report():
    unique_candidates = {}
    for candidate in candidate_records.values():
        name = candidate.get('candidateName') or 'Unknown'
        current = unique_candidates.get(name)
        if current is None or (
            candidate.get('completedInterview') and not current.get('completedInterview')
        ):
            unique_candidates[name] = candidate

    candidates = list(unique_candidates.values())
    report = {
        'generatedAt': datetime.now().astimezone().isoformat(timespec='seconds'),
        'totalApplicants': len(candidates),
        'cvScreened': sum(1 for c in candidates if c.get('cvAnalysis') is not None),
        'interviewsStarted': sum(
            1 for c in candidates
            if c.get('status') in ('Interview started', 'Lulus', 'Gagal', 'pass', 'Passed', 'fail', 'Failed')
            or c.get('completedInterview')
        ),
        'interviewsCompleted': sum(1 for c in candidates if c.get('completedInterview')),
        'passedCandidates': sum(
            1 for c in candidates if c.get('status') in ('Lulus', 'pass', 'Passed')
        ),
        'failedCandidates': sum(
            1 for c in candidates if c.get('status') in ('Gagal', 'fail', 'Failed')
        ),
        'averageScore': 0.0,
        'interviewCompletionRate': 0.0,
        'passRate': 0.0,
        'positionStats': {}
    }

    completed_scores = [
        safe_score(c.get('score'), 0.0)
        for c in candidates if c.get('completedInterview')
    ]
    if completed_scores:
        report['averageScore'] = round(sum(completed_scores) / len(completed_scores), 1)
    if report['interviewsStarted']:
        report['interviewCompletionRate'] = round(
            report['interviewsCompleted'] / report['interviewsStarted'] * 100, 1
        )
    if report['interviewsCompleted']:
        report['passRate'] = round(
            report['passedCandidates'] / report['interviewsCompleted'] * 100, 1
        )

    for candidate in candidates:
        position = candidate.get('position') or 'Tidak ditentukan'
        stats = report['positionStats'].setdefault(position, {
            'total': 0, 'screened': 0, 'interviewsStarted': 0,
            'completed': 0, 'passed': 0, 'failed': 0
        })
        stats['total'] += 1
        stats['screened'] += int(candidate.get('cvAnalysis') is not None)
        started = (
            candidate.get('status') == 'Interview started'
            or candidate.get('completedInterview')
            or candidate.get('status') in ('Lulus', 'Gagal', 'pass', 'Passed', 'fail', 'Failed')
        )
        stats['interviewsStarted'] += int(started)
        stats['completed'] += int(bool(candidate.get('completedInterview')))
        stats['passed'] += int(candidate.get('status') in ('Lulus', 'pass', 'Passed'))
        stats['failed'] += int(candidate.get('status') in ('Gagal', 'fail', 'Failed'))

    for stats in report['positionStats'].values():
        stats['completionRate'] = round(
            stats['completed'] / stats['interviewsStarted'] * 100, 1
        ) if stats['interviewsStarted'] else 0.0
        stats['passRate'] = round(
            stats['passed'] / stats['completed'] * 100, 1
        ) if stats['completed'] else 0.0

    return report


@app.route('/recruitment-report', methods=['GET'])
def public_recruitment_report():
    return render_template('recruitment_report.html')


@app.route('/api/public/recruitment-report', methods=['GET'])
def public_recruitment_report_data():
    try:
        return jsonify(build_public_recruitment_report()), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/public/recruitment-report.csv', methods=['GET'])
def public_recruitment_report_csv():
    try:
        report = build_public_recruitment_report()
        output = io.StringIO(newline='')
        writer = csv.writer(output)
        writer.writerow(['Metrik', 'Nilai'])
        writer.writerow(['Diperbarui', report['generatedAt']])
        writer.writerow(['Total pelamar unik', report['totalApplicants']])
        writer.writerow(['CV dianalisis', report['cvScreened']])
        writer.writerow(['Interview dimulai', report['interviewsStarted']])
        writer.writerow(['Interview selesai', report['interviewsCompleted']])
        writer.writerow(['Kandidat lolos', report['passedCandidates']])
        writer.writerow(['Kandidat belum lolos', report['failedCandidates']])
        writer.writerow(['Skor rata-rata interview', report['averageScore']])
        writer.writerow(['Penyelesaian interview (%)', report['interviewCompletionRate']])
        writer.writerow(['Kelulusan dari interview selesai (%)', report['passRate']])
        writer.writerow([])
        writer.writerow([
            'Posisi', 'Total pelamar', 'CV dianalisis', 'Interview dimulai',
            'Interview selesai', 'Lolos', 'Belum lolos',
            'Penyelesaian interview (%)', 'Kelulusan (%)'
        ])
        for position, stats in sorted(report['positionStats'].items()):
            csv_position = str(position)
            if csv_position.lstrip().startswith(('=', '+', '-', '@', '\t', '\r')):
                csv_position = "'" + csv_position
            writer.writerow([
                csv_position, stats['total'], stats['screened'], stats['interviewsStarted'],
                stats['completed'], stats['passed'], stats['failed'],
                stats['completionRate'], stats['passRate']
            ])
        response = Response('\ufeff' + output.getvalue(), content_type='text/csv; charset=utf-8')
        response.headers['Content-Disposition'] = 'attachment; filename=laporan-rekrutmen-inklusif.csv'
        return response
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/hr-reset', methods=['POST'])
def hr_reset():
    candidate_records.clear()
    cv_analyses.clear()
    interview_sessions.clear()
    return jsonify({'status': 'success', 'message': 'HR data reset'}), 200

@app.route('/api/custom-questions', methods=['GET'])
def get_custom_questions():
    return jsonify({'status': 'success', 'custom_questions': custom_questions}), 200

@app.route('/api/custom-questions', methods=['POST'])
def set_custom_questions():
    try:
        data = request.get_json()
        role = data.get('role')
        questions = data.get('questions', [])
        if role not in custom_questions:
            return jsonify({'status': 'error', 'message': 'Invalid role'}), 400
        if len(questions) > 10:
            return jsonify({'status': 'error', 'message': 'Maksimal 10 pertanyaan'}), 400
        custom_questions[role] = questions
        save_custom_questions()
        return jsonify({'status': 'success', 'message': f'Custom questions {role} updated'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ══════════════════════════════════════════════════════════════════════════════
# ROUTES — SIBI Recognition
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/sibi/status', methods=['GET'])
def sibi_status():
    if not SIBI_OK:
        return jsonify({"ready": False, "message": "SIBI module tidak tersedia. Install: pip install mediapipe scikit-learn"}), 200
    recognizer = get_sibi_recognizer()
    return jsonify(recognizer.get_status()), 200

@app.route('/api/sibi/recognize', methods=['POST'])
def sibi_recognize():
    if not SIBI_OK:
        return jsonify({"status": "error", "message": "SIBI tidak tersedia"}), 200
    data = request.get_json(force=True)
    frame = data.get("frame")
    if not frame:
        return jsonify({"status": "error", "message": "Frame tidak ditemukan"}), 400
    recognizer = get_sibi_recognizer()
    result = recognizer.process_frame(frame)
    return jsonify(result), 200

@app.route('/api/sibi/reset', methods=['POST'])
def sibi_reset():
    if SIBI_OK:
        get_sibi_recognizer().reset_buffer()
    return jsonify({"status": "ok", "message": "Buffer SIBI direset"}), 200

# ══════════════════════════════════════════════════════════════════════════════
# ROUTES — Emotion Detection
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/emotion/status', methods=['GET'])
def emotion_status():
    if not EMOTION_OK or get_emotion_status is None:
        return jsonify({"ready": False, "backend": "none", "message": "Install: pip install deepface tf-keras opencv-python"}), 200
    return jsonify(get_emotion_status()), 200


@app.route('/api/emotion/analyze', methods=['POST'])
def emotion_analyze():
    if not EMOTION_OK:
        return jsonify({"status": "error", "message": "Emotion module tidak tersedia. Install: pip install deepface tf-keras"}), 200
    data = request.get_json(force=True)
    session_id = data.get("sessionId", request.remote_addr)
    frame = data.get("frame")
    if not frame:
        return jsonify({"status": "error", "message": "Frame tidak ditemukan"}), 400
    detector = get_emotion_detector(session_id)
    result = detector.analyze_frame(frame)
    return jsonify(result), 200

@app.route('/api/emotion/report/<session_id>', methods=['GET'])
def emotion_report(session_id):
    if not EMOTION_OK:
        return jsonify({"total_samples": 0, "dominant_overall": "neutral", "emotion_distribution": {}, "negative_ratio": 0, "recommendation": "Emotion module tidak tersedia."}), 200
    detector = get_emotion_detector(session_id)
    report = detector.get_session_report()
    return jsonify(report), 200

# ══════════════════════════════════════════════════════════════════════════════
# ROUTES — Anti-Cheat
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/anticheat/status', methods=['GET'])
def anticheat_status_route():
    if not ANTICHEAT_OK or get_anticheat_status is None:
        return jsonify({"ready": False, "backend": "none", "message": "Install: pip install mediapipe opencv-python"}), 200
    return jsonify(get_anticheat_status()), 200


@app.route('/api/anticheat/frame', methods=['POST'])
def anticheat_frame():
    if not ANTICHEAT_OK:
        return jsonify({"violations_this_frame": [], "risk_score": 0, "total_violations": 0, "details": {}}), 200
    data = request.get_json(force=True)
    session_id = data.get("sessionId", request.remote_addr)
    frame = data.get("frame")
    if not frame:
        return jsonify({"violations_this_frame": [], "risk_score": 0}), 200
    monitor = get_monitor(session_id)
    result = monitor.check_frame(frame)
    return jsonify(result), 200

@app.route('/api/anticheat/event', methods=['POST'])
def anticheat_event():
    if not ANTICHEAT_OK:
        return jsonify({"status": "ok"}), 200
    data = request.get_json(force=True)
    session_id = data.get("sessionId", request.remote_addr)
    event_type = data.get("event")
    event_data = data.get("data", {})
    monitor = get_monitor(session_id)
    if event_type == "tab_switch":
        monitor.record_tab_switch()
    elif event_type == "copy_paste":
        monitor.record_copy_paste(event_data.get("pasted_length", 0))
    elif event_type == "question_start":
        monitor.record_question_start(event_data.get("question_id", "q0"))
    return jsonify({"status": "recorded"}), 200

@app.route('/api/anticheat/check-text', methods=['POST'])
def anticheat_check_text():
    data = request.get_json(force=True)
    session_id = data.get("sessionId", request.remote_addr)
    text = data.get("text", "")
    question_id = data.get("questionId", "")
    if not ANTICHEAT_OK:
        return jsonify({"speed_suspicious": False, "ai_detection": {"is_likely_ai": False, "confidence": 0, "signals": []}, "risk_score": 0}), 200
    monitor = get_monitor(session_id)
    speed_suspicious = monitor.check_answer_speed(question_id, text) if question_id else False
    ai_result = monitor.analyze_text_for_ai(text)
    return jsonify({"speed_suspicious": speed_suspicious, "ai_detection": ai_result, "risk_score": monitor.risk_score}), 200

@app.route('/api/anticheat/report/<session_id>', methods=['GET'])
def anticheat_report(session_id):
    if not ANTICHEAT_OK:
        return jsonify({"risk_level": "low", "risk_score": 0, "total_violations": 0, "violations_summary": {}, "recommendation": "Anti-cheat module tidak tersedia."}), 200
    monitor = get_monitor(session_id)
    report = monitor.get_cheat_report()
    return jsonify(report), 200

# ══════════════════════════════════════════════════════════════════════════════
# ROUTES — Portfolio Analyzer (CV Screening only)
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/api/portfolio/analyze', methods=['POST'])
def portfolio_analyze():
    if not PORTFOLIO_OK:
        return jsonify({"status": "error", "message": "Portfolio module tidak tersedia."}), 200
    data = request.get_json(force=True)
    session_id = data.get("sessionId", request.remote_addr)
    github_url = data.get("github_url")
    linkedin_data = data.get("linkedin_data")
    target_role = data.get("target_role", "software-developer")
    if not github_url and not linkedin_data:
        return jsonify({"status": "error", "message": "Setidaknya github_url atau linkedin_data harus diisi."}), 400
    try:
        analyzer = PortfolioAnalyzer()
        result = analyzer.analyze(github_url=github_url, linkedin_data=linkedin_data, target_role=target_role)
        if session_id in candidate_records:
            candidate_records[session_id]["portfolio_score"] = result.get("overall_score")
            candidate_records[session_id]["portfolio_analyzed"] = True
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error: {str(e)}"}), 500

@app.route('/api/portfolio/github-only', methods=['POST'])
def portfolio_github_only():
    if not PORTFOLIO_OK:
        return jsonify({"status": "error", "message": "Portfolio module tidak tersedia."}), 200
    data = request.get_json(force=True)
    github_url = data.get("github_url")
    if not github_url:
        return jsonify({"status": "error", "message": "github_url diperlukan"}), 400
    try:
        from portfolio_analyzer import GitHubAnalyzer
        analyzer = GitHubAnalyzer()
        result = analyzer.analyze(github_url)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ══════════════════════════════════════════════════════════════════════════════
# Socket.IO
# ══════════════════════════════════════════════════════════════════════════════

def determine_role_from_job(job_title, default_role='general'):
    job_title_lower = job_title.lower()
    if 'developer' in job_title_lower or 'engineer' in job_title_lower:
        return 'software-developer'
    elif 'data scientist' in job_title_lower or 'data' in job_title_lower:
        return 'data-scientist'
    elif 'product manager' in job_title_lower or 'product' in job_title_lower:
        return 'product-manager'
    return default_role

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')
    if request.sid in interview_sessions:
        del interview_sessions[request.sid]
    if request.sid in cv_analyses:
        del cv_analyses[request.sid]
    if EMOTION_OK:
        remove_emotion_detector(request.sid)
    if ANTICHEAT_OK:
        remove_monitor(request.sid)

@socketio.on('start-interview')
def handle_start_interview(data):
    role = data.get('role', 'general')
    candidate_name = data.get('candidateName', 'Candidate')
    job_id = data.get('jobId', None)
    external_session_id = data.get('sessionId')
    job_title = role
    if job_id:
        jobs = JobDatabase.get_all_jobs()
        job = next((j for j in jobs if j['id'] == job_id), None)
        if job:
            job_title = job['title']
            role = determine_role_from_job(job_title, role)
    interviewer = AIInterviewer(role, custom_questions)
    interview_sessions[request.sid] = {
        'interviewer': interviewer, 'candidateName': candidate_name,
        'jobId': job_id, 'jobTitle': job_title, 'role': role,
        'startTime': datetime.now(), 'status': 'active', 'sessionKey': None
    }
    if external_session_id and external_session_id in candidate_records:
        interview_sessions[request.sid]['sessionKey'] = external_session_id
        candidate_records[external_session_id]['position'] = job_title
        candidate_records[external_session_id]['status'] = 'Interview started'
        candidate_records[external_session_id]['updated_at'] = datetime.now().isoformat()
    else:
        existing_key = next((k for k, v in candidate_records.items() if v.get('candidateName') == candidate_name), None)
        if existing_key:
            interview_sessions[request.sid]['sessionKey'] = existing_key
            candidate_records[existing_key]['position'] = job_title
            candidate_records[existing_key]['status'] = 'Interview started'
        else:
            interview_sessions[request.sid]['sessionKey'] = None
            candidate_records[candidate_name] = {
                'candidateName': candidate_name, 'position': job_title,
                'cvAnalysis': None, 'status': 'Interview started',
                'score': None, 'completedInterview': False,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
    first_question = interviewer.get_next_question()
    emit('interview-started', {
        'message': f'Selamat datang {candidate_name}! Mari mulai interview untuk {job_title}.',
        'firstQuestion': first_question, 'jobTitle': job_title, 'role': role
    })

@socketio.on('submit-answer')
def handle_submit_answer(data):
    session = interview_sessions.get(request.sid)
    if not session:
        emit('error', {'message': 'Tidak ada sesi interview aktif.'})
        return
    answer = data.get('answer', '')
    question = data.get('question', '')
    if not answer or len(answer.strip()) < 10:
        emit('error', {'message': 'Jawaban terlalu pendek (minimal 10 karakter).'})
        return
    evaluation = session['interviewer'].evaluate_answer(answer, question)
    emit('answer-evaluated', evaluation)
    next_question = session['interviewer'].get_next_question()
    if next_question:
        emit('next-question', next_question)
    else:
        summary = session['interviewer'].get_interview_summary()
        session['status'] = 'completed'
        session['endTime'] = datetime.now()
        session['summary'] = summary
        session_key = session.get('sessionKey')
        if session_key and session_key in candidate_records:
            rec = candidate_records[session_key]
        else:
            rec = next((v for v in candidate_records.values() if v.get('candidateName') == session.get('candidateName')), None)
        if rec is None:
            rec = {
                'candidateName': session.get('candidateName', 'Unknown'),
                'position': session.get('jobTitle', 'Unknown'),
                'cvAnalysis': cv_analyses.get(request.sid),
                'status': 'Interview completed', 'completedInterview': True,
                'score': safe_score(summary.get('averageScore', 0), 0.0),
                'created_at': session.get('startTime').isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            candidate_records[session.get('candidateName')] = rec
        rec['completedInterview'] = True
        rec['score'] = safe_score(summary.get('averageScore', 0), 0.0)
        rec['status'] = 'Lulus' if rec['score'] >= 60 else 'Gagal'
        rec['position'] = session.get('jobTitle', rec.get('position', 'Unknown'))
        rec['updated_at'] = datetime.now().isoformat()
        emit('interview-completed', summary)

@socketio.on('request-feedback')
def handle_request_feedback():
    session = interview_sessions.get(request.sid)
    if session and session.get('status') == 'completed':
        emit('interview-feedback', session['summary'])

@socketio.on('emotion-frame')
def handle_emotion_frame(data):
    if not EMOTION_OK:
        return
    session_id = data.get("sessionId", request.sid)
    frame = data.get("frame")
    if not frame:
        return
    detector = get_emotion_detector(session_id)
    result = detector.analyze_frame(frame)
    emit("emotion-result", result)

if __name__ == '__main__':
    print("🚀 Starting AI Interview System Enhanced...")
    print("📱 Open http://127.0.0.1:8000 in your browser")
    print(f"🤟 SIBI Recognition: {'✅' if SIBI_OK else '❌ Install mediapipe scikit-learn'}")
    print(f"😊 Emotion Detection: {'✅' if EMOTION_OK else '❌ Install deepface tf-keras'}")
    print(f"🛡 Anti-Cheat: {'✅' if ANTICHEAT_OK else '❌ Install mediapipe'}")
    print(f"🔍 Portfolio Analyzer: {'✅' if PORTFOLIO_OK else '❌ Check portfolio_analyzer.py'}")
    socketio.run(app, host='127.0.0.1', port=8000, debug=True)
