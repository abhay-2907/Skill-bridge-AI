"""
CareerPilot AI — Roadmap Service
===================================
Generates personalized learning roadmaps using IBM Granite + RAG.
"""

import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.models.models import Roadmap, RoadmapTask, SkillGap, TaskStatus, User
from app.ai.prompts import prompt_templates
from app.rag.pipeline import rag_pipeline

logger = logging.getLogger(__name__)


class RoadmapService:

    async def generate(
        self,
        skill_gap_id: int,
        duration_days: int,
        hours_per_week: int,
        user: User,
        db: AsyncSession,
    ) -> Roadmap:
        """Generate a personalized roadmap from a skill gap analysis."""

        # Fetch skill gap
        result = await db.execute(
            select(SkillGap).where(SkillGap.id == skill_gap_id, SkillGap.user_id == user.id)
        )
        skill_gap = result.scalar_one_or_none()
        if not skill_gap:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Skill gap analysis not found")

        missing_skills = skill_gap.missing_skills or []
        if not missing_skills:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="No missing skills to create a roadmap for")

        # Determine target role from JD
        jd_result = await db.execute(
            select("job_descriptions").where_clause(None)
        )

        # Build target role string
        from app.models.models import JobDescription
        jd_res = await db.execute(
            select(JobDescription).where(JobDescription.id == skill_gap.job_description_id)
        )
        jd = jd_res.scalar_one_or_none()
        target_role = (jd.extracted_title or jd.title) if jd else "Software Engineer"

        # Generate roadmap using RAG + Granite
        prompt = prompt_templates.roadmap_generation(
            missing_skills=missing_skills,
            target_role=target_role,
            duration_days=duration_days,
            hours_per_week=hours_per_week,
        )
        raw_response = await rag_pipeline.simple_generate(prompt, max_tokens=2000, temperature=0.4)

        # Parse JSON response
        tasks = self._parse_roadmap_response(raw_response)

        # Save roadmap
        roadmap = Roadmap(
            user_id=user.id,
            skill_gap_id=skill_gap_id,
            title=f"{duration_days}-Day Roadmap for {target_role}",
            duration_days=duration_days,
            total_tasks=len(tasks),
            completed_tasks=0,
            is_active=True,
        )
        db.add(roadmap)
        await db.flush()

        # Save tasks
        for i, task_data in enumerate(tasks):
            task = RoadmapTask(
                roadmap_id=roadmap.id,
                week_number=task_data.get("week_number", (i // 3) + 1),
                day_start=task_data.get("day_start"),
                day_end=task_data.get("day_end"),
                skill=task_data.get("skill", "General"),
                topic=task_data.get("topic", "Learning"),
                task_description=task_data.get("task_description", "Complete the learning objective"),
                practice_task=task_data.get("practice_task"),
                project_suggestion=task_data.get("project_suggestion"),
                resource_url=task_data.get("resource_url"),
                resource_name=task_data.get("resource_name"),
                estimated_hours=task_data.get("estimated_hours", hours_per_week),
                difficulty=task_data.get("difficulty", "intermediate"),
                status=TaskStatus.PENDING,
                order_index=i,
            )
            db.add(task)

        await db.commit()
        await db.refresh(roadmap)

        # Load tasks
        tasks_result = await db.execute(
            select(RoadmapTask)
            .where(RoadmapTask.roadmap_id == roadmap.id)
            .order_by(RoadmapTask.order_index)
        )
        roadmap.tasks = list(tasks_result.scalars().all())
        return roadmap

    def _parse_roadmap_response(self, raw_response: str) -> list[dict]:
        """Parse the AI-generated JSON roadmap response."""
        tasks = []
        try:
            # Find JSON in response
            start = raw_response.find('{')
            if start == -1:
                start = raw_response.find('[')
            end = raw_response.rfind('}')
            if end == -1:
                end = raw_response.rfind(']')

            if start != -1 and end != -1:
                json_str = raw_response[start:end+1]
                data = json.loads(json_str)

                # Handle both array and object responses
                if isinstance(data, list):
                    tasks = data
                elif isinstance(data, dict) and "weeks" in data:
                    for week in data.get("weeks", []):
                        week_num = week.get("week_number", 1)
                        for task in week.get("tasks", []):
                            task["week_number"] = week_num
                            tasks.append(task)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse roadmap JSON: {e}")
            # Return a fallback task list
            tasks = self._fallback_tasks()

        return tasks if tasks else self._fallback_tasks()

    def _fallback_tasks(self) -> list[dict]:
        """Fallback tasks if AI generation fails."""
        return [
            {
                "week_number": 1, "skill": "Foundation", "topic": "Review & Planning",
                "task_description": "Review your current skills and create a study plan",
                "difficulty": "beginner", "estimated_hours": 5,
                "day_start": 1, "day_end": 7,
            }
        ]

    async def update_task(
        self, roadmap_id: int, task_id: int, status: TaskStatus, user_id: int, db: AsyncSession
    ) -> RoadmapTask:
        """Update a task's status and update roadmap progress."""
        result = await db.execute(
            select(RoadmapTask)
            .join(Roadmap)
            .where(RoadmapTask.id == task_id, Roadmap.user_id == user_id)
        )
        task = result.scalar_one_or_none()
        if not task:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Task not found")

        task.status = status

        # Update roadmap completion count
        roadmap_result = await db.execute(
            select(Roadmap).where(Roadmap.id == roadmap_id)
        )
        roadmap = roadmap_result.scalar_one_or_none()
        if roadmap:
            all_tasks_result = await db.execute(
                select(RoadmapTask).where(RoadmapTask.roadmap_id == roadmap_id)
            )
            all_tasks = list(all_tasks_result.scalars().all())
            roadmap.completed_tasks = sum(1 for t in all_tasks if t.status == TaskStatus.COMPLETED)

        await db.commit()
        await db.refresh(task)
        return task


roadmap_service = RoadmapService()
