"""
CareerPilot AI — Skill Normalization
=======================================
What is this?
  A dictionary-based skill normalizer that maps common variants, abbreviations,
  and misspellings to their canonical (standard) form.

Why do we need this?
  Without normalization, "JS" and "JavaScript" would be treated as different skills.
  A user with "JS" on their resume would not match a JD requiring "JavaScript".
  This causes false negatives in skill gap analysis.

How it works:
  1. Tokenize the extracted skill text
  2. Lowercase + strip whitespace
  3. Lookup in the alias dictionary
  4. Return canonical name (or original if not found)

Traditional ML approach:
  This is a rule-based/dictionary approach — deterministic and fast.
  For a production system, you could also use fuzzy matching (fuzzywuzzy/rapidfuzz)
  or train a small classifier.

Interview questions:
  Q: Why not just use an LLM to normalize skills?
  A: LLMs are slow, expensive, non-deterministic, and overkill for a lookup task.
     A dictionary lookup is O(1), consistent, and free.

  Q: How would you scale this normalizer?
  A: Store aliases in a DB table, allow admin to add new ones, use fuzzy matching
     as a fallback for unknown variants.
"""

from typing import Optional


# ── Canonical Skill Alias Map ─────────────────────────────────────────────────
# Keys = variants/aliases, Values = canonical name
# All keys must be lowercase

SKILL_ALIASES: dict[str, str] = {
    # JavaScript
    "js": "JavaScript",
    "javascript": "JavaScript",
    "java script": "JavaScript",
    "ecmascript": "JavaScript",
    "es6": "JavaScript",
    "es2015": "JavaScript",
    "es2016": "JavaScript",
    "es2017": "JavaScript",

    # TypeScript
    "ts": "TypeScript",
    "typescript": "TypeScript",

    # Python
    "python": "Python",
    "python3": "Python",
    "python 3": "Python",
    "py": "Python",

    # React
    "react": "React",
    "reactjs": "React",
    "react.js": "React",
    "react js": "React",

    # Angular
    "angular": "Angular",
    "angularjs": "Angular",

    # Vue
    "vue": "Vue.js",
    "vuejs": "Vue.js",
    "vue.js": "Vue.js",

    # Node.js
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",

    # SQL
    "sql": "SQL",
    "structured query language": "SQL",

    # PostgreSQL
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "pg": "PostgreSQL",
    "psql": "PostgreSQL",

    # MySQL
    "mysql": "MySQL",

    # MongoDB
    "mongo": "MongoDB",
    "mongodb": "MongoDB",

    # Redis
    "redis": "Redis",

    # Docker
    "docker": "Docker",
    "dockerfile": "Docker",

    # Kubernetes
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",

    # Git
    "git": "Git",
    "github": "GitHub",
    "gitlab": "GitLab",

    # AWS
    "aws": "AWS",
    "amazon web services": "AWS",

    # Azure
    "azure": "Azure",
    "microsoft azure": "Azure",

    # GCP
    "gcp": "GCP",
    "google cloud": "GCP",
    "google cloud platform": "GCP",

    # Machine Learning
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",

    # Deep Learning
    "dl": "Deep Learning",
    "deep learning": "Deep Learning",

    # Generative AI
    "gen ai": "Generative AI",
    "genai": "Generative AI",
    "generative ai": "Generative AI",

    # NLP
    "nlp": "NLP",
    "natural language processing": "NLP",

    # FastAPI
    "fastapi": "FastAPI",
    "fast api": "FastAPI",

    # Django
    "django": "Django",

    # Flask
    "flask": "Flask",

    # Spring Boot
    "spring boot": "Spring Boot",
    "springboot": "Spring Boot",

    # REST API
    "rest": "REST API",
    "rest api": "REST API",
    "restful": "REST API",
    "restful api": "REST API",

    # GraphQL
    "graphql": "GraphQL",

    # TensorFlow
    "tensorflow": "TensorFlow",
    "tf": "TensorFlow",

    # PyTorch
    "pytorch": "PyTorch",
    "torch": "PyTorch",

    # scikit-learn
    "sklearn": "scikit-learn",
    "scikit-learn": "scikit-learn",
    "scikit learn": "scikit-learn",

    # Pandas
    "pandas": "pandas",

    # NumPy
    "numpy": "NumPy",
    "np": "NumPy",

    # Java
    "java": "Java",

    # C++
    "c++": "C++",
    "cpp": "C++",

    # C#
    "c#": "C#",
    "csharp": "C#",

    # Go
    "go": "Go",
    "golang": "Go",

    # Rust
    "rust": "Rust",

    # Linux
    "linux": "Linux",
    "unix": "Unix",

    # CI/CD
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "ci cd": "CI/CD",
    "continuous integration": "CI/CD",

    # Agile
    "agile": "Agile",
    "scrum": "Scrum",
    "kanban": "Kanban",

    # Data Science
    "data science": "Data Science",
    "ds": "Data Science",

    # Power BI
    "power bi": "Power BI",
    "powerbi": "Power BI",

    # Tableau
    "tableau": "Tableau",

    # Spark
    "spark": "Apache Spark",
    "apache spark": "Apache Spark",
    "pyspark": "PySpark",

    # Kafka
    "kafka": "Apache Kafka",
    "apache kafka": "Apache Kafka",

    # Elasticsearch
    "elasticsearch": "Elasticsearch",
    "elastic search": "Elasticsearch",
    "elk": "Elasticsearch",

    # RAG
    "rag": "RAG",
    "retrieval augmented generation": "RAG",
    "retrieval-augmented generation": "RAG",

    # LLM
    "llm": "LLM",
    "large language model": "LLM",

    # API
    "api": "API",

    # HTML
    "html": "HTML",
    "html5": "HTML",

    # CSS
    "css": "CSS",
    "css3": "CSS",

    # Tailwind
    "tailwind": "Tailwind CSS",
    "tailwindcss": "Tailwind CSS",
    "tailwind css": "Tailwind CSS",

    # Next.js
    "next": "Next.js",
    "nextjs": "Next.js",
    "next.js": "Next.js",
}


class SkillNormalizer:
    """
    Normalizes skill strings to their canonical form.

    Usage:
        normalizer = SkillNormalizer()
        normalizer.normalize("reactjs")  # → "React"
        normalizer.normalize_list(["JS", "Postgres", "ML"])
        # → ["JavaScript", "PostgreSQL", "Machine Learning"]
    """

    def __init__(self, custom_aliases: Optional[dict] = None):
        self.aliases = {**SKILL_ALIASES}
        if custom_aliases:
            self.aliases.update({k.lower(): v for k, v in custom_aliases.items()})

    def normalize(self, skill: str) -> str:
        """Normalize a single skill string."""
        if not skill:
            return skill
        cleaned = skill.strip().lower()
        return self.aliases.get(cleaned, skill.strip())

    def normalize_list(self, skills: list[str]) -> list[str]:
        """Normalize a list of skill strings, removing duplicates."""
        seen = set()
        result = []
        for skill in skills:
            normalized = self.normalize(skill)
            if normalized.lower() not in seen:
                seen.add(normalized.lower())
                result.append(normalized)
        return result

    def is_known_skill(self, skill: str) -> bool:
        """Check if a skill is in the alias dictionary."""
        return skill.strip().lower() in self.aliases

    def add_alias(self, alias: str, canonical: str):
        """Add a new alias at runtime."""
        self.aliases[alias.lower()] = canonical


# Singleton
skill_normalizer = SkillNormalizer()
