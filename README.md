# Lumina — HIPAA Privacy Desk

**Industry:** Health systems & digital health (Privacy / Compliance Officers)

Lumina files your HIPAA corpus, answers with citations, and runs the workflows Privacy Officers use every week: **breach clocks**, **patient access guides**, and **BAA / vendor screens**.

## Why healthcare

| Privacy Officer pain | How Lumina bridges it |
|---|---|
| Policies are scattered; staff guess what “the policy says” | Cited Q&A over your filed PDFs |
| Breach discovery → 60-day individual notice clock slips | **Breach notification clock** + four-factor screen |
| Patient access requests stall in email (30-day §164.524) | **Access request guide** with deadline + checklist |
| Procurement shares PHI before a BAA is cleared | **BAA / vendor screen** with clause pack + blockers |
| OCR asks for evidence of gaps | **HIPAA exposure brief** over the corpus |

## Stack

FastAPI + LangChain + FAISS + OpenAI · Next.js policy desk UI · Docker Compose

## Quick start (local)

```bash
cp .env.example .env   # add a funded OPENAI_API_KEY
python -m venv venv && source venv/bin/activate
make install
# terminal 1
PYTHONPATH=. uvicorn backend.main:app --reload --port 8000
# terminal 2
cd frontend && npm run dev -- --port 3001
```

### No OpenAI key? Use the local model

If `OPENAI_API_KEY` is missing or rejected, Lumina switches to a local [Ollama](https://ollama.com) model
(default `llama3.1:8b`) for answers, suggestions and workflows, and to offline keyword embeddings for
search. OpenAI is checked once at startup; a working key is used first, with the local model as backup.

```bash
ollama pull llama3.1:8b   # once
ollama serve              # if Ollama isn't already running
```

The header shows `llama3.1:8b (local)` while the fallback is active. Local answers are slower
(roughly 5–60 s) and less reliable than GPT-4o-mini. Documents filed in local mode are kept in a
separate index (`vector_store/local/`), so re-upload them after switching back to OpenAI.

- UI: http://localhost:3001  
- API docs: http://localhost:8000/docs  
- Demo PDF: `backend/data/testing_pdfs/HIPAA_Sample_Compliance.pdf`

## Docker

```bash
# Development compose
docker compose up --build

# Production compose (requires CORS_ORIGINS + NEXT_PUBLIC_API_URL in .env)
docker compose -f docker-compose.prod.yml up --build -d
# or: make up-prod
```

## Vercel

`vercel.json` deploys two [Vercel Services](https://vercel.com/docs/services) in one project:

| Service | Root | Public paths |
|---|---|---|
| `backend` (FastAPI) | repo root, entrypoint `backend.main:app` | `/api/*`, `/health`, `/ready` |
| `frontend` (Next.js) | `frontend/` | everything else |

The browser calls the API on the same origin (`/api`), so no CORS or service bindings are needed.

Project environment variables:

| Variable | Value |
|---|---|
| `LUMINA_ENV` | `production` |
| `OPENAI_API_KEY` | funded key |
| `LUMINA_API_KEY` | API key the backend requires |
| `NEXT_PUBLIC_LUMINA_API_KEY` | same value (compiled into the browser bundle) |
| `CORS_ORIGINS` | your deployment URL, e.g. `https://lumina.vercel.app` (required at boot in production) |
| `LUMINA_TRUST_PROXY` | `true` (Vercel sets `X-Forwarded-For`, so rate limits are per client) |
| `LUMINA_MAX_UPLOAD_MB` | `4` (Vercel caps request bodies at 4.5 MB) |

Leave `NEXT_PUBLIC_API_URL` unset on Vercel. For `vercel dev`, set it to `/api`.

Known limits on Vercel:

- Filed policies are stored under `/tmp`, which is per instance and not persistent. Uploads disappear on cold starts and are not shared across instances. Durable storage (for example Vercel Blob or a hosted vector database) is needed for real use.
- Each upload request must stay under 4.5 MB in total.
- Rate limiting is in memory, so it is per instance.

## SDLC / quality gates

| Stage | Command |
|---|---|
| Install | `make install` |
| Unit tests | `make test` |
| Lint | `make lint` |
| Frontend types | `make typecheck` |
| CI | `.github/workflows/ci.yml` (pytest + ruff + eslint + tsc + next build) |

CI runs on push/PR. Backend tests use FastAPI `TestClient` and do **not** require OpenAI credits (HIPAA workflows fall back to deterministic statutory shells).

## Production checklist

1. Set `LUMINA_ENV=production`
2. Set `LUMINA_API_KEY` (required in prod) and mirror to `NEXT_PUBLIC_LUMINA_API_KEY` only for demos — prefer a BFF
3. Set `NEXT_PUBLIC_LUMINA_TENANT_ID` (or send `X-Tenant-Id`) for corpus isolation
4. Set explicit `CORS_ORIGINS` — boot **fails** if missing in prod
5. Set funded `OPENAI_API_KEY` for upload/ask/scan — `/ready` returns 503 in prod if missing
6. Set `NEXT_PUBLIC_API_URL` to the public API base (`…/api`)
7. Prefer `docker-compose.prod.yml` (non-root images, restart policy, readiness healthchecks)
8. Keep secrets in `.env` only (gitignored)
9. Confirm `/health` and `/ready` behind your load balancer

### Gap hardening already landed

- API key auth on `/api/*`
- Per-tenant FAISS paths via `X-Tenant-Id`
- PHI export acknowledgment on healthcare workflows
- Degraded `mode=fallback` banners when shells are used
- XFF spoofing ignored unless `LUMINA_TRUST_PROXY=true`
- Upload stream caps + `%PDF-` magic bytes
- Retrieval no longer dumps the whole corpus on a miss

### Production hardening already in place

- OpenAPI docs disabled in production  
- Generic 5xx / validation error bodies in production  
- Security headers + request IDs  
- Per-IP rate limiting (`LUMINA_RATE_LIMIT_PER_MINUTE`)  
- Upload size/count limits  
- Non-root Docker users  
- Central `backend/config.py` settings with boot validation  

## Core workflows

1. **File policies** — NPP, IRP/breach procedures, BAA playbooks, sanctions  
2. **Ask the corpus** — grounded answers with citation + confidence  
3. **Breach clock** — `POST /api/breach-clock`  
4. **Access guide** — `POST /api/access-request`  
5. **BAA screen** — `POST /api/baa-screen`  
6. **HIPAA exposure brief** — `POST /api/scan`

## Resume blurb

> Built **Lumina**, a HIPAA privacy desk for health systems: PDF policy RAG with citations, breach notification clocks, patient access guides, and BAA vendor screens — FastAPI + Next.js, Docker-deployable, CI-gated.
