"""Unit tests for the NLP building blocks."""
from __future__ import annotations

from app.nlp.pipeline import Document, analyze_alignment, analyze_documents, preparation_areas
from app.nlp.preprocessing import clean_text, preprocess, tokenize
from app.nlp.skills_taxonomy import category_of, extract_skills, normalise_user_skill
from app.nlp.tfidf_analyzer import TfidfAnalyzer

ML_JD = (
    "Build machine learning models. Regression, classification and feature engineering. "
    "Model evaluation with cross validation. Python, scikit-learn and PyTorch. SQL with window functions."
)
NLP_JD = (
    "Natural language processing research. Text preprocessing, TF-IDF, word2vec embeddings and transformers. "
    "Sentiment analysis and named entity recognition using spaCy and NLTK in Python."
)
SDE_JD = (
    "Software engineering internship. Strong data structures and algorithms, object oriented programming, "
    "C++ and Java. Docker containers, AWS cloud and Git version control."
)


def test_clean_text_strips_urls_and_markup():
    assert "https" not in clean_text("See <b>here</b> https://example.com/jobs now")
    assert clean_text("A   B\n\nC") == "a b c"


def test_tokenize_removes_stopwords_and_short_tokens():
    tokens = tokenize("The candidate will work with a team on Python and SQL")
    assert "the" not in tokens
    assert "candidate" not in tokens  # domain stopword
    assert "python" in tokens and "sql" in tokens


def test_preprocess_returns_string():
    assert isinstance(preprocess(ML_JD), str)
    assert "python" in preprocess(ML_JD)


def test_extract_skills_finds_canonical_names():
    found = extract_skills(ML_JD)
    assert "Machine Learning" in found
    assert "Regression" in found
    assert "Feature Engineering" in found
    assert "Model Evaluation" in found
    assert "Window Functions" in found


def test_extract_skills_handles_symbol_heavy_names():
    found = extract_skills(SDE_JD)
    assert "C++" in found
    assert "Data Structures & Algorithms" in found
    assert "Git/GitHub" in found


def test_extract_skills_empty_text():
    assert extract_skills("") == {}


def test_category_of_and_normalise_user_skill():
    assert category_of("TF-IDF") == "NLP"
    assert normalise_user_skill("dsa") == "Data Structures & Algorithms"
    assert normalise_user_skill("  pytorch ") == "TensorFlow/PyTorch"
    assert normalise_user_skill("underwater basket weaving") is None


def test_tfidf_keywords_and_similarity():
    analyzer = TfidfAnalyzer([ML_JD, NLP_JD, SDE_JD])
    assert analyzer.is_fitted
    terms = [keyword.term for keyword in analyzer.top_keywords(30)]
    assert any("python" in term for term in terms)

    scores = analyzer.similarity_to("transformers embeddings sentiment analysis")
    assert len(scores) == 3
    assert scores[1] == max(scores)  # the NLP job description is the closest


def test_tfidf_handles_empty_query():
    analyzer = TfidfAnalyzer([ML_JD, NLP_JD])
    assert analyzer.similarity_to("") == [0.0, 0.0]


def _documents() -> list[Document]:
    return [
        Document(1, "ML Intern", ML_JD, year=2024, role_family="Machine Learning"),
        Document(2, "NLP Intern", NLP_JD, year=2025, role_family="Machine Learning"),
        Document(3, "SDE Intern", SDE_JD, year=2022, role_family="Software Engineering"),
    ]


def test_analyze_documents_produces_skill_stats():
    result = analyze_documents(_documents())
    assert result.document_count == 3
    skills = {stat.skill: stat for stat in result.skills}
    assert "Python" in skills
    assert 0 < skills["Python"].frequency <= 1
    assert skills["Python"].category == "Programming"
    assert result.keywords
    roles = {row["role"]: row["count"] for row in result.role_families}
    assert roles["Machine Learning"] == 2


def test_analyze_documents_empty_corpus():
    result = analyze_documents([])
    assert result.document_count == 0
    assert result.skills == []


def test_emerging_skills_requires_two_periods():
    single_year = [Document(1, "A", ML_JD, year=2024), Document(2, "B", NLP_JD, year=2024)]
    assert analyze_documents(single_year).emerging_skills == []


def test_alignment_reports_have_and_missing():
    documents = _documents()
    analysis = analyze_documents(documents)
    alignment = analyze_alignment(documents, ["Python", "SQL", "dsa", "quantum juggling"], analysis)
    assert "Python" in alignment.user_skills
    assert "Data Structures & Algorithms" in alignment.user_skills
    assert "quantum juggling" in alignment.unmapped_user_input
    have = {item["skill"] for item in alignment.matched_skills}
    assert "Python" in have
    missing = {item["skill"] for item in alignment.missing_skills}
    assert have.isdisjoint(missing)
    assert 0.0 <= alignment.coverage <= 1.0
    assert 0.0 <= alignment.tfidf_similarity <= 1.0
    assert 0.0 <= alignment.semantic_similarity <= 1.0
    assert len(alignment.per_document_similarity) == 3


def test_alignment_with_no_user_skills():
    documents = _documents()
    analysis = analyze_documents(documents)
    alignment = analyze_alignment(documents, [], analysis)
    assert alignment.matched_skills == []
    assert alignment.tfidf_similarity == 0.0


def test_preparation_areas_only_from_observed_skills():
    analysis = analyze_documents(_documents())
    areas = preparation_areas(analysis, ["Python"])
    assert areas
    observed = {stat.skill for stat in analysis.skills}
    for area in areas:
        for topic in area["topics"]:
            assert topic["skill"] in observed
    python_topic = next(
        topic for area in areas for topic in area["topics"] if topic["skill"] == "Python"
    )
    assert python_topic["already_listed_by_user"] is True
