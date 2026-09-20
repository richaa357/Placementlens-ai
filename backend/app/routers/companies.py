"""Company search, overview and analysis endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Company, JobPosting
from app.schemas import (
    NO_DATA_MESSAGE,
    CompanyAnalysisResponse,
    CompanySummary,
    JobPostingOut,
    SearchResponse,
    SkillAlignmentRequest,
    SkillAlignmentResponse,
)
from app.services import analysis_service, company_service

router = APIRouter(prefix="/api/companies", tags=["companies"])


def _get_company_or_404(db: Session, slug: str) -> Company:
    company = db.query(Company).filter(Company.slug == slug).first()
    if company is None:
        raise HTTPException(status_code=404, detail=NO_DATA_MESSAGE)
    return company


@router.get("", response_model=list[CompanySummary])
def list_companies(db: Session = Depends(get_db)) -> list[CompanySummary]:
    companies = db.query(Company).order_by(Company.name).all()
    return [analysis_service.company_summary(company) for company in companies]


@router.get("/search", response_model=SearchResponse)
def search_company(
    q: str = Query(..., min_length=1, description="Company name entered by the user"),
    db: Session = Depends(get_db),
) -> SearchResponse:
    company, match_type, suggestions = company_service.find_company(db, q)
    company_service.record_search(db, q, company)
    return SearchResponse(
        query=q,
        match=analysis_service.company_summary(company) if company else None,
        match_type=match_type,
        suggestions=[analysis_service.company_summary(item) for item in suggestions],
        message=None if company else NO_DATA_MESSAGE,
    )


@router.get("/{slug}/analysis", response_model=CompanyAnalysisResponse)
def company_analysis(slug: str, db: Session = Depends(get_db)) -> CompanyAnalysisResponse:
    company = _get_company_or_404(db, slug)
    return analysis_service.build_company_analysis(db, company)


@router.get("/{slug}/postings", response_model=list[JobPostingOut])
def company_postings(slug: str, db: Session = Depends(get_db)) -> list[JobPostingOut]:
    company = _get_company_or_404(db, slug)
    postings = db.query(JobPosting).filter(JobPosting.company_id == company.id).all()
    return analysis_service.build_postings_out(postings)


@router.post("/{slug}/skill-alignment", response_model=SkillAlignmentResponse)
def skill_alignment(
    slug: str, payload: SkillAlignmentRequest, db: Session = Depends(get_db)
) -> SkillAlignmentResponse:
    """Skill Alignment Analysis - overlap and gaps, never a selection prediction."""
    company = _get_company_or_404(db, slug)
    skills = [skill for raw in payload.skills for skill in raw.split(",")]
    return analysis_service.build_alignment(db, company, [s.strip() for s in skills if s.strip()])
