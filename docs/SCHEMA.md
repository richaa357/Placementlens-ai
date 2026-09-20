# Database schema

SQLAlchemy models live in `backend/app/models.py`. The schema is portable
between SQLite (development default) and PostgreSQL (production) - only
`DATABASE_URL` changes. Tables are created on startup by `app.seed.init_db()`,
which also loads `DATASET_PATH` the first time the database is empty.

List-valued columns (`locations`, `aliases`, `technology_areas`,
`skills_requested`) are stored as JSON-encoded text so the same DDL works on
both engines.

## `companies`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | int PK | |
| `name` | varchar(200) | unique, indexed |
| `slug` | varchar(200) | unique, indexed; used in URLs |
| `industry` | varchar(200) | nullable |
| `description` | text | nullable |
| `website` | varchar(500) | nullable |
| `headquarters` | varchar(200) | nullable |
| `locations` | text | JSON list |
| `aliases` | text | JSON list, powers alias search (e.g. `TCS`) |
| `technology_areas` | text | JSON list |
| `is_demo` | bool | true for bundled demonstration companies |

## `sources`

Every displayed fact points at a row here.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | int PK | |
| `name` | varchar(200) | e.g. "Company careers page" |
| `url` | varchar(500) | nullable |
| `published_date` | varchar(32) | date or year the source refers to |
| `data_type` | enum | see below |
| `is_demo` | bool | |
| `notes` | text | nullable; caveats shown in the Sources section |
| `company_id` | FK → `companies.id` | nullable |

`data_type` enum values: `verified_historical`, `current_posting`,
`ai_analysis`, `user_provided`, `demo_data`.

## `job_postings`

Documents analysed by the NLP pipeline.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | int PK | |
| `company_id` | FK → `companies.id` | indexed |
| `title` | varchar(300) | |
| `role_family` | varchar(120) | nullable; drives the role distribution chart |
| `employment_type` | varchar(80) | nullable (Internship / Full-time) |
| `location` | varchar(200) | nullable |
| `posted_date` | varchar(32) | nullable |
| `description` | text | raw job description text |
| `data_type` | enum | default `current_posting` |
| `is_demo` | bool | |
| `source_id` | FK → `sources.id` | nullable |

## `placement_records`

Historical hiring / recruitment-drive records. Unique on
`(company_id, year, role)`.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | int PK | |
| `company_id` | FK → `companies.id` | indexed |
| `year` | int | indexed |
| `role` | varchar(200) | |
| `opening_type` | varchar(80) | nullable |
| `offers_count` | int | **nullable** - `null` means unverified, never 0 |
| `stipend_amount` | float | **nullable** |
| `stipend_currency` | varchar(10) | nullable |
| `stipend_period` | varchar(20) | nullable |
| `drive_date` | varchar(32) | **nullable** |
| `skills_requested` | text | JSON list |
| `data_type` | enum | default `verified_historical` |
| `is_demo` | bool | |
| `source_id` | FK → `sources.id` | nullable |

Nullability is a product requirement: the API pairs each nullable metric with a
`*_display` string containing "No verified public data available." so no
placeholder number ever reaches the UI, and aggregates sum only the values that
actually exist.

## `search_queries`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | int PK | |
| `query` | varchar(200) | indexed |
| `matched_company_id` | FK → `companies.id` | nullable |
| `created_at` | datetime | |

## Dataset format

`DATASET_PATH` points at a JSON file shaped like:

```json
{
  "is_demo": true,
  "disclaimer": "...",
  "companies": [
    {
      "name": "Example Corp", "slug": "example-corp", "aliases": ["EC"],
      "industry": "...", "website": "...", "headquarters": "...",
      "locations": ["..."], "technology_areas": ["..."],
      "overview_source": { "name": "...", "url": "...", "published_date": "2025", "data_type": "current_posting" },
      "job_postings": [ { "title": "...", "role_family": "...", "description": "...", "posted_date": "2025-01" } ],
      "placement_records": [ { "year": 2024, "role": "...", "offers_count": null, "stipend_amount": null } ]
    }
  ]
}
```

Omit or `null` any metric you cannot verify - that is the supported way to say
"unknown".
