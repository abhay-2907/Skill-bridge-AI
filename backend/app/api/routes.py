"""
CareerPilot AI — API Routes: Resume, Jobs, Skills, Roadmap, Projects, Interview, RAG, Career, Progress
========================================================================================================
All modular routers registered into FastAPI.
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.models.models import User, TaskStatus, InterviewType
from app.schemas.schemas import (
    ResumeResponse, JDAnalyzeRequest, JDResponse, SkillGapRequest, SkillGapResponse,
    RoadmapGenerateRequest, RoadmapResponse, RoadmapTaskResponse, RoadmapTaskUpdate,
    ProjectRecommendationResponse, InterviewStartRequest, InterviewAnswerRequest,
    InterviewQuestionResponse, InterviewAnswerResponse, InterviewSessionResponse,
    ChatRequest, ChatResponse, WhatIfRequest, WhatIfResponse, ProgressResponse, MessageResponse
)

from app.services.resume_service import resume_service
from app.services.job_service import job_service
from app.services.skill_service import skill_service
from app.services.roadmap_service import roadmap_service
from app.services.project_service import project_service
from app.services.interview_service import interview_service
from app.services.progress_service import progress_service
from app.rag.pipeline import rag_pipeline
from app.ai.prompts import prompt_templates
from app.ml.skill_gap import skill_gap_engine
from app.nlp.normalizer import skill_normalizer

# ── Resume Router ─────────────────────────────────────────────────────────────
resume_router = APIRouter(prefix="/resume", tags=["Resume"])

@resume_router.post("/upload", response_model=ResumeResponse)
async def upload_resume(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await resume_service.upload_and_analyze(file, user, db)

@resume_router.get("/active", response_model=Optional[ResumeResponse])
async def get_active_resume(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await resume_service.get_active_resume(user.id, db)

@resume_router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume_by_id(
    resume_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await resume_service.get_resume(resume_id, user.id, db)
    if not res:
        raise HTTPException(status_code=404, detail="Resume not found")
    return res


# ── Jobs Router ───────────────────────────────────────────────────────────────
jobs_router = APIRouter(prefix="/jobs", tags=["Job Description"])

@jobs_router.post("/analyze", response_model=JDResponse)
async def analyze_job_description(
    payload: JDAnalyzeRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await job_service.analyze_jd(
        raw_text=payload.raw_text,
        user=user,
        db=db,
        title=payload.title,
        company=payload.company
    )

@jobs_router.get("", response_model=List[JDResponse])
async def get_recent_jds(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await job_service.get_user_jds(user.id, db)


# ── Skills Router ─────────────────────────────────────────────────────────────
skills_router = APIRouter(prefix="/skills", tags=["Skills & Gap Analysis"])

@skills_router.post("/analyze", response_model=SkillGapResponse)
async def analyze_skill_gap(
    payload: SkillGapRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await skill_service.analyze_gap(
        resume_id=payload.resume_id,
        jd_id=payload.job_description_id,
        user=user,
        db=db
    )

@skills_router.get("/gap/{gap_id}", response_model=SkillGapResponse)
async def get_skill_gap(
    gap_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    gap = await skill_service.get_gap(gap_id, user.id, db)
    if not gap:
        raise HTTPException(status_code=404, detail="Gap analysis not found")
    return gap


# ── Roadmap Router ────────────────────────────────────────────────────────────
roadmap_router = APIRouter(prefix="/roadmap", tags=["Learning Roadmap"])

@roadmap_router.post("/generate", response_model=RoadmapResponse)
async def generate_roadmap(
    payload: RoadmapGenerateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await roadmap_service.generate(
        skill_gap_id=payload.skill_gap_id,
        duration_days=payload.duration_days,
        hours_per_week=payload.available_hours_per_week or 10,
        user=user,
        db=db
    )

@roadmap_router.patch("/{roadmap_id}/tasks/{task_id}", response_model=RoadmapTaskResponse)
async def update_roadmap_task(
    roadmap_id: int,
    task_id: int,
    payload: RoadmapTaskUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not payload.status:
        raise HTTPException(status_code=400, detail="Status must be provided")
    return await roadmap_service.update_task(
        roadmap_id=roadmap_id,
        task_id=task_id,
        status=payload.status,
        user_id=user.id,
        db=db
    )


# ── Projects Router ───────────────────────────────────────────────────────────
projects_router = APIRouter(prefix="/projects", tags=["Project Recommendations"])

@projects_router.get("/recommendations/{skill_gap_id}", response_model=List[ProjectRecommendationResponse])
async def get_project_recommendations(
    skill_gap_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await project_service.get_or_generate_recommendations(
        skill_gap_id=skill_gap_id,
        user=user,
        db=db
    )


# ── Interview Router ──────────────────────────────────────────────────────────
interview_router = APIRouter(prefix="/interview", tags=["Mock Interview"])

@interview_router.post("/start")
async def start_mock_interview(
    payload: InterviewStartRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    interview, question = await interview_service.start_interview(
        interview_type=payload.interview_type,
        user=user,
        db=db,
        target_role=payload.target_role,
        difficulty=payload.difficulty,
        resume_id=payload.resume_id,
        job_description_id=payload.job_description_id
    )
    return {
        "interview_id": interview.id,
        "interview_type": interview.interview_type,
        "target_role": interview.target_role,
        "difficulty": interview.difficulty,
        "question": question
    }

@interview_router.post("/{interview_id}/answer")
async def submit_interview_answer(
    interview_id: int,
    payload: InterviewAnswerRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await interview_service.submit_answer(
        interview_id=interview_id,
        answer_text=payload.answer_text,
        user=user,
        db=db
    )

@interview_router.get("/history", response_model=List[InterviewSessionResponse])
async def get_interview_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await interview_service.get_interview_history(user.id, db)


# ── RAG Career Assistant Router ───────────────────────────────────────────────
rag_router = APIRouter(prefix="/rag", tags=["RAG Career Assistant"])

@rag_router.post("/chat", response_model=ChatResponse)
async def chat_with_career_assistant(
    payload: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    rag_result = await rag_pipeline.query(
        user_query=payload.message,
        prompt_template_fn=lambda rag_context, **kw: prompt_templates.career_assistant_chat(
            user_message=payload.message,
            rag_context=rag_context,
            user_profile={"target_role": "Software Engineer"},
            conversation_history=[]
        )
    )

    return ChatResponse(
        conversation_id=payload.conversation_id or 1,
        message_id=1,
        answer=rag_result["answer"],
        sources=rag_result.get("sources", []),
        is_grounded=rag_result.get("is_grounded", False)
    )


# ── Career What-If Router ─────────────────────────────────────────────────────
career_router = APIRouter(prefix="/career", tags=["Career What-If Simulation"])

@career_router.post("/what-if", response_model=WhatIfResponse)
async def simulate_career_what_if(
    payload: WhatIfRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Retrieve user's current skills
    active_resume = await resume_service.get_active_resume(user.id, db)
    current_skills = active_resume.extracted_skills if active_resume and active_resume.extracted_skills else ["Python", "Git"]

    norm_current = skill_normalizer.normalize_list(current_skills)
    norm_hypo = skill_normalizer.normalize_list(payload.hypothetical_skills)
    combined = sorted(list(set(norm_current + norm_hypo)))

    target_role = payload.target_role or "Full Stack Engineer"
    
    # Run gap against hypothetical skills
    gap_res = skill_gap_engine.analyze(
        resume_skills=combined,
        jd_skills=["Python", "FastAPI", "PostgreSQL", "Docker", "React", "Kubernetes", "AWS"]
    )

    analysis_text = await rag_pipeline.simple_generate(
        prompt=prompt_templates.career_what_if(
            current_skills=norm_current,
            hypothetical_skills=norm_hypo,
            combined_skills=combined,
            target_role=target_role,
            remaining_gaps=gap_res["missing"],
            timeline_months=payload.timeline_months or 3
        ),
        max_tokens=800,
        temperature=0.3
    )

    return WhatIfResponse(
        current_skills=norm_current,
        hypothetical_skills=norm_hypo,
        combined_skills=combined,
        remaining_gaps=gap_res["missing"],
        coverage_improvement=gap_res["match_score"],
        analysis=analysis_text,
        recommended_projects=["Microservices Job Board", "Cloud-Native Task Queue"],
        updated_roadmap_suggestion=f"Focus first 4 weeks on {norm_hypo[0] if norm_hypo else 'core skills'}, then integrate via a portfolio project.",
        disclaimer="Simulated estimation based on skill taxonomy. Not a hiring guarantee."
    )


# ── Progress Router ───────────────────────────────────────────────────────────
progress_router = APIRouter(prefix="/progress", tags=["Progress"])

@progress_router.get("", response_model=ProgressResponse)
async def get_progress(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await progress_service.get_or_calculate_progress(user, db)
