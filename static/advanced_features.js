/**
 * advanced_features.js — SIBI, Emotion Detection, Anti-Cheat, Portfolio
 */
'use strict';

let _currentSessionId = null;
let _currentRole = 'general';
let _sibiEnabled = false;
let _sibiTimer = null;
let _sibiBuffer = '';
let _sibiPrev = null;
let _sibiSameCount = 0;
let _emotionTimer = null;
let _anticheatFrameTimer = null;
let _blurStart = null;
let _questionStartTimes = {};
let _currentQuestionId = null;
let _anticheatRiskScore = 0;
let _interviewActive = false;
let _portfolioAnalyzing = false;
let _emotionReady = false;
let _anticheatReady = false;
let _lastAlertKey = '';
let _lastAlertTs = 0;

// Event handler refs (for cleanup)
let _onBlurHandler = null;
let _onFocusHandler = null;
let _onVisibilityHandler = null;
let _onPasteHandler = null;

// ═══════════════════════════════════════════════════════════════════════════════
// UTILITY
// ═══════════════════════════════════════════════════════════════════════════════

function getVideoEl() {
  return document.getElementById('webcam-video');
}

function isWebcamActive() {
  const video = getVideoEl();
  if (!video) return false;
  const stream = video.srcObject;
  const hasTrack = stream && stream.getVideoTracks().some(t => t.readyState === 'live');
  return hasTrack && video.videoWidth > 0 && video.videoHeight > 0;
}

function captureFrame(quality = 0.65) {
  const video = getVideoEl();
  if (!video || !isWebcamActive()) return null;
  const canvas = document.createElement('canvas');
  const w = video.videoWidth || 640;
  const h = video.videoHeight || 480;
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(video, 0, 0, w, h);
  return canvas.toDataURL('image/jpeg', quality);
}

async function postJSON(url, body) {
  try {
    const resp = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!resp.ok) return null;
    return await resp.json();
  } catch (e) {
    console.debug('[Advanced]', url, e.message);
    return null;
  }
}

function showAntiCheatAlert(msg, type = 'warning') {
  const key = `${type}:${msg}`;
  const now = Date.now();
  if (key === _lastAlertKey && now - _lastAlertTs < 4000) return;
  _lastAlertKey = key;
  _lastAlertTs = now;

  const el = document.getElementById('anticheat-alert');
  if (!el) return;
  el.textContent = msg;
  el.style.background = type === 'danger' ? '#fef2f2' : '#fffbeb';
  el.style.borderColor = type === 'danger' ? '#ef4444' : '#f59e0b';
  el.style.color = type === 'danger' ? '#991b1b' : '#92400e';
  el.style.display = 'block';
  clearTimeout(el._timer);
  el._timer = setTimeout(() => { el.style.display = 'none'; }, 5000);
}

async function ensureWebcamForMonitoring() {
  if (isWebcamActive()) return true;
  const btn = document.getElementById('webcam-toggle-btn');
  if (btn && !isWebcamActive()) btn.click();
  for (let i = 0; i < 20; i++) {
    await new Promise(r => setTimeout(r, 250));
    if (isWebcamActive()) return true;
  }
  return isWebcamActive();
}

function updateMonitoringStatus() {
  const statusEl = document.getElementById('webcam-status');
  if (!statusEl || !_interviewActive) return;
  const parts = [];
  if (_emotionReady) parts.push('😊 Emosi aktif');
  if (_anticheatReady) parts.push('🛡 Anti-cheat aktif');
  if (!isWebcamActive()) {
    statusEl.innerHTML = '<span class="text-amber-600 font-semibold">⚠️ Aktifkan webcam untuk monitoring emosi & anti-cheat</span>';
    return;
  }
  if (parts.length) {
    statusEl.innerHTML = `<span class="text-green-600 font-semibold">🟢 ${parts.join(' · ')}</span>`;
  }
}

function _backendLabel(status) {
  if (!status.ready) return 'Tidak tersedia';
  if (status.backend === 'deepface') return 'DeepFace';
  if (status.backend === 'tasks' || status.backend === 'legacy') return 'MediaPipe';
  if (status.opencv_fallback) return 'OpenCV';
  return status.backend || 'Aktif';
}

function _updateModuleBadges(emo, ac) {
  const emoLabel = document.getElementById('emotion-module-label');
  const acLabel = document.getElementById('anticheat-module-label');
  if (emoLabel) {
    emoLabel.textContent = emo.ready
      ? `Emosi: ${_backendLabel(emo)}`
      : 'Emosi: tidak tersedia';
  }
  if (acLabel) {
    acLabel.textContent = ac.ready
      ? `Anti-Cheat: ${_backendLabel(ac)}`
      : 'Anti-Cheat: tidak tersedia';
  }
}

async function checkModuleStatus() {
  try {
    const [emo, ac] = await Promise.all([
      fetch('/api/emotion/status').then(r => r.json()).catch(() => ({ ready: false })),
      fetch('/api/anticheat/status').then(r => r.json()).catch(() => ({ ready: false })),
    ]);
    _emotionReady = !!emo.ready;
    _anticheatReady = !!ac.ready;
    _updateModuleBadges(emo, ac);
  } catch (e) {
    console.debug('[Advanced] status check failed', e);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// SIBI (unchanged core)
// ═══════════════════════════════════════════════════════════════════════════════

function toggleSIBI(enabled) {
  _sibiEnabled = enabled;
  if (enabled) _startSIBI();
  else _stopSIBI();
}

function _startSIBI() {
  if (_sibiTimer) clearInterval(_sibiTimer);
  _sibiTimer = setInterval(_sendSIBIFrame, 200);
  const display = document.getElementById('sibi-display');
  if (display) display.innerHTML = '<span class="text-blue-400 text-xs">✋ Menunggu tangan...</span>';
}

function _stopSIBI() {
  clearInterval(_sibiTimer);
  _sibiTimer = null;
  fetch('/api/sibi/reset', { method: 'POST' }).catch(() => {});
}

async function _sendSIBIFrame() {
  if (!_sibiEnabled) return;
  const frame = captureFrame(0.55);
  if (!frame) return;
  const result = await postJSON('/api/sibi/recognize', { frame });
  if (result) _handleSIBIResult(result);
}

function _handleSIBIResult(result) {
  const display = document.getElementById('sibi-display');
  if (!display) return;
  if (result.status === 'prediction' && result.prediction) {
    const label = result.prediction;
    const conf = result.confidence ? (result.confidence * 100).toFixed(0) : '?';
    if (label === _sibiPrev) {
      _sibiSameCount++;
      if (_sibiSameCount === 3) _sibiBuffer += label + ' ';
    } else {
      _sibiSameCount = 0;
    }
    _sibiPrev = label;
    display.innerHTML = `<div><span class="sibi-label">${label}</span><span style="color:#94a3b8;font-size:.8em;margin-left:6px">${conf}%</span></div><div class="sibi-sentence">${_sibiBuffer}</div>`;
  } else if (result.status === 'collecting') {
    display.innerHTML = `<span style="color:#94a3b8;font-size:.8em">✋ ${result.message || 'Mengumpulkan...'}</span>`;
  } else if (result.status === 'no_hand') {
    display.innerHTML = '<span style="color:#64748b;font-size:.8em">Arahkan tangan ke kamera...</span>';
  }
}

function sibiClearSentence() {
  _sibiBuffer = '';
  _sibiPrev = null;
  _sibiSameCount = 0;
}

function sibiInsertToAnswer() {
  const textarea = document.getElementById('answer-input');
  if (!textarea || !_sibiBuffer.trim()) return;
  textarea.value = textarea.value + (textarea.value ? ' ' : '') + _sibiBuffer.trim();
  textarea.dispatchEvent(new Event('input'));
  sibiClearSentence();
}

// ═══════════════════════════════════════════════════════════════════════════════
// EMOTION DETECTION
// ═══════════════════════════════════════════════════════════════════════════════

function _startEmotionDetection(sessionId) {
  if (!_emotionReady) {
    console.warn('[Emotion] Modul tidak siap');
    return;
  }
  if (_emotionTimer) clearInterval(_emotionTimer);
  _emotionTimer = setInterval(() => _analyzeEmotion(sessionId), 2500);
  _analyzeEmotion(sessionId);
}

function _stopEmotionDetection() {
  clearInterval(_emotionTimer);
  _emotionTimer = null;
}

async function _analyzeEmotion(sessionId) {
  if (!isWebcamActive()) return;
  const frame = captureFrame(0.55);
  if (!frame) return;
  const result = await postJSON('/api/emotion/analyze', { sessionId, frame });
  if (!result) return;
  if (result.status === 'success' || result.status === 'throttled') {
    _updateEmotionUI(result);
  } else if (result.status === 'no_face') {
    _updateEmotionUI({ ...result, dominant_emotion: 'no face', emoji: '📷', is_negative: false });
  }
}

function _updateEmotionUI(result) {
  const overlay = document.getElementById('emotion-overlay');
  const headerBadge = document.getElementById('emotion-header-badge');
  const emotion = result.dominant_emotion || 'neutral';
  const emoji = result.emoji || '😐';
  const color = result.is_negative ? '#ef4444' : '#16a34a';
  const bg = result.is_negative ? 'rgba(239,68,68,0.2)' : 'rgba(34,197,94,0.2)';

  if (overlay) {
    overlay.innerHTML = `
      <div class="emotion-badge" style="background:${bg};border:1px solid ${color};padding:4px 10px;border-radius:20px;">
        <span style="font-size:1.1em">${emoji}</span>
        <span style="color:${color};font-weight:600;font-size:0.8em">${emotion}</span>
      </div>`;
  }
  if (headerBadge) {
    headerBadge.innerHTML = `${emoji} <span id="emotion-label-header">${emotion}</span>`;
  }
}

async function loadEmotionReport(sessionId) {
  const section = document.getElementById('emotion-report-section');
  const content = document.getElementById('emotion-report-content');
  if (!section || !content) return;

  const report = await fetch(`/api/emotion/report/${sessionId}`).then(r => r.json()).catch(() => null);
  if (!report || report.total_samples === 0) return;

  section.classList.remove('hidden');
  const dist = report.emotion_distribution || {};
  const distHTML = Object.entries(dist).sort((a, b) => b[1] - a[1]).map(([em, pct]) => `
    <div class="flex items-center gap-2 mb-1">
      <span class="w-20 text-sm text-gray-700 capitalize">${em}</span>
      <div class="flex-1 bg-gray-200 rounded-full h-3">
        <div class="bg-indigo-500 h-3 rounded-full transition-all" style="width:${pct}%"></div>
      </div>
      <span class="text-xs text-gray-500 w-10 text-right">${pct}%</span>
    </div>`).join('');

  content.innerHTML = `
    <div class="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
      <div class="bg-white rounded-lg p-3 border text-center">
        <div class="text-2xl font-bold text-indigo-600 capitalize">${report.dominant_overall}</div>
        <div class="text-xs text-gray-500">Emosi Dominan</div>
      </div>
      <div class="bg-white rounded-lg p-3 border text-center">
        <div class="text-2xl font-bold ${report.negative_ratio > 0.4 ? 'text-red-500' : 'text-green-600'}">${(report.negative_ratio * 100).toFixed(0)}%</div>
        <div class="text-xs text-gray-500">Emosi Negatif</div>
      </div>
      <div class="bg-white rounded-lg p-3 border text-center">
        <div class="text-2xl font-bold text-blue-600">${report.total_samples}</div>
        <div class="text-xs text-gray-500">Sampel</div>
      </div>
    </div>
    <div class="mb-3">${distHTML}</div>
    <p class="text-sm text-gray-700 bg-white rounded-lg p-3 border">${report.recommendation}</p>`;
}

// ═══════════════════════════════════════════════════════════════════════════════
// ANTI-CHEAT
// ═══════════════════════════════════════════════════════════════════════════════

function _startAntiCheat(sessionId) {
  if (!_anticheatReady) {
    console.warn('[AntiCheat] Modul tidak siap');
    return;
  }
  if (_anticheatFrameTimer) clearInterval(_anticheatFrameTimer);
  _anticheatFrameTimer = setInterval(() => _checkAntiCheatFrame(sessionId), 3000);
  _checkAntiCheatFrame(sessionId);

  _onBlurHandler = () => { _blurStart = Date.now(); };
  _onFocusHandler = () => _onWindowFocus(sessionId);
  _onVisibilityHandler = () => {
    if (document.hidden) {
      _recordAntiCheatEvent(sessionId, 'tab_switch', {});
      showAntiCheatAlert('⚠️ Kamu meninggalkan halaman interview!', 'danger');
    }
  };
  _onPasteHandler = (e) => _onPaste(e, sessionId);

  window.addEventListener('blur', _onBlurHandler);
  window.addEventListener('focus', _onFocusHandler);
  document.addEventListener('visibilitychange', _onVisibilityHandler);
  document.addEventListener('paste', _onPasteHandler);

  const riskOverlay = document.getElementById('risk-overlay');
  if (riskOverlay) riskOverlay.style.display = 'block';

  console.log('[AntiCheat] Monitor aktif:', sessionId);
}

function _stopAntiCheat() {
  clearInterval(_anticheatFrameTimer);
  _anticheatFrameTimer = null;
  if (_onBlurHandler) window.removeEventListener('blur', _onBlurHandler);
  if (_onFocusHandler) window.removeEventListener('focus', _onFocusHandler);
  if (_onVisibilityHandler) document.removeEventListener('visibilitychange', _onVisibilityHandler);
  if (_onPasteHandler) document.removeEventListener('paste', _onPasteHandler);
  _onBlurHandler = _onFocusHandler = _onVisibilityHandler = _onPasteHandler = null;
}

async function _checkAntiCheatFrame(sessionId) {
  if (!isWebcamActive()) return;
  const frame = captureFrame(0.45);
  if (!frame) return;
  const result = await postJSON('/api/anticheat/frame', { sessionId, frame });
  if (!result) return;

  _anticheatRiskScore = result.risk_score || 0;
  _updateRiskUI(_anticheatRiskScore);

  const violations = result.violations_this_frame || [];
  if (violations.includes('multi_face')) {
    showAntiCheatAlert('⚠️ Terdeteksi lebih dari 1 orang di frame!', 'danger');
  }
  if (violations.includes('gaze_away')) {
    showAntiCheatAlert('👀 Mohon tetap fokus ke layar', 'warning');
  }
  if (violations.includes('no_face')) {
    showAntiCheatAlert('📷 Wajah tidak terdeteksi — pastikan kamera aktif', 'warning');
  }
}

function _updateRiskUI(score) {
  const color = score < 20 ? '#22c55e' : score < 50 ? '#f59e0b' : '#ef4444';
  const label = score < 20 ? 'Rendah' : score < 50 ? 'Sedang' : score < 75 ? 'Tinggi' : 'Kritis';

  const overlay = document.getElementById('risk-overlay');
  if (overlay) {
    overlay.style.display = 'block';
    overlay.innerHTML = `🛡 <span style="color:${color};font-weight:600">${label}</span>`;
  }
  const headerLabel = document.getElementById('risk-label-header');
  if (headerLabel) {
    headerLabel.textContent = label;
    headerLabel.style.color = color === '#22c55e' ? '#86efac' : color === '#f59e0b' ? '#fcd34d' : '#fca5a5';
  }
}

function _onWindowFocus(sessionId) {
  if (_blurStart) {
    const duration = (Date.now() - _blurStart) / 1000;
    if (duration > 2) {
      _recordAntiCheatEvent(sessionId, 'tab_switch', { duration_seconds: duration });
      showAntiCheatAlert(`⚠️ Kamu pergi selama ${duration.toFixed(0)} detik!`, 'danger');
    }
    _blurStart = null;
  }
}

function _onPaste(e, sessionId) {
  const text = (e.clipboardData || window.clipboardData).getData('text');
  _recordAntiCheatEvent(sessionId, 'copy_paste', { pasted_length: text.length });
  if (text.length > 30) {
    showAntiCheatAlert('⚠️ Paste terdeteksi dan dicatat!', 'warning');
  }
}

async function _recordAntiCheatEvent(sessionId, eventType, data) {
  await postJSON('/api/anticheat/event', { sessionId, event: eventType, data });
}

function recordQuestionStart(sessionId, questionId) {
  _currentQuestionId = questionId;
  _questionStartTimes[questionId] = Date.now();
  _recordAntiCheatEvent(sessionId, 'question_start', { question_id: questionId });
}

async function checkAnswerText(sessionId, text) {
  if (!text || text.length < 20) return;
  const result = await postJSON('/api/anticheat/check-text', {
    sessionId,
    text,
    questionId: _currentQuestionId || '',
  });
  if (!result) return;

  _anticheatRiskScore = result.risk_score ?? _anticheatRiskScore;
  _updateRiskUI(_anticheatRiskScore);

  if (result.ai_detection && result.ai_detection.is_likely_ai) {
    const conf = (result.ai_detection.confidence * 100).toFixed(0);
    showAntiCheatAlert(`🤖 Jawaban terindikasi AI (${conf}% confidence)`, 'warning');
  }
  if (result.speed_suspicious) {
    showAntiCheatAlert('⚡ Jawaban terlalu cepat — kemungkinan copy-paste', 'warning');
  }
}

async function loadAntiCheatReport(sessionId) {
  const section = document.getElementById('anticheat-report-section');
  const content = document.getElementById('anticheat-report-content');
  if (!section || !content) return;

  const report = await fetch(`/api/anticheat/report/${sessionId}`).then(r => r.json()).catch(() => null);
  if (!report) return;

  section.classList.remove('hidden');
  const levelColor = { low: '#22c55e', medium: '#f59e0b', high: '#ef4444', critical: '#7f1d1d' };
  const color = levelColor[report.risk_level] || '#6b7280';
  const summary = report.violations_summary || {};
  const summaryHTML = Object.entries(summary).filter(([, v]) => v > 0).map(([k, v]) =>
    `<span class="inline-block bg-orange-100 text-orange-800 px-2 py-1 rounded text-xs mr-2 mb-1">${k}: ${v}x</span>`
  ).join('');

  content.innerHTML = `
    <div class="flex items-center gap-4 mb-4">
      <div class="text-3xl font-bold" style="color:${color}">${report.risk_score}/100</div>
      <div>
        <div class="font-semibold capitalize" style="color:${color}">${report.risk_level || 'low'}</div>
        <div class="text-xs text-gray-500">${report.total_violations} pelanggaran</div>
      </div>
    </div>
    <div class="mb-3">${summaryHTML || '<span class="text-green-600 text-sm">✅ Tidak ada pelanggaran</span>'}</div>
    <p class="text-sm text-gray-700 bg-white rounded-lg p-3 border">${report.recommendation}</p>`;
}

// ═══════════════════════════════════════════════════════════════════════════════
// PORTFOLIO (keep existing — abbreviated imports from original)
// ═══════════════════════════════════════════════════════════════════════════════

async function runPortfolioAnalysis() {
  if (_portfolioAnalyzing) return;
  const btn = document.getElementById('portfolio-analyze-btn');
  const resultDiv = document.getElementById('portfolio-result');
  const resultContent = document.getElementById('portfolio-result-content');
  const githubUrl = (document.getElementById('portfolio-github-url')?.value || '').trim();
  const linkedinUrl = (document.getElementById('portfolio-linkedin-url')?.value || '').trim();
  if (!githubUrl && !linkedinUrl) {
    alert('Masukkan GitHub URL atau LinkedIn.');
    return;
  }
  _portfolioAnalyzing = true;
  if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Menganalisis...'; }
  if (resultDiv) resultDiv.classList.remove('hidden');
  if (resultContent) resultContent.innerHTML = '<div class="text-center py-8"><div class="spinner"></div><p class="text-gray-500 mt-2">Menganalisis portfolio...</p></div>';

  let linkedinData = null;
  const liName = document.getElementById('li-name')?.value?.trim();
  if (linkedinUrl || liName) {
    const skillsStr = document.getElementById('li-skills')?.value || '';
    linkedinData = {
      url: linkedinUrl,
      name: liName || '',
      headline: document.getElementById('li-headline')?.value?.trim() || '',
      connections: parseInt(document.getElementById('li-connections')?.value || '0'),
      skills: skillsStr.split(',').map(s => s.trim()).filter(Boolean),
      experience: [],
      certifications: [],
      recommendations: parseInt(document.getElementById('li-recs')?.value || '0'),
    };
  }

  const result = await postJSON('/api/portfolio/analyze', {
    sessionId: _currentSessionId || window.sessionId || 'portfolio',
    github_url: githubUrl || null,
    linkedin_data: linkedinData,
    target_role: _currentRole || 'software-developer',
  });

  _portfolioAnalyzing = false;
  if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-search mr-2"></i>Analisis Portfolio'; }
  if (!result || result.status !== 'success') {
    if (resultContent) resultContent.innerHTML = `<div class="text-red-600 p-4 bg-red-50 rounded-lg">❌ ${result?.message || 'Gagal'}</div>`;
    return;
  }
  _renderPortfolioResult(result, resultContent);
}

function _renderPortfolioResult(result, container) {
  if (!container) return;
  const score = result.overall_score || 0;
  const scoreColor = score >= 70 ? '#22c55e' : score >= 40 ? '#f59e0b' : '#ef4444';
  container.innerHTML = `
    <div class="border-t pt-4 mt-2">
      <div class="flex items-center gap-4 mb-4">
        <div class="score-ring text-2xl font-bold" style="color:${scoreColor};border-color:${scoreColor}">${score}</div>
        <p class="text-sm text-gray-600">${result.recommendation || ''}</p>
      </div>
    </div>`;
}

// ═══════════════════════════════════════════════════════════════════════════════
// INTERVIEW LIFECYCLE
// ═══════════════════════════════════════════════════════════════════════════════

async function onInterviewStarted(sessionId, role) {
  _currentSessionId = sessionId || window.sessionId;
  _currentRole = role || 'general';
  _interviewActive = true;

  await checkModuleStatus();
  const webcamOk = await ensureWebcamForMonitoring();
  if (!webcamOk) {
    showAntiCheatAlert('⚠️ Aktifkan webcam untuk deteksi emosi & anti-cheat', 'warning');
  }

  _startEmotionDetection(_currentSessionId);
  _startAntiCheat(_currentSessionId);
  updateMonitoringStatus();

  console.log('[Advanced] Interview monitoring started', _currentSessionId);
}

function onNewQuestion(questionNumber) {
  if (_currentSessionId) {
    recordQuestionStart(_currentSessionId, `q${questionNumber}`);
  }
}

async function onBeforeSubmitAnswer(answerText) {
  if (_currentSessionId && answerText) {
    await checkAnswerText(_currentSessionId, answerText);
  }
}

async function onInterviewCompleted(sessionId) {
  _interviewActive = false;
  _stopEmotionDetection();
  _stopAntiCheat();
  _stopSIBI();
  await loadEmotionReport(sessionId || _currentSessionId);
  await loadAntiCheatReport(sessionId || _currentSessionId);
}

window.advancedHooks = {
  onInterviewStarted,
  onNewQuestion,
  onBeforeSubmitAnswer,
  onInterviewCompleted,
  onWebcamStateChange: updateMonitoringStatus,
};

window.runPortfolioAnalysis = runPortfolioAnalysis;
window.toggleSIBI = toggleSIBI;
window.sibiClearSentence = sibiClearSentence;
window.sibiInsertToAnswer = sibiInsertToAnswer;

document.addEventListener('DOMContentLoaded', function () {
  checkModuleStatus();

  const portfolioBtn = document.getElementById('portfolio-analyze-btn');
  if (portfolioBtn) portfolioBtn.addEventListener('click', runPortfolioAnalysis);

  fetch('/api/sibi/status').then(r => r.json()).then(status => {
    const sibiPanel = document.getElementById('sibi-panel');
    if (sibiPanel && !status.ready) {
      sibiPanel.querySelector('#sibi-display').innerHTML =
        '<span class="text-amber-400 text-xs">SIBI opsional — pip install mediapipe scikit-learn</span>';
    }
  }).catch(() => {});

  console.log('[Advanced Features] Loaded ✅');
});
