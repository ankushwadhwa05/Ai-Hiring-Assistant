import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime
import os
# 1. Try to get the URL from Docker's environment variables
DATABASE_URL = os.environ.get("DATABASE_URL")

# 2. If it's not in the environment, fallback to Streamlit secrets (for local testing)
if not DATABASE_URL:
    try:
        DATABASE_URL = st.secrets["DATABASE_URL"]
    except Exception:
        pass

if not DATABASE_URL:
    raise ValueError("Database URL is missing!")
# 2. Set up the SQLAlchemy Engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 3. Define the Database Tables
class Candidate(Base):
    __tablename__ = "candidates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True)
    resume_summary = Column(Text)
    applied_date = Column(DateTime, default=datetime.datetime.utcnow)

class Interview(Base):
    __tablename__ = "interviews"
    
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    job_role = Column(String)
    technical_score = Column(Integer, default=0)
    sentiment = Column(String, default="Neutral")
    status = Column(String, default="In Progress")
    session_state = Column(String, nullable=True) 

    
class ChatLog(Base):
    __tablename__ = "chat_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"))
    sender = Column(String)  # 'User' or 'Gemini'
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

# 4. Function to create the tables in Supabase
def init_db():
    Base.metadata.create_all(bind=engine)

# Get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()