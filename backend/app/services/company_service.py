"""Company lookup: exact, alias and fuzzy matching on the user's search term."""
from __future__ import annotations

import difflib
import json

from sqlalchemy.orm import Session

from app.models import Company, SearchQuery


def _normalise(value: str) -> str:
    return " ".join(value.lower().replace("&", "and").split())


def _aliases(company: Company) -> list[str]:
    try:
        return json.loads(company.aliases or "[]")
    except json.JSONDecodeError:
        return []


def find_company(db: Session, query: str) -> tuple[Company | None, str, list[Company]]:
    """Return (company, match_type, suggestions).

    match_type is one of exact / alias / fuzzy / none. Fuzzy matching only
    accepts close matches (ratio >= 0.82) so that a typo resolves but an
    unknown company does not silently resolve to an unrelated one.
    """
    normalised = _normalise(query)
    if not normalised:
        return None, "none", []

    companies = db.query(Company).all()
    by_name = {_normalise(company.name): company for company in companies}
    if normalised in by_name:
        return by_name[normalised], "exact", []

    for company in companies:
        if normalised == _normalise(company.slug) or normalised in {_normalise(a) for a in _aliases(company)}:
            return company, "alias", []

    candidates: dict[str, Company] = dict(by_name)
    for company in companies:
        for alias in _aliases(company):
            candidates[_normalise(alias)] = company

    close = difflib.get_close_matches(normalised, list(candidates), n=1, cutoff=0.82)
    if close:
        return candidates[close[0]], "fuzzy", []

    # Substring suggestions ("micro" -> Microsoft) are offered but not auto-selected.
    suggestions = [company for key, company in candidates.items() if normalised in key or key in normalised]
    unique: list[Company] = []
    for company in suggestions:
        if company not in unique:
            unique.append(company)
    return None, "none", unique[:5]


def record_search(db: Session, query: str, company: Company | None) -> None:
    db.add(SearchQuery(query=query[:200], matched_company_id=company.id if company else None))
    db.commit()
