# Lumina — Compliance RAG Assistant

Upload policy PDFs, ask grounded compliance questions, get **cited answers** with confidence scores.

Built with **FastAPI + LangChain + FAISS + OpenAI** and a **Next.js** UI. Designed as a resume-ready, one-command demo.

## Architecture (fixed)

| Layer | Behavior |
|-------|----------|
| Retrieval | Code-gated — LLM is never called without vector context |
| Prompt | Single canonical template (`llm_workflow.py`) |
| Response | Typed JSON: `answer`, `citation`, `confidence`, `sources` |
| Store | Process singleton FAISS (`text-embedding-3-small`) |
| Deploy | Docker Compose: backend `:8000` + frontend `:3000` |

## Product MVPs

1. **Document Library** — `GET/DELETE /api/documents` list & clear indexed PDFs  
2. **Suggested Questions** — `GET /api/suggestions` grounded prompt chips  
3. **Compliance Risk Scan** — `POST /api/scan` gaps + strengths brief  

UI: policy-desk workspace (Fraunces + Sora, paper canvas, teal signal) — typically `http://localhost:3001` when port 3000 is busy.

## Production notes

- Set `LUMINA_ENV=production` to disable OpenAPI docs and harden error payloads.
- Set explicit `CORS_ORIGINS` for your deployed frontend.
- Secrets stay in `.env` (never commit). `.cursor/` is ignored.

## Quick start (Docker)

```bash
cp .env.example .env
# put your OpenAI key in .env

docker compose up --build
```

- UI: http://localhost:3000  
- API docs: http://localhost:8000/docs  
- Health: http://localhost:8000/health  

Set `LUMINA_SEED_SAMPLE_DOCS=true` to auto-index sample PDFs under `backend/data/testing_pdfs/` (requires OpenAI embedding credits).

**Note:** upload/ask need a funded `OPENAI_API_KEY`. Without credits the API stays up but embedding/generation calls return provider errors.

## Local development

### Backend

```bash
python -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env   # add OPENAI_API_KEY

export PYTHONPATH=.
uvicorn backend.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
# ensure .env.local has NEXT_PUBLIC_API_URL=http://localhost:8000/api
npm install
npm run dev
```

## Demo flow (for interviews)

1. Open http://localhost:3000  
2. Upload `backend/data/testing_pdfs/GDPR_Sample_Compliance.pdf` (or use seed)  
3. Ask: *“What are the data breach notification requirements?”*  
4. Show citation + confidence + source file in the response card  

## API

- `POST /api/upload` — multipart PDF upload  
- `POST /api/ask` — `{ "question": "..." }` → structured answer  
- `GET /health` — readiness + chunk count  

## Eval

```bash
cd promptfoo-tests
npx promptfoo eval
```

## Security note (demo scope)

This is a **local/demo** stack: `/api/upload` and `/api/ask` are unauthenticated. Do not expose publicly without auth, rate limits, and per-tenant indexes. FAISS uses pickle deserialization — only load indexes you created.

## Resume blurb

> Built **Lumina**, an end-to-end RAG compliance assistant: PDF ingestion → FAISS retrieval → grounded OpenAI answers with citations, FastAPI + Next.js, Docker-deployable, with prompt-injection guards and promptfoo evals.
