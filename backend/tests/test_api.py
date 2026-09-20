"""API level tests, including the data-honesty guarantees."""
from __future__ import annotations

from app.schemas import INSUFFICIENT_DATA_MESSAGE, NO_DATA_MESSAGE


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["counts"]["companies"] > 0


def test_list_companies(client):
    response = client.get("/api/companies")
    assert response.status_code == 200
    names = [company["name"] for company in response.json()]
    assert "Google" in names


def test_search_exact_and_case_insensitive(client):
    body = client.get("/api/companies/search", params={"q": "  google "}).json()
    assert body["match_type"] == "exact"
    assert body["match"]["slug"] == "google"


def test_search_alias(client):
    body = client.get("/api/companies/search", params={"q": "TCS"}).json()
    assert body["match_type"] == "alias"
    assert body["match"]["name"] == "Tata Consultancy Services"


def test_search_fuzzy_typo(client):
    body = client.get("/api/companies/search", params={"q": "Microsft"}).json()
    assert body["match_type"] == "fuzzy"
    assert body["match"]["slug"] == "microsoft"


def test_search_unknown_company_returns_no_data_message(client):
    body = client.get("/api/companies/search", params={"q": "Definitely Not A Real Company"}).json()
    assert body["match"] is None
    assert body["match_type"] == "none"
    assert body["message"] == NO_DATA_MESSAGE


def test_analysis_payload(client):
    body = client.get("/api/companies/google/analysis").json()
    assert body["overview"]["name"] == "Google"
    assert body["overview"]["technology_areas"]
    assert body["historical"]["has_data"] is True
    assert body["skill_analysis"]["has_data"] is True
    assert body["ai_analysis"]["has_data"] is True
    assert body["ai_analysis"]["method"]["similarity"] == "cosine similarity"
    assert body["preparation_areas"]
    assert body["sources"]


def test_analysis_marks_demo_data(client):
    body = client.get("/api/companies/google/analysis").json()
    assert body["data_quality"]["contains_demo_data"] is True
    assert body["historical"]["contains_demo_data"] is True
    assert any(record["is_demo"] for record in body["historical"]["records"])


def test_missing_values_are_never_invented(client):
    body = client.get("/api/companies/google/analysis").json()
    for record in body["historical"]["records"]:
        if record["offers_count"] is None:
            assert record["offers_count_display"] == NO_DATA_MESSAGE
        if record["drive_date"] is None:
            assert record["drive_date_display"] == NO_DATA_MESSAGE
    stipend_free = [r for r in body["historical"]["records"] if r["stipend_display"] == NO_DATA_MESSAGE]
    assert stipend_free, "demo dataset should contain records without a stipend"


def test_analysis_unknown_company_404(client):
    response = client.get("/api/companies/not-a-company/analysis")
    assert response.status_code == 404
    assert response.json()["detail"] == NO_DATA_MESSAGE


def test_postings_endpoint(client):
    postings = client.get("/api/companies/zoho/postings").json()
    assert postings
    assert all(posting["source"] is not None for posting in postings)


def test_skill_alignment(client):
    response = client.post(
        "/api/companies/google/skill-alignment",
        json={"skills": ["Python, SQL", "Machine Learning", "Streamlit"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["has_data"] is True
    assert "not a prediction" in body["disclaimer"]
    have = {item["skill"] for item in body["skills_i_have"]}
    assert "Python" in have
    learn = {item["skill"] for item in body["skills_to_learn"]}
    assert have.isdisjoint(learn)
    assert body["user_input_data_type"] == "user_provided"
    assert body["analysis_data_type"] == "ai_analysis"


def test_skill_alignment_with_unknown_skill(client):
    body = client.post(
        "/api/companies/zoho/skill-alignment", json={"skills": ["Python", "kite surfing"]}
    ).json()
    assert "kite surfing" in body["skills_not_recognised"]


def test_taxonomy_endpoint(client):
    body = client.get("/api/skills/taxonomy").json()
    assert "Machine Learning" in body["categories"]
    assert any(skill["name"] == "TF-IDF" for skill in body["skills"])


def test_insufficient_data_message_used_for_thin_corpus(db, client):
    from app.models import Company
    from app.services import analysis_service

    company = Company(name="Empty Co", slug="empty-co", industry="Unknown", is_demo=False)
    db.add(company)
    db.commit()
    result = analysis_service.build_company_analysis(db, company)
    assert result.historical.has_data is False
    assert result.historical.message == NO_DATA_MESSAGE
    assert result.skill_analysis.message == INSUFFICIENT_DATA_MESSAGE
    assert result.ai_analysis.message == INSUFFICIENT_DATA_MESSAGE
    alignment = analysis_service.build_alignment(db, company, ["Python"])
    assert alignment.has_data is False
    db.delete(company)
    db.commit()
