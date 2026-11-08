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
2. Set explicit `CORS_ORIGINS` to your real frontend origin(s) — boot **fails** if missing in prod
3. Set funded `OPENAI_API_KEY` for upload/ask/scan
4. Set `NEXT_PUBLIC_API_URL` to the public API base (`…/api`)
5. Prefer `docker-compose.prod.yml` (non-root images, restart policy, readiness healthchecks)
6. Keep secrets in `.env` only (gitignored)
7. Confirm `/health` and `/ready` behind your load balancer

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
