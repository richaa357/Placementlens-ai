"""Pydantic response/request models (the public API contract)."""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.models import DataType

NO_DATA_MESSAGE = "No verified public data available."
INSUFFICIENT_DATA_MESSAGE = "Insufficient verified data"


class SourceOut(BaseModel):
    id: int
    name: str
    url: str | None = None
    published_date: str | None = None
    data_type: DataType
    is_demo: bool
    notes: str | None = None


class CompanySummary(BaseModel):
    id: int
    name: str
    slug: str
    industry: str | None = None
    headquarters: str | None = None
    is_demo: bool


class SearchResponse(BaseModel):
    query: str
    match: CompanySummary | None = None
    match_type: str = Field(description="exact | alias | fuzzy | none")
    suggestions: list[CompanySummary] = []
    message: str | None = None


class CompanyOverview(BaseModel):
    id: int
    name: str
    slug: str
    industry: str | None
    description: str | None
    website: str | None
    headquarters: str | None
    locations: list[str]
    technology_areas: list[str]
    typical_roles: list[str]
    required_skills: list[str]
    is_demo: bool
    data_type: DataType
    notes: str | None = None


class JobPostingOut(BaseModel):
    id: int
    title: str
    role_family: str | None
    employment_type: str | None
    location: str | None
    posted_date: str | None
    description: str
    data_type: DataType
    is_demo: bool
    source: SourceOut | None = None


class PlacementRecordOut(BaseModel):
    id: int
    year: int
    role: str
    opening_type: str | None
    offers_count: int | None
    offers_count_display: str
    stipend_display: str
    drive_date: str | None
    drive_date_display: str
    skills_requested: list[str]
    data_type: DataType
    is_demo: bool
    source: SourceOut | None = None


class YearlyPoint(BaseModel):
    year: int
    records: int
    offers_count: int | None
    offers_count_display: str


class HistoricalAnalysis(BaseModel):
    has_data: bool
    message: str | None = None
    records: list[PlacementRecordOut] = []
    by_year: list[YearlyPoint] = []
    roles: list[dict] = []
    hiring_frequency: dict = {}
    stipend_observations: list[dict] = []
    data_type: DataType = DataType.VERIFIED_HISTORICAL
    contains_demo_data: bool = False


class SkillStatOut(BaseModel):
    skill: str
    category: str
    document_count: int
    mention_count: int
    frequency: float


class SkillAnalysis(BaseModel):
    has_data: bool
    message: str | None = None
    analysed_document_count: int = 0
    skills: list[SkillStatOut] = []
    by_category: dict[str, list[SkillStatOut]] = {}
    heatmap: dict = {}
    data_type: DataType = DataType.AI_ANALYSIS


class AIAnalysis(BaseModel):
    has_data: bool
    message: str | None = None
    method: dict = {}
    keywords: list[dict] = []
    emerging_skills: list[dict] = []
    role_distribution: list[dict] = []
    data_type: DataType = DataType.AI_ANALYSIS


class SkillAlignmentRequest(BaseModel):
    skills: list[str] = Field(default_factory=list, description="Free-text skills provided by the user")


class SkillAlignmentResponse(BaseModel):
    has_data: bool
    message: str | None = None
    disclaimer: str = (
        "Skill Alignment Analysis compares the skills you entered with the skills found in the "
        "analysed job descriptions and historical records. It is not a prediction of selection."
    )
    company: CompanySummary | None = None
    skills_i_have: list[dict] = []
    skills_frequently_requested: list[dict] = []
    skills_to_learn: list[dict] = []
    skills_not_recognised: list[str] = []
    additional_skills: list[str] = []
    coverage: float = 0.0
    tfidf_similarity: float = 0.0
    semantic_similarity: float = 0.0
    semantic_backend: str = "none"
    per_document_similarity: list[dict] = []
    user_input_data_type: DataType = DataType.USER_PROVIDED
    analysis_data_type: DataType = DataType.AI_ANALYSIS


class PreparationArea(BaseModel):
    area: str
    priority_score: float
    topics: list[dict]


class CompanyAnalysisResponse(BaseModel):
    overview: CompanyOverview
    historical: HistoricalAnalysis
    skill_analysis: SkillAnalysis
    ai_analysis: AIAnalysis
    preparation_areas: list[PreparationArea]
    sources: list[SourceOut]
    data_quality: dict
