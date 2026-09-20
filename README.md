# PlacementLens AI

Research companies and understand their placement opportunities using historical data and AI.

PlacementLens AI takes a single input - a company name - and returns a structured
dashboard: company overview, historical placement analysis, skill analysis by
category, an NLP analysis of the job descriptions, an optional *Skill Alignment
Analysis* against your own skills, and a "What should I prepare?" section.

## Data honesty rules

These rules are enforced in code, not just in the UI copy:

* The application never invents salaries, hiring numbers, placement percentages,
  interview questions, recruitment dates or selection probabilities. Missing
  values are returned as `null` and rendered as **"No verified public data available."**
* A corpus too small to analyse produces **"Insufficient verified data"** rather than a chart.
* Every fact carries a `data_type`, and the UI colour-codes it:

  | `data_type` | Meaning |
  | --- | --- |
  | `verified_historical` | Sourced historical record |
  | `current_posting` | Current job-posting information |
  | `ai_analysis` | Derived by the NLP/ML pipeline from the documents listed under Sources |
  | `user_provided` | Entered by the user |
  | `demo_data` | Clearly labelled demonstration data shipped with this repository |

* The skill comparison is called **Skill Alignment Analysis**. It reports overlap,
  gaps and cosine similarity - it is *not* a prediction of selection, and the app
  does not rank companies.

### About the bundled dataset

Out of the box the app runs on `backend/app/data/demo_dataset.json`, a
**demonstration dataset**. Company overview fields link to public company pages;
the job descriptions are illustrative texts written for this project so the NLP
pipeline has something to analyse, and the placement records are sample values.
The dashboard shows a red "Demonstration data" banner whenever demo records are
involved. Replace the file (or set `DATASET_PATH`) with your placement cell's
export (set `"is_demo": false` in the file, or `DATASET_IS_DEMO=false` if the
file omits the flag) to analyse real data.

## Project structure

```
placementlens-ai/
├── backend/
│   ├── app/
│   │   ├── config.py            # settings (env driven)
│   │   ├── database.py          # SQLAlchemy engine/session
│   │   ├── models.py            # Company, JobPosting, PlacementRecord, Source
│   │   ├── schemas.py           # Pydantic API contract
│   │   ├── seed.py              # dataset loader / DB bootstrap
│   │   ├── main.py              # FastAPI app
│   │   ├── data/demo_dataset.json
│   │   ├── nlp/
│   │   │   ├── preprocessing.py   # cleaning, tokenising, lemmatising
│   │   │   ├── skills_taxonomy.py # skill categories + alias matching
│   │   │   ├── tfidf_analyzer.py  # TF-IDF keywords + cosine similarity
│   │   │   ├── embeddings.py      # sentence-transformers / Word2Vec / SVD
│   │   │   └── pipeline.py        # analysis + skill alignment
│   │   ├── routers/             # /api/companies, /api/health, /api/skills
│   │   └── services/            # search + dashboard assembly
│   ├── tests/                   # pytest unit + API tests
│   ├── requirements.txt
│   └── .env.example
├── frontend/                    # React + TypeScript + Vite + Plotly
│   ├── src/components/          # dashboard sections and charts
│   ├── src/api.ts               # typed API client
│   └── .env.example
└── docs/
    ├── API.md                   # endpoint reference
    ├── SCHEMA.md                # database schema
    └── DEPLOYMENT.md            # deployment instructions
```

## Setup

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm      # optional but recommended
python -m nltk.downloader stopwords wordnet  # optional fallback backend
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

The database is created and seeded automatically on first start.
Interactive API docs: <http://localhost:8000/docs>.

If neither spaCy nor NLTK data is available the preprocessing falls back to a
pure-Python tokeniser; the active backend is reported by `GET /api/health`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev     # http://localhost:5173
```

### Tests

```bash
cd backend && python -m pytest        # 30 unit + API tests
cd frontend && npm run lint && npm run build
```

## Machine learning / NLP pipeline

1. **Preprocessing** (`nlp/preprocessing.py`) - lowercase, strip URLs/markup,
   tokenise, lemmatise (spaCy → NLTK → regex fallback), drop English and
   recruitment-domain stopwords.
2. **Skill extraction** (`nlp/skills_taxonomy.py`) - ~55 canonical skills across
   Machine Learning, Deep Learning, NLP, SQL/Data, Programming and Tools, matched
   through word-boundary alias regexes that survive tokens such as `C++` and `scikit-learn`.
3. **TF-IDF** (`nlp/tfidf_analyzer.py`) - unigram+bigram, sublinear term
   frequency; used for keyword extraction and cosine similarity.
4. **Embeddings** (`nlp/embeddings.py`) - sentence-transformers when enabled,
   otherwise Word2Vec trained on the local corpus, otherwise TF-IDF + TruncatedSVD.
   The backend actually used is reported in the API response and in the UI.
5. **Analysis** (`nlp/pipeline.py`) - skill frequencies per category, role
   distribution, emerging-skill detection (recent vs earlier document share),
   category × year heatmap, and the Skill Alignment Analysis.

## License

Provided as-is for educational use. Verify any placement information against
your institution's official records before relying on it.
