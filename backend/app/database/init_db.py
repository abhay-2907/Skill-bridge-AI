"""
CareerPilot AI — Database Initialization
==========================================
Creates all tables from SQLAlchemy models.
Run this once on startup or via: python -m app.database.init_db
"""

import asyncio
from app.database.session import engine, Base

# Import all models so Base knows about them before creating tables
from app.models import models  # noqa: F401


async def init_db():
    """Drop and recreate all tables (development only) or create if not exists."""
    async with engine.begin() as conn:
        # Creates tables that don't exist yet; leaves existing ones alone
        await conn.run_sync(Base.metadata.create_all)
    print("[INFO] Database tables created successfully.")


if __name__ == "__main__":
    asyncio.run(init_db())
