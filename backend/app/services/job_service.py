"""
CareerPilot AI — Job Description Service
==========================================
Business logic for JD analysis and extraction.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.models.models import JobDescription, User
from app.nlp.extractor import jd_extractor
from app.nlp.normalizer import skill_normalizer
from app.ai.prompts import prompt_templates
from app.rag.pipeline import rag_pipeline

logger = logging.getLogger(__name__)


class JobService:

    async def analyze_jd(
        self, raw_text: str, user: User, db: AsyncSession,
        title: Optional[str] = None, company: Optional[str] = None
    ) -> JobDescription:
        """Analyze a job description text and save results."""

        # Extract structured data using NLP
        extracted = jd_extractor.extract_all(raw_text)

        # Normalize skills
        required_skills = skill_normalizer.normalize_list(extracted.get("required_skills", []))
        preferred_skills = skill_normalizer.normalize_list(extracted.get("preferred_skills", []))
        technologies = skill_normalizer.normalize_list(extracted.get("technologies", []))

        # Create JD record
        jd = JobDescription(
            user_id=user.id,
            title=title or extracted.get("title"),
            company=company,
            raw_text=raw_text,
            extracted_title=extracted.get("title"),
            extracted_required_skills=required_skills,
            extracted_preferred_skills=preferred_skills,
            extracted_technologies=technologies,
            extracted_responsibilities=extracted.get("responsibilities", []),
            extracted_experience_required=extracted.get("experience_required"),
            extracted_education_required=extracted.get("education_required"),
            extracted_domain=extracted.get("domain"),
            extracted_role_type=extracted.get("role_type"),
        )
        db.add(jd)
        await db.flush()

        # Generate AI analysis
        try:
            ai_analysis = await self._generate_ai_analysis(raw_text, extracted)
            jd.ai_analysis = ai_analysis
        except Exception as e:
            logger.error(f"JD AI analysis failed: {e}")

        await db.commit()
        await db.refresh(jd)
        return jd

    async def _generate_ai_analysis(self, raw_text: str, extracted: dict) -> str:
        prompt = prompt_templates.jd_analysis(raw_text, extracted)
        return await rag_pipeline.simple_generate(prompt, max_tokens=600, temperature=0.4)

    async def get_jd(self, jd_id: int, user_id: int, db: AsyncSession) -> Optional[JobDescription]:
        result = await db.execute(
            select(JobDescription).where(
                JobDescription.id == jd_id, JobDescription.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_user_jds(self, user_id: int, db: AsyncSession) -> list[JobDescription]:
        result = await db.execute(
            select(JobDescription)
            .where(JobDescription.user_id == user_id)
            .order_by(JobDescription.created_at.desc())
            .limit(10)
        )
        return list(result.scalars().all())


job_service = JobService()
