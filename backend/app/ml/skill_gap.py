"""
CareerPilot AI — Skill Gap Engine (Traditional ML)
====================================================
What is this?
  The core skill comparison engine. Uses Python set operations + TF-IDF +
  cosine similarity to compute skill gaps between a resume and a job description.

Why traditional ML instead of LLM here?
  - Skill matching is a deterministic, structured task
  - The LLM is used later to EXPLAIN the gap in natural language
  - Python set operations are instant, accurate, and free
  - TF-IDF + cosine similarity adds semantic similarity for partial matches

What is TF-IDF?
  TF-IDF = Term Frequency × Inverse Document Frequency
  - TF: How often does a term appear in THIS document?
  - IDF: How rare is the term across ALL documents?
  - High TF-IDF = term is common in this doc but rare overall → distinctive
  Used here to represent skill text as vectors for similarity comparison.

What is Cosine Similarity?
  Measures the angle between two vectors in high-dimensional space.
  - cosine(θ) = 1 → identical
  - cosine(θ) = 0 → completely different
  - Formula: (A · B) / (|A| × |B|)
  Used here to find "partial" skill matches (e.g., SQL → PostgreSQL).

Interview questions:
  Q: What is the difference between exact matching and semantic matching?
  A: Exact = "Python" == "Python". Semantic uses vector representations to
     find similar concepts even with different wording.

  Q: What are limitations of TF-IDF for skill matching?
  A: No understanding of context. "Java" (language) and "Java" (island) get
     the same representation. Doesn't understand synonyms without a dictionary.
"""

from typing import Optional
import logging

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.nlp.normalizer import skill_normalizer

logger = logging.getLogger(__name__)

# Threshold above which two skills are considered "related" (partial match)
PARTIAL_MATCH_THRESHOLD = 0.35
# Threshold above which two skills are considered "same" (exact-like match)
EXACT_MATCH_THRESHOLD = 0.80


class SkillGapEngine:
    """
    Computes skill gaps between resume skills and JD skills.

    Pipeline:
    1. Normalize all skills (JS → JavaScript, etc.)
    2. Exact match: direct set intersection
    3. Partial match: TF-IDF cosine similarity for near-matches
    4. Missing: what the JD requires but resume doesn't have
    5. Compute a match score (clearly labeled as approximation)
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            analyzer="char_wb",  # Character n-grams work well for skill names
            ngram_range=(2, 4),
            min_df=1,
        )

    def analyze(
        self,
        resume_skills: list[str],
        jd_skills: list[str],
    ) -> dict:
        """
        Main analysis method. Returns detailed gap analysis.

        Args:
            resume_skills: Skills extracted from resume
            jd_skills: Skills extracted from job description

        Returns:
            dict with: matched, missing, partial, match_score, details
        """
        if not jd_skills:
            return {
                "matched": [],
                "missing": [],
                "partial": [],
                "match_score": 0.0,
                "score_explanation": "No JD skills provided.",
            }

        # Step 1: Normalize
        norm_resume = skill_normalizer.normalize_list(resume_skills)
        norm_jd = skill_normalizer.normalize_list(jd_skills)

        # Step 2: Exact matching (case-insensitive)
        resume_lower = {s.lower(): s for s in norm_resume}
        jd_lower = {s.lower(): s for s in norm_jd}

        matched = []
        remaining_jd = []

        for jd_lower_skill, jd_original in jd_lower.items():
            if jd_lower_skill in resume_lower:
                matched.append(jd_original)
            else:
                remaining_jd.append(jd_original)

        # Step 3: Partial matching via TF-IDF cosine similarity
        partial_matches = []
        truly_missing = []

        remaining_resume = [s for s in norm_resume if s.lower() not in {m.lower() for m in matched}]

        if remaining_jd and remaining_resume:
            partial_results = self._find_partial_matches(remaining_resume, remaining_jd)
            for jd_skill, best_match, score in partial_results:
                if score >= PARTIAL_MATCH_THRESHOLD:
                    partial_matches.append({
                        "jd_skill": jd_skill,
                        "resume_skill": best_match,
                        "similarity": round(score, 2),
                        "note": f"Your '{best_match}' is related to the required '{jd_skill}'"
                    })
                else:
                    truly_missing.append(jd_skill)
        else:
            truly_missing = remaining_jd

        # Step 4: Compute match score
        # Score = (exact_matches + 0.5 * partial_matches) / total_jd_skills * 100
        # IMPORTANT: This is an approximation for practice purposes only
        total = len(norm_jd)
        score_numerator = len(matched) + 0.5 * len(partial_matches)
        match_score = round((score_numerator / total * 100) if total > 0 else 0.0, 1)

        return {
            "matched": matched,
            "missing": truly_missing,
            "partial": partial_matches,
            "match_score": match_score,
            "score_explanation": (
                f"Approximation: ({len(matched)} exact + {len(partial_matches)}×0.5 partial) "
                f"/ {total} JD skills × 100. "
                "This is a practice metric, not an official ATS score."
            ),
            "resume_skills_normalized": norm_resume,
            "jd_skills_normalized": norm_jd,
        }

    def _find_partial_matches(
        self,
        resume_skills: list[str],
        jd_skills: list[str],
    ) -> list[tuple[str, str, float]]:
        """
        Use TF-IDF + cosine similarity to find partial skill matches.

        Returns list of (jd_skill, best_resume_match, similarity_score)
        """
        all_skills = resume_skills + jd_skills

        try:
            # Fit TF-IDF on all skills
            tfidf_matrix = self.vectorizer.fit_transform(all_skills)

            n_resume = len(resume_skills)
            resume_vectors = tfidf_matrix[:n_resume]
            jd_vectors = tfidf_matrix[n_resume:]

            # Compute pairwise cosine similarity: shape = (n_jd, n_resume)
            similarity_matrix = cosine_similarity(jd_vectors, resume_vectors)

            results = []
            for jd_idx, jd_skill in enumerate(jd_skills):
                if similarity_matrix.shape[1] == 0:
                    results.append((jd_skill, "", 0.0))
                    continue
                best_resume_idx = np.argmax(similarity_matrix[jd_idx])
                best_score = float(similarity_matrix[jd_idx][best_resume_idx])
                best_resume_skill = resume_skills[best_resume_idx]
                results.append((jd_skill, best_resume_skill, best_score))

            return results

        except Exception as e:
            logger.error(f"Error in partial matching: {e}")
            return [(skill, "", 0.0) for skill in jd_skills]

    def prioritize_gaps(self, missing_skills: list[str]) -> list[dict]:
        """
        Categorize and prioritize missing skills by type.
        Returns a structured list with priority info.
        """
        categories = {
            "Core/Language": ["Python", "Java", "JavaScript", "TypeScript", "Go", "C++"],
            "Framework": ["FastAPI", "Django", "React", "Angular", "Spring Boot"],
            "Database": ["PostgreSQL", "MySQL", "MongoDB", "Redis"],
            "Cloud/DevOps": ["AWS", "Azure", "GCP", "Docker", "Kubernetes", "CI/CD"],
            "AI/ML": ["Machine Learning", "Deep Learning", "NLP", "RAG", "LLM"],
        }

        result = []
        for skill in missing_skills:
            category = "Other"
            for cat_name, cat_skills in categories.items():
                if skill in cat_skills:
                    category = cat_name
                    break
            result.append({
                "skill": skill,
                "category": category,
                "priority": "High" if category in ["Core/Language", "Framework"] else "Medium",
            })

        return result


skill_gap_engine = SkillGapEngine()
