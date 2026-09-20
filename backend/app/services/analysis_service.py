"""Assembles the dashboard payload for a company.

Rule enforced throughout this module: if the underlying data is missing we emit
`NO_DATA_MESSAGE` / `INSUFFICIENT_DATA_MESSAGE` instead of deriving a number.
Aggregates (e.g. offers per year) are only produced from records that actually
carry a value, and the count of records lacking a value is reported alongside.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict

from sqlalchemy.orm import Session

from app.models import Company, DataType, JobPosting, PlacementRecord, Source
from app.nlp.pipeline import (
    AnalysisResult,
    Document,
    analyze_alignment,
    analyze_documents,
    preparation_areas,
)
from app.nlp.preprocessing import active_backend
from app.schemas import (
    INSUFFICIENT_DATA_MESSAGE,
    NO_DATA_MESSAGE,
    AIAnalysis,
    CompanyAnalysisResponse,
    CompanyOverview,
    CompanySummary,
    HistoricalAnalysis,
    JobPostingOut,
    PlacementRecordOut,
    PreparationArea,
    SkillAlignmentResponse,
    SkillAnalysis,
    SkillStatOut,
    SourceOut,
    YearlyPoint,
)

MIN_DOCUMENTS_FOR_ANALYSIS = 2


def _json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return [str(item) for item in parsed] if isinstance(parsed, list) else []


def _source_out(source: Source | None) -> SourceOut | None:
    if source is None:
        return None
    return SourceOut(
        id=source.id,
        name=source.name,
        url=source.url,
        published_date=source.published_date,
        data_type=source.data_type,
        is_demo=source.is_demo,
        notes=source.notes,
    )


def company_summary(company: Company) -> CompanySummary:
    return CompanySummary(
        id=company.id,
        name=company.name,
        slug=company.slug,
        industry=company.industry,
        headquarters=company.headquarters,
        is_demo=company.is_demo,
    )


def build_documents(postings: list[JobPosting], records: list[PlacementRecord]) -> list[Document]:
    """The corpus analysed by the NLP pipeline: job descriptions + skill lists."""
    documents: list[Document] = [
        Document(
            doc_id=posting.id,
            title=posting.title,
            text=posting.description,
            year=int(posting.posted_date[:4]) if posting.posted_date and posting.posted_date[:4].isdigit() else None,
            role_family=posting.role_family,
            origin="job_posting",
        )
        for posting in postings
    ]
    for record in records:
        skills = _json_list(record.skills_requested)
        if not skills:
            continue
        documents.append(
            Document(
                doc_id=100000 + record.id,
                title=f"{record.role} ({record.year})",
                text=", ".join(skills),
                year=record.year,
                role_family=record.role,
                origin="placement_record",
            )
        )
    return documents


def _stipend_display(record: PlacementRecord) -> str:
    if record.stipend_amount is None:
        return NO_DATA_MESSAGE
    currency = record.stipend_currency or ""
    period = f"/{record.stipend_period}" if record.stipend_period else ""
    return f"{currency} {record.stipend_amount:,.0f}{period}".strip()


def _record_out(record: PlacementRecord) -> PlacementRecordOut:
    return PlacementRecordOut(
        id=record.id,
        year=record.year,
        role=record.role,
        opening_type=record.opening_type,
        offers_count=record.offers_count,
        offers_count_display=str(record.offers_count) if record.offers_count is not None else NO_DATA_MESSAGE,
        stipend_display=_stipend_display(record),
        drive_date=record.drive_date,
        drive_date_display=record.drive_date or NO_DATA_MESSAGE,
        skills_requested=_json_list(record.skills_requested),
        data_type=record.data_type,
        is_demo=record.is_demo,
        source=_source_out(record.source),
    )


def build_historical(records: list[PlacementRecord]) -> HistoricalAnalysis:
    if not records:
        return HistoricalAnalysis(has_data=False, message=NO_DATA_MESSAGE)

    by_year: dict[int, list[PlacementRecord]] = defaultdict(list)
    for record in records:
        by_year[record.year].append(record)

    yearly: list[YearlyPoint] = []
    for year in sorted(by_year):
        counted = [r.offers_count for r in by_year[year] if r.offers_count is not None]
        total = sum(counted) if counted else None
        yearly.append(
            YearlyPoint(
                year=year,
                records=len(by_year[year]),
                offers_count=total,
                offers_count_display=str(total) if total is not None else NO_DATA_MESSAGE,
            )
        )

    role_counter: Counter = Counter(record.role for record in records)
    roles = [
        {
            "role": role,
            "record_count": count,
            "years": sorted({r.year for r in records if r.role == role}),
            "offers_count": (
                sum(r.offers_count for r in records if r.role == role and r.offers_count is not None)
                if any(r.offers_count is not None for r in records if r.role == role)
                else None
            ),
        }
        for role, count in role_counter.most_common()
    ]

    years = sorted(by_year)
    span = years[-1] - years[0] + 1 if years else 0
    frequency = {
        "years_with_records": len(years),
        "year_span": span,
        "first_year": years[0] if years else None,
        "last_year": years[-1] if years else None,
        "records_per_year": round(len(records) / len(years), 2) if years else None,
        "label": (
            f"Records found in {len(years)} of the last {span} year(s)"
            if years
            else INSUFFICIENT_DATA_MESSAGE
        ),
    }

    stipends = [
        {
            "year": record.year,
            "role": record.role,
            "display": _stipend_display(record),
            "amount": record.stipend_amount,
            "currency": record.stipend_currency,
            "period": record.stipend_period,
            "source": _source_out(record.source).model_dump() if record.source else None,
        }
        for record in sorted(records, key=lambda r: r.year, reverse=True)
        if record.stipend_amount is not None
    ]

    return HistoricalAnalysis(
        has_data=True,
        message=None if len(records) >= 2 else INSUFFICIENT_DATA_MESSAGE,
        records=[_record_out(record) for record in sorted(records, key=lambda r: (-r.year, r.role))],
        by_year=yearly,
        roles=roles,
        hiring_frequency=frequency,
        stipend_observations=stipends,
        data_type=records[0].data_type,
        contains_demo_data=any(record.is_demo for record in records),
    )


def _skill_out(stat) -> SkillStatOut:
    return SkillStatOut(
        skill=stat.skill,
        category=stat.category,
        document_count=stat.document_count,
        mention_count=stat.mention_count,
        frequency=stat.frequency,
    )


def build_skill_analysis(analysis: AnalysisResult) -> SkillAnalysis:
    if analysis.document_count < MIN_DOCUMENTS_FOR_ANALYSIS or not analysis.skills:
        return SkillAnalysis(
            has_data=False,
            message=INSUFFICIENT_DATA_MESSAGE,
            analysed_document_count=analysis.document_count,
        )
    return SkillAnalysis(
        has_data=True,
        analysed_document_count=analysis.document_count,
        skills=[_skill_out(stat) for stat in analysis.skills],
        by_category={
            category: [_skill_out(stat) for stat in stats]
            for category, stats in analysis.skills_by_category.items()
            if stats
        },
        heatmap=analysis.heatmap,
    )


def build_ai_analysis(analysis: AnalysisResult, semantic_backend: str) -> AIAnalysis:
    if analysis.document_count < MIN_DOCUMENTS_FOR_ANALYSIS:
        return AIAnalysis(has_data=False, message=INSUFFICIENT_DATA_MESSAGE)
    return AIAnalysis(
        has_data=True,
        method={
            "preprocessing_backend": active_backend(),
            "keyword_extraction": "TF-IDF (unigrams + bigrams, sublinear tf)",
            "semantic_model": semantic_backend,
            "similarity": "cosine similarity",
            "documents_analysed": analysis.document_count,
            "note": "Derived by analysing the job descriptions and historical skill lists listed under Sources.",
        },
        keywords=analysis.keywords,
        emerging_skills=analysis.emerging_skills,
        role_distribution=analysis.role_families,
    )


def build_overview(company: Company, analysis: AnalysisResult, postings: list[JobPosting]) -> CompanyOverview:
    roles = sorted({posting.role_family or posting.title for posting in postings})
    required = [stat.skill for stat in analysis.skills[:12]]
    return CompanyOverview(
        id=company.id,
        name=company.name,
        slug=company.slug,
        industry=company.industry,
        description=company.description,
        website=company.website,
        headquarters=company.headquarters,
        locations=_json_list(company.locations),
        technology_areas=_json_list(company.technology_areas),
        typical_roles=roles,
        required_skills=required,
        is_demo=company.is_demo,
        data_type=DataType.DEMO_DATA if company.is_demo else DataType.VERIFIED_HISTORICAL,
        notes=(
            "Overview fields come from the company's public information page; the roles and skills "
            "listed here are extracted from the analysed job descriptions."
        ),
    )


def build_company_analysis(db: Session, company: Company) -> CompanyAnalysisResponse:
    postings = db.query(JobPosting).filter(JobPosting.company_id == company.id).all()
    records = db.query(PlacementRecord).filter(PlacementRecord.company_id == company.id).all()
    sources = db.query(Source).filter(Source.company_id == company.id).all()

    documents = build_documents(postings, records)
    analysis = analyze_documents(documents)

    # The semantic model is only reported here; it is exercised on demand by the
    # skill-alignment endpoint where a user query actually needs embedding.
    from app.nlp.embeddings import SemanticModel

    semantic_backend = (
        SemanticModel([f"{doc.title}. {doc.text}" for doc in documents]).backend if documents else "none"
    )

    skill_analysis = build_skill_analysis(analysis)
    return CompanyAnalysisResponse(
        overview=build_overview(company, analysis, postings),
        historical=build_historical(records),
        skill_analysis=skill_analysis,
        ai_analysis=build_ai_analysis(analysis, semantic_backend),
        preparation_areas=[PreparationArea(**area) for area in preparation_areas(analysis)],
        sources=[s for s in (_source_out(source) for source in sources) if s is not None],
        data_quality={
            "job_postings": len(postings),
            "placement_records": len(records),
            "records_without_offer_count": sum(1 for r in records if r.offers_count is None),
            "records_without_stipend": sum(1 for r in records if r.stipend_amount is None),
            "records_without_drive_date": sum(1 for r in records if r.drive_date is None),
            "contains_demo_data": company.is_demo or any(r.is_demo for r in records) or any(p.is_demo for p in postings),
            "no_data_message": NO_DATA_MESSAGE,
            "insufficient_data_message": INSUFFICIENT_DATA_MESSAGE,
        },
    )


def build_alignment(db: Session, company: Company, skills: list[str]) -> SkillAlignmentResponse:
    postings = db.query(JobPosting).filter(JobPosting.company_id == company.id).all()
    records = db.query(PlacementRecord).filter(PlacementRecord.company_id == company.id).all()
    documents = build_documents(postings, records)
    analysis = analyze_documents(documents)

    if analysis.document_count < MIN_DOCUMENTS_FOR_ANALYSIS or not analysis.skills:
        return SkillAlignmentResponse(
            has_data=False,
            message=INSUFFICIENT_DATA_MESSAGE,
            company=company_summary(company),
        )

    alignment = analyze_alignment(documents, skills, analysis)
    frequently_requested = [
        {
            "skill": stat.skill,
            "category": stat.category,
            "frequency": stat.frequency,
            "document_count": stat.document_count,
            "user_has_it": stat.skill in alignment.user_skills,
        }
        for stat in analysis.skills[:15]
    ]
    return SkillAlignmentResponse(
        has_data=True,
        company=company_summary(company),
        skills_i_have=alignment.matched_skills,
        skills_frequently_requested=frequently_requested,
        skills_to_learn=alignment.missing_skills,
        skills_not_recognised=alignment.unmapped_user_input,
        additional_skills=alignment.extra_skills,
        coverage=alignment.coverage,
        tfidf_similarity=alignment.tfidf_similarity,
        semantic_similarity=alignment.semantic_similarity,
        semantic_backend=alignment.semantic_backend,
        per_document_similarity=alignment.per_document_similarity,
    )


def build_postings_out(postings: list[JobPosting]) -> list[JobPostingOut]:
    return [
        JobPostingOut(
            id=posting.id,
            title=posting.title,
            role_family=posting.role_family,
            employment_type=posting.employment_type,
            location=posting.location,
            posted_date=posting.posted_date,
            description=posting.description,
            data_type=posting.data_type,
            is_demo=posting.is_demo,
            source=_source_out(posting.source),
        )
        for posting in postings
    ]
