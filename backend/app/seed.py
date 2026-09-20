"""Load a dataset JSON file into the database.

The bundled dataset (app/data/demo_dataset.json) is a DEMONSTRATION dataset:
every placement record it contains is flagged `is_demo=True` so the API and the
UI can label it. Point `DATASET_PATH` at your own export (same JSON shape) to
analyse real placement-cell data.
"""
from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal, engine
from app.models import Base, Company, DataType, JobPosting, PlacementRecord, Source


def _slugify(value: str) -> str:
    return "-".join("".join(ch.lower() if ch.isalnum() else " " for ch in value).split())


def load_dataset(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def seed_database(db: Session, dataset: dict, *, dataset_is_demo: bool = True) -> int:
    """Insert every company from `dataset`. Existing companies are skipped."""
    inserted = 0
    demo_flag = bool(dataset.get("is_demo", dataset_is_demo))
    for entry in dataset.get("companies", []):
        name = entry["name"]
        if db.query(Company).filter(Company.name == name).first():
            continue
        company = Company(
            name=name,
            slug=entry.get("slug") or _slugify(name),
            industry=entry.get("industry"),
            description=entry.get("description"),
            website=entry.get("website"),
            headquarters=entry.get("headquarters"),
            locations=json.dumps(entry.get("locations", [])),
            technology_areas=json.dumps(entry.get("technology_areas", [])),
            aliases=json.dumps(entry.get("aliases", [])),
            is_demo=demo_flag,
        )
        db.add(company)
        db.flush()

        overview_source = None
        raw_source = entry.get("overview_source")
        if raw_source:
            overview_source = Source(
                name=raw_source["name"],
                url=raw_source.get("url"),
                published_date=raw_source.get("published_date"),
                data_type=DataType(raw_source.get("data_type", "verified_historical")),
                is_demo=bool(raw_source.get("is_demo", False)),
                notes=raw_source.get("notes"),
                company_id=company.id,
            )
            db.add(overview_source)
            db.flush()

        posting_source = Source(
            name=f"{name} - job description corpus ({'demonstration data' if demo_flag else 'imported dataset'})",
            url=entry.get("website"),
            published_date=None,
            data_type=DataType.DEMO_DATA if demo_flag else DataType.CURRENT_POSTING,
            is_demo=demo_flag,
            notes=dataset.get("disclaimer"),
            company_id=company.id,
        )
        record_source = Source(
            name=f"{name} - historical placement records ({'demonstration data' if demo_flag else 'imported dataset'})",
            url=None,
            published_date=None,
            data_type=DataType.DEMO_DATA if demo_flag else DataType.VERIFIED_HISTORICAL,
            is_demo=demo_flag,
            notes=dataset.get("disclaimer"),
            company_id=company.id,
        )
        db.add_all([posting_source, record_source])
        db.flush()

        for posting in entry.get("job_postings", []):
            db.add(
                JobPosting(
                    company_id=company.id,
                    title=posting["title"],
                    role_family=posting.get("role_family"),
                    employment_type=posting.get("employment_type"),
                    location=posting.get("location"),
                    posted_date=posting.get("posted_date"),
                    description=posting["description"],
                    data_type=DataType.DEMO_DATA if demo_flag else DataType.CURRENT_POSTING,
                    is_demo=demo_flag,
                    source_id=posting_source.id,
                )
            )
        for record in entry.get("placement_records", []):
            db.add(
                PlacementRecord(
                    company_id=company.id,
                    year=record["year"],
                    role=record["role"],
                    opening_type=record.get("opening_type"),
                    offers_count=record.get("offers_count"),
                    stipend_amount=record.get("stipend_amount"),
                    stipend_currency=record.get("stipend_currency"),
                    stipend_period=record.get("stipend_period"),
                    drive_date=record.get("drive_date"),
                    skills_requested=json.dumps(record.get("skills_requested", [])),
                    data_type=DataType.DEMO_DATA if demo_flag else DataType.VERIFIED_HISTORICAL,
                    is_demo=demo_flag,
                    source_id=record_source.id,
                )
            )
        inserted += 1
    db.commit()
    return inserted


def init_db() -> None:
    """Create tables and seed the configured dataset when the DB is empty."""
    settings = get_settings()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Company).count() == 0:
            dataset = load_dataset(settings.dataset_path)
            seed_database(db, dataset, dataset_is_demo=settings.dataset_is_demo)
    finally:
        db.close()


if __name__ == "__main__":  # pragma: no cover - manual utility
    init_db()
    print("Database initialised at", get_settings().database_url)
