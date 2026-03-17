# =========================================================================
# Run this script ONCE to add the two new columns to your Supabase DB.
# After running, you can delete this file.
#
#   python database_migration.py
# =========================================================================

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in .env")

engine = create_engine(DATABASE_URL)

migrations = [
    # 1. Track whether an interview is in-progress or completed
    """
    ALTER TABLE interviews
    ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'in_progress';
    """,

    # 2. Store full session JSON so server restarts don't lose state
    """
    ALTER TABLE interviews
    ADD COLUMN IF NOT EXISTS session_state TEXT;
    """,
]

with engine.connect() as conn:
    for sql in migrations:
        conn.execute(text(sql))
        conn.commit()
    print("✅ Migration complete — both columns added to 'interviews' table.")
