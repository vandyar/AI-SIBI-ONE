"""
portfolio_analyzer.py - AI Portfolio Analyzer
Analisis GitHub (via REST API publik) + LinkedIn (form manual).
Digunakan khusus di CV Screening section.
"""
import re
import json
import math
import urllib.request
import urllib.error
from datetime import datetime, timezone
from urllib.parse import urlparse

GITHUB_API_BASE = "https://api.github.com"
HEADERS_GITHUB = {"Accept": "application/vnd.github+json", "User-Agent": "AI-Interview-Platform/1.0"}

LANG_WEIGHTS = {
    "python": 3, "javascript": 3, "typescript": 3, "java": 3,
    "go": 3, "rust": 3, "kotlin": 2, "swift": 2, "c++": 2,
    "c#": 2, "ruby": 2, "php": 2, "html": 1, "css": 1, "shell": 1
}


def _fetch_json(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers=HEADERS_GITHUB)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code in [404, 403]: return None
        return None
    except Exception:
        return None


def _extract_github_username(url_or_username):
    s = url_or_username.strip()
    if not s: return None
    if "github.com" in s:
        path = urlparse(s).path.strip("/").split("/")
        return path[0] if path else None
    if re.match(r'^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$', s):
        return s
    return None


class GitHubAnalyzer:
    def analyze(self, username_or_url):
        username = _extract_github_username(username_or_url)
        if not username:
            return {"status": "error", "message": "Username/URL GitHub tidak valid.", "github_score": 0, "insights": []}
        profile = _fetch_json(f"{GITHUB_API_BASE}/users/{username}")
        if not profile or "login" not in profile:
            return {"status": "error", "message": f"Profil GitHub '{username}' tidak ditemukan.", "github_score": 0, "insights": []}
        repos_raw = _fetch_json(f"{GITHUB_API_BASE}/users/{username}/repos?per_page=100&sort=updated") or []
        own_repos = [r for r in repos_raw if not r.get("fork", True)]
        languages = {}
        for repo in own_repos[:30]:
            lang = repo.get("language")
            if lang:
                languages[lang] = languages.get(lang, 0) + 1
        total_stars = sum(r.get("stargazers_count", 0) for r in own_repos)
        top_repos = sorted(own_repos, key=lambda r: r.get("stargazers_count", 0), reverse=True)[:5]
        commit_weeks = self._fetch_commit_activity(username, own_repos[:5])
        has_readme_count = sum(1 for r in own_repos[:10] if r.get("description"))
        score = self._calculate_score(profile, own_repos, languages, total_stars, commit_weeks, has_readme_count)
        insights = self._build_insights(profile, own_repos, languages, total_stars, commit_weeks, top_repos)
        return {
            "status": "success", "username": username,
            "profile_url": f"https://github.com/{username}",
            "avatar_url": profile.get("avatar_url"),
            "name": profile.get("name") or username,
            "bio": profile.get("bio") or "",
            "company": profile.get("company") or "",
            "location": profile.get("location") or "",
            "public_repos": profile.get("public_repos", 0),
            "followers": profile.get("followers", 0),
            "following": profile.get("following", 0),
            "total_stars": total_stars, "languages": languages,
            "top_repos": [{"name": r["name"], "stars": r.get("stargazers_count", 0), "description": r.get("description") or "", "language": r.get("language") or "", "url": r.get("html_url", "")} for r in top_repos],
            "github_score": score, "insights": insights,
            "account_created": profile.get("created_at", "")[:10],
            "last_active": profile.get("updated_at", "")[:10],
        }

    def _fetch_commit_activity(self, username, repos):
        total = 0
        for repo in repos:
            data = _fetch_json(f"{GITHUB_API_BASE}/repos/{username}/{repo['name']}/stats/commit_activity")
            if isinstance(data, list):
                total += sum(w.get("total", 0) for w in data)
        return total

    def _calculate_score(self, profile, repos, languages, stars, commits, readme_count):
        score = 0
        score += min(len(repos) / 2, 10)
        weighted_langs = sum(LANG_WEIGHTS.get(l.lower(), 1) for l in languages.keys())
        score += min(weighted_langs * 1.5, 15)
        if stars > 0: score += min(math.log(stars + 1) * 3, 15)
        if commits > 0: score += min(math.log(commits + 1) * 4, 20)
        completeness = 0
        if profile.get("bio"): completeness += 3
        if profile.get("company"): completeness += 2
        if profile.get("blog"): completeness += 2
        if profile.get("location"): completeness += 1
        score += min(completeness, 10)
        score += min(readme_count * 1.5, 15)
        followers = profile.get("followers", 0)
        if followers > 0: score += min(math.log(followers + 1) * 3, 15)
        return min(int(score), 100)

    def _build_insights(self, profile, repos, languages, stars, commits, top_repos):
        insights = []
        created = profile.get("created_at", "")
        if created:
            try:
                age_years = (datetime.now(timezone.utc) - datetime.fromisoformat(created.replace("Z", "+00:00"))).days / 365
                insights.append(f"Akun GitHub berumur {age_years:.1f} tahun")
            except Exception:
                pass
        if languages:
            top_lang = max(languages, key=languages.get)
            insights.append(f"Bahasa dominan: {top_lang} ({languages[top_lang]} repo)")
            if len(languages) >= 5:
                insights.append(f"Menguasai {len(languages)} bahasa pemrograman")
        if stars > 50: insights.append(f"✅ Proyek diminati komunitas ({stars} total stars)")
        elif stars > 10: insights.append(f"Proyek mendapat perhatian ({stars} stars)")
        if commits > 500: insights.append("✅ Aktivitas coding sangat tinggi (>500 commit/tahun)")
        elif commits > 100: insights.append("Kontribusi aktif dalam 1 tahun terakhir")
        elif commits < 20 and len(repos) > 10: insights.append("⚠️ Banyak repo tapi aktivitas commit rendah")
        if top_repos and top_repos[0].get("stars", 0) > 10:
            insights.append(f"Repo terpopuler: {top_repos[0]['name']} ({top_repos[0]['stars']} stars)")
        followers = profile.get("followers", 0)
        if followers > 100: insights.append(f"✅ Diikuti {followers} developer lain")
        return insights


class LinkedInAnalyzer:
    def analyze_from_data(self, profile_data):
        score = self._calculate_score(profile_data)
        insights = self._build_insights(profile_data)
        return {
            "status": "success",
            "profile_url": profile_data.get("url", ""),
            "name": profile_data.get("name", ""),
            "headline": profile_data.get("headline", ""),
            "linkedin_score": score, "insights": insights,
            "summary": {
                "connections": profile_data.get("connections", 0),
                "experience_count": len(profile_data.get("experience", [])),
                "skills_count": len(profile_data.get("skills", [])),
                "certifications": len(profile_data.get("certifications", [])),
                "recommendations": profile_data.get("recommendations", 0)
            }
        }

    def _calculate_score(self, data):
        score = 0
        if data.get("headline"): score += 5
        if data.get("summary"): score += 5
        if data.get("location"): score += 3
        exp = data.get("experience", [])
        total_exp_years = sum(float(e.get("duration_years", 0)) for e in exp)
        score += min(total_exp_years * 4, 20)
        score += min(len(exp) * 2, 10)
        edu = data.get("education", [])
        if any(e.get("degree", "").lower() in ["s2", "s3", "master", "phd", "doctorate"] for e in edu): score += 10
        elif edu: score += 6
        score += min(len(data.get("skills", [])) * 1, 15)
        connections = int(data.get("connections", 0))
        if connections >= 500: score += 10
        elif connections >= 200: score += 7
        elif connections >= 50: score += 4
        score += min(len(data.get("certifications", [])) * 3, 9)
        score += min(int(data.get("recommendations", 0)) * 2, 6)
        return min(int(score), 100)

    def _build_insights(self, data):
        insights = []
        exp = data.get("experience", [])
        total_years = sum(float(e.get("duration_years", 0)) for e in exp)
        if total_years >= 5: insights.append(f"✅ Pengalaman kerja {total_years:.0f}+ tahun")
        elif total_years >= 2: insights.append(f"Pengalaman kerja {total_years:.0f} tahun")
        connections = int(data.get("connections", 0))
        if connections >= 500: insights.append("✅ Jaringan profesional kuat (500+ koneksi)")
        skills = data.get("skills", [])
        if len(skills) >= 15: insights.append(f"Profil skill lengkap ({len(skills)} skill)")
        elif len(skills) < 5: insights.append("⚠️ Profil skill kurang lengkap")
        certs = data.get("certifications", [])
        if certs: insights.append(f"Memiliki {len(certs)} sertifikasi profesional")
        recs = int(data.get("recommendations", 0))
        if recs >= 5: insights.append(f"✅ Direkomendasikan {recs} orang")
        return insights


class PortfolioAnalyzer:
    def __init__(self):
        self.github = GitHubAnalyzer()
        self.linkedin = LinkedInAnalyzer()

    def analyze(self, github_url=None, linkedin_data=None, target_role="software-developer"):
        github_result = {}
        linkedin_result = {}
        if github_url:
            github_result = self.github.analyze(github_url)
        if linkedin_data:
            linkedin_result = self.linkedin.analyze_from_data(linkedin_data)
        g_score = github_result.get("github_score", 0) if github_result.get("status") == "success" else 0
        l_score = linkedin_result.get("linkedin_score", 0) if linkedin_result.get("status") == "success" else 0
        if github_url and linkedin_data: overall_score = int(g_score * 0.6 + l_score * 0.4)
        elif github_url: overall_score = g_score
        else: overall_score = l_score
        recommendation = self._generate_recommendation(overall_score, target_role)
        all_insights = github_result.get("insights", []) + linkedin_result.get("insights", [])
        return {"status": "success", "overall_score": overall_score, "github": github_result, "linkedin": linkedin_result, "all_insights": all_insights, "recommendation": recommendation, "analyzed_at": datetime.now().isoformat()}

    def _generate_recommendation(self, score, role):
        if score >= 80: return f"🌟 SANGAT DIREKOMENDASIKAN untuk posisi {role}. Portofolio menunjukkan keahlian tinggi."
        elif score >= 60: return f"✅ LAYAK untuk posisi {role}. Portofolio cukup baik."
        elif score >= 40: return f"ℹ️ PERLU EVALUASI LEBIH untuk posisi {role}. Ada potensi namun perlu dikembangkan."
        else: return f"⚠️ Portofolio TERBATAS untuk posisi {role}. Minta portofolio tambahan atau demo project."
