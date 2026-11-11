import re
import random
from datetime import datetime
import os

class CVAnalyzer:
    """Analyzer untuk CV - extract skills, experience, education"""
    
    def __init__(self):
        self.skills_database = self._load_skills_database()
    
    def _load_skills_database(self):
        return {
            'programming_languages': [
                'python', 'javascript', 'java', 'c++', 'c#', 'go', 'rust', 'php', 'ruby', 'swift',
                'kotlin', 'scala', 'typescript', 'perl', 'r', 'matlab', 'sql', 'nosql'
            ],
            'frontend': [
                'react', 'angular', 'vue', 'html', 'css', 'sass', 'less', 'webpack', 'gulp',
                'bootstrap', 'tailwind', 'figma', 'adobe xd', 'sketch', 'responsive'
            ],
            'backend': [
                'nodejs', 'express', 'django', 'flask', 'spring', 'laravel', 'fastapi',
                'graphql', 'rest api', 'microservices', 'monolithic'
            ],
            'databases': [
                'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'firestore',
                'dynamodb', 'cassandra', 'oracle', 'sql server'
            ],
            'devops': [
                'docker', 'kubernetes', 'jenkins', 'gitlab ci', 'github actions', 'aws', 'azure',
                'gcp', 'terraform', 'ansible', 'prometheus', 'grafana'
            ],
            'data_science': [
                'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'scikit-learn',
                'pandas', 'numpy', 'data analysis', 'nlp', 'computer vision', 'statistics'
            ],
            'tools': [
                'git', 'jira', 'confluence', 'slack', 'linux', 'unix', 'windows', 'macos',
                'vim', 'vs code', 'intellij', 'postman', 'swagger'
            ],
            'soft_skills': [
                'leadership', 'communication', 'teamwork', 'problem solving', 'critical thinking',
                'project management', 'agile', 'scrum', 'kanban', 'presentation'
            ]
        }
    
    def analyze_cv_text(self, cv_text):
        if not cv_text:
            return {
                'skills': [], 'programming_languages': [], 'frameworks': [],
                'tools': [], 'soft_skills': [], 'experience_level': 'entry',
                'total_skills_found': 0, 'summary': {}
            }
        
        cv_text_lower = cv_text.lower()
        extracted_skills = {
            'programming_languages': [], 'frontend': [], 'backend': [],
            'databases': [], 'devops': [], 'data_science': [], 'tools': [], 'soft_skills': []
        }
        
        for category, skills_list in self.skills_database.items():
            for skill in skills_list:
                if skill.lower() in cv_text_lower:
                    extracted_skills[category].append(skill)
        
        experience_level = self._determine_experience_level(cv_text_lower, extracted_skills)
        summary = self._generate_cv_summary(extracted_skills, experience_level)
        
        return {
            'skills': self._flatten_skills(extracted_skills),
            'programming_languages': extracted_skills.get('programming_languages', []),
            'frameworks': extracted_skills.get('frontend', []) + extracted_skills.get('backend', []),
            'tools': extracted_skills.get('devops', []) + extracted_skills.get('tools', []),
            'soft_skills': extracted_skills.get('soft_skills', []),
            'databases': extracted_skills.get('databases', []),
            'data_science': extracted_skills.get('data_science', []),
            'experience_level': experience_level,
            'total_skills_found': len(self._flatten_skills(extracted_skills)),
            'summary': summary
        }
    
    def _determine_experience_level(self, cv_text, extracted_skills):
        total_skills = len(self._flatten_skills(extracted_skills))
        years_pattern = r'(\d+)\+? years?'
        years_matches = re.findall(years_pattern, cv_text)
        max_years = max([int(m) for m in years_matches]) if years_matches else 0
        
        if max_years >= 10 or total_skills >= 20:
            return 'senior'
        elif max_years >= 5 or total_skills >= 12:
            return 'mid'
        elif max_years >= 2 or total_skills >= 5:
            return 'junior'
        else:
            return 'entry'
    
    def _flatten_skills(self, extracted_skills):
        all_skills = []
        for category, skills in extracted_skills.items():
            all_skills.extend(skills)
        return list(set(all_skills))
    
    def _generate_cv_summary(self, extracted_skills, experience_level):
        categories_found = [cat for cat, skills in extracted_skills.items() if skills]
        return {
            'experience_level': experience_level,
            'categories_found': len(categories_found),
            'strongest_category': max(extracted_skills.items(), key=lambda x: len(x[1]))[0] if any(extracted_skills.values()) else None,
            'categories': categories_found
        }


class JobDatabase:
    @staticmethod
    def get_all_jobs():
        return [
            {'id': 1, 'title': 'Senior Software Developer', 'description': 'Kami mencari Senior Developer dengan pengalaman 5+ tahun', 'required_skills': ['python', 'javascript', 'react', 'nodejs', 'docker', 'git'], 'required_experience': 'senior', 'salary_range': '8-12 juta', 'company': 'Tech Corp', 'location': 'Jakarta', 'type': 'full-time'},
            {'id': 2, 'title': 'Data Scientist', 'description': 'Bergabunglah sebagai Data Scientist untuk menganalisis big data', 'required_skills': ['python', 'machine learning', 'pandas', 'tensorflow', 'sql', 'data analysis'], 'required_experience': 'mid', 'salary_range': '7-10 juta', 'company': 'Data Solutions', 'location': 'Jakarta', 'type': 'full-time'},
            {'id': 3, 'title': 'Frontend Developer', 'description': 'Kami butuh Frontend Developer berpengalaman dengan React', 'required_skills': ['javascript', 'react', 'html', 'css', 'responsive', 'git'], 'required_experience': 'junior', 'salary_range': '5-7 juta', 'company': 'Web Innovations', 'location': 'Jakarta', 'type': 'full-time'},
            {'id': 4, 'title': 'DevOps Engineer', 'description': 'DevOps Engineer untuk infrastruktur dan CI/CD', 'required_skills': ['docker', 'kubernetes', 'linux', 'aws', 'jenkins', 'terraform'], 'required_experience': 'mid', 'salary_range': '7-11 juta', 'company': 'Cloud Systems', 'location': 'Jakarta', 'type': 'full-time'},
            {'id': 5, 'title': 'Junior Python Developer', 'description': 'Perfect untuk Fresh Graduate atau early career developers', 'required_skills': ['python', 'django', 'sql', 'git', 'rest api'], 'required_experience': 'junior', 'salary_range': '4-6 juta', 'company': 'StartUp Hub', 'location': 'Jakarta', 'type': 'full-time'},
            {'id': 6, 'title': 'Full Stack Developer', 'description': 'Full Stack Developer dengan kemampuan frontend dan backend', 'required_skills': ['javascript', 'react', 'nodejs', 'mongodb', 'python', 'docker'], 'required_experience': 'mid', 'salary_range': '6-9 juta', 'company': 'Digital Agency', 'location': 'Bandung', 'type': 'full-time'},
            {'id': 7, 'title': 'Product Manager', 'description': 'Product Manager untuk mengembangkan produk kami', 'required_skills': ['project management', 'communication', 'analytics', 'agile', 'leadership'], 'required_experience': 'mid', 'salary_range': '8-11 juta', 'company': 'Product House', 'location': 'Jakarta', 'type': 'full-time'},
            {'id': 8, 'title': 'QA Engineer', 'description': 'QA Engineer untuk testing dan quality assurance', 'required_skills': ['testing', 'automation', 'selenium', 'python', 'git', 'problemsolving'], 'required_experience': 'junior', 'salary_range': '5-7 juta', 'company': 'Quality Tech', 'location': 'Jakarta', 'type': 'full-time'}
        ]
    
    @staticmethod
    def filter_by_experience(experience_level):
        return [job for job in JobDatabase.get_all_jobs() if job['required_experience'] == experience_level]


class JobMatcher:
    @staticmethod
    def calculate_match_score(cv_analysis, job):
        cv_skills = set(cv_analysis['skills'])
        required_skills = set(job['required_skills'])
        matched_skills = cv_skills.intersection(required_skills)
        skill_match_percentage = (len(matched_skills) / len(required_skills)) * 100 if required_skills else 0
        cv_exp_level = cv_analysis['experience_level']
        job_exp_level = job['required_experience']
        experience_match = JobMatcher._calculate_experience_match(cv_exp_level, job_exp_level)
        overall_score = (skill_match_percentage * 0.7) + (experience_match * 100 * 0.3)
        return {
            'job_id': job['id'], 'job_title': job['title'],
            'match_percentage': round(overall_score, 1),
            'skill_match_percentage': round(skill_match_percentage, 1),
            'matched_skills': list(matched_skills),
            'missing_skills': list(required_skills - cv_skills),
            'experience_match': experience_match > 0.7,
            'is_recommended': overall_score >= 50
        }
    
    @staticmethod
    def _calculate_experience_match(cv_exp, job_exp):
        scoring = {
            'entry': {'entry': 1.0, 'junior': 0.7, 'mid': 0.3, 'senior': 0.1},
            'junior': {'entry': 0.8, 'junior': 1.0, 'mid': 0.8, 'senior': 0.3},
            'mid': {'entry': 1.0, 'junior': 0.9, 'mid': 1.0, 'senior': 0.7},
            'senior': {'entry': 1.0, 'junior': 1.0, 'mid': 0.9, 'senior': 1.0}
        }
        return scoring.get(cv_exp, {}).get(job_exp, 0.5)
    
    @staticmethod
    def get_recommended_jobs(cv_analysis, limit=5):
        all_jobs = JobDatabase.get_all_jobs()
        matches = []
        for job in all_jobs:
            match_score = JobMatcher.calculate_match_score(cv_analysis, job)
            if match_score['is_recommended']:
                matches.append({**job, 'match_score': match_score})
        matches.sort(key=lambda x: x['match_score']['match_percentage'], reverse=True)
        return matches[:limit]


class AdvancedAIEngine:
    def __init__(self):
        self.knowledge_base = self._load_knowledge_base()
        self._common_stopwords = {
            'the', 'and', 'for', 'with', 'that', 'this', 'from', 'your', 'about', 'have', 'what', 'when',
            'where', 'how', 'why', 'can', 'you', 'are', 'was', 'were', 'will', 'would', 'could', 'should',
            'dan', 'yang', 'dengan', 'untuk', 'dari', 'pada', 'atau', 'juga', 'kami', 'saya', 'anda',
            'apa', 'bagaimana', 'mengapa', 'kapan', 'dimana', 'tentang', 'dalam', 'sudah', 'belum'
        }
    
    def _load_knowledge_base(self):
        return {
            'software-developer': {
                'concepts': ['object-oriented programming', 'design patterns', 'data structures', 'algorithms', 'version control', 'testing', 'debugging', 'code review', 'agile methodology', 'clean code', 'refactoring', 'performance optimization', 'security', 'database design', 'API development', 'microservices', 'containerization', 'CI/CD', 'monitoring', 'logging'],
                'technologies': ['python', 'javascript', 'java', 'c++', 'c#', 'go', 'rust', 'react', 'angular', 'vue', 'node.js', 'django', 'flask', 'spring', 'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'git', 'jenkins', 'jira', 'confluence'],
                'skills': ['problem solving', 'analytical thinking', 'attention to detail', 'communication', 'teamwork', 'time management', 'learning ability', 'creativity', 'adaptability', 'leadership']
            },
            'data-scientist': {
                'concepts': ['machine learning', 'deep learning', 'statistical analysis', 'data preprocessing', 'feature engineering', 'model validation', 'cross-validation', 'overfitting', 'bias-variance tradeoff', 'ensemble methods', 'neural networks', 'natural language processing', 'computer vision', 'time series analysis', 'clustering', 'classification', 'regression', 'dimensionality reduction'],
                'technologies': ['python', 'r', 'sql', 'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'keras', 'matplotlib', 'seaborn', 'plotly', 'jupyter', 'spark', 'hadoop', 'aws sagemaker', 'google colab', 'kaggle', 'tableau', 'power bi'],
                'skills': ['mathematical thinking', 'statistical reasoning', 'data intuition', 'business acumen', 'storytelling', 'critical thinking', 'experimental design', 'hypothesis testing', 'data visualization']
            },
            'product-manager': {
                'concepts': ['product strategy', 'market research', 'user research', 'user experience', 'product lifecycle', 'roadmapping', 'prioritization', 'stakeholder management', 'agile methodology', 'scrum', 'kanban', 'sprint planning', 'retrospectives', 'metrics and KPIs', 'A/B testing', 'customer feedback', 'competitive analysis', 'go-to-market strategy', 'pricing strategy'],
                'technologies': ['jira', 'confluence', 'figma', 'sketch', 'invision', 'mixpanel', 'amplitude', 'google analytics', 'hotjar', 'userzoom', 'typeform', 'survey monkey', 'slack', 'zoom', 'microsoft teams', 'notion', 'airtable'],
                'skills': ['leadership', 'communication', 'strategic thinking', 'user empathy', 'data analysis', 'project management', 'negotiation', 'presentation', 'decision making', 'problem solving', 'creativity', 'adaptability']
            }
        }
    
    def analyze_answer_sophistication(self, answer, question, role):
        processed_answer = self._preprocess_text(answer)
        processed_question = self._preprocess_text(question or "")
        metrics = {
            'length_score': self._calculate_length_score(answer),
            'vocabulary_score': self._calculate_vocabulary_score(processed_answer),
            'technical_score': self._calculate_technical_relevance(processed_answer, role),
            'question_relevance_score': self._calculate_question_relevance(processed_question, processed_answer),
            'structure_score': self._calculate_structure_score(answer),
            'sentiment_score': self._calculate_sentiment_score(answer),
            'specificity_score': self._calculate_specificity_score(answer),
            'example_score': self._calculate_example_score(answer),
            'impact_score': self._calculate_impact_score(answer)
        }
        return metrics
    
    def _preprocess_text(self, text):
        text = text.lower()
        text = re.sub(r'[^a-zA-Z0-9\s\.\,\!\?\-]', ' ', text)
        words = text.split()
        return ' '.join([w for w in words if len(w) > 2])
    
    def _calculate_length_score(self, answer):
        words = len(answer.split())
        if words < 20: return 0.3
        elif words < 50: return 0.6
        elif words < 100: return 0.8
        else: return 1.0
    
    def _calculate_vocabulary_score(self, processed_answer):
        words = processed_answer.split()
        if not words: return 0.0
        ttr = len(set(words)) / len(words)
        return min(ttr * 2, 1.0)
    
    def _calculate_technical_relevance(self, processed_answer, role):
        if role not in self.knowledge_base: return 0.5
        role_concepts = (self.knowledge_base[role]['concepts'] + self.knowledge_base[role]['technologies'] + self.knowledge_base[role]['skills'])
        answer_words = set(processed_answer.lower().split())
        concept_words = set()
        for concept in role_concepts:
            concept_words.update(concept.lower().split())
        matches = len(answer_words.intersection(concept_words))
        total_concept_words = len(concept_words)
        if total_concept_words == 0: return 0.5
        return min(matches / (total_concept_words * 0.1), 1.0)
    
    def _calculate_structure_score(self, answer):
        sentences = answer.split('.')
        if len(sentences) < 2: return 0.3
        connectors = ['because', 'therefore', 'however', 'although', 'furthermore', 'additionally']
        connector_count = sum(1 for c in connectors if c.lower() in answer.lower())
        has_structure = bool(re.search(r'[\-\*]\s|\d+\.\s', answer))
        base_score = min(connector_count * 0.2, 0.6)
        return min(base_score + (0.2 if has_structure else 0), 1.0)
    
    def _calculate_sentiment_score(self, answer):
        positive_words = ['good', 'great', 'excellent', 'successful', 'improved', 'achieved', 'solved', 'created', 'developed', 'implemented']
        negative_words = ['bad', 'failed', 'problem', 'issue', 'difficult', 'challenging', 'struggled', 'complicated']
        answer_lower = answer.lower()
        positive_count = sum(1 for w in positive_words if w in answer_lower)
        negative_count = sum(1 for w in negative_words if w in answer_lower)
        if positive_count == 0 and negative_count == 0: return 0.5
        return positive_count / (positive_count + negative_count)
    
    def _calculate_specificity_score(self, answer):
        patterns = [r'\d+%', r'\d+ years?', r'\d+ months?', r'\$\d+', r'\d+ users?', r'[A-Z]{2,}', r'v\d+\.\d+']
        return min(sum(1 for p in patterns if re.search(p, answer)) * 0.2, 1.0)
    
    def _calculate_example_score(self, answer):
        indicators = ['for example', 'for instance', 'such as', 'specifically', 'when i', 'i worked on', 'i developed', 'i created']
        return min(sum(1 for i in indicators if i.lower() in answer.lower()) * 0.25, 1.0)
    
    def _calculate_impact_score(self, answer):
        indicators = ['increased', 'decreased', 'improved', 'reduced', 'achieved', 'accomplished', 'delivered', 'resulted in', 'impact', 'outcome', 'result', 'success', 'efficiency']
        return min(sum(1 for i in indicators if i.lower() in answer.lower()) * 0.2, 1.0)

    def _calculate_question_relevance(self, processed_question, processed_answer):
        q_words = {w for w in processed_question.split() if len(w) > 2 and w not in self._common_stopwords}
        a_words = {w for w in processed_answer.split() if len(w) > 2 and w not in self._common_stopwords}
        if not q_words:
            return 0.65
        overlap = len(q_words.intersection(a_words))
        coverage = overlap / len(q_words)
        if coverage >= 0.75:
            return 1.0
        if coverage >= 0.5:
            return 0.85
        if coverage >= 0.3:
            return 0.65
        if coverage >= 0.15:
            return 0.45
        return 0.25
    
    def generate_intelligent_score(self, answer, question, role):
        metrics = self.analyze_answer_sophistication(answer, question, role)
        weights = {
            'length_score': 0.12,
            'vocabulary_score': 0.08,
            'technical_score': 0.22,
            'question_relevance_score': 0.22,
            'structure_score': 0.12,
            'sentiment_score': 0.04,
            'specificity_score': 0.12,
            'example_score': 0.06,
            'impact_score': 0.02
        }

        # Base quality score [0..1]
        total_score = sum(metrics[key] * weights[key] for key in weights)
        relevance = metrics.get('question_relevance_score', 0.0)
        detail_level = (
            metrics.get('specificity_score', 0.0) * 0.45 +
            metrics.get('example_score', 0.0) * 0.35 +
            metrics.get('structure_score', 0.0) * 0.20
        )

        # Scoring rubric:
        # 1) Jawaban tidak sesuai pertanyaan => skor kecil
        # 2) Jawaban sesuai tapi kurang detail => skor standar
        # 3) Jawaban sesuai + detail => skor lebih tinggi
        if relevance < 0.30:
            # Irrelevant answer should stay low.
            final_score = int(15 + (total_score * 25))   # 15..40
        elif relevance < 0.65:
            # Partially relevant answer: medium range.
            final_score = int(35 + (total_score * 35))   # 35..70
        else:
            if detail_level < 0.45:
                # Relevant but not detailed => standard score.
                final_score = int(58 + (total_score * 17))  # 58..75
            elif detail_level < 0.70:
                # Relevant and somewhat detailed.
                final_score = int(68 + (total_score * 20))  # 68..88
            else:
                # Relevant and detailed.
                final_score = int(78 + (total_score * 22))  # 78..100

        final_score = max(0, min(100, final_score))
        return final_score, metrics
    
    def generate_intelligent_feedback(self, answer, question, role, metrics):
        feedback_parts = []
        strengths = []
        if metrics['technical_score'] > 0.7: strengths.append("strong technical knowledge")
        if metrics['structure_score'] > 0.7: strengths.append("well-organized response")
        if metrics['specificity_score'] > 0.7: strengths.append("specific examples")
        if metrics['example_score'] > 0.7: strengths.append("good use of examples")
        if strengths:
            feedback_parts.insert(0, f"Excellent work on {', '.join(strengths)}!")
        if metrics['length_score'] < 0.5:
            feedback_parts.append("Consider providing more detailed answers with specific examples.")
        if metrics['technical_score'] < 0.6:
            feedback_parts.append("Try to incorporate more role-specific technical concepts and terminology.")
        if metrics['structure_score'] < 0.6:
            feedback_parts.append("Organize your answer with clear structure and logical flow.")
        if metrics['specificity_score'] < 0.5:
            feedback_parts.append("Include specific numbers, metrics, or concrete examples to strengthen your response.")
        if metrics['example_score'] < 0.5:
            feedback_parts.append("Support your points with real-world examples or personal experiences.")
        if metrics['impact_score'] < 0.5:
            feedback_parts.append("Discuss the impact and results of your actions or decisions.")
        return ' '.join(feedback_parts)
    
    def generate_follow_up_question(self, answer, question, role, metrics):
        follow_ups = {
            'software-developer': ["Can you elaborate on the specific technologies you used?", "What challenges did you face and how did you overcome them?", "How did you ensure code quality?", "What was the business impact of your solution?"],
            'data-scientist': ["What specific algorithms did you use and why?", "How did you validate your results?", "What was the business impact of your analysis?", "How did you handle data quality issues?"],
            'product-manager': ["How did you measure the success of that feature?", "What user research methods did you use?", "How did you handle competing stakeholder priorities?", "What was the go-to-market strategy?"]
        }
        if metrics['specificity_score'] < 0.6: return "Can you provide more specific details about that experience?"
        elif metrics['example_score'] < 0.6: return "Could you share a specific example to illustrate your point?"
        elif metrics['impact_score'] < 0.6: return "What were the measurable results or impact of your actions?"
        else:
            role_questions = follow_ups.get(role, follow_ups.get('software-developer', []))
            return random.choice(role_questions) if role_questions else "Can you elaborate further?"
    

class AIInterviewer:
    def __init__(self, role='general', custom_questions=None):
        self.role = role
        self.ai_engine = AdvancedAIEngine()
        self.interview_history = []
        self.current_question_index = 0
        self.questions = self._get_questions_for_role(role, custom_questions or {})
    
    def _get_questions_for_role(self, role, custom_questions):
        base_questions = {
            'software-developer': [
                "Can you tell me about your experience with Python and how you've used it in real projects?",
                "How do you approach debugging complex issues in production systems?",
                "What's your methodology for writing clean, maintainable code that scales?",
                "How do you stay updated with the latest technologies and industry trends?",
                "Can you describe a challenging project where you had to make architectural decisions?",
                "How do you handle working in a team environment with different skill levels?",
                "What's your experience with version control systems and collaborative development?",
                "How do you approach code reviews and ensure code quality?",
                "What's your testing strategy for ensuring robust and reliable software?",
                "How do you handle tight deadlines while maintaining code quality?"
            ],
            'data-scientist': [
                "Can you explain your experience with machine learning algorithms and when you'd use each type?",
                "How do you handle missing data and outliers in your datasets?",
                "What's your approach to feature engineering and selecting the right features?",
                "How do you validate your models and prevent overfitting?",
                "Can you describe a data visualization project that provided business insights?",
                "How do you handle large-scale data processing and performance optimization?",
                "What's your experience with statistical analysis and hypothesis testing?",
                "How do you communicate technical results to non-technical stakeholders?",
                "What's your approach to A/B testing and experimental design?",
                "How do you stay current with the latest ML research and techniques?"
            ],
            'product-manager': [
                "Can you tell me about a product you successfully launched and the strategy behind it?",
                "How do you gather and prioritize user requirements from multiple stakeholders?",
                "What's your approach to competitive analysis and market positioning?",
                "How do you handle conflicts between different stakeholder priorities?",
                "Can you describe your experience with agile methodologies and sprint planning?",
                "How do you measure product success and what metrics do you track?",
                "What's your approach to user research and understanding user needs?",
                "How do you handle scope creep and changing requirements?",
                "Can you describe a time you had to pivot a product strategy?",
                "How do you balance user needs with business goals and technical constraints?"
            ],
            'general': [
                "Tell me about yourself and your professional background.",
                "What are your greatest strengths and areas for improvement?",
                "Where do you see yourself in 5 years professionally?",
                "Why are you interested in this position and company?",
                "What motivates you in your work and drives your performance?",
                "How do you handle stress and pressure in high-stakes situations?",
                "Can you describe a time you failed and what you learned from it?",
                "What's your leadership style and how do you motivate others?",
                "How do you handle criticism and feedback from others?",
                "What questions do you have for me about the role and company?"
            ]
        }
        if role in custom_questions and custom_questions[role]:
            return custom_questions[role]
        return base_questions.get(role, base_questions['general'])
    
    def get_next_question(self):
        if self.current_question_index < len(self.questions):
            question = self.questions[self.current_question_index]
            self.current_question_index += 1
            return {'question': question, 'questionNumber': self.current_question_index, 'totalQuestions': len(self.questions)}
        return None
    
    def evaluate_answer(self, answer, question):
        score, metrics = self.ai_engine.generate_intelligent_score(answer, question, self.role)
        feedback = self.ai_engine.generate_intelligent_feedback(answer, question, self.role, metrics)
        follow_up = self.ai_engine.generate_follow_up_question(answer, question, self.role, metrics)
        evaluation = {'question': question, 'answer': answer, 'score': score, 'feedback': feedback, 'follow_up': follow_up, 'metrics': metrics, 'timestamp': datetime.now().isoformat()}
        self.interview_history.append(evaluation)
        return evaluation
    
    def get_interview_summary(self):
        if not self.interview_history:
            return {'totalQuestions': len(self.questions), 'answeredQuestions': 0, 'averageScore': 0, 'overallFeedback': "No answers provided.", 'detailedFeedback': [], 'aiInsights': {}, 'improvementAreas': [], 'strengths': []}
        scores = [e['score'] for e in self.interview_history]
        average_score = sum(scores) / len(scores)
        ai_insights = self._generate_ai_insights()
        improvement_areas, strengths = self._analyze_performance_patterns()
        return {
            'totalQuestions': len(self.questions),
            'answeredQuestions': len(self.interview_history),
            'averageScore': round(average_score),
            'overallFeedback': self._generate_overall_feedback(average_score),
            'detailedFeedback': self.interview_history,
            'aiInsights': ai_insights,
            'improvementAreas': improvement_areas,
            'strengths': strengths
        }
    
    def _generate_ai_insights(self):
        if not self.interview_history: return {}
        all_metrics = [e['metrics'] for e in self.interview_history]
        insights = {
            'communication_strength': sum(m['vocabulary_score'] for m in all_metrics) / len(all_metrics),
            'technical_depth': sum(m['technical_score'] for m in all_metrics) / len(all_metrics),
            'answer_quality': sum(m['structure_score'] for m in all_metrics) / len(all_metrics),
            'concrete_examples': sum(m['example_score'] for m in all_metrics) / len(all_metrics),
            'impact_focus': sum(m['impact_score'] for m in all_metrics) / len(all_metrics)
        }
        insights_text = []
        if insights['communication_strength'] > 0.7: insights_text.append("Strong communication skills demonstrated throughout the interview.")
        if insights['technical_depth'] > 0.7: insights_text.append("Excellent technical knowledge and understanding shown.")
        if insights['concrete_examples'] > 0.7: insights_text.append("Great use of specific examples to support your points.")
        insights['summary'] = ' '.join(insights_text)
        return insights
    
    def _analyze_performance_patterns(self):
        if not self.interview_history: return [], []
        all_metrics = [e['metrics'] for e in self.interview_history]
        avg_metrics = {key: sum(m[key] for m in all_metrics) / len(all_metrics) for key in all_metrics[0].keys()}
        improvement_areas = []
        if avg_metrics.get('technical_score', 0) < 0.6: improvement_areas.append("Technical depth and role-specific knowledge")
        if avg_metrics.get('structure_score', 0) < 0.6: improvement_areas.append("Answer structure and organization")
        if avg_metrics.get('specificity_score', 0) < 0.6: improvement_areas.append("Providing specific examples and metrics")
        strengths = []
        if avg_metrics.get('vocabulary_score', 0) > 0.7: strengths.append("Strong vocabulary and communication skills")
        if avg_metrics.get('sentiment_score', 0) > 0.7: strengths.append("Positive and confident communication style")
        if avg_metrics.get('length_score', 0) > 0.7: strengths.append("Comprehensive and detailed responses")
        return improvement_areas, strengths
    
    def _generate_overall_feedback(self, average_score):
        if average_score >= 90: return "Exceptional performance! You demonstrated outstanding knowledge, communication skills, and technical expertise throughout the interview."
        elif average_score >= 80: return "Excellent performance! You showed strong understanding and excellent communication skills with room for minor improvements."
        elif average_score >= 70: return "Very good performance! You have a solid foundation with good communication skills and some areas for enhancement."
        elif average_score >= 60: return "Good performance! You demonstrated basic competence with several areas that could benefit from improvement."
        else: return "Fair performance. Focus on providing more detailed answers, specific examples, and demonstrating deeper technical knowledge."
