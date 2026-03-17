import os
import uuid
import json

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from textblob import TextBlob
from google import genai
from google.genai import types
from dotenv import load_dotenv

from database import init_db, SessionLocal
import crud

load_dotenv()
init_db()

app = FastAPI(title="HireAI")
templates = Jinja2Templates(directory="templates")

_api_key = os.environ.get("GEMINI_API_KEY")
if not _api_key:
    raise RuntimeError("GEMINI_API_KEY env var not set.")
gemini_client = genai.Client(api_key=_api_key)

sessions: dict = {}          # session_id  -> session dict
email_to_session: dict = {}  # email       -> session_id

REQUIRED_FIELDS = ["Years of Experience", "Current Location", "Tech Stack"]
EXIT_KEYWORDS   = {"quit", "exit", "goodbye", "bye", "stop"}


# ============================================================
# Helpers
# ============================================================

def analyze_sentiment(text: str) -> dict:
    blob = TextBlob(text)
    p = round(blob.sentiment.polarity, 2)
    s = round(blob.sentiment.subjectivity, 2)
    label = "Positive" if p > 0.2 else "Negative" if p < -0.2 else "Neutral"
    return {"label": label, "polarity": p, "subjectivity": s}


def build_system_prompt(stage: str, language: str, name: str) -> str:
    base = (
        f"You are an AI technical recruiter. "
        f"CRITICAL: Respond ONLY in {language}. "
        f"Be professional, warm, and empathetic. "
        f"You are interviewing {name} — use their name naturally. "
        f"Do NOT solve coding questions for the candidate; stay focused on the interview.\n"
    )
    if stage == "gathering":
        return base + (
            f"OBJECTIVE: Gather these details: {', '.join(REQUIRED_FIELDS)}. "
            "Ask 1-2 items at a time. Acknowledge answers contextually. "
            "Once ALL details are collected, append the exact token TRANSITION_TO_TECH "
            "on its own line at the very end of your message, then ask if they are ready "
            "for technical questions based on their stack."
        )
    elif stage == "tech_questions":
        return base + (
            "OBJECTIVE: Ask 3-5 targeted technical questions based on the candidate's "
            "declared tech stack, strictly one at a time. Briefly evaluate each answer "
            "before proceeding. Once all questions are covered, append the exact token "
            "END_INTERVIEW on its own line at the end, thank the candidate, and tell "
            "them a recruiter will be in touch."
        )
    else:
        return base + "The interview has ended. Politely say goodbye."


def build_contents(messages: list, candidate_name: str) -> list:
    contents = [
        types.Content(
            role="user",
            parts=[types.Part(text=f"Hi, I am {candidate_name}. I am ready to begin my interview.")],
        )
    ]
    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        contents.append(
            types.Content(role=role, parts=[types.Part(text=m["content"])])
        )
    return contents


def persist_session(db, session_id: str):
    """Save current in-memory session state to Supabase after every message."""
    s = sessions.get(session_id)
    if s:
        crud.save_session_state(db, s["interview_id"], json.dumps(s))


# ============================================================
# Pydantic models
# ============================================================

class StartRequest(BaseModel):
    name: str
    email: str
    role: str
    language: str = "English"


class MessageRequest(BaseModel):
    message: str


# ============================================================
# Routes
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/session/start")
async def start_session(req: StartRequest):
    """
    Email-based session logic:
      Case 1 — new email           : create fresh session
      Case 2 — completed interview : block, already participated
      Case 3 — in-progress         : restore and resume
    """
    db = SessionLocal()
    try:
        candidate = crud.get_candidate_by_email(db, req.email)

        if candidate:
            interview = crud.get_latest_interview(db, candidate.id)

            if interview:
                # ── Case 2: already finished ──────────────────────────────
                if interview.status == "Completed":
                    return {
                        "status": "already_participated",
                        "message": (
                            f"Hi {candidate.name}! You have already completed your interview "
                            f"for the {interview.job_role} role. Our recruiting team will be "
                            f"in touch with you shortly. Thank you for your interest! 🎉"
                        ),
                    }

                # ── Case 3: in-progress — check in-memory first ───────────
                existing_sid = email_to_session.get(req.email)
                if existing_sid and existing_sid in sessions:
                    s = sessions[existing_sid]
                    return {
                        "status": "resumed",
                        "session_id": existing_sid,
                        "candidate_name": s["candidate_name"],
                        "role": s["role"],
                        "language": s["language"],
                        "stage": s["stage"],
                        "messages": s["messages"],
                        "sentiment": s["sentiment"],
                        "q_count": s["q_count"],
                    }

                # Server restarted — rebuild from Supabase JSON
                raw = crud.get_session_state(db, interview.id)
                if raw:
                    restored = json.loads(raw)
                    new_sid = str(uuid.uuid4())
                    sessions[new_sid] = restored
                    email_to_session[req.email] = new_sid
                    return {
                        "status": "resumed",
                        "session_id": new_sid,
                        "candidate_name": restored["candidate_name"],
                        "role": restored["role"],
                        "language": restored["language"],
                        "stage": restored["stage"],
                        "messages": restored["messages"],
                        "sentiment": restored["sentiment"],
                        "q_count": restored["q_count"],
                    }

        # ── Case 1: brand new candidate ───────────────────────────────────
        if not candidate:
            candidate = crud.create_candidate(db, req.name, req.email)

        interview  = crud.create_interview(db, candidate.id, req.role)
        session_id = str(uuid.uuid4())
        greeting   = (
            f"Hello {req.name}! Welcome. I'm your AI technical interviewer today. "
            f"Let's start with some background — could you tell me about your years of experience "
            f"and your current location?"
        )

        session_data = {
            "interview_id": interview.id,
            "email": req.email,
            "candidate_name": req.name,
            "role": req.role,
            "language": req.language,
            "stage": "gathering",
            "messages": [{"role": "model", "content": greeting}],
            "sentiment": {"label": "Neutral", "polarity": 0.0, "subjectivity": 0.0},
            "q_count": 0,
        }

        sessions[session_id]          = session_data
        email_to_session[req.email]   = session_id

        crud.log_chat_message(db, interview.id, "Gemini", greeting)
        persist_session(db, session_id)

        return {
            "status": "created",
            "session_id": session_id,
            "candidate_name": req.name,
            "role": req.role,
            "language": req.language,
            "stage": "gathering",
            "messages": [{"role": "model", "content": greeting}],
            "sentiment": {"label": "Neutral", "polarity": 0.0, "subjectivity": 0.0},
            "q_count": 0,
        }

    finally:
        db.close()


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Restore session on tab reload via localStorage session_id."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found or expired.")
    s = sessions[session_id]
    return {
        "candidate_name": s["candidate_name"],
        "role": s["role"],
        "language": s.get("language", "English"),
        "stage": s["stage"],
        "messages": s["messages"],
        "sentiment": s["sentiment"],
        "q_count": s["q_count"],
    }


@app.post("/api/session/{session_id}/message")
async def send_message(session_id: str, req: MessageRequest):
    """Send a candidate message and receive the AI reply."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found or expired.")

    s  = sessions[session_id]
    db = SessionLocal()

    try:
        text = req.message.strip()
        if not text:
            raise HTTPException(status_code=400, detail="Empty message.")

        sentiment = analyze_sentiment(text)
        s["sentiment"] = sentiment
        s["messages"].append({"role": "user", "content": text})
        crud.log_chat_message(db, s["interview_id"], "User", text)

        # Exit shortcut
        if any(k in text.lower() for k in EXIT_KEYWORDS) or s["stage"] == "ended":
            farewell = (
                "Thank you for your time today! Our recruiting team will review your profile "
                "and be in touch soon. Best of luck! 👋"
            )
            s["messages"].append({"role": "model", "content": farewell})
            s["stage"] = "ended"
            crud.log_chat_message(db, s["interview_id"], "Gemini", farewell)
            crud.update_interview_metrics(db, s["interview_id"], score=0, sentiment=sentiment["label"])
            crud.mark_interview_completed(db, s["interview_id"])
            persist_session(db, session_id)
            return {"reply": farewell, "stage": "ended", "sentiment": sentiment}

        # Call Gemini
        contents = build_contents(s["messages"], s["candidate_name"])
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=build_system_prompt(
                    s["stage"], s["language"], s["candidate_name"]
                ),
                temperature=0.4,
            ),
        )

        reply: str = response.text

        if "TRANSITION_TO_TECH" in reply:
            s["stage"] = "tech_questions"
            # s["tech_tags"] = extract_tech_tags(s["messages"])
            reply = reply.replace("TRANSITION_TO_TECH", "").strip()

        if "END_INTERVIEW" in reply:
            s["stage"] = "ended"
            reply = reply.replace("END_INTERVIEW", "").strip()
            crud.update_interview_metrics(db, s["interview_id"], score=85, sentiment=sentiment["label"])
            crud.mark_interview_completed(db, s["interview_id"])

        if s["stage"] == "tech_questions":
            s["q_count"] += 1

        s["messages"].append({"role": "model", "content": reply})
        crud.log_chat_message(db, s["interview_id"], "Gemini", reply)

        # Persist to DB after every message so server restarts lose nothing
        persist_session(db, session_id)

        return {
            "reply": reply,
            "stage": s["stage"],
            "sentiment": sentiment,
            "q_count": s["q_count"],
        }

    except Exception as exc:
        err = str(exc).lower()
        if "429" in err or "quota" in err or "rate limit" in err:
            raise HTTPException(
                status_code=429,
                detail="Rate limit hit. Please wait 60 seconds and try again.",
            )
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        db.close()
