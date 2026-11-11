# 🎯 CV Workflow & Job Matching Feature

## 📋 Ringkasan Fitur

Fitur workflow CV telah berhasil ditambahkan ke AI Interview Platform. Workflow baru memungkinkan user untuk:

1. **Upload CV** - User mengunggah CV mereka dalam format teks
2. **CV Analysis** - Sistem menganalisis CV untuk mengekstrak skills, pengalaman, dan bahasa pemrograman
3. **Job Matching** - Sistem mencari job yang sesuai dengan CV user
4. **Job Selection** - User memilih job dari rekomendasi yang ditampilkan
5. **Interview** - User melakukan interview untuk posisi yang dipilih

---

## 🔄 Workflow Alur

```
┌─────────────────────┐
│   1. CV Upload      │ (Input CV dalam bentuk teks)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  2. CV Analysis & Extraction Skills  │ (AI menganalisis CV)
│     - Detect experience level        │
│     - Extract programming languages  │
│     - Identify frameworks & tools    │
└──────────┬──────────────────────────┘
           │
           ▼
┌──────────────────────────────┐
│  3. Job Recommendations      │ (AI mencari job matching)
│     - Match skills vs job req │
│     - Show match score        │
│     - Display top 5 jobs      │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────┐
│  4. Job Selection        │ (User pilih job)
│     - View job details   │
│     - Select position    │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  5. Interview Setup      │ (Persiapan interview)
│     - Show job info      │
│     - Ready button       │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────────────┐
│  6. Start Interview              │ (Wawancara dimulai)
│     - Role-specific questions    │
│     - Real-time feedback         │
│     - Performance analysis       │
└──────────────────────────────────┘
```

---

## 🛠️ Komponen yang Ditambahkan

### Backend (Python/Flask)

#### **1. ai_engine.py - Kelas Baru**

- **`CVAnalyzer`** - Menganalisis CV dan mengekstrak informasi
  - `analyze_cv_text()` - Ekstrak skills dari teks CV
  - `_determine_experience_level()` - Tentukan level pengalaman
  - Deteksi: Programming Languages, Frameworks, Databases, DevOps, Data Science, Soft Skills

- **`JobDatabase`** - Database job listings
  - `get_all_jobs()` - Get semua job (~8 posisi tersedia)
  - `filter_by_experience()` - Filter berdasarkan level
  - `filter_by_location()` - Filter berdasarkan lokasi

- **`JobMatcher`** - Mencocokkan CV dengan job
  - `calculate_match_score()` - Hitung similarity score
  - `get_recommended_jobs()` - Dapatkan rekomendasi (top 5)
  - Scoring: 70% skills match + 30% experience level match

#### **2. app.py - Routes Baru**

```python
POST /api/upload-cv          # Upload dan analyze CV
POST /api/analyze-cv         # Get CV analysis details
GET  /api/get-jobs           # Get semua jobs
POST /api/recommended-jobs   # Get job recommendations
GET  /api/job-details/<id>   # Get detail spesific job
```

#### **3. Socket.IO Events Update**

- `start-interview` sekarang menerima `jobId` parameter
- Auto-detect interview role berdasarkan job title
- Update session dengan job information

### Frontend (HTML/JavaScript)

#### **1. templates/index.html - Sections Baru**

**Step 1: CV Upload Section**
- Input nama kandidat
- Text area untuk CV/Resume
- Show loading state saat analyzing

**Step 2: CV Analysis Section**
- Display experience level badge
- Show total skills found
- List programming languages
- List all extracted skills
- Button ke job recommendations

**Step 3: Job Recommendations Section**
- Display job cards dengan match percentage
- Show matched skills (green badges)
- Show missing skills (yellow badges)
- Display company, location, salary range
- Select button untuk setiap job

**Step 4: Interview Setup Section**
- Show job details yang dipilih
- Company & job title preview
- Question count & duration info
- Start interview button
- Choose different job button

#### **2. static/script.js - Functions Baru**

```javascript
// CV Workflow Functions
handleCVUpload()              // Upload & analyze CV
showCVAnalysis()             // Display analysis results
getRecommendedJobs()         // Fetch job recommendations
displayJobRecommendations()  // Show job cards
selectJob()                  // Handle job selection
showInterviewSetup()         // Show interview ready screen
startInterviewFromJob()      // Start interview dengan job

// Helper Functions
generateSessionId()          // Create unique session
backToCV()                   // Navigate back to CV
backToJobsRecommendations() // Navigate back to jobs
```

---

## 📊 Job Database

Total **8 job listings** tersedia:

1. **Senior Software Developer** - 5+ tahun eksp
2. **Data Scientist** - Mid level
3. **Frontend Developer** - Junior level
4. **DevOps Engineer** - Mid level
5. **Junior Python Developer** - Junior level
6. **Full Stack Developer** - Mid level
7. **Product Manager** - Mid level
8. **QA Engineer** - Junior level

Setiap job memiliki:
- Job title & description
- Required skills
- Required experience level
- Salary range
- Company & location
- Employment type

---

## 🎯 Fitur-Fitur Utama

### 1. **CV Analysis Engine**
```
Skills Extraction:
├── Programming Languages (Python, JS, Java, C++, Go, Rust, etc)
├── Frontend (React, Vue, Angular, HTML, CSS, etc)
├── Backend (Node.js, Django, Flask, Spring, etc)
├── Databases (MySQL, PostgreSQL, MongoDB, Redis, etc)
├── DevOps (Docker, Kubernetes, AWS, Azure, Jenkins, etc)
├── Data Science (ML, TensorFlow, PyTorch, Pandas, etc)
├── Tools (Git, Jira, Slack, Linux, VS Code, etc)
└── Soft Skills (Leadership, Communication, Teamwork, etc)

Experience Level Detection:
- Entry Level (< 2 years)
- Junior (2-5 years)
- Mid Level (5-10 years)
- Senior (> 10 years)
```

### 2. **Job Matching Algorithm**
```
Match Score = (Skill Match % × 0.7) + (Experience Match × 100 × 0.3)

Skill Match: Intersection of CV skills vs required job skills
Experience Match: Compatibility antara CV level vs job level

Recommendation Filter: Hanya job dengan match score >= 50%
Sorting: Descending by match score
Limit: Top 5 jobs
```

### 3. **Session Management**
- Unique session ID untuk setiap user
- Persist CV analysis during session
- Track selected job
- Maintain user context through workflow

---

## 🚀 Cara Menggunakan

### Step-by-Step:

1. **Buka aplikasi** → http://localhost:5000

2. **Upload CV**
   - Masukkan nama lengkap
   - Paste CV/Resume Anda
   - Click "Analyze My CV"

3. **Lihat Analysis**
   - Review experience level
   - Check skills terdeteksi
   - Lihat programming languages
   - Click "Find Matching Jobs"

4. **Pilih Job**
   - Lihat job recommendations
   - Check match percentage
   - Review matched skills
   - Click "Select This Position"

5. **Siap Interview**
   - Review job details
   - Click "Start Interview"

6. **Wawancara**
   - Jawab pertanyaan yang diberikan
   - Get real-time feedback
   - Complete all 10 questions

7. **Hasil**
   - View score dan feedback
   - Download results

---

## 💡 Contoh CV untuk Testing

```
JOHN DOE
Senior Software Developer

EXPERIENCE:
- 8 years as Software Developer
- 5 years with Python, JavaScript, React
- 3 years with Docker, Kubernetes, AWS
- Experience with MongoDB, PostgreSQL
- Led team of 5 developers

SKILLS:
Python, JavaScript, React, Node.js, Django, Flask,
Docker, Kubernetes, AWS, Git, MongoDB, PostgreSQL,
HTML, CSS, REST API, Microservices, Agile, Leadership

EDUCATION:
Bachelor of Computer Science
```

Expected Result:
- Experience Level: **Senior**
- Total Skills: **20+**
- Recommended Jobs:
  1. Senior Software Developer (95% match)
  2. Full Stack Developer (85% match)
  3. DevOps Engineer (75% match)

---

## 📝 API Responses

### POST /api/upload-cv
```json
{
  "status": "success",
  "analysis": {
    "skills": ["python", "javascript", "react", ...],
    "experience_level": "senior",
    "total_skills_found": 20,
    "programming_languages": ["python", "javascript", ...],
    "frameworks": ["react", "nodejs", ...],
    "databases": ["mongodb", "postgresql"],
    "summary": {
      "experience_level": "senior",
      "categories_found": 7
    }
  }
}
```

### POST /api/recommended-jobs
```json
{
  "status": "success",
  "recommended_jobs": [
    {
      "id": 1,
      "title": "Senior Software Developer",
      "match_score": {
        "match_percentage": 95.0,
        "matched_skills": ["python", "javascript", "react", ...],
        "missing_skills": ["kubernetes"]
      }
    }
  ]
}
```

---

## 🔧 Teknologi Stack

**Backend:**
- Python 3.8+
- Flask 2.3.3
- Flask-SocketIO 5.3.6
- Custom NLP for CV Analysis

**Frontend:**
- HTML5 / CSS3 (Tailwind CSS)
- JavaScript (ES6+)
- Socket.IO Client

**AI Engine:**
- Text analysis & pattern matching
- Skills extraction
- Experience level detection
- Job matching algorithm

---

## 📋 Checklist Implementasi

- ✅ CV upload functionality
- ✅ CV analysis engine (skills extraction)
- ✅ Experience level detection
- ✅ Job database dengan 8 posisi
- ✅ Job matching algorithm
- ✅ Match score calculation
- ✅ Frontend workflow UI (5 sections)
- ✅ CV analysis display
- ✅ Job recommendations display
- ✅ Job selection flow
- ✅ Interview integration
- ✅ Session management
- ✅ Backend routes API
- ✅ Error handling
- ✅ Loading states

---

## 🎓 Cara Extend/Develop

### Tambah Job Baru
Di `ai_engine.py`, edit method `JobDatabase.get_all_jobs()`:

```python
{
    'id': 9,
    'title': 'Your Job Title',
    'description': 'Job description',
    'required_skills': ['skill1', 'skill2', ...],
    'required_experience': 'mid',  # entry, junior, mid, senior
    'salary_range': 'XX-XX juta',
    'company': 'Company Name',
    'location': 'City',
    'type': 'full-time'
}
```

### Improve CV Analysis
Tambahkan more skills atau patterns di `CVAnalyzer._load_skills_database()`:

```python
'your_category': [
    'skill1', 'skill2', 'skill3'
]
```

### Custom Matching Algorithm
Modifikasi `JobMatcher._calculate_experience_match()` untuk adjust scoring weights.

---

## 🐛 Known Limitations

1. CV parsing berbasis text matching (tidak full NLP)
2. Tidak support file upload (hanya text paste)
3. Job database statik (tidak dari database)
4. Matching algorithm simple (bisa di-improve dengan ML)
5. No user account/persistence

---

## 🚀 Future Improvements

1. **File Upload** - Support PDF/DOCX upload
2. **Real NLP** - Use spaCy/NLTK untuk better CV parsing
3. **Database** - Persist jobs ke database
4. **ML Matching** - Use ML model untuk better matching
5. **User Accounts** - Save user profiles & history
6. **Resume Optimization** - Suggest CV improvements
7. **Job Alerts** - Notify user tentang new matching jobs
8. **Analytics** - Track application metrics

---

## 📞 Support

Jika ada masalah:
1. Check console untuk error messages
2. Ensure server running: `python app.py`
3. Clear browser cache jika ada issue
4. Check Python syntax dengan `python -m py_compile filename.py`

---

✨ **Fitur telah berhasil diimplementasikan dan siap digunakan!** ✨
