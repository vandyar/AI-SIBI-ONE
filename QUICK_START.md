# ⚡ Quick Start Guide - CV Workflow Feature

## 🎯 5 Langkah Mulai

### 1️⃣ Start Server
```bash
python app.py
```
Buka browser: **http://localhost:5000**

### 2️⃣ Upload CV Anda
Gunakan format teks. Contoh minimal:

```
NAME: John Developer
EXPERIENCE: 5+ years
SKILLS: Python, JavaScript, React, Node.js, Docker, MongoDB
EDUCATION: BS Computer Science
```

> **Tips:** Semakin detail CV Anda, semakin akurat hasilnya!

### 3️⃣ Lihat CV Analysis
Sistem akan menampilkan:
- 📊 Experience Level (Entry/Junior/Mid/Senior)
- 🔧 Total Skills Ditemukan
- 💻 Programming Languages
- 🎯 Soft Skills

### 4️⃣ Pilih Job Recommendations
Lihat job yang cocok dengan:
- ✅ Match percentage (%)
- 🟢 Skills yang match (green)
- 🟡 Skills perlu dipelajari (yellow)
- 💼 Company & Lokasi
- 💰 Salary range

### 5️⃣ Mulai Interview
Siap? Klik "Start Interview" untuk:
- 🎤 10 pertanyaan terkait job
- 📝 Real-time AI feedback
- 📊 Performance scoring
- 🏆 Interview results

---

## 🧪 Testing dengan Sample CV

### Sample CV #1: Senior Developer
```
PROFILE: Senior Full Stack Developer

EXPERIENCE:
- 8 years software development
- 6 years with Python & JavaScript
- 4 years with React and Node.js
- 3 years DevOps (Docker, Kubernetes)
- 2 years with AWS

SKILLS:
Programming: Python, JavaScript, Java, TypeScript
Frontend: React, Vue, HTML, CSS, Responsive Design
Backend: Node.js, Django, Flask, Spring, REST API
DevOps: Docker, Kubernetes, AWS, Jenkins, Terraform
Databases: MongoDB, PostgreSQL, MySQL, Redis
Tools: Git, Jira, Linux, VS Code

ACHIEVEMENTS:
- Led team of 10 developers
- Decreased deployment time by 60%
- Architected microservices for 2M+ users
- Open source contributor (500+ stars)
```

**Expected Result:** 
- Level: **Senior** ⭐
- Skills Found: **25+** 
- Top Match: **Senior Software Developer** (95%)

### Sample CV #2: Junior Developer
```
PROFILE: Junior Frontend Developer

EXPERIENCE:
- 2 years as Junior Developer
- 1.5 years with React
- 1 year with JavaScript

SKILLS:
- JavaScript, React, HTML, CSS
- Git, Figma, Responsive Design
- Problem solving, Teamwork

PROJECTS:
- Built e-commerce site with React
- Developed todo app with React Hooks
- Collaborated in team of 3 developers
```

**Expected Result:**
- Level: **Junior** 👶
- Skills Found: **8**
- Top Match: **Frontend Developer** (80%)

### Sample CV #3: Data Scientist
```
PROFILE: Data Scientist

EXPERIENCE:
- 4 years data science role
- 3 years machine learning
- 2 years deep learning

SKILLS:
Python, Pandas, NumPy, Scikit-learn, TensorFlow,
PyTorch, SQL, Statistics, Data Visualization,
Machine Learning, Deep Learning, MLOps

PROJECTS:
- Built recommendation system (89% accuracy)
- Time series forecasting for sales prediction
- Computer vision for image classification
```

**Expected Result:**
- Level: **Mid** 👨‍💼
- Skills Found: **15**
- Top Match: **Data Scientist** (90%)

---

## 🔍 Debugging Tips

### Issue: CV tidak teranalisis
**Solution:**
- Pastikan CV minimal 50 karakter
- Ubah teks ke lowercase
- Gunakan full skill names (mis: "Python" bukan "py")

### Issue: No job recommendations
**Solution:**
- Upload CV dengan lebih banyak skills
- Pastikan skills match dengan job requirements
- Check match score harus >= 50%

### Issue: Server tidak jalan
**Solution:**
```bash
# Install dependencies
pip install -r requirements.txt

# Verify Python version
python --version  # Should be 3.8+

# Run with debug mode
python app.py
```

### Issue: Interview questions random
**Solution:**
- Role dipilih otomatis dari job title
- Bisa override dengan manual role selection jika perlu

---

## 📊 What Gets Detected

### Programming Languages (15+)
Python, JavaScript, Java, C++, C#, Go, Rust, PHP, Ruby, Swift, TypeScript, Scala, R, MATLAB, SQL

### Frameworks & Tools
**Frontend:** React, Angular, Vue, Bootstrap, Tailwind
**Backend:** Node.js, Django, Flask, Spring, Laravel
**DevOps:** Docker, Kubernetes, AWS, Azure, GCP, Jenkins
**Databases:** MongoDB, PostgreSQL, MySQL, Redis, Firestore

### Soft Skills (10+)
Leadership, Communication, Teamwork, Problem Solving, Project Management, Agile, Scrum, etc.

---

## 🎯 Interview Role Mapping

Sistem auto-detects role dari job title:

| Job Title | Interview Role |
|-----------|---|
| Software Developer | software-developer |
| Backend Developer | software-developer |
| Frontend Developer | software-developer |
| Full Stack Developer | software-developer |
| DevOps Engineer | software-developer |
| Data Scientist | data-scientist |
| Product Manager | product-manager |
| QA Engineer | software-developer |

---

## 💾 Export Results

Hasil interview bisa di-download sebagai JSON:
```json
{
  "candidateName": "Your Name",
  "jobId": 1,
  "jobTitle": "Position Title",
  "results": {
    "averageScore": 82,
    "answeredQuestions": 10,
    "detailedFeedback": [...],
    "strengths": [...],
    "improvementAreas": [...]
  }
}
```

---

## 📱 Mobile Support

✅ Responsive design untuk mobile
✅ Touch-friendly buttons
⚠️ Audio recording may not work on all mobile browsers

---

## 🚀 Next Steps

1. **Upload your real CV** dan lihat hasilnya
2. **Pick a job** yang sesuai dengan profile Anda
3. **Practice interview** untuk posisi tersebut
4. **Check feedback** dan improve weak areas
5. **Repeat** untuk different job positions

---

## 📚 Learn More

- Check `CV_WORKFLOW_FEATURE.md` untuk dokumentasi lengkap
- Visit `README.md` untuk general platform info
- Check terminal output untuk debugging info

---

## ❓ FAQ

**Q: Berapa lama proses CV analysis?**
A: Instan (< 1 detik)

**Q: Berapa job bisa di-recommend?**
A: Max 5 job dengan match score >= 50%

**Q: Bisa ubah job setelah select?**
A: Ya, klik "Choose Different Job" di interview setup

**Q: Hasil interview disimpan?**
A: Bisa download JSON, tapi tidak auto-saved ke database

**Q: Bisa upload PDF?**
A: Tidak, hanya text paste untuk sekarang

**Q: Accents/special characters support?**
A: Ya, semua bahasa support!

---

**Ready? Buka http://localhost:5000 dan mulai! 🚀**

