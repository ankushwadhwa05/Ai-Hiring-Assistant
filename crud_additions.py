# =========================================================================
# ADD THESE FUNCTIONS TO YOUR EXISTING crud.py
# =========================================================================
# These support:
#   - email uniqueness check
#   - interview status tracking
#   - full session state persistence (JSON) for server-restart resilience
# =========================================================================

from sqlalchemy.orm import Session
from models import Candidate, Interview   # adjust import to match your file


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
    """Flip interview.status to 'completed' so duplicate emails are blocked."""
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if interview:
        interview.status = "completed"
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
