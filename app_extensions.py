"""
app_extensions.py
=================
Potongan kode ini berisi semua ROUTE dan SOCKET EVENT baru yang perlu ditambahkan
ke app.py yang sudah ada. Salin isi file ini ke bagian bawah app.py (sebelum
blok `if __name__ == '__main__':`).

Juga tambahkan import berikut di bagian atas app.py:
    from sibi_recognition import get_sibi_recognizer
    from emotion_detector import get_emotion_detector, remove_emotion_detector
    from anti_cheat import get_monitor, remove_monitor
    from portfolio_analyzer import PortfolioAnalyzer
"""

# ─── IMPORT BARU (tambahkan di atas app.py) ───────────────────────────────────
# from sibi_recognition import get_sibi_recognizer
# from emotion_detector import get_emotion_detector, remove_emotion_detector
# from anti_cheat import get_monitor, remove_monitor
# from portfolio_analyzer import PortfolioAnalyzer

# ═══════════════════════════════════════════════════════════════════════════════
# BAGIAN 1: SIBI RECOGNITION ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

# @app.route('/api/sibi/status', methods=['GET'])
def sibi_status():
    """Cek apakah SIBI recognizer siap."""
    recognizer = get_sibi_recognizer()
    return jsonify(recognizer.get_status()), 200


# @app.route('/api/sibi/recognize', methods=['POST'])
def sibi_recognize():
    """
    Proses satu frame untuk pengenalan isyarat SIBI.

    Body JSON:
        { "frame": "data:image/jpeg;base64,..." }

    Response JSON:
        {
            "status": "prediction" | "collecting" | "no_hand" | "error",
            "prediction": "A" | "B" | ... | null,
            "confidence": 0.85,
            "buffer_size": 168,
            "message": "Isyarat terdeteksi: A"
        }
    """
    data = request.get_json(force=True)
    frame = data.get("frame")
    if not frame:
        return jsonify({"status": "error", "message": "Frame tidak ditemukan"}), 400

    recognizer = get_sibi_recognizer()
    result = recognizer.process_frame(frame)
    return jsonify(result), 200


# @app.route('/api/sibi/reset', methods=['POST'])
def sibi_reset():
    """Reset buffer keypoint SIBI."""
    get_sibi_recognizer().reset_buffer()
    return jsonify({"status": "ok", "message": "Buffer SIBI direset"}), 200


# ═══════════════════════════════════════════════════════════════════════════════
# BAGIAN 2: EMOTION DETECTION ROUTES & SOCKET EVENTS
# ═══════════════════════════════════════════════════════════════════════════════

# @app.route('/api/emotion/analyze', methods=['POST'])
def emotion_analyze():
    """
    Analisis emosi dari satu frame.

    Body JSON:
        {
            "sessionId": "abc123",
            "frame": "data:image/jpeg;base64,..."
        }

    Response JSON:
        {
            "status": "success",
            "dominant_emotion": "happy",
            "emotion_scores": {"happy": 85.3, "neutral": 10.1, ...},
            "emoji": "😊",
            "is_negative": false
        }
    """
    data = request.get_json(force=True)
    session_id = data.get("sessionId", request.remote_addr)
    frame = data.get("frame")

    if not frame:
        return jsonify({"status": "error", "message": "Frame tidak ditemukan"}), 400

    detector = get_emotion_detector(session_id)
    result = detector.analyze_frame(frame)
    return jsonify(result), 200


# @app.route('/api/emotion/report/<session_id>', methods=['GET'])
def emotion_report(session_id):
    """
    Ambil laporan emosi sesi interview.

    Response JSON:
        {
            "total_samples": 42,
            "dominant_overall": "neutral",
            "emotion_distribution": {"neutral": 60.0, "happy": 25.0, ...},
            "negative_ratio": 0.05,
            "recommendation": "Kandidat tampil profesional..."
        }
    """
    detector = get_emotion_detector(session_id)
    report = detector.get_session_report()
    return jsonify(report), 200


# Socket.IO — emit emosi real-time ke HR dashboard
# Tambahkan handler ini ke bagian Socket.IO di app.py:

# @socketio.on('emotion-frame')
def handle_emotion_frame(data):
    """
    Terima frame dari kandidat, analisis emosi, emit hasil ke room HR.

    Data:
        { "sessionId": str, "frame": str (base64) }
    """
    session_id = data.get("sessionId", request.sid)
    frame = data.get("frame")

    if not frame:
        return

    detector = get_emotion_detector(session_id)
    result = detector.analyze_frame(frame)

    # Emit ke klien yang mengirim (kandidat)
    emit("emotion-result", result)

    # Opsional: broadcast ke room HR (jika ada HR monitoring dashboard)
    # emit("hr-emotion-update", {"sessionId": session_id, **result}, room="hr-room")


# ═══════════════════════════════════════════════════════════════════════════════
# BAGIAN 3: ANTI-CHEAT ROUTES & SOCKET EVENTS
# ═══════════════════════════════════════════════════════════════════════════════

# @app.route('/api/anticheat/frame', methods=['POST'])
def anticheat_frame():
    """
    Analisis frame untuk pelanggaran (multi-face, gaze, dll).

    Body JSON:
        {
            "sessionId": "abc123",
            "frame": "data:image/jpeg;base64,..."
        }
    """
    data = request.get_json(force=True)
    session_id = data.get("sessionId", request.remote_addr)
    frame = data.get("frame")

    if not frame:
        return jsonify({"violations_this_frame": [], "risk_score": 0}), 200

    monitor = get_monitor(session_id)
    result = monitor.check_frame(frame)
    return jsonify(result), 200


# @app.route('/api/anticheat/event', methods=['POST'])
def anticheat_event():
    """
    Catat event pelanggaran dari frontend (tab switch, copy-paste, dll).

    Body JSON:
        {
            "sessionId": "abc123",
            "event": "tab_switch" | "copy_paste",
            "data": { "pasted_length": 120 }   // opsional
        }
    """
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


# @app.route('/api/anticheat/check-text', methods=['POST'])
def anticheat_check_text():
    """
    Deteksi apakah teks jawaban kemungkinan dibuat oleh AI.

    Body JSON:
        {
            "sessionId": "abc123",
            "text": "jawaban kandidat...",
            "questionId": "q3"
        }
    """
    data = request.get_json(force=True)
    session_id = data.get("sessionId", request.remote_addr)
    text = data.get("text", "")
    question_id = data.get("questionId", "")

    monitor = get_monitor(session_id)

    # Cek kecepatan jawaban
    speed_suspicious = monitor.check_answer_speed(question_id, text) if question_id else False

    # Cek AI text
    ai_result = monitor.analyze_text_for_ai(text)

    return jsonify({
        "speed_suspicious": speed_suspicious,
        "ai_detection": ai_result,
        "risk_score": monitor.risk_score
    }), 200


# @app.route('/api/anticheat/report/<session_id>', methods=['GET'])
def anticheat_report(session_id):
    """
    Ambil laporan anti-cheat sesi interview.

    Response JSON:
        {
            "risk_level": "low" | "medium" | "high" | "critical",
            "risk_score": 25,
            "violations_summary": {"tab_switch": 2, "copy_paste": 0, ...},
            "recommendation": "..."
        }
    """
    monitor = get_monitor(session_id)
    report = monitor.get_cheat_report()
    return jsonify(report), 200


# ═══════════════════════════════════════════════════════════════════════════════
# BAGIAN 4: PORTFOLIO ANALYZER ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

# @app.route('/api/portfolio/analyze', methods=['POST'])
def portfolio_analyze():
    """
    Analisis profil GitHub dan/atau LinkedIn kandidat.

    Body JSON:
        {
            "sessionId": "abc123",
            "github_url": "https://github.com/username",  // opsional
            "linkedin_data": {                             // opsional
                "url": "https://linkedin.com/in/username",
                "name": "John Doe",
                "headline": "Senior Software Engineer",
                "connections": 500,
                "experience": [
                    {"title": "SWE", "company": "Google", "duration_years": 3}
                ],
                "education": [
                    {"degree": "S1 Informatika", "school": "UI"}
                ],
                "skills": ["Python", "Go", "Kubernetes"],
                "certifications": ["AWS Solutions Architect"],
                "recommendations": 8
            },
            "target_role": "software-developer"
        }

    Response JSON:
        {
            "status": "success",
            "overall_score": 78,
            "github": { ... },
            "linkedin": { ... },
            "all_insights": ["Akun GitHub 5 tahun", "..."],
            "recommendation": "✅ Kandidat LAYAK..."
        }
    """
    data = request.get_json(force=True)
    session_id = data.get("sessionId", request.remote_addr)
    github_url = data.get("github_url")
    linkedin_data = data.get("linkedin_data")
    target_role = data.get("target_role", "software-developer")

    if not github_url and not linkedin_data:
        return jsonify({
            "status": "error",
            "message": "Setidaknya satu dari github_url atau linkedin_data harus disertakan."
        }), 400

    try:
        analyzer = PortfolioAnalyzer()
        result = analyzer.analyze(
            github_url=github_url,
            linkedin_data=linkedin_data,
            target_role=target_role
        )

        # Simpan ke candidate_records jika sesi ada
        if session_id in candidate_records:
            candidate_records[session_id]["portfolio_score"] = result.get("overall_score")
            candidate_records[session_id]["portfolio_analyzed"] = True

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error menganalisis portfolio: {str(e)}"
        }), 500


# @app.route('/api/portfolio/github-only', methods=['POST'])
def portfolio_github_only():
    """
    Shortcut: analisis GitHub saja (lebih cepat).

    Body JSON:
        { "github_url": "https://github.com/username" }
    """
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


# ═══════════════════════════════════════════════════════════════════════════════
# BAGIAN 5: CLEANUP — tambahkan ke handle_disconnect yang sudah ada
# ═══════════════════════════════════════════════════════════════════════════════

# Di dalam @socketio.on('disconnect') yang sudah ada, tambahkan:
#
#   remove_emotion_detector(request.sid)
#   remove_monitor(request.sid)
#
# Contoh full handler baru:
#
# @socketio.on('disconnect')
# def handle_disconnect():
#     print(f'Client disconnected: {request.sid}')
#     if request.sid in interview_sessions:
#         del interview_sessions[request.sid]
#     if request.sid in cv_analyses:
#         del cv_analyses[request.sid]
#     remove_emotion_detector(request.sid)   # ← TAMBAHKAN INI
#     remove_monitor(request.sid)            # ← TAMBAHKAN INI


# ═══════════════════════════════════════════════════════════════════════════════
# BAGIAN 6: REGISTRASI ROUTE — tambahkan ke app.py setelah import
# ═══════════════════════════════════════════════════════════════════════════════

def register_extension_routes(app_instance):
    """
    Daftarkan semua route extension ke Flask app.
    Panggil dari app.py setelah app = Flask(__name__):

        from app_extensions import register_extension_routes
        register_extension_routes(app)
    """
    app_instance.add_url_rule('/api/sibi/status',       'sibi_status',          sibi_status,          methods=['GET'])
    app_instance.add_url_rule('/api/sibi/recognize',    'sibi_recognize',       sibi_recognize,       methods=['POST'])
    app_instance.add_url_rule('/api/sibi/reset',        'sibi_reset',           sibi_reset,           methods=['POST'])

    app_instance.add_url_rule('/api/emotion/analyze',   'emotion_analyze',      emotion_analyze,      methods=['POST'])
    app_instance.add_url_rule('/api/emotion/report/<session_id>', 'emotion_report', emotion_report,   methods=['GET'])

    app_instance.add_url_rule('/api/anticheat/frame',   'anticheat_frame',      anticheat_frame,      methods=['POST'])
    app_instance.add_url_rule('/api/anticheat/event',   'anticheat_event',      anticheat_event,      methods=['POST'])
    app_instance.add_url_rule('/api/anticheat/check-text', 'anticheat_check_text', anticheat_check_text, methods=['POST'])
    app_instance.add_url_rule('/api/anticheat/report/<session_id>', 'anticheat_report', anticheat_report, methods=['GET'])

    app_instance.add_url_rule('/api/portfolio/analyze', 'portfolio_analyze',    portfolio_analyze,    methods=['POST'])
    app_instance.add_url_rule('/api/portfolio/github-only', 'portfolio_github_only', portfolio_github_only, methods=['POST'])

    print("[Extensions] ✅ Semua route extension terdaftar.")
