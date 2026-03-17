# HireAI — FastAPI Migration Guide

## What changed (and why)

| Before | After |
|---|---|
| Streamlit (rerun-based) | FastAPI + HTML frontend |
| `st.session_state` dies on reload | `sessionId` in `localStorage` persists across reloads |
| Single thread, polling | Async REST API |
| Fixed Streamlit UI | Fully custom dark UI |

---

## Running locally

```bash
# 1. Install deps
pip install -r requirements.txt
python -m textblob.download_corpora

# 2. Create .env
echo "GEMINI_API_KEY=your_key_here" >> .env
echo "DATABASE_URL=your_supabase_pooler_url" >> .env

# 3. Run
uvicorn main:app --reload --port 8000
# Open http://localhost:8000
```

## Running with Docker

```bash
docker build -t hireai .
docker run -p 8000:8000 \
  -e GEMINI_API_KEY="your_key" \
  -e DATABASE_URL="your_supabase_url" \
  hireai
```

---

## How session persistence works

1. On `Start Interview`, the backend creates a UUID `session_id` and returns it
2. The frontend saves it to `localStorage` under `hireai_session_id`
3. On every page load, if a `session_id` is found in localStorage, the frontend calls
   `GET /api/session/{session_id}` to restore the full chat history and state
4. The user sees a "Session restored" banner and can continue exactly where they left off

> **Note:** Sessions are currently stored in-memory on the server. A server restart
> will lose active sessions. To make sessions truly persistent, serialise the
> `sessions` dict to Supabase (a simple `sessions` table with a JSONB `data` column
> is enough).

---

## Hosting recommendations

| Platform | Best for | Notes |
|---|---|---|
| **Railway** | Easiest drop-in from Render | Docker-native, free tier, auto-deploy from GitHub |
| **Google Cloud Run** | Production / scales to zero | Pairs naturally with Gemini API; generous free tier |
| **Fly.io** | Low-latency, global | Deploy close to your Supabase region |
| **Render** (keep) | Current, familiar | Works, but cold-start on free tier is slow |
| **Hugging Face Spaces** | Portfolio visibility | Free, but no persistent server state — needs DB sessions |

---

## Files kept unchanged
- `database.py` — no changes needed
- `crud.py` — no changes needed
- `docker-compose.yml` (if you have one) — just update port 8501 → 8000
