"""
CareerPilot AI — Progress Service
===================================
Aggregates learning, interview scores, and roadmap completion metrics.
"""

from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.models import Progress, Roadmap, RoadmapTask, Interview, InterviewAnswer, TaskStatus, User


class ProgressService:

    async def get_or_calculate_progress(self, user: User, db: AsyncSession) -> dict:
        """Calculate and return live user progress metrics."""

        # 1. Roadmaps & Tasks
        roadmap_res = await db.execute(
            select(Roadmap).where(Roadmap.user_id == user.id, Roadmap.is_active == True)
        )
        roadmaps = list(roadmap_res.scalars().all())
        roadmap_ids = [r.id for r in roadmaps]

        total_tasks = 0
        completed_tasks = 0
        if roadmap_ids:
            task_res = await db.execute(
                select(RoadmapTask).where(RoadmapTask.roadmap_id.in_(roadmap_ids))
            )
            tasks = list(task_res.scalars().all())
            total_tasks = len(tasks)
            completed_tasks = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)

        # 2. Interviews & Answers
        interview_res = await db.execute(
            select(Interview).where(Interview.user_id == user.id)
        )
        interviews = list(interview_res.scalars().all())
        total_interviews = len(interviews)
        completed_interviews = sum(1 for i in interviews if i.status.value == "completed")

        # Average interview score
        ans_res = await db.execute(
            select(func.avg(InterviewAnswer.ai_score))
            .join(Interview)
            .where(Interview.user_id == user.id, InterviewAnswer.ai_score.isnot(None))
        )
        avg_score = ans_res.scalar()
        avg_score_val = round(float(avg_score), 1) if avg_score is not None else 0.0

        # Weak and Strong Areas from Answers
        ans_weak_res = await db.execute(
            select(InterviewAnswer.detected_weakness)
            .join(Interview)
            .where(Interview.user_id == user.id, InterviewAnswer.detected_weakness.isnot(None))
            .limit(10)
        )
        weak_areas = list(set([w[0] for w in ans_weak_res.fetchall() if w[0]]))

        # Percentage calculations
        roadmap_pct = round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0.0
        interview_pct = round((completed_interviews / total_interviews * 100), 1) if total_interviews > 0 else 0.0

        return {
            "total_roadmap_tasks": total_tasks,
            "completed_roadmap_tasks": completed_tasks,
            "total_interviews": total_interviews,
            "completed_interviews": completed_interviews,
            "average_interview_score": avg_score_val,
            "skills_learned": [t.skill for t in tasks if t.status == TaskStatus.COMPLETED][:10] if roadmap_ids else [],
            "weak_areas": weak_areas,
            "strong_areas": [],
            "roadmap_completion_percentage": roadmap_pct,
            "interview_completion_percentage": interview_pct,
        }


progress_service = ProgressService()
