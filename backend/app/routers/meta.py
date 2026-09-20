"""Health and taxonomy endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Company, JobPosting, PlacementRecord
from app.nlp.preprocessing import active_backend
from app.nlp.skills_taxonomy import CATEGORIES, SKILLS

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "nlp_backend": active_backend(),
        "sentence_transformers_enabled": settings.enable_sentence_transformers,
        "dataset_is_demo": settings.dataset_is_demo,
        "counts": {
            "companies": db.query(Company).count(),
            "job_postings": db.query(JobPosting).count(),
            "placement_records": db.query(PlacementRecord).count(),
        },
    }


@router.get("/skills/taxonomy")
def taxonomy() -> dict:
    return {
        "categories": CATEGORIES,
        "skills": [
            {"name": skill.name, "category": skill.category, "aliases": list(skill.aliases)}
            for skill in SKILLS
        ],
    }
