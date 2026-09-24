"""
CareerPilot AI — FastAPI Application Entry Point
==================================================
Initializes FastAPI, registers middleware (CORS, error handling),
includes all API routers, and configures lifespan events.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.database.init_db import init_db
from app.api.auth import router as auth_router
from app.api.routes import (
    resume_router, jobs_router, skills_router, roadmap_router,
    projects_router, interview_router, rag_router, career_router, progress_router
)

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - [%(levelname)s] - %(name)s: %(message)s"
)
logger = logging.getLogger("careerpilot-ai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: database initialization and teardown."""
    logger.info("Initializing database schema...")
    try:
        await init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.warning(f"Could not connect to PostgreSQL ({e}). Operating in memory/mock DB mode.")
    yield
    logger.info("Shutting down CareerPilot AI backend...")


app = FastAPI(lifespan=lifespan)

# ── CORS Middleware ───────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global Exception Handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error processing {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again or check server logs."}
    )


# ── Register Routers ──────────────────────────────────────────────────────────
api_prefix = "/api"
app.include_router(auth_router, prefix=api_prefix)
app.include_router(resume_router, prefix=api_prefix)
app.include_router(jobs_router, prefix=api_prefix)
app.include_router(skills_router, prefix=api_prefix)
app.include_router(roadmap_router, prefix=api_prefix)
app.include_router(projects_router, prefix=api_prefix)
app.include_router(interview_router, prefix=api_prefix)
app.include_router(rag_router, prefix=api_prefix)
app.include_router(career_router, prefix=api_prefix)
app.include_router(progress_router, prefix=api_prefix)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }
