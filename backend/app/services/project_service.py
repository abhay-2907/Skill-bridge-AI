"""
CareerPilot AI — Project Recommendations Service
==================================================
Recommends hands-on portfolio projects based on skill gaps.
Uses traditional ML gap priority + IBM Granite generation.
"""

import json
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import ProjectRecommendation, SkillGap, User
from app.ai.prompts import prompt_templates
from app.rag.pipeline import rag_pipeline

logger = logging.getLogger(__name__)


class ProjectService:

    async def get_or_generate_recommendations(
        self,
        skill_gap_id: int,
        user: User,
        db: AsyncSession,
    ) -> list[ProjectRecommendation]:
        """
        Fetch existing recommendations for a skill gap, or generate new ones using AI.
        """
        # Check existing
        result = await db.execute(
            select(ProjectRecommendation).where(
                ProjectRecommendation.skill_gap_id == skill_gap_id,
                ProjectRecommendation.user_id == user.id,
            )
        )
        existing = list(result.scalars().all())
        if existing:
            return existing

        # Fetch skill gap
        gap_res = await db.execute(
            select(SkillGap).where(SkillGap.id == skill_gap_id, SkillGap.user_id == user.id)
        )
        skill_gap = gap_res.scalar_one_or_none()
        if not skill_gap:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Skill gap record not found")

        missing_skills = skill_gap.missing_skills or []
        target_role = "Software Engineer"
        if skill_gap.job_description:
            target_role = skill_gap.job_description.extracted_title or skill_gap.job_description.title or target_role

        # Generate projects via RAG + Granite
        rag_result = await rag_pipeline.query(
            user_query=f"portfolio project ideas for {target_role} practicing {', '.join(missing_skills[:5])}",
            prompt_template_fn=lambda rag_context, **kw: prompt_templates.project_recommendations(
                missing_skills=missing_skills if missing_skills else ["Fullstack Development"],
                target_role=target_role,
                rag_context=rag_context,
            ),
        )

        projects_data = self._parse_projects_json(rag_result["answer"], missing_skills)

        saved_projects = []
        for p in projects_data:
            rec = ProjectRecommendation(
                user_id=user.id,
                skill_gap_id=skill_gap_id,
                title=p.get("title", "Portfolio Project"),
                description=p.get("description", "A practical project targeting your skill gaps."),
                skills_covered=p.get("skills_covered", missing_skills[:3]),
                difficulty=p.get("difficulty", "intermediate"),
                estimated_days=p.get("estimated_days", 14),
                technologies=p.get("technologies", missing_skills[:4]),
                expected_outcome=p.get("expected_outcome", "Demonstrate end-to-end implementation skills."),
                features=p.get("features", []),
            )
            db.add(rec)
            saved_projects.append(rec)

        await db.commit()
        for p in saved_projects:
            await db.refresh(p)

        return saved_projects

    def _parse_projects_json(self, raw_text: str, fallback_skills: list[str]) -> list[dict]:
        try:
            start = raw_text.find('[')
            end = raw_text.rfind(']')
            if start != -1 and end != -1:
                return json.loads(raw_text[start:end+1])
        except Exception as e:
            logger.error(f"Error parsing projects JSON: {e}")

        # Fallback project
        return [
            {
                "title": "Full-Stack AI Application",
                "description": "Build an end-to-end system integrating API backend, database, and front-end.",
                "skills_covered": fallback_skills[:3] if fallback_skills else ["Python", "FastAPI"],
                "difficulty": "intermediate",
                "estimated_days": 14,
                "technologies": fallback_skills[:4] if fallback_skills else ["FastAPI", "PostgreSQL"],
                "features": ["User authentication", "REST API architecture", "Interactive dashboard"],
                "expected_outcome": "Production-ready portfolio artifact to demonstrate in interviews.",
            }
        ]

    async def get_user_saved_projects(self, user_id: int, db: AsyncSession) -> list[ProjectRecommendation]:
        res = await db.execute(
            select(ProjectRecommendation).where(
                ProjectRecommendation.user_id == user_id,
                ProjectRecommendation.is_saved == True
            )
        )
        return list(res.scalars().all())


project_service = ProjectService()
