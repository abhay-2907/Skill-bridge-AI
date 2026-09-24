"""
CareerPilot AI — SQLAlchemy ORM Models
=========================================
What is an ORM?
  Object-Relational Mapper: maps Python classes → database tables.
  Instead of writing raw SQL, you work with Python objects.

Why SQLAlchemy?
  - Most mature Python ORM
  - Async support via asyncpg
  - Handles migrations (with Alembic)
  - Relationships, lazy/eager loading, etc.

Interview tip:
  Q: What is the N+1 query problem?
  A: Fetching a list of objects, then querying relationships one-by-one.
     Fix with joinedload() or selectinload() to fetch in one query.
"""

from datetime import datetime, timezone
from typing import Optional, List
import enum

from sqlalchemy import (
    String, Text, Boolean, Integer, Float, DateTime,
    ForeignKey, Enum as SAEnum, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


def utcnow():
    return datetime.now(timezone.utc)


# ── Enums ─────────────────────────────────────────────────────────────────────

class InterviewType(str, enum.Enum):
    TECHNICAL = "technical"
    HR = "hr"
    BEHAVIORAL = "behavioral"
    PROJECT = "project"
    PYTHON = "python"
    AI_ML = "ai_ml"
    GENAI = "genai"
    RAG = "rag"
    SQL = "sql"
    SYSTEM_DESIGN = "system_design"


class InterviewStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class SkillLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# ── Users ─────────────────────────────────────────────────────────────────────

class User(Base):
    """Core authentication table."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    profile: Mapped[Optional["UserProfile"]] = relationship("UserProfile", back_populates="user", uselist=False)
    resumes: Mapped[List["Resume"]] = relationship("Resume", back_populates="user")
    job_descriptions: Mapped[List["JobDescription"]] = relationship("JobDescription", back_populates="user")
    roadmaps: Mapped[List["Roadmap"]] = relationship("Roadmap", back_populates="user")
    interviews: Mapped[List["Interview"]] = relationship("Interview", back_populates="user")
    conversations: Mapped[List["Conversation"]] = relationship("Conversation", back_populates="user")


class UserProfile(Base):
    """Extended user profile: career goals, experience level, target role."""
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    target_role: Mapped[Optional[str]] = mapped_column(String(255))
    experience_level: Mapped[Optional[str]] = mapped_column(String(50))  # fresher, junior, mid, senior
    career_goal: Mapped[Optional[str]] = mapped_column(Text)
    available_hours_per_week: Mapped[Optional[int]] = mapped_column(Integer, default=10)
    current_skills: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500))
    github_url: Mapped[Optional[str]] = mapped_column(String(500))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user: Mapped["User"] = relationship("User", back_populates="profile")


# ── Resumes ───────────────────────────────────────────────────────────────────

class Resume(Base):
    """Uploaded resume + all extracted data."""
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    filename: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    file_type: Mapped[str] = mapped_column(String(10))  # pdf, docx, txt
    raw_text: Mapped[Optional[str]] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # latest resume flag

    # Extracted fields
    extracted_name: Mapped[Optional[str]] = mapped_column(String(255))
    extracted_email: Mapped[Optional[str]] = mapped_column(String(255))
    extracted_phone: Mapped[Optional[str]] = mapped_column(String(50))
    extracted_skills: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    extracted_education: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    extracted_experience: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    extracted_projects: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    extracted_certifications: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    extracted_summary: Mapped[Optional[str]] = mapped_column(Text)
    years_of_experience: Mapped[Optional[float]] = mapped_column(Float)

    # AI analysis
    ai_analysis: Mapped[Optional[str]] = mapped_column(Text)
    analysis_status: Mapped[str] = mapped_column(String(20), default="pending")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user: Mapped["User"] = relationship("User", back_populates="resumes")
    skill_gaps: Mapped[List["SkillGap"]] = relationship("SkillGap", back_populates="resume")


# ── Job Descriptions ──────────────────────────────────────────────────────────

class JobDescription(Base):
    """Job descriptions entered/uploaded by the user."""
    __tablename__ = "job_descriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[Optional[str]] = mapped_column(String(255))
    company: Mapped[Optional[str]] = mapped_column(String(255))
    raw_text: Mapped[str] = mapped_column(Text)

    # Extracted fields
    extracted_title: Mapped[Optional[str]] = mapped_column(String(255))
    extracted_required_skills: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    extracted_preferred_skills: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    extracted_technologies: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    extracted_responsibilities: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    extracted_experience_required: Mapped[Optional[str]] = mapped_column(String(100))
    extracted_education_required: Mapped[Optional[str]] = mapped_column(String(255))
    extracted_domain: Mapped[Optional[str]] = mapped_column(String(100))
    extracted_role_type: Mapped[Optional[str]] = mapped_column(String(100))

    ai_analysis: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship("User", back_populates="job_descriptions")
    skill_gaps: Mapped[List["SkillGap"]] = relationship("SkillGap", back_populates="job_description")


# ── Skill Gap Analysis ────────────────────────────────────────────────────────

class SkillGap(Base):
    """Result of comparing a Resume against a Job Description."""
    __tablename__ = "skill_gaps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    resume_id: Mapped[int] = mapped_column(Integer, ForeignKey("resumes.id", ondelete="CASCADE"))
    job_description_id: Mapped[int] = mapped_column(Integer, ForeignKey("job_descriptions.id", ondelete="CASCADE"))

    matched_skills: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    missing_skills: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    partial_skills: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    match_score: Mapped[Optional[float]] = mapped_column(Float)  # 0-100, clearly labeled as approximation

    ai_explanation: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    resume: Mapped["Resume"] = relationship("Resume", back_populates="skill_gaps")
    job_description: Mapped["JobDescription"] = relationship("JobDescription", back_populates="skill_gaps")
    roadmaps: Mapped[List["Roadmap"]] = relationship("Roadmap", back_populates="skill_gap")


# ── Roadmap ───────────────────────────────────────────────────────────────────

class Roadmap(Base):
    """Personalized learning roadmap for a user."""
    __tablename__ = "roadmaps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    skill_gap_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("skill_gaps.id"))
    title: Mapped[str] = mapped_column(String(255))
    duration_days: Mapped[int] = mapped_column(Integer, default=30)  # 30, 60, 90
    total_tasks: Mapped[int] = mapped_column(Integer, default=0)
    completed_tasks: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user: Mapped["User"] = relationship("User", back_populates="roadmaps")
    skill_gap: Mapped[Optional["SkillGap"]] = relationship("SkillGap", back_populates="roadmaps")
    tasks: Mapped[List["RoadmapTask"]] = relationship("RoadmapTask", back_populates="roadmap", cascade="all, delete-orphan")


class RoadmapTask(Base):
    """Individual task within a learning roadmap."""
    __tablename__ = "roadmap_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    roadmap_id: Mapped[int] = mapped_column(Integer, ForeignKey("roadmaps.id", ondelete="CASCADE"))
    week_number: Mapped[int] = mapped_column(Integer)
    day_start: Mapped[Optional[int]] = mapped_column(Integer)
    day_end: Mapped[Optional[int]] = mapped_column(Integer)
    skill: Mapped[str] = mapped_column(String(255))
    topic: Mapped[str] = mapped_column(String(255))
    task_description: Mapped[str] = mapped_column(Text)
    practice_task: Mapped[Optional[str]] = mapped_column(Text)
    project_suggestion: Mapped[Optional[str]] = mapped_column(Text)
    resource_url: Mapped[Optional[str]] = mapped_column(String(500))
    resource_name: Mapped[Optional[str]] = mapped_column(String(255))
    estimated_hours: Mapped[Optional[float]] = mapped_column(Float)
    difficulty: Mapped[Optional[str]] = mapped_column(String(20))  # easy, medium, hard
    status: Mapped[TaskStatus] = mapped_column(SAEnum(TaskStatus), default=TaskStatus.PENDING)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    roadmap: Mapped["Roadmap"] = relationship("Roadmap", back_populates="tasks")


# ── Projects ──────────────────────────────────────────────────────────────────

class ProjectRecommendation(Base):
    """AI-recommended projects based on skill gaps."""
    __tablename__ = "project_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    skill_gap_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("skill_gaps.id"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    skills_covered: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    difficulty: Mapped[Optional[str]] = mapped_column(String(20))
    estimated_days: Mapped[Optional[int]] = mapped_column(Integer)
    technologies: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    expected_outcome: Mapped[Optional[str]] = mapped_column(Text)
    features: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    is_saved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


# ── Interviews ────────────────────────────────────────────────────────────────

class Interview(Base):
    """A mock interview session."""
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    resume_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("resumes.id"))
    job_description_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("job_descriptions.id"))
    interview_type: Mapped[InterviewType] = mapped_column(SAEnum(InterviewType))
    target_role: Mapped[Optional[str]] = mapped_column(String(255))
    difficulty: Mapped[str] = mapped_column(String(20), default="intermediate")
    status: Mapped[InterviewStatus] = mapped_column(SAEnum(InterviewStatus), default=InterviewStatus.IN_PROGRESS)
    total_questions: Mapped[int] = mapped_column(Integer, default=0)
    answered_questions: Mapped[int] = mapped_column(Integer, default=0)
    overall_score: Mapped[Optional[float]] = mapped_column(Float)  # AI-generated practice signal
    weak_topics: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    strong_topics: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    summary_feedback: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship("User", back_populates="interviews")
    questions: Mapped[List["InterviewQuestion"]] = relationship("InterviewQuestion", back_populates="interview", cascade="all, delete-orphan")


class InterviewQuestion(Base):
    """Individual question within an interview session."""
    __tablename__ = "interview_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    interview_id: Mapped[int] = mapped_column(Integer, ForeignKey("interviews.id", ondelete="CASCADE"))
    question_text: Mapped[str] = mapped_column(Text)
    question_type: Mapped[Optional[str]] = mapped_column(String(50))  # conceptual, practical, behavioral
    topic: Mapped[Optional[str]] = mapped_column(String(255))
    skill: Mapped[Optional[str]] = mapped_column(String(255))
    difficulty: Mapped[Optional[str]] = mapped_column(String(20))
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    is_followup: Mapped[bool] = mapped_column(Boolean, default=False)
    followup_reason: Mapped[Optional[str]] = mapped_column(Text)  # why was this followup asked
    rag_sources: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    interview: Mapped["Interview"] = relationship("Interview", back_populates="questions")
    answer: Mapped[Optional["InterviewAnswer"]] = relationship("InterviewAnswer", back_populates="question", uselist=False)


class InterviewAnswer(Base):
    """User's answer to an interview question + AI feedback."""
    __tablename__ = "interview_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("interview_questions.id", ondelete="CASCADE"))
    interview_id: Mapped[int] = mapped_column(Integer, ForeignKey("interviews.id", ondelete="CASCADE"))
    answer_text: Mapped[str] = mapped_column(Text)
    ai_score: Mapped[Optional[float]] = mapped_column(Float)  # 0-10, practice signal only
    what_was_correct: Mapped[Optional[str]] = mapped_column(Text)
    what_was_missing: Mapped[Optional[str]] = mapped_column(Text)
    incorrect_concepts: Mapped[Optional[str]] = mapped_column(Text)
    better_answer: Mapped[Optional[str]] = mapped_column(Text)
    concepts_to_study: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    rag_sources: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    detected_weakness: Mapped[Optional[str]] = mapped_column(String(255))  # for adaptive follow-up
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    question: Mapped["InterviewQuestion"] = relationship("InterviewQuestion", back_populates="answer")


# ── Conversations (RAG Chat) ──────────────────────────────────────────────────

class Conversation(Base):
    """A career assistant chat session."""
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[Optional[str]] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user: Mapped["User"] = relationship("User", back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Individual message in a conversation."""
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"))
    role: Mapped[MessageRole] = mapped_column(SAEnum(MessageRole))
    content: Mapped[str] = mapped_column(Text)
    rag_sources: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")


# ── Knowledge Base Documents ──────────────────────────────────────────────────

class Document(Base):
    """A document ingested into the knowledge base."""
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    source: Mapped[Optional[str]] = mapped_column(String(500))
    document_type: Mapped[Optional[str]] = mapped_column(String(50))
    role: Mapped[Optional[str]] = mapped_column(String(100))
    technology: Mapped[Optional[str]] = mapped_column(String(100))
    skill: Mapped[Optional[str]] = mapped_column(String(100))
    topic: Mapped[Optional[str]] = mapped_column(String(100))
    difficulty: Mapped[Optional[str]] = mapped_column(String(20))
    raw_content: Mapped[Optional[str]] = mapped_column(Text)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    is_indexed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    chunks: Mapped[List["DocumentChunk"]] = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    """A text chunk from a document, ready for embedding."""
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(Integer, ForeignKey("documents.id", ondelete="CASCADE"))
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    faiss_index_id: Mapped[Optional[int]] = mapped_column(Integer)  # index in FAISS
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    document: Mapped["Document"] = relationship("Document", back_populates="chunks")


# ── Progress ──────────────────────────────────────────────────────────────────

class Progress(Base):
    """Tracks overall learning and interview progress for a user."""
    __tablename__ = "progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    total_roadmap_tasks: Mapped[int] = mapped_column(Integer, default=0)
    completed_roadmap_tasks: Mapped[int] = mapped_column(Integer, default=0)
    total_interviews: Mapped[int] = mapped_column(Integer, default=0)
    completed_interviews: Mapped[int] = mapped_column(Integer, default=0)
    average_interview_score: Mapped[Optional[float]] = mapped_column(Float)
    skills_learned: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    weak_areas: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    strong_areas: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    last_activity: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
