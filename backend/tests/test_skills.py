import pytest
from app.nlp.normalizer import skill_normalizer
from app.ml.skill_gap import skill_gap_engine

def test_skill_normalization():
    assert skill_normalizer.normalize("js") == "JavaScript"
    assert skill_normalizer.normalize("reactjs") == "React"
    assert skill_normalizer.normalize("postgres") == "PostgreSQL"
    assert skill_normalizer.normalize("fast api") == "FastAPI"

def test_skill_gap_engine():
    resume_skills = ["Python", "SQL", "Git", "React"]
    jd_skills = ["Python", "FastAPI", "PostgreSQL", "Docker", "Git", "AWS"]

    result = skill_gap_engine.analyze(resume_skills, jd_skills)

    assert "Python" in result["matched"]
    assert "Git" in result["matched"]
    assert "FastAPI" in result["missing"]
    assert "Docker" in result["missing"]
    assert "AWS" in result["missing"]
    assert result["match_score"] > 0
