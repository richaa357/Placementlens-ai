"""Database models.

Provenance is a first class concern: every fact that the dashboard renders is
attached to a `Source` and carries a `data_type` so the UI can distinguish
verified historical data from current postings, demo data and AI analysis.
"""
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class DataType(str, enum.Enum):
    """Where a piece of information came from.

    The frontend colour-codes every card and table row by this value.
    """

    VERIFIED_HISTORICAL = "verified_historical"
    CURRENT_POSTING = "current_posting"
    AI_ANALYSIS = "ai_analysis"
    USER_PROVIDED = "user_provided"
    DEMO_DATA = "demo_data"


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    published_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    data_type: Mapped[DataType] = mapped_column(Enum(DataType))
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True)
    company: Mapped["Company | None"] = relationship(back_populates="sources")


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    industry: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    headquarters: Mapped[str | None] = mapped_column(String(200), nullable=True)
    locations: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-encoded list
    aliases: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-encoded list
    technology_areas: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-encoded list
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)

    sources: Mapped[list[Source]] = relationship(back_populates="company", cascade="all, delete-orphan")
    postings: Mapped[list["JobPosting"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )
    records: Mapped[list["PlacementRecord"]] = relationship(
        back_populates="company", cascade="all, delete-orphan"
    )


class JobPosting(Base):
    """An internship / entry level job description used by the NLP pipeline."""

    __tablename__ = "job_postings"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    role_family: Mapped[str | None] = mapped_column(String(120), nullable=True)
    employment_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    posted_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    data_type: Mapped[DataType] = mapped_column(Enum(DataType), default=DataType.CURRENT_POSTING)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), nullable=True)

    company: Mapped[Company] = relationship(back_populates="postings")
    source: Mapped[Source | None] = relationship()


class PlacementRecord(Base):
    """A historical hiring / campus recruitment record.

    Numeric fields are nullable on purpose: a record may legitimately exist
    without a verified headcount or stipend, in which case the API returns
    `null` and the UI renders "No verified public data available." rather than
    an invented number.
    """

    __tablename__ = "placement_records"
    __table_args__ = (UniqueConstraint("company_id", "year", "role", name="uq_record"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    role: Mapped[str] = mapped_column(String(200))
    opening_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    offers_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stipend_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    stipend_currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    stipend_period: Mapped[str | None] = mapped_column(String(20), nullable=True)
    drive_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    skills_requested: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    data_type: Mapped[DataType] = mapped_column(Enum(DataType), default=DataType.VERIFIED_HISTORICAL)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), nullable=True)

    company: Mapped[Company] = relationship(back_populates="records")
    source: Mapped[Source | None] = relationship()


class SearchQuery(Base):
    """Simple analytics table: which company names users searched for."""

    __tablename__ = "search_queries"

    id: Mapped[int] = mapped_column(primary_key=True)
    query: Mapped[str] = mapped_column(String(200), index=True)
    matched_company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
