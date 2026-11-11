// ===== GLOBAL VARIABLES =====
let socket;
let currentInterviewData = {};
let currentQuestion = null;
let currentCVAnalysis = null;
let selectedJobId = null;
let sessionId = null;

// Webcam & Audio Variables
let localStream = null;
let mediaRecorder = null;

// HR Dashboard statistics
const hrStats = {
  totalApplicants: 0,
  passedCandidates: 0,
  failedCandidates: 0,
  totalScore: 0,
  completedInterviews: 0,
  positionStats: {},
  candidates: []
};

function toFiniteNumber(value, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

// Current questions for editing
let currentQuestions = [];

async function resetHrStats() {
  try {
    const response = await fetch('/api/hr-reset', { method: 'POST' });
    const data = await response.json();
    if (data.status === 'success') {
      hrStats.totalApplicants = 0;
      hrStats.passedCandidates = 0;
      hrStats.failedCandidates = 0;
      hrStats.totalScore = 0;
      hrStats.completedInterviews = 0;
      hrStats.positionStats = {};
      hrStats.candidates = [];
      updateHrDashboardUI();
      showNotification('HR metrics reset successfully', 'success');
    } else {
      showNotification('Gagal mereset HR metrics', 'error');
    }
  } catch (error) {
    console.error('Error resetting HR stats', error);
    showNotification('Error resetting HR metrics', 'error');
  }
}

function renderQuestions() {
  const questionsList = document.getElementById("questions-list");
  questionsList.innerHTML = "";
  
  currentQuestions.forEach((question, index) => {
    const questionDiv = document.createElement("div");
    questionDiv.className = "flex items-center space-x-2 p-2 border border-gray-200 rounded";
    
    const questionText = document.createElement("span");
    questionText.className = "flex-1";
    questionText.textContent = question;
    
    const editBtn = document.createElement("button");
    editBtn.className = "bg-yellow-500 text-white px-2 py-1 rounded text-sm hover:bg-yellow-600";
    editBtn.textContent = "Edit";
    editBtn.onclick = () => editQuestion(index);
    
    const deleteBtn = document.createElement("button");
    deleteBtn.className = "bg-red-500 text-white px-2 py-1 rounded text-sm hover:bg-red-600";
    deleteBtn.textContent = "Delete";
    deleteBtn.onclick = () => deleteQuestion(index);
    
    questionDiv.appendChild(questionText);
    questionDiv.appendChild(editBtn);
    questionDiv.appendChild(deleteBtn);
    questionsList.appendChild(questionDiv);
  });
  
  // Update add button visibility
  const addBtn = document.getElementById("add-question-btn");
  addBtn.style.display = currentQuestions.length < 10 ? "block" : "none";
}

function editQuestion(index) {
  const questionsList = document.getElementById("questions-list");
  const questionDiv = questionsList.children[index];
  
  const questionText = questionDiv.querySelector("span");
  const originalText = questionText.textContent;
  
  // Replace span with input
  const input = document.createElement("input");
  input.type = "text";
  input.className = "flex-1 px-2 py-1 border border-gray-300 rounded";
  input.value = originalText;
  
  const saveBtn = document.createElement("button");
  saveBtn.className = "bg-green-500 text-white px-2 py-1 rounded text-sm hover:bg-green-600";
  saveBtn.textContent = "Save";
  saveBtn.onclick = () => {
    const newText = input.value.trim();
    if (newText) {
      currentQuestions[index] = newText;
      renderQuestions();
      showNotification('Question updated', 'success');
    }
  };
  
  const cancelBtn = document.createElement("button");
  cancelBtn.className = "bg-gray-500 text-white px-2 py-1 rounded text-sm hover:bg-gray-600";
  cancelBtn.textContent = "Cancel";
  cancelBtn.onclick = () => renderQuestions();
  
  questionDiv.innerHTML = "";
  questionDiv.appendChild(input);
  questionDiv.appendChild(saveBtn);
  questionDiv.appendChild(cancelBtn);
  
  input.focus();
}

function deleteQuestion(index) {
  if (confirm("Are you sure you want to delete this question?")) {
    currentQuestions.splice(index, 1);
    renderQuestions();
    showNotification('Question deleted', 'success');
  }
}

function addQuestion() {
  if (currentQuestions.length >= 10) {
    showNotification('Maximum 10 questions allowed', 'error');
    return;
  }
  
  const questionsList = document.getElementById("questions-list");
  const questionDiv = document.createElement("div");
  questionDiv.className = "flex items-center space-x-2 p-2 border border-gray-200 rounded";
  
  const input = document.createElement("input");
  input.type = "text";
  input.className = "flex-1 px-2 py-1 border border-gray-300 rounded";
  input.placeholder = "Enter new question";
  
  const saveBtn = document.createElement("button");
  saveBtn.className = "bg-green-500 text-white px-2 py-1 rounded text-sm hover:bg-green-600";
  saveBtn.textContent = "Save";
  saveBtn.onclick = () => {
    const newText = input.value.trim();
    if (newText) {
      currentQuestions.push(newText);
      renderQuestions();
      showNotification('Question added', 'success');
    }
  };
  
  const cancelBtn = document.createElement("button");
  cancelBtn.className = "bg-gray-500 text-white px-2 py-1 rounded text-sm hover:bg-gray-600";
  cancelBtn.textContent = "Cancel";
  cancelBtn.onclick = () => renderQuestions();
  
  questionDiv.appendChild(input);
  questionDiv.appendChild(saveBtn);
  questionDiv.appendChild(cancelBtn);
  questionsList.appendChild(questionDiv);
  
  input.focus();
}

async function loadAndRenderQuestions() {
  try {
    const role = document.getElementById("question-role").value;
    const response = await fetch('/api/custom-questions');
    const data = await response.json();
    if (data.status === 'success') {
      currentQuestions = data.custom_questions[role] || [];
      renderQuestions();
      showNotification('Questions loaded successfully', 'success');
    } else {
      showNotification('Failed to load questions', 'error');
    }
  } catch (error) {
    console.error('Error loading custom questions', error);
    showNotification('Error loading questions', 'error');
  }
}

async function saveAllQuestions() {
  try {
    const role = document.getElementById("question-role").value;
    
    if (currentQuestions.length > 10) {
      showNotification('Maximum 10 questions allowed per role', 'error');
      return;
    }
    
    const response = await fetch('/api/custom-questions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        role: role,
        questions: currentQuestions
      })
    });
    const data = await response.json();
    if (data.status === 'success') {
      showNotification('Questions saved successfully', 'success');
    } else {
      showNotification('Failed to save questions', 'error');
    }
  } catch (error) {
    console.error('Error saving custom questions', error);
    showNotification('Error saving questions', 'error');
  }
}

function addOrUpdateCandidateHistory(name, position, score, status) {
  const existing = hrStats.candidates.find(item => item.name === name);
  if (existing) {
    existing.position = position;
    existing.score = score;
    existing.status = status;
  } else {
    hrStats.candidates.push({ name, position, score, status });
  }
}

function updateHrDashboardUI() {
  // Sinkronisasi jumlah pelamar unique berdasarkan nama
  hrStats.totalApplicants = new Set(hrStats.candidates.map(c => c.name)).size;

  document.getElementById("hr-total-applicants").textContent = hrStats.totalApplicants;
  document.getElementById("hr-passed").textContent = hrStats.passedCandidates;
  document.getElementById("hr-failed").textContent = hrStats.failedCandidates;
  const safeTotalScore = toFiniteNumber(hrStats.totalScore, 0);
  const safeCompleted = toFiniteNumber(hrStats.completedInterviews, 0);
  const averageScore = safeCompleted > 0 ? (safeTotalScore / safeCompleted).toFixed(1) : "0.0";
  document.getElementById("hr-average-score").textContent = averageScore;
  document.getElementById("hr-completed-interviews").textContent = safeCompleted;
  document.querySelectorAll("[data-hr-average-score]").forEach(element => {
    element.textContent = averageScore;
  });

  const applicantNamesEl = document.getElementById("hr-applicant-names");
  const uniqueNames = [...new Set(hrStats.candidates.map(c => c.name).filter(Boolean))];
  if (applicantNamesEl) {
    applicantNamesEl.textContent = uniqueNames.length > 0 ? `(${uniqueNames.join(', ')})` : '(belum ada kandidat)';
  }

  const candidateDetailEl = document.getElementById("hr-candidate-detail");
  if (candidateDetailEl) {
    if (hrStats.candidates.length === 0) {
      candidateDetailEl.textContent = 'Belum ada detail kandidat.';
    } else {
      const uniqueByName = [];
      const seen = new Set();
      hrStats.candidates.forEach(item => {
        if (!seen.has(item.name)) {
          seen.add(item.name);
          uniqueByName.push(item);
        } else {
          const existing = uniqueByName.find(i => i.name === item.name);
          if (existing && item.completedInterview) {
            Object.assign(existing, item);
          }
        }
      });
      const lines = uniqueByName.map(item => {
        const scoreText = item.score != null ? item.score : 'n/a';
        return `${item.name}: status=${item.status || 'Unknown'}, skor=${scoreText}, posisi=${item.position || 'Unknown'}`;
      });
      candidateDetailEl.innerHTML = lines.map(line => `<div>${line}</div>`).join('');
    }
  }
}


async function refreshHrStats() {
  try {
    const response = await fetch('/api/hr-stats');
    const data = await response.json();
    if (data.status === 'success') {
      hrStats.totalApplicants = data.totalApplicants;
      hrStats.passedCandidates = data.passedCandidates;
      hrStats.failedCandidates = data.failedCandidates;
      hrStats.totalScore = data.totalScore;
      hrStats.completedInterviews = toFiniteNumber(data.completedInterviews, 0);
      hrStats.positionStats = data.positionStats;
      hrStats.candidates = data.candidates.map(x => ({
        name: x.candidateName || x.name || 'Unknown',
        position: x.position || 'Unknown',
        score: toFiniteNumber(x.score, 0),
        status: x.status || 'Screened'
      }));
      hrStats.totalScore = hrStats.candidates.reduce((acc, c) => acc + toFiniteNumber(c.score, 0), 0);
      updateHrDashboardUI();
    }
  } catch (error) {
    console.error('Gagal refresh HR stats', error);
  }
}

let audioChunks = [];
let recordingStartTime = null;
let recordingTimer = null;
let isRecording = false;
let isMicEnabled = false;

// Face recognition state
let faceStream = null;
let faceReferenceUploaded = false;
let faceRecognitionPassed = false;
let faceDatabase = [];
let faceMode = 'server';
let attendancePollTimer = null;
let lastAttendanceCount = 0;
let liveFeedActive = false;

// Audio enhancement variables
let speechRecognition = null;
let durationInterval = null;
let audioContext = null;
let analyser = null;
let waveformAnimFrame = null;

// ===== HELPER: Stop Face Camera =====
function stopFaceCamera() {
  stopLiveAbsensi();
  stopAttendancePolling();
  stopBrowserFacePreview();
}

function stopBrowserFacePreview() {
  if (faceStream) {
    faceStream.getTracks().forEach(t => t.stop());
    faceStream = null;
  }
  const video = document.getElementById("face-video");
  if (video) {
    video.srcObject = null;
    video.classList.add("hidden");
  }
  const placeholder = document.getElementById("face-feed-placeholder");
  if (placeholder && !liveFeedActive) {
    placeholder.classList.remove("hidden");
  }
}

function startAttendancePolling() {
  stopAttendancePolling();
  lastAttendanceCount = -1;
  reloadAttendanceTable();
  attendancePollTimer = setInterval(chkNewAttendanceScan, 1000);
}

function stopAttendancePolling() {
  if (attendancePollTimer) {
    clearInterval(attendancePollTimer);
    attendancePollTimer = null;
  }
}

async function chkNewAttendanceScan() {
  try {
    const res = await fetch('/countTodayScan');
    const data = await res.json();
    const cnt = data.rowcount || 0;
    const countEl = document.getElementById('today-scan-count');
    if (countEl) countEl.textContent = cnt;
    if (cnt > lastAttendanceCount) {
      await reloadAttendanceTable();
      checkCandidateAttendanceMatch();
    }
    lastAttendanceCount = cnt;
  } catch (err) {
    console.debug('Attendance poll:', err.message);
  }
}

async function reloadAttendanceTable() {
  const tbody = document.getElementById('scandata');
  if (!tbody) return;
  try {
    const res = await fetch('/loadData');
    const data = await res.json();
    tbody.innerHTML = '';
    const rows = data.response || [];
    if (rows.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" class="text-center text-gray-500 py-3 text-sm">Belum ada absensi hari ini</td></tr>';
      return;
    }
    rows.forEach(item => {
      if (!item || item.length < 5) return;
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${item[0]}</td><td>${item[2]}</td><td>${item[3]}</td><td>${item[4]}</td>`;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.debug('Load attendance:', err.message);
  }
}

function checkCandidateAttendanceMatch() {
  const candidateName = (currentInterviewData.candidateName || '').trim().toLowerCase();
  if (!candidateName || !document.getElementById('use-face-recognition')?.checked) return;
  const rows = document.querySelectorAll('#scandata tr');
  rows.forEach(row => {
    const nameCell = row.cells[1];
    if (!nameCell) return;
    const scannedName = nameCell.textContent.trim().toLowerCase();
    if (scannedName && (scannedName === candidateName || scannedName.includes(candidateName) || candidateName.includes(scannedName))) {
      faceRecognitionPassed = true;
      enableProceedToAnalysis();
      updateFaceStatusBadge(true);
      showFaceResult(`Absensi tercatat untuk ${nameCell.textContent}. Anda dapat lanjut ke analisis CV.`, true);
    }
  });
}

function setFaceMode(mode) {
  faceMode = mode;
  const serverTab = document.getElementById('face-mode-server');
  const browserTab = document.getElementById('face-mode-browser');
  if (serverTab) serverTab.classList.toggle('active', mode === 'server');
  if (browserTab) browserTab.classList.toggle('active', mode === 'browser');

  const liveBtn = document.getElementById('start-live-absensi-btn');
  const stopBtn = document.getElementById('stop-live-absensi-btn');
  const startCam = document.getElementById('start-camera-btn');
  const captureBtn = document.getElementById('capture-face-btn');
  const verifyDb = document.getElementById('verify-database-btn');

  if (mode === 'server') {
    liveBtn?.classList.remove('hidden');
    stopBtn?.classList.toggle('hidden', !liveFeedActive);
    startCam?.classList.add('hidden');
    captureBtn?.classList.add('hidden');
    verifyDb?.classList.add('hidden');
    stopBrowserFacePreview();
    if (!liveFeedActive) {
      document.getElementById('face-feed-placeholder')?.classList.remove('hidden');
    }
  } else {
    if (liveFeedActive) stopLiveAbsensi();
    liveBtn?.classList.add('hidden');
    stopBtn?.classList.add('hidden');
    startCam?.classList.remove('hidden');
    captureBtn?.classList.remove('hidden');
    verifyDb?.classList.remove('hidden');
  }
}

function startLiveAbsensi(event) {
  if (event?.preventDefault) event.preventDefault();
  const img = document.getElementById('face-live-feed');
  const placeholder = document.getElementById('face-feed-placeholder');
  const video = document.getElementById('face-video');
  if (!img) return;

  stopBrowserFacePreview();
  img.onerror = () => {
    showFaceResult('Gagal membuka kamera server. Pastikan webcam terhubung & OpenCV terinstall.', false);
    stopLiveAbsensi();
  };
  img.src = '/video_feed?' + Date.now();
  img.classList.remove('hidden');
  placeholder?.classList.add('hidden');
  video?.classList.add('hidden');
  liveFeedActive = true;

  document.getElementById('start-live-absensi-btn')?.classList.add('hidden');
  document.getElementById('stop-live-absensi-btn')?.classList.remove('hidden');
  showFaceResult('Live absensi aktif — hadapkan wajah ke kamera. Progress bar muncul saat dikenali.', true);
  startAttendancePolling();
}

function stopLiveAbsensi() {
  const img = document.getElementById('face-live-feed');
  if (img) {
    img.src = '';
    img.onerror = null;
    img.classList.add('hidden');
  }
  liveFeedActive = false;
  if (faceMode === 'server') {
    document.getElementById('face-feed-placeholder')?.classList.remove('hidden');
    document.getElementById('start-live-absensi-btn')?.classList.remove('hidden');
    document.getElementById('stop-live-absensi-btn')?.classList.add('hidden');
  }
}

function initFaceRecognitionSection() {
  setFaceMode('server');
  startAttendancePolling();
  loadFaceDatabase();
  disableProceedToAnalysis();
  updateFaceStatusBadge(false);
}

// ===== STEP PROGRESS BAR =====
function setActiveStep(step) {
  for (let i = 1; i <= 5; i++) {
    const circle = document.getElementById(`step-circle-${i}`);
    const label = document.getElementById(`step-label-${i}`);
    if (!circle || !label) continue;

    circle.classList.remove('active', 'done');
    label.classList.remove('active', 'done');

    if (i < step) {
      circle.classList.add('done');
      circle.innerHTML = '<i class="fas fa-check" style="font-size:12px;"></i>';
      label.classList.add('done');
    } else if (i === step) {
      circle.classList.add('active');
      circle.innerHTML = i;
      label.classList.add('active');
    } else {
      circle.innerHTML = i;
    }
  }

  for (let i = 1; i <= 4; i++) {
    const line = document.getElementById(`step-line-${i}`);
    if (!line) continue;
    if (i < step) {
      line.classList.add('done');
    } else {
      line.classList.remove('done');
    }
  }

  const progressBar = document.getElementById('step-progress-bar');
  if (progressBar) {
    progressBar.classList.toggle('hidden', step > 5);
  }
}

function showMainMenu() {
  document.body.classList.remove('hr-dashboard-active', 'candidate-dashboard-active');
  document.getElementById('menu-selection-section').classList.remove('hidden');
  document.getElementById('hr-dashboard-section').classList.add('hidden');
  document.getElementById('step-progress-bar').classList.add('hidden');

  const sections = ['cv-upload-section','face-recognition-section','cv-analysis-section','job-recommendations-section','interview-setup-section','interview-section','results-section'];
  sections.forEach(id => { const el = document.getElementById(id); if (el) el.classList.add('hidden'); });
}

function showHRDashboard() {
  document.body.classList.remove('candidate-dashboard-active');
  document.body.classList.add('hr-dashboard-active');
  document.getElementById('menu-selection-section').classList.add('hidden');
  document.getElementById('hr-dashboard-section').classList.remove('hidden');
  document.getElementById('step-progress-bar').classList.add('hidden');
  refreshHrStats();
  if (window.refreshRecruitmentReport) window.refreshRecruitmentReport();
  loadAndRenderQuestions();
  console.log('HR dashboard shown, stats:', hrStats);

}

function showCVScreening() {
  document.body.classList.remove('hr-dashboard-active');
  document.body.classList.add('candidate-dashboard-active');
  document.getElementById('menu-selection-section').classList.add('hidden');
  document.getElementById('hr-dashboard-section').classList.add('hidden');
  document.getElementById('step-progress-bar').classList.remove('hidden');

  const sections = ['face-recognition-section','cv-analysis-section','job-recommendations-section','interview-setup-section','interview-section','results-section'];
  sections.forEach(id => {const el = document.getElementById(id); if (el) el.classList.add('hidden');});
  document.getElementById('cv-upload-section').classList.remove('hidden');
  setActiveStep(1);
  replaySectionAnimation('cv-upload-section');
}

// ===== INITIALIZATION =====
document.addEventListener("DOMContentLoaded", function () {
  initializeSocket();
  setupEventListeners();
  setupCharacterCounter();
  sessionId = generateSessionId();
  showMainMenu();
  updateHrDashboardUI();
  loadFaceDatabase();
});

function generateSessionId() {
  sessionId = "session_" + Date.now() + "_" + Math.random().toString(36).substr(2, 9);
  window.sessionId = sessionId;
  return sessionId;
}

function initializeSocket() {
  socket = io();
  window.socket = socket;

  socket.on("connect", () => {
    console.log("Connected to Python Flask server");
  });

  socket.on("interview-started", (data) => {
    console.log("Interview started:", data);
    startInterview(data);
  });

  socket.on("next-question", (questionData) => {
    console.log("Next question:", questionData);
    hideTypingIndicator();
    displayNextQuestion(questionData);
  });

  socket.on("answer-evaluated", (evaluation) => {
    console.log("Answer evaluated:", evaluation);
    displayAnswerEvaluation(evaluation);
  });

  socket.on("interview-completed", (summary) => {
    console.log("Interview completed:", summary);
    showInterviewResults(summary);
  });

  socket.on("error", (error) => {
    console.error("Socket error:", error);
    showError(error.message);
  });
}

// ===== SETUP EVENT LISTENERS =====
function setupEventListeners() {
  // CV Upload
  const cvUploadForm = document.getElementById("cv-upload-form");
  if (cvUploadForm) {
    cvUploadForm.addEventListener("submit", async function (e) {
      e.preventDefault();
      await handleCVUpload();
    });
  }

  // CV Analysis to Jobs
  const findJobsBtn = document.getElementById("find-jobs-btn");
  if (findJobsBtn) {
    findJobsBtn.addEventListener("click", getRecommendedJobs);
  }

  // Back to face from CV analysis
  const backToFaceBtn = document.getElementById("back-to-face-btn");
  if (backToFaceBtn) {
    backToFaceBtn.addEventListener("click", function () {
      document.getElementById("cv-analysis-section").classList.add("hidden");
      document.getElementById("face-recognition-section").classList.remove("hidden");
      setActiveStep(2);
    });
  }

  // Start Interview
  const startInterviewBtn = document.getElementById("start-interview-btn");
  if (startInterviewBtn) {
    startInterviewBtn.addEventListener("click", startInterviewFromJob);
  }

  // Submit answer
  const submitAnswerBtn = document.getElementById("submit-answer-btn");
  if (submitAnswerBtn) {
    submitAnswerBtn.addEventListener("click", submitAnswer);
  }

  // Restart interview
  const restartInterviewBtn = document.getElementById("restart-interview-btn");
  if (restartInterviewBtn) {
    restartInterviewBtn.addEventListener("click", restartInterview);
  }

  // Download results
  const downloadResultsBtn = document.getElementById("download-results-btn");
  if (downloadResultsBtn) {
    downloadResultsBtn.addEventListener("click", downloadResults);
  }

  // Webcam controls
  const webcamToggleBtn = document.getElementById("webcam-toggle-btn");
  if (webcamToggleBtn) {
    webcamToggleBtn.addEventListener("click", toggleWebcam);
  }

  // Audio controls
  const micToggleBtn = document.getElementById("mic-toggle-btn");
  if (micToggleBtn) {
    micToggleBtn.addEventListener("click", toggleMicrophone);
  }

  const recordBtn = document.getElementById("record-btn");
  if (recordBtn) {
    recordBtn.addEventListener("click", startRecording);
  }

  const stopRecordBtn = document.getElementById("stop-record-btn");
  if (stopRecordBtn) {
    stopRecordBtn.addEventListener("click", stopRecording);
  }

  const ttsBtn = document.getElementById("tts-btn");
  if (ttsBtn) {
    ttsBtn.addEventListener("click", speakQuestion);
  }

  // Face recognition controls
  const uploadReferenceBtn = document.getElementById("upload-reference-btn");
  const startFaceCameraBtn = document.getElementById("start-camera-btn");
  const captureFaceBtn = document.getElementById("capture-face-btn");
  const skipFaceBtn = document.getElementById("skip-face-recognition");
  const useFaceCheckbox = document.getElementById("use-face-recognition");

  if (uploadReferenceBtn) {
    uploadReferenceBtn.addEventListener("click", uploadReference);
  }
  
  const registerFaceBtn = document.getElementById("register-face-btn");
  const verifyDatabaseBtn = document.getElementById("verify-database-btn");
  const loadFaceDbBtn = document.getElementById("load-face-db-btn");
  const clearFaceDbBtn = document.getElementById("clear-face-db-btn");

  if (registerFaceBtn) {
    registerFaceBtn.addEventListener("click", registerFace);
  }
  if (verifyDatabaseBtn) {
    verifyDatabaseBtn.addEventListener("click", verifyDatabase);
  }
  if (loadFaceDbBtn) {
    loadFaceDbBtn.addEventListener("click", loadFaceDatabase);
  }
  if (clearFaceDbBtn) {
    clearFaceDbBtn.addEventListener("click", clearFaceDatabase);
  }

  const startLiveBtn = document.getElementById("start-live-absensi-btn");
  const stopLiveBtn = document.getElementById("stop-live-absensi-btn");
  const faceModeServer = document.getElementById("face-mode-server");
  const faceModeBrowser = document.getElementById("face-mode-browser");

  if (startLiveBtn) startLiveBtn.addEventListener("click", startLiveAbsensi);
  if (stopLiveBtn) stopLiveBtn.addEventListener("click", stopLiveAbsensi);
  if (faceModeServer) faceModeServer.addEventListener("click", () => setFaceMode('server'));
  if (faceModeBrowser) faceModeBrowser.addEventListener("click", () => setFaceMode('browser'));
  
  if (startFaceCameraBtn) {
    startFaceCameraBtn.addEventListener("click", startFaceCamera);
  }
  if (captureFaceBtn) {
    captureFaceBtn.addEventListener("click", captureFace);
  }
  if (skipFaceBtn) {
    skipFaceBtn.addEventListener("click", skipFaceRecognition);
  }

  if (useFaceCheckbox) {
    useFaceCheckbox.addEventListener("change", function () {
      const status = this.checked
        ? "Face recognition aktif"
        : "Face recognition dinonaktifkan";
      showFaceResult(status, this.checked);
      if (!this.checked) {
        faceRecognitionPassed = true;
        enableProceedToAnalysis();
      } else {
        faceRecognitionPassed = false;
        disableProceedToAnalysis();
      }
    });
  }

  // Tombol Lanjut ke Analisis CV (dari Face Recognition)
  const proceedBtn = document.getElementById("proceed-to-cv-analysis-btn");
  if (proceedBtn) {
    proceedBtn.addEventListener("click", function () {
      showCVAnalysisFromFace();
    });
  }

  // Tombol Kembali ke Upload CV (dari Face Recognition)
  const backToUploadBtn = document.getElementById("back-to-cv-upload-btn");
  if (backToUploadBtn) {
    backToUploadBtn.addEventListener("click", function () {
      stopFaceCamera();
      document.getElementById("face-recognition-section").classList.add("hidden");
      document.getElementById("cv-upload-section").classList.remove("hidden");
      faceRecognitionPassed = false;
      faceReferenceUploaded = false;
      setActiveStep(1);
    });
  }

  // Back to CV btn (dari job recommendations -> kembali ke cv analysis)
  const backToCVBtn = document.getElementById("back-to-cv-btn");
  if (backToCVBtn) {
    backToCVBtn.addEventListener("click", backToCV);
  }

  const hrResetBtn = document.getElementById("hr-reset-btn");
  if (hrResetBtn) {
    hrResetBtn.addEventListener("click", resetHrStats);
  }

  const loadQuestionsBtn = document.getElementById("load-questions-btn");
  if (loadQuestionsBtn) {
    loadQuestionsBtn.addEventListener("click", loadAndRenderQuestions);
  }

  const saveAllQuestionsBtn = document.getElementById("save-all-questions-btn");
  if (saveAllQuestionsBtn) {
    saveAllQuestionsBtn.addEventListener("click", saveAllQuestions);
  }

  const addQuestionBtn = document.getElementById("add-question-btn");
  if (addQuestionBtn) {
    addQuestionBtn.addEventListener("click", addQuestion);
  }

  const questionRoleSelect = document.getElementById("question-role");
  if (questionRoleSelect) {
    questionRoleSelect.addEventListener("change", loadAndRenderQuestions);
  }

  // Menu selection main
  const menuHrBtn = document.getElementById("menu-hr-btn");
  if (menuHrBtn) {
    menuHrBtn.addEventListener("click", showHRDashboard);
  }

  const menuCvBtn = document.getElementById("menu-cv-btn");
  if (menuCvBtn) {
    menuCvBtn.addEventListener("click", showCVScreening);
  }

  const menuBackBtnHr = document.getElementById("menu-back-btn-hr");
  if (menuBackBtnHr) {
    menuBackBtnHr.addEventListener("click", showMainMenu);
  }

  const hrOverflowMenu = document.getElementById("hr-overflow-menu");
  if (hrOverflowMenu) {
    document.addEventListener("click", (event) => {
      if (!hrOverflowMenu.contains(event.target)) {
        hrOverflowMenu.open = false;
      }
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && hrOverflowMenu.open) {
        hrOverflowMenu.open = false;
        hrOverflowMenu.querySelector("summary")?.focus();
      }
    });
  }

  const menuBackBtnCv = document.getElementById("menu-back-btn-cv");
  if (menuBackBtnCv) {
    menuBackBtnCv.addEventListener("click", function () {
      stopFaceCamera();
      showMainMenu();
    });
  }

  document.querySelectorAll(".dashboard-mobile-menu").forEach(button => {
    button.addEventListener("click", () => {
      button.closest(".hr-dashboard-shell, .candidate-dashboard-shell")?.classList.toggle("nav-open");
    });
  });

  document.querySelectorAll(".dashboard-nav a[href^='#']").forEach(link => {
    link.addEventListener("click", () => {
      link.closest(".hr-dashboard-shell, .candidate-dashboard-shell")?.classList.remove("nav-open");
    });
  });

  // Choose different job btn
  const chooseDifferentJobBtn = document.getElementById("choose-different-job-btn");
  if (chooseDifferentJobBtn) {
    chooseDifferentJobBtn.addEventListener("click", backToJobsRecommendations);
  }
}

// ===== CV WORKFLOW FUNCTIONS =====

async function handleCVUpload() {
  let candidateName = document.getElementById("candidate-name-cv").value.trim();
  const cvText = document.getElementById("cv-text").value.trim();

  if (!candidateName) {
    candidateName = "Unknown";
  }

  console.log('handleCVUpload start', { candidateName, cvTextLength: cvText.length });

  if (!cvText) {
    showError("Please fill in CV text");
    return;
  }

  if (cvText.length < 20) {
    showError("CV text must be at least 20 characters");
    return;
  }

  // Tambahi segera data kandidat ke HR sebelum request (agar langsung terlihat)
  addOrUpdateCandidateHistory(candidateName, "CV Screening", 0, "Screened");
  if (!hrStats.positionStats["CV Screening"]) {
    hrStats.positionStats["CV Screening"] = { total: 0, completed: 0, passed: 0, failed: 0 };
  }
  hrStats.positionStats["CV Screening"].total += 1;
  hrStats.totalApplicants = hrStats.candidates.length;
  updateHrDashboardUI();

  const cvUploadLoading = document.getElementById("cv-upload-loading");
  const cvUploadForm = document.getElementById("cv-upload-form");
  cvUploadForm.style.display = "none";
  cvUploadLoading.classList.remove("hidden");

  try {
    const response = await fetch("/api/upload-cv", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        cvText: cvText,
        candidateName: candidateName,
        position: "CV Screening",
        sessionId: sessionId,
      }),
    });

    const data = await response.json();
    console.log('CV upload response:', data);

    if (data.status === "success") {
      console.log('CV upload success', data);
      currentCVAnalysis = data.analysis;
      currentInterviewData.candidateName = candidateName;
      currentInterviewData.cvAnalysis = data.analysis;

      addOrUpdateCandidateHistory(candidateName, "CV Screening", 0, "Screened");

      if (!hrStats.positionStats["CV Screening"]) {
        hrStats.positionStats["CV Screening"] = { total: 0, completed: 0, passed: 0, failed: 0 };
      }
      hrStats.positionStats["CV Screening"].total += 1;

      hrStats.totalApplicants = hrStats.candidates.length;
      updateHrDashboardUI();
      console.log('hrStats after cv upload', hrStats);

      cvUploadLoading.classList.add("hidden");
      cvUploadForm.style.display = "block";
      document.getElementById("cv-upload-section").classList.add("hidden");
      document.getElementById("face-recognition-section").classList.remove("hidden");

      faceRecognitionPassed = false;
      faceReferenceUploaded = false;
      initFaceRecognitionSection();
      setActiveStep(2);
      replaySectionAnimation('face-recognition-section');
    } else {
      showError(data.message);
      cvUploadLoading.classList.add("hidden");
      cvUploadForm.style.display = "block";
    }
  } catch (error) {
    console.error("Error uploading CV:", error);
    showError("Error uploading CV: " + error.message);
    cvUploadLoading.classList.add("hidden");
    cvUploadForm.style.display = "block";
  }
}

function showCVAnalysisFromFace() {
  stopFaceCamera();
  const analysis = currentInterviewData.cvAnalysis || currentCVAnalysis;
  const candidateName = currentInterviewData.candidateName;
  document.getElementById("face-recognition-section").classList.add("hidden");
  showCVAnalysis(analysis, candidateName);
  setActiveStep(3);
}

function updateFaceStatusBadge(passed) {
  const badge = document.getElementById("face-status-badge");
  if (!badge) return;
  if (passed) {
    badge.innerHTML = `
      <span class="status-badge status-badge--success">
        <i class="fas fa-check-circle mr-1"></i> Verifikasi Berhasil
      </span>`;
  } else {
    badge.innerHTML = `
      <span class="status-badge status-badge--waiting">
        <i class="fas fa-clock mr-1"></i> Menunggu Verifikasi
      </span>`;
  }
}

function replaySectionAnimation(sectionId) {
  const section = document.getElementById(sectionId);
  if (!section) return;
  section.querySelectorAll('.anim-fade-up').forEach(el => {
    el.style.animation = 'none';
    el.offsetHeight;
    el.style.animation = '';
  });
}

function enableProceedToAnalysis() {
  const btn = document.getElementById("proceed-to-cv-analysis-btn");
  if (!btn) return;
  btn.disabled = false;
  btn.classList.remove("opacity-50", "cursor-not-allowed");
  btn.classList.add("hover:scale-[1.02]");
}

function disableProceedToAnalysis() {
  const btn = document.getElementById("proceed-to-cv-analysis-btn");
  if (!btn) return;
  btn.disabled = true;
  btn.classList.add("opacity-50", "cursor-not-allowed");
  btn.classList.remove("hover:scale-[1.02]");
}

function showCVAnalysis(analysis, candidateName) {
  currentInterviewData.candidateName = candidateName;

  document.getElementById("exp-level-badge").textContent = analysis.experience_level.toUpperCase();
  document.getElementById("skills-count").textContent = analysis.total_skills_found;
  document.getElementById("categories-count").textContent = analysis.summary.categories_found;

  const skillsList = document.getElementById("skills-list");
  skillsList.innerHTML = "";
  if (analysis.skills && analysis.skills.length > 0) {
    analysis.skills.forEach((skill) => {
      const skillTag = document.createElement("span");
      skillTag.className = "bg-blue-100 text-blue-800 text-sm font-semibold py-1 px-3 rounded-full";
      skillTag.textContent = skill;
      skillsList.appendChild(skillTag);
    });
  }

  const languagesList = document.getElementById("languages-list");
  languagesList.innerHTML = "";
  if (analysis.programming_languages && analysis.programming_languages.length > 0) {
    analysis.programming_languages.forEach((lang) => {
      const langTag = document.createElement("span");
      langTag.className = "bg-purple-100 text-purple-800 text-sm font-semibold py-1 px-3 rounded-full";
      langTag.textContent = lang;
      languagesList.appendChild(langTag);
    });
  } else {
    const noLangTag = document.createElement("span");
    noLangTag.className = "text-gray-500 text-sm italic";
    noLangTag.textContent = "No programming languages detected";
    languagesList.appendChild(noLangTag);
  }

  document.getElementById("cv-upload-section").classList.add("hidden");
  document.getElementById("face-recognition-section").classList.add("hidden");
  document.getElementById("cv-analysis-section").classList.remove("hidden");
  replaySectionAnimation('cv-analysis-section');
}

async function getRecommendedJobs() {
  if (!currentCVAnalysis) {
    showError("No CV analysis found");
    return;
  }

  try {
    const response = await fetch("/api/recommended-jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sessionId: sessionId }),
    });

    const data = await response.json();

    if (data.status === "success") {
      displayJobRecommendations(data.recommended_jobs);
      setActiveStep(4);
    } else {
      showError(data.message);
    }
  } catch (error) {
    console.error("Error fetching jobs:", error);
    showError("Error fetching job recommendations");
  }
}

function displayJobRecommendations(jobs) {
  const jobsList = document.getElementById("jobs-list");
  jobsList.innerHTML = "";

  if (jobs.length === 0) {
    const noJob = document.createElement("div");
    noJob.className = "text-center py-8 text-gray-600";
    noJob.innerHTML = "<p>No matching jobs found. Please check your CV or try later.</p>";
    jobsList.appendChild(noJob);
  } else {
    jobs.forEach((job) => {
      const matchScore = job.match_score;
      const jobCard = document.createElement("div");
      jobCard.className = "bg-white border-l-4 border-blue-500 rounded-lg p-6 shadow-md hover:shadow-lg transition cursor-pointer";
      jobCard.innerHTML = `
        <div class="flex justify-between items-start mb-3">
          <div>
            <h3 class="text-xl font-bold text-gray-800">${job.title}</h3>
            <p class="text-gray-600">${job.company} • ${job.location}</p>
          </div>
          <div class="text-right">
            <div class="text-3xl font-bold text-green-600">${matchScore.match_percentage}%</div>
            <p class="text-sm text-gray-500">Match</p>
          </div>
        </div>
        <p class="text-gray-700 mb-4">${job.description}</p>
        <div class="mb-4">
          <p class="text-sm font-semibold text-gray-700 mb-2">Your Matched Skills:</p>
          <div class="flex flex-wrap gap-2">
            ${matchScore.matched_skills.map(skill => `<span class="bg-green-100 text-green-800 text-xs px-2 py-1 rounded">${skill}</span>`).join("")}
          </div>
        </div>
        ${matchScore.missing_skills.length > 0 ? `
          <div class="mb-4">
            <p class="text-sm font-semibold text-gray-700 mb-2">Skills to Learn:</p>
            <div class="flex flex-wrap gap-2">
              ${matchScore.missing_skills.slice(0, 3).map(skill => `<span class="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded">${skill}</span>`).join("")}
            </div>
          </div>` : ""}
        <button class="w-full mt-4 bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded transition">
          Select This Position
        </button>
      `;
      jobCard.querySelector("button").addEventListener("click", () => selectJob(job));
      jobsList.appendChild(jobCard);
    });
  }

  document.getElementById("cv-analysis-section").classList.add("hidden");
  document.getElementById("job-recommendations-section").classList.remove("hidden");
}

function selectJob(job) {
  selectedJobId = job.id;
  currentInterviewData.selectedJobTitle = job.title || "Unknown";
  const jobTitle = job.title || "Unknown";
  if (!hrStats.positionStats[jobTitle]) {
    hrStats.positionStats[jobTitle] = { total: 0, completed: 0, passed: 0, failed: 0 };
  }
  hrStats.positionStats[jobTitle].total += 1;
  updateHrDashboardUI();
  showInterviewSetup(job);
  setActiveStep(5);
}

function showInterviewSetup(job) {
  document.getElementById("job-selected-title").textContent = `You selected: ${job.title}`;
  document.getElementById("interview-job-title").textContent = job.title;
  document.getElementById("interview-company").textContent = job.company;

  document.getElementById("job-recommendations-section").classList.add("hidden");
  document.getElementById("interview-setup-section").classList.remove("hidden");

  enableStartInterview();
}

function enableStartInterview() {
  const startInterviewBtn = document.getElementById("start-interview-btn");
  if (!startInterviewBtn) return;
  startInterviewBtn.disabled = false;
  startInterviewBtn.classList.remove("opacity-70", "cursor-not-allowed");
  startInterviewBtn.classList.add("hover:bg-green-700", "transform", "hover:scale-105");
}

function startInterviewFromJob() {
  if (!selectedJobId) {
    showError("No job selected");
    return;
  }

  if (!currentInterviewData.candidateName) {
    showError("Candidate name not found");
    return;
  }

  socket.emit("start-interview", {
    role: "general",
    candidateName: currentInterviewData.candidateName,
    jobId: selectedJobId,
    sessionId: sessionId
  });
}

function backToCV() {
  document.getElementById("job-recommendations-section").classList.add("hidden");
  document.getElementById("cv-analysis-section").classList.remove("hidden");
  setActiveStep(3);
}

function backToJobsRecommendations() {
  document.getElementById("interview-setup-section").classList.add("hidden");
  document.getElementById("job-recommendations-section").classList.remove("hidden");
  setActiveStep(4);
}

// ===== INTERVIEW FUNCTIONS =====

function addMessage(sender, message, type = "message") {
  const chatMessages = document.getElementById("chat-messages");
  const messageDiv = document.createElement("div");
  messageDiv.className = "chat-bubble";

  if (sender === "ai") {
    messageDiv.innerHTML = `
      <div class="bg-blue-50 border-l-4 border-blue-500 p-4 rounded text-gray-800">
        <strong class="text-blue-600">AI Interviewer:</strong>
        <p class="mt-2 whitespace-pre-wrap">${message}</p>
      </div>`;
  } else if (sender === "user") {
    messageDiv.innerHTML = `
      <div class="bg-green-50 border-l-4 border-green-500 p-4 rounded text-gray-800">
        <strong class="text-green-600">Your Answer:</strong>
        <p class="mt-2 whitespace-pre-wrap">${message}</p>
      </div>`;
  }

  chatMessages.appendChild(messageDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function startInterview(data) {
  const interviewSection = document.getElementById("interview-section");
  const cvUploadSection = document.getElementById("cv-upload-section");
  const faceRecognitionSection = document.getElementById("face-recognition-section");
  const cvAnalysisSection = document.getElementById("cv-analysis-section");
  const jobRecommendationsSection = document.getElementById("job-recommendations-section");
  const interviewSetupSection = document.getElementById("interview-setup-section");
  const resultsSection = document.getElementById("results-section");

  cvUploadSection.classList.add("hidden");
  faceRecognitionSection.classList.add("hidden");
  cvAnalysisSection.classList.add("hidden");
  jobRecommendationsSection.classList.add("hidden");
  interviewSetupSection.classList.add("hidden");
  resultsSection.classList.add("hidden");
  interviewSection.classList.remove("hidden");

  const progressBar = document.getElementById("step-progress-bar");
  if (progressBar) progressBar.style.display = "none";

  const currentRole = document.getElementById("current-role");
  if (currentRole) {
    currentRole.textContent = data.jobTitle || data.role || "Interview";
  }

  const candidateName = currentInterviewData.candidateName || data.candidateName || "Unknown";
  const jobTitle = data.jobTitle || data.role || "General";
  addOrUpdateCandidateHistory(candidateName, jobTitle, 0, "In Progress");
  if (hrStats.totalApplicants === 0) {
    hrStats.totalApplicants = 1;
  }
  updateHrDashboardUI();

  addMessage("ai", data.message, "welcome");

  if (data.firstQuestion) {
    setTimeout(() => {
      displayNextQuestion(data.firstQuestion);
    }, 1000);
  }

  const answerInput = document.getElementById("answer-input");
  if (answerInput) {
    setTimeout(() => { answerInput.focus(); }, 1500);
  }

  showNotification("💪 You got this! Remember to take your time with each answer", "info");

  // Aktifkan anti-cheat & deteksi emosi
  if (window.advancedHooks && window.advancedHooks.onInterviewStarted) {
    window.advancedHooks.onInterviewStarted(sessionId, data.role || "general");
  }
}

function displayNextQuestion(questionData) {
  currentQuestion = questionData;

  const questionCounter = document.getElementById("question-counter");
  const currentQuestionText = document.getElementById("current-question-text");

  if (questionCounter) {
    questionCounter.textContent = `${questionData.questionNumber}/${questionData.totalQuestions}`;
  }

  if (currentQuestionText) {
    currentQuestionText.textContent = questionData.question;
  }

  addMessage("ai", questionData.question, "question");

  const answerInput = document.getElementById("answer-input");
  if (answerInput) {
    answerInput.value = "";
    answerInput.focus();
  }

  updateCharCount();

  if (window.advancedHooks && window.advancedHooks.onNewQuestion) {
    window.advancedHooks.onNewQuestion(questionData.questionNumber || 1);
  }
}

function displayAnswerEvaluation(evaluation) {
  const feedback = `Score: ${evaluation.score}/100\n\n💬 Feedback: ${evaluation.feedback}`;
  addMessage("ai", feedback, "evaluation");

  const submitAnswerBtn = document.getElementById("submit-answer-btn");
  if (submitAnswerBtn) {
    submitAnswerBtn.disabled = false;
    submitAnswerBtn.innerHTML = '<i class="fas fa-paper-plane mr-2"></i>Submit Answer';
  }

  showTypingIndicator();
}

function showTypingIndicator() {
  const chatMessages = document.getElementById("chat-messages");
  const typingDiv = document.createElement("div");
  typingDiv.className = "flex items-center space-x-2 text-gray-500 italic";
  typingDiv.id = "typing-indicator";
  typingDiv.innerHTML = `
    <div class="typing-indicator"></div>
    <span>Python AI is preparing the next question...</span>`;
  chatMessages.appendChild(typingDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function hideTypingIndicator() {
  const typingIndicator = document.getElementById("typing-indicator");
  if (typingIndicator) typingIndicator.remove();
}

async function submitAnswer() {
  const answerInput = document.getElementById("answer-input");
  const answer = answerInput.value.trim();

  if (answer.length < 10) {
    showError("Please provide a detailed answer (at least 10 characters)");
    return;
  }

  if (!currentQuestion) {
    showError("No question available");
    return;
  }

  if (window.advancedHooks && window.advancedHooks.onBeforeSubmitAnswer) {
    await window.advancedHooks.onBeforeSubmitAnswer(answer);
  }

  const submitAnswerBtn = document.getElementById("submit-answer-btn");
  submitAnswerBtn.disabled = true;
  submitAnswerBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Evaluating...';

  addMessage("user", answer, "answer");

  socket.emit("submit-answer", {
    answer: answer,
    question: currentQuestion.question,
  });

  answerInput.value = "";
  updateCharCount();
}

function showInterviewResults(summary) {
  const interviewSection = document.getElementById("interview-section");
  const resultsSection = document.getElementById("results-section");

  interviewSection.classList.add("hidden");
  resultsSection.classList.remove("hidden");

  document.getElementById("final-score").textContent = summary.averageScore;
  const threshold = 60; // threshold lebih realistis, bisa diatur lagi
  const passStatus = summary.averageScore >= threshold;
  const passStatusEl = document.getElementById("pass-status");
  passStatusEl.textContent = passStatus ? `Lulus (Skor minimum ${threshold})` : `Tidak Lulus (skor di bawah ${threshold})`;
  passStatusEl.className = passStatus ? "text-green-600 font-semibold" : "text-red-600 font-semibold";

  document.getElementById("score-label").textContent = getScoreLabel(summary.averageScore);

  const answerQuality = summary.aiInsights?.answer_quality ?? 0;
  const impactFocus = summary.aiInsights?.impact_focus ?? 0;
  document.getElementById("answer-quality-score").textContent = `${Math.round(answerQuality * 100)}%`;
  document.getElementById("impact-focus-score").textContent = `${Math.round(impactFocus * 100)}%`;

  if (!passStatus && summary.improvementAreas && summary.improvementAreas.length > 0) {
    summary.overallFeedback = summary.overallFeedback + "\nPerbaiki: " + summary.improvementAreas.join(", ");
  }

  document.getElementById("overall-feedback").textContent = summary.overallFeedback;

  // Wawasan yang Didukung AI
  const aiInsightsEl = document.getElementById("ai-insights");
  aiInsightsEl.innerHTML = "";
  if (summary.aiInsights) {
    const insightEntries = Object.entries(summary.aiInsights);
    insightEntries.forEach(([key, value]) => {
      if (key === "summary") return;
      const card = document.createElement("div");
      card.className = "bg-white rounded-lg border border-gray-200 p-4";
      card.innerHTML = `<h4 class='font-semibold text-gray-800 mb-2'>${toTitleCase(key.replace(/_/g, ' '))}</h4><p>${(typeof value === 'number' ? (value * 100).toFixed(0) + '%': value)}</p>`;
      aiInsightsEl.appendChild(card);
    });
    if (summary.aiInsights.summary) {
      const summaryCard = document.createElement("div");
      summaryCard.className = "bg-white rounded-lg border border-gray-200 p-4 md:col-span-2";
      summaryCard.innerHTML = `<h4 class='font-semibold text-gray-800 mb-2'>Ringkasan Wawasan AI</h4><p>${summary.aiInsights.summary}</p>`;
      aiInsightsEl.appendChild(summaryCard);
    }
  } else {
    aiInsightsEl.innerHTML = "<p>Tidak ada wawasan AI.</p>";
  }

  // Kekuatan dan Area perbaikan
  const strengthsEl = document.getElementById("strengths-list");
  const improvementEl = document.getElementById("improvement-list");
  strengthsEl.innerHTML = "";
  improvementEl.innerHTML = "";

  (summary.strengths || []).forEach((item) => {
    const li = document.createElement("div");
    li.textContent = item;
    strengthsEl.appendChild(li);
  });

  (summary.improvementAreas || []).forEach((item) => {
    const li = document.createElement("div");
    li.textContent = item;
    improvementEl.appendChild(li);
  });

  if ((summary.strengths || []).length === 0) {
    strengthsEl.innerHTML = '<div>Tidak ada kekuatan teridentifikasi.</div>';
  }
  if ((summary.improvementAreas || []).length === 0) {
    improvementEl.innerHTML = '<div>Tidak ada area perbaikan yang ditemukan.</div>';
  }

  // Umpan Balik Terperinci
  const detailedFeedbackEl = document.getElementById("detailed-feedback");
  detailedFeedbackEl.innerHTML = "";
  if (summary.detailedFeedback && summary.detailedFeedback.length > 0) {
    summary.detailedFeedback.forEach((entry, idx) => {
      const card = document.createElement("div");
      card.className = "bg-white p-4 rounded-lg border border-gray-200";
      card.innerHTML = `
        <h4 class='font-semibold text-gray-800 mb-1'>Pertanyaan ${idx + 1}: ${entry.question}</h4>
        <p><strong>Jawaban:</strong> ${entry.answer}</p>
        <p><strong>Skor:</strong> ${entry.score}</p>
        <p><strong>Feedback:</strong> ${entry.feedback}</p>
        <p><strong>Follow-up:</strong> ${entry.follow_up}</p>
      `;
      detailedFeedbackEl.appendChild(card);
    });
  } else {
    detailedFeedbackEl.innerHTML = '<div>Tidak ada umpan balik terperinci.</div>';
  }

  currentInterviewData.results = summary;

  const isPass = passStatus;
  if (isPass) {
    hrStats.passedCandidates += 1;
  } else {
    hrStats.failedCandidates += 1;
  }

  const candidateNameFinal = currentInterviewData.candidateName || "Unknown";
  const currentJobTitle = currentInterviewData.selectedJobTitle || document.getElementById("interview-job-title")?.textContent || "Unknown";
  const scoreFinal = toFiniteNumber(summary.averageScore, 0);

  addOrUpdateCandidateHistory(candidateNameFinal, currentJobTitle, scoreFinal, isPass ? 'Lulus' : 'Gagal');

  hrStats.completedInterviews += 1;
  hrStats.totalScore = toFiniteNumber(hrStats.totalScore, 0) + scoreFinal;

  if (!hrStats.positionStats[currentJobTitle]) {
    hrStats.positionStats[currentJobTitle] = { total: 0, completed: 0, passed: 0, failed: 0 };
  }
  hrStats.positionStats[currentJobTitle].completed += 1;
  if (isPass) {
    hrStats.positionStats[currentJobTitle].passed += 1;
  } else {
    hrStats.positionStats[currentJobTitle].failed += 1;
  }

  updateHrDashboardUI();
  refreshHrStats();
  showNotification("Interview completed! 🎊", "success");

  if (window.advancedHooks && window.advancedHooks.onInterviewCompleted) {
    window.advancedHooks.onInterviewCompleted(sessionId);
  }
}

function toTitleCase(str) {
  return str.replace(/\w\S*/g, function(txt){
    return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
  });
}

function getScoreLabel(score) {
  if (score >= 90) return "Excellent";
  if (score >= 80) return "Very Good";
  if (score >= 70) return "Good";
  if (score >= 60) return "Fair";
  return "Needs Improvement";
}

function restartInterview() {
  location.reload();
}

function downloadResults() {
  if (!currentInterviewData.results) {
    showError("No results to download");
    return;
  }

  // Generate Word-compatible HTML content
  const results = currentInterviewData.results;
  const cvAnalysis = currentInterviewData.cvAnalysis || {};
  const candidateName = currentInterviewData.candidateName || "-";

  const htmlContent = `
    <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word" xmlns="http://www.w3.org/TR/REC-html40">
      <head><meta charset="utf-8"><title>Penilaian Interview</title></head>
      <body>
        <h1>Penilaian Interview</h1>
        <p><strong>Nama Kandidat:</strong> ${candidateName}</p>
        <h2>Deskripsi Akhir Penilaian Interview</h2>
        <p><strong>Skor Akhir:</strong> ${results.averageScore || "-"}</p>
        <p><strong>Label:</strong> ${results.label || getScoreLabel(results.averageScore || 0)}</p>
        <p><strong>Umpan Balik:</strong> ${results.overallFeedback || "-"}</p>

        <h3>Rangkuman CV</h3>
        <p><strong>Level Pengalaman:</strong> ${cvAnalysis.experience_level || "-"}</p>
        <p><strong>Total Skill Ditemukan:</strong> ${cvAnalysis.total_skills_found || "-"}</p>
        <p><strong>Summary:</strong> ${cvAnalysis.summary ? JSON.stringify(cvAnalysis.summary) : "-"}</p>

        <h3>Detail Interview</h3>
        <ul>
          ${results.details ? results.details.map(item => `<li><strong>${item.question}</strong>: ${item.answer} (Score: ${item.score || "-"})</li>`).join("") : "<li>Tidak ada detail pertanyaan</li>"}
        </ul>
      </body>
    </html>
  `;

  const blob = new Blob([htmlContent], { type: "application/msword" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `hasil-interview-${new Date().getTime()}.doc`;
  a.click();
}

// ===== UTILITY FUNCTIONS =====

function setupCharacterCounter() {
  const answerInput = document.getElementById("answer-input");
  if (answerInput) {
    answerInput.addEventListener("input", updateCharCount);
  }
}

function updateCharCount() {
  const answerInput = document.getElementById("answer-input");
  const charCount = document.getElementById("char-count");
  const submitAnswerBtn = document.getElementById("submit-answer-btn");

  if (charCount && answerInput) {
    const count = answerInput.value.length;
    charCount.textContent = count;
    if (submitAnswerBtn) {
      submitAnswerBtn.disabled = count < 10;
    }
  }
}

// ===== WEBCAM (FIXED) =====
async function toggleWebcam() {
  const webcamVideo = document.getElementById("webcam-video");
  const webcamToggleBtn = document.getElementById("webcam-toggle-btn");
  const webcamPlaceholder = document.getElementById("webcam-placeholder");
  const webcamStatus = document.getElementById("webcam-status");

  if (localStream && localStream.getVideoTracks().length > 0) {
    // Turn OFF
    localStream.getTracks().forEach((track) => track.stop());
    localStream = null;
    webcamVideo.srcObject = null;
    webcamVideo.style.display = "none";
    if (webcamPlaceholder) webcamPlaceholder.style.display = "flex";
    if (webcamStatus) webcamStatus.textContent = 'Click "Enable Webcam" to start monitoring';
    webcamToggleBtn.innerHTML = '<i class="fas fa-camera mr-1"></i>Enable Webcam';
    webcamToggleBtn.className = webcamToggleBtn.className.replace("bg-red-600 hover:bg-red-700", "bg-blue-600 hover:bg-blue-700");
    if (window.advancedHooks && window.advancedHooks.onWebcamStateChange) {
      window.advancedHooks.onWebcamStateChange();
    }
  } else {
    // Turn ON
    try {
      localStream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
      webcamVideo.srcObject = localStream;
      webcamVideo.style.display = "block";
      // FIXED: hide placeholder & update status
      if (webcamPlaceholder) webcamPlaceholder.style.display = "none";
      if (webcamStatus) {
        webcamStatus.innerHTML = '<span class="text-green-600 font-semibold">🟢 Webcam active — you are being monitored</span>';
      }
      webcamToggleBtn.innerHTML = '<i class="fas fa-camera mr-1"></i>Disable Webcam';
      showNotification("Webcam enabled", "success");
      if (window.advancedHooks && window.advancedHooks.onWebcamStateChange) {
        setTimeout(() => window.advancedHooks.onWebcamStateChange(), 300);
      }
    } catch (error) {
      showError("Webcam access denied");
    }
  }
}

// ===== AUDIO & RECORDING (FIXED + ENHANCED) =====

async function toggleMicrophone() {
  try {
    if (isMicEnabled) {
      // Turn OFF mic
      if (mediaRecorder && mediaRecorder.stream) {
        mediaRecorder.stream.getTracks().forEach((track) => track.stop());
      }
      if (audioContext) {
        audioContext.close();
        audioContext = null;
      }
      stopWaveform();
      isMicEnabled = false;
      document.getElementById("mic-toggle-btn").innerHTML = '<i class="fas fa-microphone mr-1"></i>Enable';
      document.getElementById("record-btn").disabled = true;

      // Show idle text again
      const idleText = document.getElementById("waveform-idle-text");
      if (idleText) idleText.style.display = "flex";

    } else {
      // Turn ON mic
      const audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(audioStream);
      isMicEnabled = true;
      document.getElementById("record-btn").disabled = false;
      document.getElementById("mic-toggle-btn").innerHTML = '<i class="fas fa-microphone-slash mr-1"></i>Disable';
      showNotification("Microphone enabled — klik Start Recording lalu bicara!", "success");

      // Hide idle text
      const idleText = document.getElementById("waveform-idle-text");
      if (idleText) idleText.style.display = "none";

      // Setup waveform visualizer
      audioContext = new (window.AudioContext || window.webkitAudioContext)();
      analyser = audioContext.createAnalyser();
      analyser.fftSize = 64;
      const source = audioContext.createMediaStreamSource(audioStream);
      source.connect(analyser);
      drawWaveform();
    }
  } catch (error) {
    showError("Microphone access denied");
  }
}

function drawWaveform() {
  const canvas = document.getElementById("waveform-canvas");
  if (!canvas || !analyser) return;
  const ctx = canvas.getContext("2d");
  const bufferLength = analyser.frequencyBinCount;
  const dataArray = new Uint8Array(bufferLength);

  function draw() {
    waveformAnimFrame = requestAnimationFrame(draw);
    analyser.getByteFrequencyData(dataArray);
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const barWidth = (canvas.width / bufferLength) * 2.2;
    let x = 0;
    for (let i = 0; i < bufferLength; i++) {
      const barHeight = (dataArray[i] / 255) * canvas.height;
      const gradient = ctx.createLinearGradient(0, canvas.height, 0, 0);
      gradient.addColorStop(0, isRecording ? "#ef4444" : "#6366f1");
      gradient.addColorStop(1, isRecording ? "#f97316" : "#a78bfa");
      ctx.fillStyle = gradient;
      ctx.beginPath();
      // Fallback for browsers without roundRect
      if (ctx.roundRect) {
        ctx.roundRect(x, canvas.height - barHeight, barWidth - 2, Math.max(barHeight, 2), 2);
      } else {
        ctx.rect(x, canvas.height - barHeight, barWidth - 2, Math.max(barHeight, 2));
      }
      ctx.fill();
      x += barWidth;
    }
  }
  draw();
}

function stopWaveform() {
  if (waveformAnimFrame) {
    cancelAnimationFrame(waveformAnimFrame);
    waveformAnimFrame = null;
  }
  const canvas = document.getElementById("waveform-canvas");
  if (canvas) {
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }
}

function startRecording() {
  if (!mediaRecorder || !isMicEnabled) return;
  audioChunks = [];

  mediaRecorder.ondataavailable = (e) => {
    if (e.data.size > 0) audioChunks.push(e.data);
  };

  mediaRecorder.onstop = () => {
    // Create audio playback after recording stops
    const blob = new Blob(audioChunks, { type: "audio/webm" });
    const url = URL.createObjectURL(blob);

    let player = document.getElementById("audio-playback");
    if (!player) {
      player = document.createElement("audio");
      player.id = "audio-playback";
      player.controls = true;
      player.className = "w-full mt-2 rounded-lg border border-gray-200";
      const waveformEl = document.getElementById("audio-waveform");
      if (waveformEl && waveformEl.parentNode) {
        waveformEl.parentNode.insertBefore(player, waveformEl.nextSibling);
      }
    }
    player.src = url;

    // Add playback label if not exists
    if (!document.getElementById("playback-label")) {
      const label = document.createElement("p");
      label.id = "playback-label";
      label.className = "text-xs text-gray-500 mt-1 text-center";
      label.textContent = "🔊 Dengarkan rekaman sebelum submit";
      player.parentNode.insertBefore(label, player.nextSibling);
    }

    showNotification("✅ Rekaman selesai — dengarkan atau submit jawaban!", "success");
  };

  mediaRecorder.start(100); // collect data every 100ms
  isRecording = true;
  recordingStartTime = Date.now();

  // Update UI → recording state
  document.getElementById("record-btn").disabled = true;
  document.getElementById("stop-record-btn").disabled = false;

  const statusEl = document.getElementById("recording-status");
  const pulseEl = document.getElementById("recording-pulse");
  if (statusEl) {
    statusEl.textContent = "● REC";
    statusEl.className = "text-xs bg-red-100 text-red-700 px-2 py-1 rounded font-bold";
  }
  if (pulseEl) {
    pulseEl.className = "w-3 h-3 bg-red-500 rounded-full animate-pulse";
  }

  // ===== DURATION TIMER (FIXED) =====
  durationInterval = setInterval(() => {
    const elapsed = Math.floor((Date.now() - recordingStartTime) / 1000);
    const mins = String(Math.floor(elapsed / 60)).padStart(2, "0");
    const secs = String(elapsed % 60).padStart(2, "0");
    const durEl = document.getElementById("recording-duration");
    if (durEl) durEl.textContent = `${mins}:${secs}`;
  }, 1000);

  // ===== SPEECH-TO-TEXT → AUTO-FILL ANSWER =====
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SR) {
    speechRecognition = new SR();
    speechRecognition.lang = "en-US"; //ini loh kalau mau ubah interview ke indo ganti jadi ID
    speechRecognition.continuous = true;
    speechRecognition.interimResults = true;

    let finalTranscript = "";

    speechRecognition.onresult = (event) => {
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript + " ";
        } else {
          interim += event.results[i][0].transcript;
        }
      }
      const answerInput = document.getElementById("answer-input");
      if (answerInput) {
        answerInput.value = finalTranscript + interim;
        updateCharCount();
        answerInput.scrollTop = answerInput.scrollHeight;
      }
    };

    speechRecognition.onerror = (e) => {
      if (e.error !== "no-speech") {
        console.warn("Speech recognition error:", e.error);
      }
    };

    // Auto-restart jika browser stop sendiri aseli cuy
    speechRecognition.onend = () => {
      if (isRecording && speechRecognition) {
        try { speechRecognition.start(); } catch (e) { /* already started */ }
      }
    };

    speechRecognition.start();
    showNotification("🎙️ Bicara sekarang — jawaban otomatis terisi di kolom!", "info");
  } else {
    showNotification("⚠️ Browser tidak support speech-to-text, silakan ketik manual", "info");
  }
}

function stopRecording() {
  if (!mediaRecorder || !isRecording) return;
  isRecording = false;

  mediaRecorder.stop();

  
  if (speechRecognition) {
    speechRecognition.onend = null; 
    try { speechRecognition.stop(); } catch (e) {}
    speechRecognition = null;
  }

  
  clearInterval(durationInterval);
  durationInterval = null;

  
  document.getElementById("record-btn").disabled = false;
  document.getElementById("stop-record-btn").disabled = true;

  const statusEl = document.getElementById("recording-status");
  const pulseEl = document.getElementById("recording-pulse");
  if (statusEl) {
    statusEl.textContent = "Idle";
    statusEl.className = "text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded";
  }
  if (pulseEl) {
    pulseEl.className = "w-3 h-3 bg-gray-400 rounded-full";
  }
}

function speakQuestion() {
  if (!currentQuestion) {
    showError("No question to speak");
    return;
  }
  const utterance = new SpeechSynthesisUtterance(currentQuestion.question);
  utterance.rate = 0.95;
  window.speechSynthesis.speak(utterance);
}

function showError(message) {
  alert("Error: " + message);
}

function showNotification(message, type = "info") {
  console.log(`[${type.toUpperCase()}] ${message}`);

  // Visual toast notification
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    container.className = "fixed bottom-6 right-6 z-50 flex flex-col gap-2";
    document.body.appendChild(container);
  }

  const colorMap = {
    info: "bg-blue-600",
    success: "bg-green-600",
    error: "bg-red-600",
    warning: "bg-yellow-500",
  };

  const toast = document.createElement("div");
  toast.className = `${colorMap[type] || "bg-gray-700"} text-white px-4 py-3 rounded-lg shadow-lg text-sm font-medium flex items-center gap-2 transition-all duration-300 opacity-0 translate-y-2`;
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);

  // Animate in
  requestAnimationFrame(() => {
    toast.classList.remove("opacity-0", "translate-y-2");
    toast.classList.add("opacity-100", "translate-y-0");
  });

  // Auto remove after 3.5s
  setTimeout(() => {
    toast.classList.add("opacity-0");
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ===== Face Recognition Helpers =====

function showFaceResult(message, success = false) {
  const faceResult = document.getElementById("face-result");
  if (!faceResult) return;
  faceResult.classList.add('anim-fade-up');
  faceResult.innerHTML = `<i class="fas fa-${success ? 'check-circle text-green-600' : 'times-circle text-red-600'} mr-2"></i><span class="text-gray-800">${message}</span>`;
  faceResult.style.color = success ? "#166534" : "#991b1b";
  faceResult.style.borderColor = success ? "#86efac" : "#fca5a5";
  faceResult.style.backgroundColor = success ? "#f0fdf4" : "#fef2f2";
}

async function uploadReference(event) {
  event.preventDefault();
  const fileInput = document.getElementById("reference-image-input");
  if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
    showFaceResult("Pilih file referensi terlebih dahulu.", false);
    return;
  }

  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append("reference_image", file);
  formData.append("sessionId", sessionId);

  try {
    const res = await fetch("/upload_reference", { method: "POST", body: formData });
    const data = await res.json();
    if (data.success) {
      faceReferenceUploaded = true;
      showFaceResult(data.message, true);
    } else {
      showFaceResult(data.message, false);
    }
  } catch (err) {
    showFaceResult("Gagal upload referensi: " + err, false);
  }
}

function displayFaceDatabaseList(faces) {
  faceDatabase = faces || [];
  const listEl = document.getElementById("face-database-list");
  const countEl = document.getElementById("face-db-count");
  if (!listEl || !countEl) return;
  countEl.textContent = faceDatabase.length;
  if (faceDatabase.length === 0) {
    listEl.innerHTML = '<div>Tidak ada wajah terdaftar.</div>';
    return;
  }
  listEl.innerHTML = faceDatabase.map(item =>
    `<div class="px-3 py-2 bg-indigo-50 rounded-lg border border-indigo-200 text-indigo-900 text-sm">${item.name}</div>`
  ).join('');
}

async function loadFaceDatabase(event) {
  if (event && event.preventDefault) event.preventDefault();
  try {
    const res = await fetch('/face_list');
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    const data = await res.json();
    if (data.success) {
      displayFaceDatabaseList(data.faces);
      showFaceResult('Database wajah dimuat.', true);
    } else {
      showFaceResult('Gagal memuat database wajah.', false);
    }
  } catch (err) {
    showFaceResult('Gagal memuat database wajah: ' + err.message, false);
  }
}

async function clearFaceDatabase(event) {
  if (event && event.preventDefault) event.preventDefault();
  const confirmed = confirm('Apakah Anda yakin ingin menghapus semua data wajah?');
  if (!confirmed) return;
  try {
    const res = await fetch('/face_clear', { method: 'POST' });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    const data = await res.json();
    if (data.success) {
      displayFaceDatabaseList([]);
      showFaceResult(data.message, true);
    } else {
      showFaceResult(data.message, false);
    }
  } catch (err) {
    showFaceResult('Gagal menghapus database: ' + err.message, false);
  }
}

function captureFrameFromVideo() {
  const video = document.getElementById("face-video");
  const canvas = document.getElementById("face-canvas");
  if (!video || !canvas) return null;
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  return canvas.toDataURL("image/jpeg");
}

async function registerFace(event) {
  event.preventDefault();
  const nameInput = document.getElementById("register-name-input");
  const name = nameInput?.value.trim();
  if (!name) {
    showFaceResult("Masukkan nama pengguna sebelum mendaftar wajah.", false);
    return;
  }
  if (!faceStream) {
    if (faceMode === 'server') {
      setFaceMode('browser');
    }
    showFaceResult("Mengaktifkan kamera browser untuk registrasi...", true);
    await startFaceCamera(event);
    if (!faceStream) return;
  }
  const dataUrl = captureFrameFromVideo();
  if (!dataUrl) {
    showFaceResult("Gagal menangkap frame dari kamera.", false);
    return;
  }
  try {
    const res = await fetch('/face_register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, captured_image: dataUrl })
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    const data = await res.json();
    if (data.success) {
      showFaceResult(data.message, true);
      nameInput.value = '';
      loadFaceDatabase();
    } else {
      showFaceResult(data.message, false);
    }
  } catch (err) {
    showFaceResult('Gagal mendaftarkan wajah: ' + err.message, false);
  }
}

async function verifyDatabase(event) {
  event.preventDefault();
  if (!faceStream) {
    showFaceResult("Aktifkan kamera dulu untuk verifikasi.", false);
    return;
  }
  const dataUrl = captureFrameFromVideo();
  if (!dataUrl) {
    showFaceResult("Gagal menangkap frame dari kamera.", false);
    return;
  }
  try {
    const res = await fetch('/verify_database', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ captured_image: dataUrl })
    });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    const data = await res.json();
    if (data.success && data.match) {
      faceRecognitionPassed = true;
      showFaceResult(`${data.message}`, true);
      updateFaceStatusBadge(true);
      enableProceedToAnalysis();
    } else if (data.success && !data.match) {
      faceRecognitionPassed = false;
      showFaceResult(data.message, false);
      updateFaceStatusBadge(false);
      disableProceedToAnalysis();
    } else {
      showFaceResult(data.message || 'Verifikasi database gagal.', false);
      disableProceedToAnalysis();
    }
  } catch (err) {
    showFaceResult('Gagal verifikasi database: ' + err.message, false);
    disableProceedToAnalysis();
  }
}

async function startFaceCamera(event) {
  if (event?.preventDefault) event.preventDefault();

  if (!document.getElementById("use-face-recognition").checked) {
    showFaceResult("Face recognition dinonaktifkan. Gunakan opsi Lewati jika perlu.", false);
    return;
  }

  const consent = confirm("Kamera browser akan digunakan untuk verifikasi identitas. Lanjut?");
  if (!consent) {
    showFaceResult("Persetujuan dibatalkan.", false);
    return;
  }

  try {
    stopLiveAbsensi();
    faceStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false });
    const video = document.getElementById("face-video");
    const placeholder = document.getElementById("face-feed-placeholder");
    const liveImg = document.getElementById("face-live-feed");
    video.srcObject = faceStream;
    video.classList.remove("hidden");
    placeholder?.classList.add("hidden");
    liveImg?.classList.add("hidden");
    await video.play();
    showFaceResult("Kamera browser aktif. Silakan capture atau verifikasi wajah.", true);
  } catch (err) {
    showFaceResult("Gagal mengakses kamera: " + err.message, false);
  }
}

async function captureFace(event) {
  event.preventDefault();

  if (!document.getElementById("use-face-recognition").checked) {
    showFaceResult("Face recognition dinonaktifkan. Gunakan opsi Lewati jika perlu.", false);
    return;
  }

  if (!faceReferenceUploaded) {
    showFaceResult("Upload foto referensi terlebih dahulu.", false);
    return;
  }

  if (!faceStream) {
    showFaceResult("Kamera belum diaktifkan.", false);
    return;
  }

  const video = document.getElementById("face-video");
  const canvas = document.getElementById("face-canvas");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  const dataUrl = canvas.toDataURL("image/jpeg");

  try {
    const res = await fetch("/verify_face", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sessionId, captured_image: dataUrl }),
    });
    const data = await res.json();

    if (data.success && data.match) {
      faceRecognitionPassed = true;
      showFaceResult(data.message, true);
      updateFaceStatusBadge(true);
      enableProceedToAnalysis();

      setTimeout(() => {
        stopFaceCamera();
        showFaceResult("✅ Verifikasi berhasil! Kamera dimatikan. Klik 'Lanjut ke Analisis CV'.", true);
      }, 1500);

    } else if (data.success && !data.match) {
      faceRecognitionPassed = false;
      showFaceResult(data.message, false);
      updateFaceStatusBadge(false);
      disableProceedToAnalysis();
    } else {
      showFaceResult(data.message || "Verifikasi gagal.", false);
      disableProceedToAnalysis();
    }
  } catch (err) {
    showFaceResult("Gagal verifikasi: " + err, false);
    disableProceedToAnalysis();
  }
}

function skipFaceRecognition(event) {
  event.preventDefault();
  document.getElementById("use-face-recognition").checked = false;
  stopFaceCamera();
  faceRecognitionPassed = true;
  showFaceResult("Face verification dilewati. Anda dapat lanjut ke analisis CV.", true);
  updateFaceStatusBadge(true);
  enableProceedToAnalysis();
}