# API reference

Base URL: `http://localhost:8000`. Interactive OpenAPI docs are served at
`/docs` (Swagger UI) and `/redoc`; the schema itself is at `/openapi.json`.

Every object that represents a fact carries `data_type`
(`verified_historical` | `current_posting` | `ai_analysis` | `user_provided` |
`demo_data`) and, where relevant, `is_demo`. Unknown numeric values are `null`
and are paired with a `*_display` string containing
`"No verified public data available."`.

## `GET /api/health`

```json
{ "status": "ok", "app": "PlacementLens AI", "nlp_backend": "spacy",
  "sentence_transformers_enabled": false, "dataset_is_demo": true,
  "counts": { "companies": 6, "job_postings": 26, "placement_records": 27 } }
```

## `GET /api/skills/taxonomy`

Canonical skills grouped by category (Machine Learning, Deep Learning, NLP,
SQL/Data, Programming, Tools) with their aliases.

## `GET /api/companies`

List of `CompanySummary` (`id`, `name`, `slug`, `industry`, `headquarters`, `is_demo`).

## `GET /api/companies/search?q=<name>`

Resolves a free-text company name.

| Field | Notes |
| --- | --- |
| `match` | `CompanySummary` or `null` |
| `match_type` | `exact`, `alias`, `fuzzy` or `none` |
| `suggestions` | Closest known companies when there is no confident match |
| `message` | Populated with a no-data message when `match_type` is `none` |

## `GET /api/companies/{slug}/analysis`

The dashboard payload.

* `overview` - industry, description, website, locations, technology areas,
  typical roles, required skills.
* `historical` - `records` (year, role, opening type, offers, stipend, drive
  date, skills, source), `by_year`, `roles`, `hiring_frequency`,
  `stipend_observations`. `has_data=false` plus
  `message: "Insufficient verified data"` when there is nothing verifiable.
* `skill_analysis` - per-skill `document_count` / `mention_count` / `frequency`,
  `by_category`, and a category × year `heatmap`.
* `ai_analysis` - `method` (preprocessing backend, vectoriser, semantic model),
  TF-IDF `keywords`, `emerging_skills` (recent vs earlier document share) and
  `role_distribution`.
* `preparation_areas` - the "What should I prepare?" list, derived only from
  skills observed in the analysed documents.
* `sources` - every source backing the sections above.
* `data_quality` - document counts, demo flags and analysis coverage.

Returns `404` when the slug is unknown.

## `GET /api/companies/{slug}/postings`

Current job postings (`data_type: current_posting`) with their source.

## `POST /api/companies/{slug}/skill-alignment`

```json
{ "skills": ["Python", "SQL", "Machine Learning", "NLP"] }
```

Response (`Skill Alignment Analysis`, never a selection prediction):

| Field | Meaning |
| --- | --- |
| `skills_i_have` | User skills also requested by the company |
| `skills_frequently_requested` | Most requested skills in the corpus |
| `skills_to_learn` | Requested skills the user did not list |
| `skills_not_recognised` | Inputs that matched no canonical skill |
| `additional_skills` | User skills not requested in this corpus |
| `coverage` | Share of requested skills the user holds |
| `tfidf_similarity` / `semantic_similarity` | Cosine similarity of the user's skill text against the corpus |
| `semantic_backend` | `sentence-transformers`, `word2vec`, `tfidf-svd` or `none` |
| `per_document_similarity` | Similarity per analysed document |

`has_data=false` with `"Insufficient verified data"` when fewer than two
documents are available for the company.
