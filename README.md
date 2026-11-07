# Lumina — HIPAA Privacy Desk

**Industry:** Health systems & digital health (Privacy / Compliance Officers)

Lumina is a grounded policy desk for the people who live inside HIPAA every day. File your privacy corpus, interrogate it with citations, and run the three workflows that dominate Privacy Officer platforms: **breach clocks**, **patient access requests**, and **BAA / vendor screens**.

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

## Quick start

```bash
cp .env.example .env   # add a funded OPENAI_API_KEY
docker compose up --build
# or local: backend :8000 + frontend :3001
```

- UI: http://localhost:3001  
- API docs: http://localhost:8000/docs  
- Demo PDF: `backend/data/testing_pdfs/HIPAA_Sample_Compliance.pdf`

## Core workflows

1. **File policies** — NPP, IRP/breach procedures, BAA playbooks, sanctions  
2. **Ask the corpus** — grounded answers with citation + confidence  
3. **Breach clock** — `POST /api/breach-clock`  
4. **Access guide** — `POST /api/access-request`  
5. **BAA screen** — `POST /api/baa-screen`  
6. **HIPAA exposure brief** — `POST /api/scan`

## Production notes

- Set `LUMINA_ENV=production` to disable OpenAPI docs and harden errors  
- Set explicit `CORS_ORIGINS` for your frontend  
- Keep secrets in `.env` (gitignored). `.cursor/` is ignored  

## Resume blurb

> Built **Lumina**, a HIPAA privacy desk for health systems: PDF policy RAG with citations, breach notification clocks, patient access guides, and BAA vendor screens — FastAPI + Next.js, Docker-deployable.
