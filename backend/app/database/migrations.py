import psycopg2
from app.database.connection import get_db_connection
from app.utils.logging import logger

MIGRATIONS_SQL = """
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Jobs Table
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recruiter_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    extracted_metadata JSONB,
    cleaned_jd TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Candidates Table
CREATE TABLE IF NOT EXISTS candidates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recruiter_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    email TEXT,
    resume_url TEXT,
    original_pdf_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Resume Metadata Table
CREATE TABLE IF NOT EXISTS resume_metadata (
    candidate_id UUID PRIMARY KEY REFERENCES candidates(id) ON DELETE CASCADE,
    skills TEXT[] DEFAULT '{}',
    experience_years NUMERIC DEFAULT 0,
    education JSONB DEFAULT '[]',
    companies TEXT[] DEFAULT '{}',
    certifications TEXT[] DEFAULT '{}',
    projects JSONB DEFAULT '[]',
    achievements TEXT[] DEFAULT '{}',
    parsed_json JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Candidate Embeddings Reference Table
CREATE TABLE IF NOT EXISTS candidate_embeddings (
    candidate_id UUID PRIMARY KEY REFERENCES candidates(id) ON DELETE CASCADE,
    chroma_id TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Ranking History Table
CREATE TABLE IF NOT EXISTS ranking_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    candidate_id UUID REFERENCES candidates(id) ON DELETE CASCADE,
    recruiter_id UUID REFERENCES users(id) ON DELETE CASCADE,
    overall_score NUMERIC NOT NULL,
    semantic_score NUMERIC NOT NULL,
    technical_score NUMERIC NOT NULL,
    domain_score NUMERIC NOT NULL,
    growth_score NUMERIC NOT NULL,
    bias_free_eval JSONB NOT NULL,
    full_eval JSONB NOT NULL,
    explainability JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Enable Row Level Security (RLS) on all tables if not already enabled
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE resume_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE candidate_embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE ranking_history ENABLE ROW LEVEL SECURITY;

-- Attempt to drop existing policies to avoid conflicts, then recreate
-- We wrap in DO blocks to ignore errors if the policy doesn't exist
DO $$
BEGIN
    DROP POLICY IF EXISTS user_self_access ON users;
    DROP POLICY IF EXISTS jobs_owner_access ON jobs;
    DROP POLICY IF EXISTS candidates_owner_access ON candidates;
    DROP POLICY IF EXISTS resume_metadata_owner_access ON resume_metadata;
    DROP POLICY IF EXISTS candidate_embeddings_owner_access ON candidate_embeddings;
    DROP POLICY IF EXISTS ranking_history_owner_access ON ranking_history;
EXCEPTION
    WHEN others THEN NULL;
END $$;

-- Add RLS Policies (Allow all requests for now, or match owner IDs.
-- Since FastAPI connects as a superuser/service role or via single PostgreSQL client,
-- these policies will be active but can allow reading/writing based on query structures.)
CREATE POLICY user_self_access ON users FOR ALL USING (TRUE);
CREATE POLICY jobs_owner_access ON jobs FOR ALL USING (TRUE);
CREATE POLICY candidates_owner_access ON candidates FOR ALL USING (TRUE);
CREATE POLICY resume_metadata_owner_access ON resume_metadata FOR ALL USING (TRUE);
CREATE POLICY candidate_embeddings_owner_access ON candidate_embeddings FOR ALL USING (TRUE);
CREATE POLICY ranking_history_owner_access ON ranking_history FOR ALL USING (TRUE);
"""

def run_migrations():
    """Execute the database migrations to create schemas in Supabase."""
    logger.info("Starting database migration on Supabase...")
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(MIGRATIONS_SQL)
        conn.commit()
        logger.info("Database migrations completed successfully!")
        return True
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Migration failed: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    run_migrations()
