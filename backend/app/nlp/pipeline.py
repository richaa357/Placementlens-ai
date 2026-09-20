"""The analysis pipeline that turns documents into dashboard content.

Inputs are job descriptions (+ their year) and historical skill lists; outputs
are skill frequencies by taxonomy category, TF-IDF keywords, role families,
emerging skills and the skill-alignment comparison.

Everything produced here is AI/statistical *analysis* of the underlying
documents - it is tagged `ai_analysis` by the API so the UI never presents it
as verified historical fact.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field

from app.nlp.embeddings import SemanticModel
from app.nlp.skills_taxonomy import CATEGORIES, category_of, extract_skills, normalise_user_skill
from app.nlp.tfidf_analyzer import TfidfAnalyzer


@dataclass
class Document:
    """A single analysed text (a job description or a historical skill list)."""

    doc_id: int
    title: str
    text: str
    year: int | None = None
    role_family: str | None = None
    origin: str = "job_posting"  # job_posting | placement_record


@dataclass
class SkillStat:
    skill: str
    category: str
    document_count: int          # in how many documents the skill appears
    mention_count: int           # total alias matches
    frequency: float             # document_count / number of documents


@dataclass
class AnalysisResult:
    document_count: int = 0
    skills: list[SkillStat] = field(default_factory=list)
    skills_by_category: dict[str, list[SkillStat]] = field(default_factory=dict)
    keywords: list[dict] = field(default_factory=list)
    emerging_skills: list[dict] = field(default_factory=list)
    role_families: list[dict] = field(default_factory=list)
    heatmap: dict = field(default_factory=dict)
    semantic_backend: str = "none"


def _skill_documents(documents: list[Document]) -> tuple[list[dict[str, int]], Counter, Counter]:
    per_doc: list[dict[str, int]] = []
    doc_counter: Counter = Counter()
    mention_counter: Counter = Counter()
    for doc in documents:
        found = extract_skills(f"{doc.title}\n{doc.text}")
        per_doc.append(found)
        for skill, hits in found.items():
            doc_counter[skill] += 1
            mention_counter[skill] += hits
    return per_doc, doc_counter, mention_counter


def analyze_documents(documents: list[Document]) -> AnalysisResult:
    result = AnalysisResult(document_count=len(documents))
    if not documents:
        return result

    per_doc, doc_counter, mention_counter = _skill_documents(documents)
    total = len(documents)

    stats = [
        SkillStat(
            skill=skill,
            category=category_of(skill) or "Other",
            document_count=count,
            mention_count=mention_counter[skill],
            frequency=round(count / total, 4),
        )
        for skill, count in doc_counter.most_common()
    ]
    result.skills = stats
    by_category: dict[str, list[SkillStat]] = {category: [] for category in CATEGORIES}
    for stat in stats:
        by_category.setdefault(stat.category, []).append(stat)
    result.skills_by_category = by_category

    # --- TF-IDF keyword extraction --------------------------------------
    analyzer = TfidfAnalyzer([f"{doc.title}. {doc.text}" for doc in documents])
    result.keywords = [{"term": kw.term, "weight": kw.weight} for kw in analyzer.top_keywords(30)]

    # --- role families ---------------------------------------------------
    role_counter: Counter = Counter()
    for doc in documents:
        role_counter[doc.role_family or doc.title] += 1
    result.role_families = [
        {"role": role, "count": count, "share": round(count / total, 4)}
        for role, count in role_counter.most_common()
    ]

    # --- emerging skills --------------------------------------------------
    # A skill is "emerging" when its share of recent documents is materially
    # higher than its share of older documents. Requires documents on both
    # sides of the split, otherwise we report nothing rather than guessing.
    years = sorted({doc.year for doc in documents if doc.year is not None})
    if len(years) >= 2:
        split = years[len(years) // 2]
        recent_idx = [i for i, doc in enumerate(documents) if doc.year is not None and doc.year >= split]
        older_idx = [i for i, doc in enumerate(documents) if doc.year is not None and doc.year < split]
        if recent_idx and older_idx:
            emerging = []
            for skill in doc_counter:
                recent_share = sum(1 for i in recent_idx if skill in per_doc[i]) / len(recent_idx)
                older_share = sum(1 for i in older_idx if skill in per_doc[i]) / len(older_idx)
                delta = recent_share - older_share
                if delta >= 0.2:
                    emerging.append(
                        {
                            "skill": skill,
                            "category": category_of(skill) or "Other",
                            "recent_share": round(recent_share, 4),
                            "earlier_share": round(older_share, 4),
                            "delta": round(delta, 4),
                            "recent_period": f"{split}+",
                            "earlier_period": f"before {split}",
                        }
                    )
            result.emerging_skills = sorted(emerging, key=lambda item: item["delta"], reverse=True)[:10]

    # --- heatmap: category x year ----------------------------------------
    grid: dict[str, dict[int, int]] = defaultdict(lambda: defaultdict(int))
    for doc, found in zip(documents, per_doc):
        if doc.year is None:
            continue
        for skill in found:
            grid[category_of(skill) or "Other"][doc.year] += 1
    heat_years = sorted({year for row in grid.values() for year in row})
    result.heatmap = {
        "years": heat_years,
        "categories": [category for category in CATEGORIES if category in grid],
        "values": [[grid[category].get(year, 0) for year in heat_years] for category in CATEGORIES if category in grid],
    }

    result.semantic_backend = "not-computed"
    return result


@dataclass
class AlignmentResult:
    user_skills: list[str]
    unmapped_user_input: list[str]
    matched_skills: list[dict]
    missing_skills: list[dict]
    extra_skills: list[str]
    coverage: float
    tfidf_similarity: float
    semantic_similarity: float
    semantic_backend: str
    per_document_similarity: list[dict]


def analyze_alignment(
    documents: list[Document],
    raw_user_skills: list[str],
    analysis: AnalysisResult,
    top_n_missing: int = 12,
) -> AlignmentResult:
    """Compare a user's self-reported skills with the company's requirements.

    This is deliberately *not* a selection prediction: it reports overlap,
    gaps and cosine similarity between the user's skill text and the job
    descriptions.
    """
    canonical: list[str] = []
    unmapped: list[str] = []
    for raw in raw_user_skills:
        mapped = normalise_user_skill(raw)
        if mapped and mapped not in canonical:
            canonical.append(mapped)
        elif not mapped and raw.strip():
            unmapped.append(raw.strip())

    required = {stat.skill: stat for stat in analysis.skills}
    matched = [
        {
            "skill": skill,
            "category": required[skill].category,
            "frequency": required[skill].frequency,
            "document_count": required[skill].document_count,
        }
        for skill in canonical
        if skill in required
    ]
    matched.sort(key=lambda item: item["frequency"], reverse=True)
    missing = [
        {
            "skill": stat.skill,
            "category": stat.category,
            "frequency": stat.frequency,
            "document_count": stat.document_count,
        }
        for stat in analysis.skills
        if stat.skill not in canonical
    ][:top_n_missing]
    extra = [skill for skill in canonical if skill not in required]

    coverage = round(len(matched) / len(required), 4) if required else 0.0

    query = ", ".join(canonical + unmapped)
    texts = [f"{doc.title}. {doc.text}" for doc in documents]
    tfidf = TfidfAnalyzer(texts)
    tfidf_scores = tfidf.similarity_to(query) if query else [0.0] * len(texts)
    semantic = SemanticModel(texts)
    semantic_scores = semantic.similarity_to(query) if query else [0.0] * len(texts)

    per_document = [
        {
            "document_id": doc.doc_id,
            "title": doc.title,
            "year": doc.year,
            "tfidf_similarity": tfidf_scores[i] if i < len(tfidf_scores) else 0.0,
            "semantic_similarity": semantic_scores[i] if i < len(semantic_scores) else 0.0,
        }
        for i, doc in enumerate(documents)
    ]

    return AlignmentResult(
        user_skills=canonical,
        unmapped_user_input=unmapped,
        matched_skills=matched,
        missing_skills=missing,
        extra_skills=extra,
        coverage=coverage,
        tfidf_similarity=round(max(tfidf_scores) if tfidf_scores else 0.0, 4),
        semantic_similarity=round(max(semantic_scores) if semantic_scores else 0.0, 4),
        semantic_backend=semantic.backend,
        per_document_similarity=per_document,
    )


# Preparation areas are derived only from the skills actually observed in the
# analysed documents - never from a hard-coded "what companies want" list.
PREPARATION_CATEGORY_ORDER = ["Programming", "SQL/Data", "Machine Learning", "NLP", "Deep Learning", "Tools"]


def preparation_areas(analysis: AnalysisResult, user_skills: list[str] | None = None) -> list[dict]:
    """Group the observed skills into preparation areas, most requested first."""
    have = {skill.lower() for skill in (user_skills or [])}
    areas: list[dict] = []
    for category in PREPARATION_CATEGORY_ORDER:
        stats = [stat for stat in analysis.skills_by_category.get(category, []) if stat.document_count > 0]
        if not stats:
            continue
        stats.sort(key=lambda stat: stat.frequency, reverse=True)
        areas.append(
            {
                "area": category,
                "priority_score": round(sum(stat.frequency for stat in stats) / len(stats), 4),
                "topics": [
                    {
                        "skill": stat.skill,
                        "frequency": stat.frequency,
                        "document_count": stat.document_count,
                        "already_listed_by_user": stat.skill.lower() in have,
                    }
                    for stat in stats[:8]
                ],
            }
        )
    areas.sort(key=lambda area: area["priority_score"], reverse=True)
    return areas
