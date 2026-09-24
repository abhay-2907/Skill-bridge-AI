"""
CareerPilot AI — Pydantic Schemas
====================================
What is this?
  Pydantic models that define the shape of request/response data for the API.

Why separate from ORM models?
  ORM models represent the database structure.
  Pydantic schemas represent the API contract.
  Keeping them separate lets you:
  - Expose only certain fields to the client
  - Validate and coerce request data
  - Return different shapes for list vs detail views
  - Version your API without changing the DB

Interview tip:
  Q: What does `model_config = ConfigDict(from_attributes=True)` do?
  A: Tells Pydantic to read data from ORM model attributes (not just dicts).
     Required for `model_validate(orm_object)` to work.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models.models import InterviewType, InterviewStatus, TaskStatus, MessageRole


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=2, max_length=255)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    full_name: str
    is_active: bool
    created_at: datetime


# ═══════════════════════════════════════════════════════════════════════════════
# USER PROFILE SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class UserProfileUpdate(BaseModel):
    target_role: Optional[str] = None
    experience_level: Optional[str] = None
    career_goal: Optional[str] = None
    available_hours_per_week: Optional[int] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    bio: Optional[str] = None


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    target_role: Optional[str]
    experience_level: Optional[str]
    career_goal: Optional[str]
    available_hours_per_week: Optional[int]
    linkedin_url: Optional[str]
    github_url: Optional[str]
    bio: Optional[str]
    current_skills: Optional[List[str]]


# ═══════════════════════════════════════════════════════════════════════════════
# RESUME SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    filename: str
    file_type: str
    extracted_name: Optional[str]
    extracted_email: Optional[str]
    extracted_phone: Optional[str]
    extracted_skills: Optional[List[str]]
    extracted_education: Optional[List[Any]]
    extracted_experience: Optional[List[Any]]
    extracted_projects: Optional[List[Any]]
    extracted_certifications: Optional[List[Any]]
    extracted_summary: Optional[str]
    years_of_experience: Optional[float]
    ai_analysis: Optional[str]
    analysis_status: str
    created_at: datetime


# ═══════════════════════════════════════════════════════════════════════════════
# JOB DESCRIPTION SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class JDAnalyzeRequest(BaseModel):
    raw_text: str = Field(..., min_length=50)
    title: Optional[str] = None
    company: Optional[str] = None


class JDResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    title: Optional[str]
    company: Optional[str]
    extracted_title: Optional[str]
    extracted_required_skills: Optional[List[str]]
    extracted_preferred_skills: Optional[List[str]]
    extracted_technologies: Optional[List[str]]
    extracted_responsibilities: Optional[List[str]]
    extracted_experience_required: Optional[str]
    extracted_education_required: Optional[str]
    extracted_domain: Optional[str]
    extracted_role_type: Optional[str]
    ai_analysis: Optional[str]
    created_at: datetime


# ═══════════════════════════════════════════════════════════════════════════════
# SKILL GAP SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class SkillGapRequest(BaseModel):
    resume_id: int
    job_description_id: int


class SkillGapResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    resume_id: int
    job_description_id: int
    matched_skills: Optional[List[str]]
    missing_skills: Optional[List[str]]
    partial_skills: Optional[List[dict]]
    match_score: Optional[float]
    ai_explanation: Optional[str]
    created_at: datetime


# ═══════════════════════════════════════════════════════════════════════════════
# ROADMAP SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class RoadmapGenerateRequest(BaseModel):
    skill_gap_id: int
    duration_days: int = Field(default=30, ge=30, le=90)
    available_hours_per_week: Optional[int] = 10


class RoadmapTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    week_number: int
    day_start: Optional[int]
    day_end: Optional[int]
    skill: str
    topic: str
    task_description: str
    practice_task: Optional[str]
    project_suggestion: Optional[str]
    resource_url: Optional[str]
    resource_name: Optional[str]
    estimated_hours: Optional[float]
    difficulty: Optional[str]
    status: TaskStatus
    order_index: int


class RoadmapTaskUpdate(BaseModel):
    status: Optional[TaskStatus] = None
    task_description: Optional[str] = None
    resource_url: Optional[str] = None


class RoadmapResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    duration_days: int
    total_tasks: int
    completed_tasks: int
    is_active: bool
    tasks: List[RoadmapTaskResponse]
    created_at: datetime


# ═══════════════════════════════════════════════════════════════════════════════
# PROJECT RECOMMENDATION SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class ProjectRecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str
    skills_covered: Optional[List[str]]
    difficulty: Optional[str]
    estimated_days: Optional[int]
    technologies: Optional[List[str]]
    expected_outcome: Optional[str]
    features: Optional[List[str]]
    is_saved: bool


# ═══════════════════════════════════════════════════════════════════════════════
# INTERVIEW SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class InterviewStartRequest(BaseModel):
    interview_type: InterviewType
    target_role: Optional[str] = None
    difficulty: str = "intermediate"
    resume_id: Optional[int] = None
    job_description_id: Optional[int] = None


class InterviewAnswerRequest(BaseModel):
    answer_text: str = Field(..., min_length=1)


class InterviewQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    question_text: str
    question_type: Optional[str]
    topic: Optional[str]
    skill: Optional[str]
    difficulty: Optional[str]
    order_index: int
    is_followup: bool
    followup_reason: Optional[str]


class InterviewAnswerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    answer_text: str
    ai_score: Optional[float]
    what_was_correct: Optional[str]
    what_was_missing: Optional[str]
    incorrect_concepts: Optional[str]
    better_answer: Optional[str]
    concepts_to_study: Optional[List[str]]
    rag_sources: Optional[List[dict]]


class InterviewSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    interview_type: InterviewType
    target_role: Optional[str]
    difficulty: str
    status: InterviewStatus
    total_questions: int
    answered_questions: int
    overall_score: Optional[float]
    summary_feedback: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]


class NextQuestionResponse(BaseModel):
    interview_id: int
    question: InterviewQuestionResponse
    is_complete: bool = False


# ═══════════════════════════════════════════════════════════════════════════════
# RAG / CONVERSATION SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[int] = None


class RAGSource(BaseModel):
    title: str
    document_type: Optional[str]
    relevance_score: float
    content_preview: str


class ChatResponse(BaseModel):
    conversation_id: int
    message_id: int
    answer: str
    sources: List[RAGSource]
    is_grounded: bool  # True if RAG found relevant context


# ═══════════════════════════════════════════════════════════════════════════════
# CAREER WHAT-IF SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class WhatIfRequest(BaseModel):
    hypothetical_skills: List[str] = Field(..., min_length=1)
    timeline_months: Optional[int] = 3
    target_role: Optional[str] = None
    resume_id: Optional[int] = None


class WhatIfResponse(BaseModel):
    current_skills: List[str]
    hypothetical_skills: List[str]
    combined_skills: List[str]
    remaining_gaps: List[str]
    coverage_improvement: float  # % improvement (approximation)
    analysis: str
    recommended_projects: List[str]
    updated_roadmap_suggestion: str
    disclaimer: str


# ═══════════════════════════════════════════════════════════════════════════════
# PROGRESS SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class ProgressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    total_roadmap_tasks: int
    completed_roadmap_tasks: int
    total_interviews: int
    completed_interviews: int
    average_interview_score: Optional[float]
    skills_learned: Optional[List[str]]
    weak_areas: Optional[List[str]]
    strong_areas: Optional[List[str]]
    roadmap_completion_percentage: float
    interview_completion_percentage: float


# ═══════════════════════════════════════════════════════════════════════════════
# GENERIC
# ═══════════════════════════════════════════════════════════════════════════════

class MessageResponse(BaseModel):
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
