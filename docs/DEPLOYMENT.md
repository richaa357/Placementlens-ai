# Deployment

The backend is a standard ASGI app (`app.main:app`) and the frontend builds to
static files, so any Python host + any static host works. Below are the paths
that have been exercised locally plus the settings each target needs.

## 1. Configuration

| Variable | Where | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | backend | `sqlite:///./placementlens.db` for dev, `postgresql+psycopg://...` for production |
| `CORS_ORIGINS` | backend | Comma-separated list of allowed frontend origins |
| `DATASET_PATH` | backend | Dataset loaded when the database is empty |
| `DATASET_IS_DEMO` | backend | Keep `true` while the bundled demo dataset is in use |
| `ENABLE_SENTENCE_TRANSFORMERS` | backend | `true` only if `requirements-optional.txt` is installed |
| `VITE_API_BASE_URL` | frontend | Backend base URL, baked in at **build** time |

`VITE_*` variables are inlined during `npm run build`, so rebuild the frontend
after changing the backend URL.

## 2. PostgreSQL

```bash
pip install "psycopg[binary]"
createdb placementlens
export DATABASE_URL="postgresql+psycopg://placementlens:password@db-host:5432/placementlens"
python -m app.seed      # creates tables and loads DATASET_PATH
```

The models are engine-agnostic; no SQLite-specific types are used.

## 3. Backend (any container/VM host: Render, Railway, Fly.io, ECS, ...)

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

For multiple workers use `gunicorn -k uvicorn.workers.UvicornWorker app.main:app -w 2`.
Two workers is a reasonable default: each holds its own in-process NLP models.

A ready-to-use `backend/Dockerfile` is included (build it with `backend/` as the
context):

```bash
docker build -t placementlens-api backend
docker run -p 8000:8000 -e CORS_ORIGINS=https://your-frontend.example.com placementlens-api
```

Health check endpoint: `GET /api/health`.

## 4. Frontend (Vercel / Netlify / Cloudflare Pages / any static host)

```bash
cd frontend
VITE_API_BASE_URL=https://your-backend.example.com npm run build
# deploy the ./dist directory
```

Vercel/Netlify settings: build command `npm run build`, output directory `dist`,
environment variable `VITE_API_BASE_URL`. The app is a single page, so configure
an SPA rewrite of `/*` → `/index.html` if you add routing.

## 5. Checklist before going live

* Set `CORS_ORIGINS` to the deployed frontend origin (not `*`).
* Replace the demo dataset, or leave the demo banner visible so users know the
  numbers are illustrative.
* Serve both apps over HTTPS; browsers block an HTTPS page calling an HTTP API.
* Back up the database if you import real placement-cell records.
