"""PlacementLens AI - FastAPI application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import companies, meta
from app.seed import init_db

settings = get_settings()

DESCRIPTION = """
Research companies and understand their placement opportunities using historical
data and AI.

Every response labels its `data_type`:

* `verified_historical` - sourced historical record
* `current_posting` - current job-posting information
* `ai_analysis` - derived by the NLP/ML pipeline from the documents listed under Sources
* `user_provided` - entered by the user
* `demo_data` - clearly labelled demonstration data shipped with the project

When a value cannot be verified the API returns
`"No verified public data available."` or `"Insufficient verified data"` rather
than an estimated number.
"""


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description=DESCRIPTION,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meta.router)
app.include_router(companies.router)


@app.get("/", tags=["meta"])
def root() -> dict:
    return {"app": settings.app_name, "docs": "/docs", "health": "/api/health"}
