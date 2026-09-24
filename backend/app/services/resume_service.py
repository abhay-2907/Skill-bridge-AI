"""
CareerPilot AI — Resume Service
==================================
Business logic for resume upload, parsing, extraction, and AI analysis.
"""

import os
import uuid
import logging
from pathlib import Path
from typing import Optional

from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import Resume, User
from app.parsers.pdf_parser import pdf_parser
from app.parsers.docx_parser import docx_parser, text_parser
from app.nlp.extractor import resume_extractor
from app.nlp.normalizer import skill_normalizer
from app.ai.prompts import prompt_templates
from app.rag.pipeline import rag_pipeline
from app.core.config import settings

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("uploads/resumes")
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
MAX_FILE_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024  # bytes


class ResumeService:

    async def upload_and_analyze(
        self, file: UploadFile, user: User, db: AsyncSession
    ) -> Resume:
        """
        Full pipeline:
        1. Validate file (type + size)
        2. Save to disk
        3. Parse text
        4. Extract structured data
        5. Normalize skills
        6. Generate AI analysis
        7. Save to DB
        """
        # Step 1: Validate
        ext = self._get_extension(file.filename)
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '{ext}' not allowed. Supported: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB}MB"
            )

        # Step 2: Save file
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        safe_filename = f"{user.id}_{uuid.uuid4().hex}.{ext}"
        file_path = UPLOAD_DIR / safe_filename

        with open(file_path, "wb") as f:
            f.write(content)

        # Step 3: Parse text
        raw_text = self._parse_text(content, ext)
        if not raw_text or len(raw_text.strip()) < 50:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not extract text from this file. If it's a scanned PDF, please use a text-based PDF."
            )

        # Step 4: Extract structured data
        extracted = resume_extractor.extract_all(raw_text)

        # Step 5: Normalize skills
        normalized_skills = skill_normalizer.normalize_list(extracted.get("skills", []))

        # Mark previous resumes as inactive
        await db.execute(
            Resume.__table__.update()
            .where(Resume.user_id == user.id)
            .values(is_active=False)
        )

        # Step 6: Save to DB
        resume = Resume(
            user_id=user.id,
            filename=file.filename,
            file_path=str(file_path),
            file_type=ext,
            raw_text=raw_text,
            is_active=True,
            extracted_name=extracted.get("name"),
            extracted_email=extracted.get("email"),
            extracted_phone=extracted.get("phone"),
            extracted_skills=normalized_skills,
            extracted_education=extracted.get("education", []),
            extracted_experience=extracted.get("experience", []),
            extracted_projects=extracted.get("projects", []),
            extracted_certifications=extracted.get("certifications", []),
            extracted_summary=extracted.get("summary"),
            years_of_experience=extracted.get("years_of_experience"),
            analysis_status="analyzing",
        )
        db.add(resume)
        await db.flush()  # Get the ID

        # Step 7: Generate AI analysis (async, non-blocking)
        try:
            ai_analysis = await self._generate_ai_analysis(raw_text, extracted)
            resume.ai_analysis = ai_analysis
            resume.analysis_status = "completed"
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            resume.analysis_status = "failed"

        await db.commit()
        await db.refresh(resume)
        return resume

    def _parse_text(self, content: bytes, ext: str) -> str:
        """Route to correct parser based on file extension."""
        if ext == "pdf":
            return pdf_parser.parse_bytes(content)
        elif ext == "docx":
            return docx_parser.parse_bytes(content)
        else:  # txt
            return text_parser.parse_bytes(content)

    def _get_extension(self, filename: str) -> str:
        """Extract and validate file extension."""
        if not filename or "." not in filename:
            return ""
        return filename.rsplit(".", 1)[-1].lower()

    async def _generate_ai_analysis(self, raw_text: str, extracted: dict) -> str:
        """Generate AI-powered resume analysis using IBM Granite."""
        prompt = prompt_templates.resume_analysis(raw_text, extracted)
        return await rag_pipeline.simple_generate(prompt, max_tokens=600, temperature=0.4)

    async def get_resume(self, resume_id: int, user_id: int, db: AsyncSession) -> Optional[Resume]:
        """Fetch a resume by ID, ensuring ownership."""
        result = await db.execute(
            select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_active_resume(self, user_id: int, db: AsyncSession) -> Optional[Resume]:
        """Get the user's most recent active resume."""
        result = await db.execute(
            select(Resume)
            .where(Resume.user_id == user_id, Resume.is_active == True)
            .order_by(Resume.created_at.desc())
        )
        return result.scalar_one_or_none()


resume_service = ResumeService()
