"""
CareerPilot AI — Skill Gap Service
=====================================
Orchestrates skill gap analysis between resume and JD.
"""

import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.models.models import Resume, JobDescription, SkillGap, User
from app.ml.skill_gap import skill_gap_engine
from app.ai.prompts import prompt_templates
from app.rag.pipeline import rag_pipeline

logger = logging.getLogger(__name__)


class SkillService:

    async def analyze_gap(
        self,
        resume_id: int,
        jd_id: int,
        user: User,
        db: AsyncSession,
    ) -> SkillGap:
        """Run skill gap analysis between a resume and job description."""

        # Fetch resume
        resume_result = await db.execute(
            select(Resume).where(Resume.id == resume_id, Resume.user_id == user.id)
        )
        resume = resume_result.scalar_one_or_none()
        if not resume:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Resume not found")

        # Fetch JD
        jd_result = await db.execute(
            select(JobDescription).where(JobDescription.id == jd_id, JobDescription.user_id == user.id)
        )
        jd = jd_result.scalar_one_or_none()
        if not jd:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Job description not found")

        # Run ML gap analysis
        resume_skills = resume.extracted_skills or []
        jd_skills = list(set(
            (jd.extracted_required_skills or []) +
            (jd.extracted_technologies or [])
        ))

        gap_result = skill_gap_engine.analyze(resume_skills, jd_skills)

        # Build partial skill list
        partial = gap_result.get("partial", [])

        # Generate AI explanation using RAG
        target_role = jd.extracted_title or jd.title or "the target role"
        rag_result = await rag_pipeline.query(
            user_query=f"skill gap analysis for {target_role}: missing {', '.join(gap_result['missing'][:5])}",
            prompt_template_fn=lambda rag_context, **kw: prompt_templates.skill_gap_explanation(
                matched=gap_result["matched"],
                missing=gap_result["missing"],
                partial=partial,
                target_role=target_role,
                rag_context=rag_context,
            ),
        )

        # Save to DB
        skill_gap = SkillGap(
            user_id=user.id,
            resume_id=resume_id,
            job_description_id=jd_id,
            matched_skills=gap_result["matched"],
            missing_skills=gap_result["missing"],
            partial_skills=partial,
            match_score=gap_result["match_score"],
            ai_explanation=rag_result["answer"],
        )
        db.add(skill_gap)
        await db.commit()
        await db.refresh(skill_gap)
        return skill_gap

    async def get_gap(self, gap_id: int, user_id: int, db: AsyncSession) -> Optional[SkillGap]:
        result = await db.execute(
            select(SkillGap).where(SkillGap.id == gap_id, SkillGap.user_id == user_id)
        )
        return result.scalar_one_or_none()


skill_service = SkillService()
