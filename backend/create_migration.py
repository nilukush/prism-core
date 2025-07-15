#!/usr/bin/env python3
"""
Script to create initial Alembic migration for PRISM.
This ensures all models are properly imported before generating migration.
"""

import sys
import os
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import all models to ensure they're registered
from backend.src.models.base import Base
from backend.src.models.user import User
from backend.src.models.organization import Organization  
from backend.src.models.project import Project
from backend.src.models.story import Story
from backend.src.models.document import Document
from backend.src.models.integration import Integration
from backend.src.models.analytics import AnalyticsEvent
from backend.src.models.ai_context import AIContext

# Import Alembic
from alembic.config import Config
from alembic import command

def create_migration():
    """Create initial migration."""
    # Get alembic config
    alembic_cfg = Config(str(backend_dir / "alembic.ini"))
    
    # Create revision
    command.revision(
        alembic_cfg,
        autogenerate=True,
        message="Initial schema with all models"
    )
    
    print("✅ Migration created successfully!")
    print("Run 'docker-compose exec backend alembic upgrade head' to apply it.")

if __name__ == "__main__":
    create_migration()