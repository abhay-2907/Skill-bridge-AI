"""
CareerPilot AI — Interview Service
=====================================
Adaptive mock interview: question generation, answer evaluation, follow-up logic.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import (
    Interview, InterviewQuestion, InterviewAnswer,
    InterviewType, InterviewStatus, User
)
from app.ai.prompts import prompt_templates
from app.rag.pipeline import rag_pipeline

logger = logging.getLogger(__name__)

# Topics mapped to interview types
INTERVIEW_TOPICS = {
    InterviewType.TECHNICAL: ["Data Structures", "Algorithms", "System Design basics", "OOP", "Databases"],
    InterviewType.PYTHON: ["Python fundamentals", "OOP in Python", "decorators", "generators", "async/await", "memory management"],
    InterviewType.AI_ML: ["Machine Learning", "supervised learning", "neural networks", "overfitting", "model evaluation"],
    InterviewType.GENAI: ["LLM", "RAG", "prompt engineering", "fine-tuning", "vector embeddings", "FAISS"],
    InterviewType.RAG: ["RAG pipeline", "embeddings", "FAISS", "chunking", "retrieval", "context window"],
    InterviewType.SQL: ["SQL joins", "indexing", "transactions", "normalization", "query optimization"],
    InterviewType.HR: ["strengths", "weaknesses", "career goals", "work experience", "teamwork"],
    InterviewType.BEHAVIORAL: ["conflict resolution", "leadership", "problem solving", "time management", "failure"],
    InterviewType.SYSTEM_DESIGN: ["scalability", "load balancing", "caching", "database design", "microservices"],
    InterviewType.PROJECT: ["project architecture", "technical decisions", "challenges faced", "impact"],
}


class InterviewService:

    async def start_interview(
        self,
        interview_type: InterviewType,
        user: User,
        db: AsyncSession,
        target_role: Optional[str] = None,
        difficulty: str = "intermediate",
        resume_id: Optional[int] = None,
        job_description_id: Optional[int] = None,
    ) -> tuple[Interview, InterviewQuestion]:
        """Start a new interview session and generate the first question."""

        interview = Interview(
            user_id=user.id,
            resume_id=resume_id,
            job_description_id=job_description_id,
            interview_type=interview_type,
            target_role=target_role or "Software Engineer",
            difficulty=difficulty,
            status=InterviewStatus.IN_PROGRESS,
        )
        db.add(interview)
        await db.flush()

        # Generate first question
        question = await self._generate_question(
            interview=interview,
            db=db,
            topic=self._pick_topic(interview_type),
            order_index=0,
        )

        interview.total_questions = 1
        await db.commit()
        await db.refresh(interview)
        await db.refresh(question)
        return interview, question

    async def submit_answer(
        self,
        interview_id: int,
        answer_text: str,
        user: User,
        db: AsyncSession,
    ) -> dict:
        """
        Process user's answer:
        1. Evaluate the answer with AI
        2. Detect weakness
        3. Generate adaptive follow-up question
        4. Return feedback + next question
        """
        # Fetch interview
        interview_result = await db.execute(
            select(Interview).where(Interview.id == interview_id, Interview.user_id == user.id)
        )
        interview = interview_result.scalar_one_or_none()
        if not interview:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Interview session not found")

        if interview.status != InterviewStatus.IN_PROGRESS:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Interview is already completed")

        # Get the latest unanswered question
        questions_result = await db.execute(
            select(InterviewQuestion)
            .where(InterviewQuestion.interview_id == interview_id)
            .order_by(InterviewQuestion.order_index.desc())
        )
        latest_question = questions_result.scalar_one_or_none()
        if not latest_question:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="No question found for this interview")

        # Evaluate answer with AI
        evaluation = await self._evaluate_answer(
            question=latest_question.question_text,
            answer=answer_text,
            role=interview.target_role,
        )

        # Save answer + feedback
        answer = InterviewAnswer(
            question_id=latest_question.id,
            interview_id=interview_id,
            answer_text=answer_text,
            ai_score=evaluation.get("ai_score"),
            what_was_correct=evaluation.get("what_was_correct"),
            what_was_missing=evaluation.get("what_was_missing"),
            incorrect_concepts=evaluation.get("incorrect_concepts"),
            better_answer=evaluation.get("better_answer"),
            concepts_to_study=evaluation.get("concepts_to_study", []),
            detected_weakness=evaluation.get("detected_weakness"),
        )
        db.add(answer)

        interview.answered_questions += 1

        # Check if interview is complete (10 questions max)
        MAX_QUESTIONS = 10
        is_complete = interview.answered_questions >= MAX_QUESTIONS

        next_question = None
        if not is_complete:
            # Adaptive: if weakness detected, target that topic
            weakness = evaluation.get("detected_weakness")
            topic = weakness if weakness else self._pick_topic(interview.interview_type)

            next_question = await self._generate_question(
                interview=interview,
                db=db,
                topic=topic,
                order_index=interview.answered_questions,
                is_followup=bool(weakness),
                followup_reason=f"Weakness detected in: {weakness}" if weakness else None,
            )
            interview.total_questions += 1

        if is_complete:
            interview.status = InterviewStatus.COMPLETED
            interview.ended_at = datetime.now(timezone.utc)
            # Generate summary
            summary = await self._generate_summary(interview, db)
            interview.summary_feedback = summary

        await db.commit()
        await db.refresh(answer)

        return {
            "feedback": answer,
            "next_question": next_question,
            "is_complete": is_complete,
            "questions_answered": interview.answered_questions,
        }

    async def _generate_question(
        self,
        interview: Interview,
        db: AsyncSession,
        topic: str,
        order_index: int,
        is_followup: bool = False,
        followup_reason: Optional[str] = None,
    ) -> InterviewQuestion:
        """Generate an interview question using RAG + Granite."""

        # Get previous questions to avoid repetition
        prev_result = await db.execute(
            select(InterviewQuestion.question_text)
            .where(InterviewQuestion.interview_id == interview.id)
        )
        previous_questions = [row[0] for row in prev_result.fetchall()]

        # Use RAG to find relevant question context
        rag_result = await rag_pipeline.query(
            user_query=f"{interview.interview_type.value} interview question about {topic} for {interview.target_role}",
            prompt_template_fn=lambda rag_context, **kw: prompt_templates.interview_question_generation(
                role=interview.target_role,
                topic=topic,
                difficulty=interview.difficulty,
                interview_type=interview.interview_type.value,
                rag_context=rag_context,
                previous_questions=previous_questions,
            ),
        )

        question_text = rag_result["answer"].strip()
        # Clean up AI response (remove quotes, numbering)
        question_text = question_text.lstrip('123456789. "\'').strip()

        question = InterviewQuestion(
            interview_id=interview.id,
            question_text=question_text,
            question_type="conceptual" if interview.interview_type in [InterviewType.TECHNICAL, InterviewType.PYTHON] else "behavioral",
            topic=topic,
            skill=topic,
            difficulty=interview.difficulty,
            order_index=order_index,
            is_followup=is_followup,
            followup_reason=followup_reason,
            rag_sources=rag_result.get("sources", []),
        )
        db.add(question)
        await db.flush()
        return question

    async def _evaluate_answer(self, question: str, answer: str, role: str) -> dict:
        """Evaluate a user's answer using RAG + Granite."""
        rag_result = await rag_pipeline.query(
            user_query=f"{question} evaluation for {role}",
            prompt_template_fn=lambda rag_context, **kw: prompt_templates.interview_answer_evaluation(
                question=question,
                user_answer=answer,
                role=role,
                rag_context=rag_context,
            ),
        )

        # Parse JSON response
        try:
            raw = rag_result["answer"]
            start = raw.find('{')
            end = raw.rfind('}')
            if start != -1 and end != -1:
                return json.loads(raw[start:end+1])
        except (json.JSONDecodeError, ValueError):
            pass

        return {
            "ai_score": 5.0,
            "what_was_correct": "Response received",
            "what_was_missing": "Could not parse detailed feedback",
            "incorrect_concepts": "None detected",
            "better_answer": "Please refer to official documentation for this topic.",
            "concepts_to_study": [],
            "detected_weakness": None,
        }

    async def _generate_summary(self, interview: Interview, db: AsyncSession) -> str:
        """Generate end-of-interview summary."""
        prompt = prompt_templates.interview_summary(
            interview_type=interview.interview_type.value,
            role=interview.target_role,
            questions_answered=interview.answered_questions,
            weak_topics=interview.weak_topics or [],
            strong_topics=interview.strong_topics or [],
        )
        return await rag_pipeline.simple_generate(prompt, max_tokens=500, temperature=0.4)

    def _pick_topic(self, interview_type: InterviewType) -> str:
        """Pick a topic for the given interview type."""
        import random
        topics = INTERVIEW_TOPICS.get(interview_type, ["General Software Engineering"])
        return random.choice(topics)

    async def get_interview_history(self, user_id: int, db: AsyncSession) -> list[Interview]:
        result = await db.execute(
            select(Interview)
            .where(Interview.user_id == user_id)
            .order_by(Interview.started_at.desc())
            .limit(20)
        )
        return list(result.scalars().all())


interview_service = InterviewService()
