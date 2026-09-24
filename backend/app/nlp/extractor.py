"""
CareerPilot AI — Skill & Entity Extractor
===========================================
What is this?
  Extracts skills, education, experience, contact info, and other entities
  from raw resume or job description text using:
  1. Regex patterns (for structured data like email, phone, dates)
  2. Keyword matching against a known skill list
  3. spaCy NER (for names, organizations, dates)

Why traditional NLP instead of just asking an LLM?
  - Speed: regex/spaCy is milliseconds vs seconds for LLM
  - Cost: no API call needed
  - Determinism: same input → same output every time
  - Privacy: text doesn't leave the server for extraction
  - The LLM is used later to EXPLAIN results, not compute them

How extraction works:
  1. Tokenize and clean text
  2. Run regex for contact info
  3. Scan skill keywords against normalized text
  4. Use spaCy for NER (names, dates, orgs)
  5. Heuristic section detection for education/experience

Interview questions:
  Q: What is NER?
  A: Named Entity Recognition — a type of sequence labeling that identifies
     and classifies named entities (Person, Organization, Date, Location) in text.

  Q: What is TF-IDF?
  A: Term Frequency–Inverse Document Frequency. Measures how important a word
     is to a document relative to a corpus. Rare words that appear often in a
     doc get high scores. Used here for text similarity.
"""

import re
from typing import Optional
import logging

try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
except Exception:
    SPACY_AVAILABLE = False
    nlp = None

from app.nlp.normalizer import skill_normalizer

logger = logging.getLogger(__name__)

# ── Comprehensive skill keyword list ─────────────────────────────────────────
KNOWN_SKILLS = [
    # Languages
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust",
    "Kotlin", "Swift", "PHP", "Ruby", "Scala", "R", "MATLAB",
    # Web Frontend
    "React", "Angular", "Vue.js", "Next.js", "HTML", "CSS", "Tailwind CSS",
    "Bootstrap", "jQuery", "Sass", "Redux", "Svelte",
    # Web Backend
    "FastAPI", "Django", "Flask", "Spring Boot", "Node.js", "Express.js",
    "Laravel", "Rails", "ASP.NET", "Gin",
    # Databases
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Oracle",
    "Cassandra", "DynamoDB", "Elasticsearch", "Neo4j", "InfluxDB",
    # Cloud
    "AWS", "Azure", "GCP", "Heroku", "Vercel", "Netlify",
    # DevOps
    "Docker", "Kubernetes", "CI/CD", "GitHub Actions", "Jenkins",
    "Terraform", "Ansible", "Linux",
    # AI/ML
    "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
    "TensorFlow", "PyTorch", "scikit-learn", "Keras", "OpenCV",
    "pandas", "NumPy", "Matplotlib", "Seaborn", "XGBoost",
    # GenAI / LLM
    "Generative AI", "LLM", "RAG", "LangChain", "OpenAI",
    "IBM Granite", "Hugging Face", "FAISS", "Pinecone", "ChromaDB",
    "Prompt Engineering", "Fine-tuning",
    # Data Engineering
    "Apache Spark", "PySpark", "Apache Kafka", "Airflow",
    "dbt", "ETL", "Data Warehousing",
    # BI/Analytics
    "Tableau", "Power BI", "Looker", "SQL Analytics",
    # APIs
    "REST API", "GraphQL", "gRPC", "WebSockets",
    # Testing
    "pytest", "Jest", "Selenium", "Cypress", "Unit Testing",
    # Concepts
    "Agile", "Scrum", "Git", "GitHub", "GitLab",
    "System Design", "Microservices", "Object-Oriented Programming",
    "Data Structures", "Algorithms",
    # Soft Skills (sometimes in JDs)
    "Communication", "Leadership", "Problem Solving", "Team Collaboration",
]

# Section headers in resumes
SECTION_HEADERS = {
    "skills": ["skills", "technical skills", "key skills", "core competencies", "technologies"],
    "education": ["education", "academic background", "qualifications", "degrees"],
    "experience": ["experience", "work experience", "professional experience", "employment"],
    "projects": ["projects", "personal projects", "key projects", "portfolio"],
    "certifications": ["certifications", "certificates", "credentials", "courses"],
    "summary": ["summary", "profile", "objective", "about", "professional summary"],
}


class ResumeExtractor:
    """Extracts structured information from raw resume text."""

    def __init__(self):
        # Pre-compile regex patterns for performance
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        self.phone_pattern = re.compile(
            r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}'
        )
        self.url_pattern = re.compile(
            r'https?://[^\s<>"{}|\\^`\[\]]+'
        )
        self.linkedin_pattern = re.compile(
            r'linkedin\.com/in/[\w-]+'
        )
        self.github_pattern = re.compile(
            r'github\.com/[\w-]+'
        )
        self.year_pattern = re.compile(
            r'\b(19|20)\d{2}\b'
        )

        # Build normalized skill set for matching
        self._skill_lookup = {}
        for skill in KNOWN_SKILLS:
            self._skill_lookup[skill.lower()] = skill

    def extract_all(self, text: str) -> dict:
        """
        Main extraction method. Returns a dictionary with all extracted fields.
        """
        if not text or len(text.strip()) < 10:
            return self._empty_result()

        clean_text = self._clean_text(text)
        sections = self._detect_sections(clean_text)

        return {
            "name": self._extract_name(clean_text),
            "email": self._extract_email(clean_text),
            "phone": self._extract_phone(clean_text),
            "linkedin": self._extract_linkedin(clean_text),
            "github": self._extract_github(clean_text),
            "skills": self._extract_skills(clean_text),
            "education": self._extract_education(sections.get("education", "")),
            "experience": self._extract_experience(sections.get("experience", "")),
            "projects": self._extract_projects(sections.get("projects", "")),
            "certifications": self._extract_certifications(sections.get("certifications", "")),
            "summary": self._extract_summary(sections.get("summary", "")),
            "years_of_experience": self._estimate_experience_years(clean_text),
        }

    def _clean_text(self, text: str) -> str:
        """Remove excessive whitespace and normalize unicode."""
        text = re.sub(r'\s+', ' ', text)
        text = text.replace('\u2022', '•').replace('\ufeff', '')
        return text.strip()

    def _detect_sections(self, text: str) -> dict[str, str]:
        """
        Split resume text into logical sections based on headers.
        Returns a dict mapping section_type → section_text.
        """
        sections = {}
        lines = text.split('\n') if '\n' in text else text.split('. ')
        current_section = "general"
        section_text = []

        for line in lines:
            line_lower = line.lower().strip()
            detected = None
            for section_type, headers in SECTION_HEADERS.items():
                if any(h in line_lower for h in headers) and len(line_lower) < 50:
                    detected = section_type
                    break

            if detected:
                if section_text:
                    sections[current_section] = ' '.join(section_text)
                current_section = detected
                section_text = []
            else:
                section_text.append(line)

        if section_text:
            sections[current_section] = ' '.join(section_text)

        return sections

    def _extract_name(self, text: str) -> Optional[str]:
        """Extract person name using spaCy NER, clean line patterns, or email/filename heuristics."""
        if SPACY_AVAILABLE and nlp:
            try:
                doc = nlp(text[:800])
                for ent in doc.ents:
                    if ent.label_ == "PERSON" and 2 <= len(ent.text.split()) <= 4:
                        clean_n = ent.text.strip()
                        if not any(char.isdigit() for char in clean_n) and "@" not in clean_n:
                            return clean_n
            except Exception:
                pass

        # Split text into original non-empty lines
        raw_lines = [l.strip() for l in text.replace('\r', '\n').split('\n') if l.strip()]
        for line in raw_lines[:5]:
            # Remove punctuation except spaces
            clean_line = re.sub(r'[^A-Za-z\s_]', '', line).strip()
            # Handle underscores in names like Abhay_Singh_Yadav
            clean_line = clean_line.replace('_', ' ')
            words = [w for w in clean_line.split() if len(w) > 1]
            if 2 <= len(words) <= 4:
                # Exclude header terms
                line_lower = clean_line.lower()
                if not any(h in line_lower for h in ["resume", "curriculum", "vitae", "email", "phone", "skills", "experience", "education"]):
                    return " ".join([w.capitalize() for w in words])

        # Heuristic from email username (e.g. ay2204490@gmail.com -> Abhay)
        email_match = self.email_pattern.search(text)
        if email_match:
            username = email_match.group(0).split('@')[0]
            clean_user = re.sub(r'[^A-Za-z]', ' ', username).strip()
            words = [w.capitalize() for w in clean_user.split() if len(w) > 2]
            if words:
                return " ".join(words)

        return "Candidate User"

    def _extract_email(self, text: str) -> Optional[str]:
        match = self.email_pattern.search(text)
        return match.group(0).lower() if match else None

    def _extract_phone(self, text: str) -> Optional[str]:
        match = self.phone_pattern.search(text)
        return match.group(0) if match else None

    def _extract_linkedin(self, text: str) -> Optional[str]:
        match = self.linkedin_pattern.search(text)
        return f"https://{match.group(0)}" if match else None

    def _extract_github(self, text: str) -> Optional[str]:
        match = self.github_pattern.search(text)
        return f"https://{match.group(0)}" if match else None

    def _extract_skills(self, text: str) -> list[str]:
        """
        Extract skills by scanning for known skill keywords.
        Handles multi-word skills and normalization.
        """
        found_skills = set()
        text_lower = text.lower()

        for skill in KNOWN_SKILLS:
            skill_lower = skill.lower()
            # Use word boundary search to avoid partial matches
            pattern = r'\b' + re.escape(skill_lower) + r'\b'
            if re.search(pattern, text_lower):
                normalized = skill_normalizer.normalize(skill)
                found_skills.add(normalized)

        # Also check for aliases
        from app.nlp.normalizer import SKILL_ALIASES
        for alias, canonical in SKILL_ALIASES.items():
            pattern = r'\b' + re.escape(alias) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(canonical)

        return sorted(list(found_skills))

    def _extract_education(self, text: str) -> list[dict]:
        """Extract education entries from education section."""
        if not text:
            return []

        entries = []
        degree_patterns = [
            r'\b(B\.?Tech|B\.?E\.?|B\.?S\.?|B\.?Sc|M\.?Tech|M\.?S\.?|M\.?Sc|MBA|Ph\.?D|Bachelor|Master|Associate)\b',
        ]

        for pattern in degree_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Extract surrounding context
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 100)
                entry_text = text[start:end].strip()
                entries.append({"raw": entry_text, "degree": match.group(0)})

        return entries if entries else [{"raw": text[:200], "degree": "Not detected"}]

    def _extract_experience(self, text: str) -> list[dict]:
        """Extract experience entries."""
        if not text:
            return []

        entries = []
        # Look for company + year patterns
        year_matches = list(self.year_pattern.finditer(text))

        if year_matches:
            for i, match in enumerate(year_matches[:6]):  # limit to 6 entries
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 150)
                entries.append({"raw": text[start:end].strip()})
        else:
            # No years found — just return raw text snippets
            chunks = [text[i:i+200] for i in range(0, min(len(text), 600), 200)]
            entries = [{"raw": c} for c in chunks]

        return entries

    def _extract_projects(self, text: str) -> list[dict]:
        """Extract project entries."""
        if not text:
            return []
        # Split by common project delimiters
        projects = re.split(r'\n\s*\n|•|\d+\.\s', text)
        result = []
        for p in projects[:5]:  # limit to 5 projects
            p = p.strip()
            if len(p) > 20:
                result.append({"raw": p[:300]})
        return result

    def _extract_certifications(self, text: str) -> list[str]:
        """Extract certification names."""
        if not text:
            return []
        certs = [
            line.strip() for line in text.split('\n')
            if len(line.strip()) > 5 and len(line.strip()) < 200
        ]
        return certs[:10]

    def _extract_summary(self, text: str) -> Optional[str]:
        """Extract professional summary."""
        if not text:
            return None
        return text.strip()[:500] if len(text.strip()) > 10 else None

    def _estimate_experience_years(self, text: str) -> Optional[float]:
        """
        Estimate years of experience by finding earliest/latest years or number of projects/skills.
        """
        years = [int(y) for y in self.year_pattern.findall(text)]
        if len(years) >= 2:
            years = sorted(set(years))
            valid_years = [y for y in years if 2010 <= y <= 2030]
            if len(valid_years) >= 2:
                diff = float(max(valid_years) - min(valid_years))
                return max(1.0, min(diff, 15.0))
        
        # Fallback heuristic based on length and skill count
        skills = self._extract_skills(text)
        if len(skills) > 10:
            return 3.0
        elif len(skills) > 5:
            return 2.0
        return 1.0

    def _empty_result(self) -> dict:
        return {
            "name": None, "email": None, "phone": None,
            "linkedin": None, "github": None, "skills": [],
            "education": [], "experience": [], "projects": [],
            "certifications": [], "summary": None, "years_of_experience": None,
        }


class JDExtractor:
    """Extracts structured requirements from job description text."""

    def __init__(self):
        self.resume_extractor = ResumeExtractor()

    def extract_all(self, text: str) -> dict:
        """Extract all relevant info from a job description."""
        if not text:
            return {}

        clean_text = re.sub(r'\s+', ' ', text).strip()

        return {
            "title": self._extract_title(clean_text),
            "required_skills": self._extract_skills(clean_text, required=True),
            "preferred_skills": self._extract_skills(clean_text, required=False),
            "technologies": self.resume_extractor._extract_skills(clean_text),
            "responsibilities": self._extract_responsibilities(clean_text),
            "experience_required": self._extract_experience_req(clean_text),
            "education_required": self._extract_education_req(clean_text),
            "domain": self._classify_domain(clean_text),
            "role_type": self._classify_role_type(clean_text),
        }

    def _extract_title(self, text: str) -> Optional[str]:
        """Extract job title from first few lines."""
        lines = [l.strip() for l in text[:300].split('\n') if l.strip()]
        if lines:
            return lines[0][:100]
        return None

    def _extract_skills(self, text: str, required: bool = True) -> list[str]:
        """Extract skills, optionally from 'required' vs 'preferred' sections."""
        text_lower = text.lower()

        if required:
            keywords = ["required", "must have", "must-have", "mandatory", "essential", "requirements"]
        else:
            keywords = ["preferred", "nice to have", "nice-to-have", "bonus", "plus", "good to have"]

        # Find relevant section
        section_text = text
        for kw in keywords:
            idx = text_lower.find(kw)
            if idx != -1:
                section_text = text[idx:idx+1000]
                break

        return self.resume_extractor._extract_skills(section_text)

    def _extract_responsibilities(self, text: str) -> list[str]:
        """Extract bullet-point responsibilities."""
        # Look for bullet points or numbered lists
        bullets = re.findall(r'[•\-\*]\s*([^\n•\-\*]{10,200})', text)
        if bullets:
            return [b.strip() for b in bullets[:10]]
        return []

    def _extract_experience_req(self, text: str) -> Optional[str]:
        """Extract experience requirement (e.g., '3-5 years')."""
        patterns = [
            r'\d+\+?\s*years?\s+of\s+experience',
            r'\d+\s*[-–]\s*\d+\s+years?\s+of\s+experience',
            r'minimum\s+\d+\s+years?',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None

    def _extract_education_req(self, text: str) -> Optional[str]:
        """Extract education requirement."""
        patterns = [
            r"Bachelor'?s?\s+degree",
            r"Master'?s?\s+degree",
            r"B\.?Tech|M\.?Tech|B\.?E|M\.?E",
            r"Ph\.?D",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None

    def _classify_domain(self, text: str) -> str:
        """Classify the job domain based on keyword frequency."""
        domain_keywords = {
            "Data Science": ["data science", "data analyst", "analytics", "statistics", "modeling"],
            "Backend": ["backend", "back-end", "server-side", "api development", "microservices"],
            "Frontend": ["frontend", "front-end", "ui development", "react", "angular"],
            "Full Stack": ["full stack", "fullstack", "full-stack"],
            "DevOps": ["devops", "sre", "infrastructure", "deployment", "ci/cd"],
            "AI/ML": ["machine learning", "deep learning", "neural", "mlops", "model training"],
            "Mobile": ["android", "ios", "mobile development", "flutter", "react native"],
            "Cybersecurity": ["security", "penetration testing", "soc", "devsecops"],
        }
        text_lower = text.lower()
        scores = {domain: 0 for domain in domain_keywords}
        for domain, keywords in domain_keywords.items():
            scores[domain] = sum(1 for kw in keywords if kw in text_lower)

        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "General Software Engineering"

    def _classify_role_type(self, text: str) -> str:
        """Classify role type: internship, junior, mid, senior, lead."""
        text_lower = text.lower()
        if any(w in text_lower for w in ["intern", "internship", "trainee"]):
            return "Internship"
        if any(w in text_lower for w in ["senior", "sr.", "lead", "principal", "staff"]):
            return "Senior"
        if any(w in text_lower for w in ["junior", "jr.", "entry level", "entry-level", "fresher"]):
            return "Junior"
        if any(w in text_lower for w in ["manager", "director", "head of", "vp", "chief"]):
            return "Management"
        return "Mid-level"


# Singletons
resume_extractor = ResumeExtractor()
jd_extractor = JDExtractor()
