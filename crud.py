from sqlalchemy.orm import Session
from database import Candidate, Interview, ChatLog

# 1. Register a New Candidate
def create_candidate(db: Session, name: str, email: str, resume_summary: str = ""):
    # Check if candidate already exists to avoid duplicates
    existing_candidate = db.query(Candidate).filter(Candidate.email == email).first()
    if existing_candidate:
        return existing_candidate
        
    db_candidate = Candidate(name=name, email=email, resume_summary=resume_summary)
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    return db_candidate

# 2. Start a New Interview Session
def create_interview(db: Session, candidate_id: int, job_role: str):
    db_interview = Interview(
        candidate_id=candidate_id, 
        job_role=job_role,
        status="In Progress" # You can add this column to your database.py model later
    )
    db.add(db_interview)
    db.commit()
    db.refresh(db_interview)
    return db_interview

# 3. Log Every Single Chat Message
def log_chat_message(db: Session, interview_id: int, sender: str, message: str):
    db_chat = ChatLog(
        interview_id=interview_id,
        sender=sender,
        message=message
    )
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    return db_chat

# 4. Update Final Scores and Sentiment (Called at the end of the interview)
def update_interview_metrics(db: Session, interview_id: int, score: int, sentiment: str):
    db_interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if db_interview:
        db_interview.technical_score = score
        db_interview.sentiment = sentiment
        db_interview.status = "Completed"
        db.commit()
        db.refresh(db_interview)
    return db_interview

# ── Candidate ─────────────────────────────────────────────────────────────

def get_candidate_by_email(db: Session, email: str):
    """Return the Candidate row for this email, or None if not found."""
    return db.query(Candidate).filter(Candidate.email == email).first()


# ── Interview ─────────────────────────────────────────────────────────────

def get_latest_interview(db: Session, candidate_id: int):
    """Return the most recent Interview row for a candidate, or None."""
    return (
        db.query(Interview)
        .filter(Interview.candidate_id == candidate_id)
        .order_by(Interview.id.desc())
        .first()
    )


def mark_interview_completed(db: Session, interview_id: int):
    """Flip interview.status to 'Completed' so duplicate emails are blocked."""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if interview:
        interview.status = "Completed"
        db.commit()


# ── Session state (JSON blob) ─────────────────────────────────────────────

def save_session_state(db: Session, interview_id: int, state_json: str):
    """
    Upsert the full session dict (serialised as JSON) onto the interview row.
    Requires the `session_state` TEXT/JSONB column — see migration below.
    """
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if interview:
        interview.session_state = state_json
        db.commit()


def get_session_state(db: Session, interview_id: int):
    """Return the raw JSON string, or None if not set."""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if interview and hasattr(interview, "session_state"):
        return interview.session_state
    return None
