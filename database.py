
import json
import os
from pathlib import Path
from typing import Any

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import Json, RealDictCursor

load_dotenv(Path(__file__).with_name(".env"))

# ============================================================
# FILE PATHS
# ============================================================

BASE_DIR = Path(__file__).parent
JOBS_JSON_FILE = BASE_DIR / "jobs.json"

# ============================================================
# POSTGRES CONFIG
# ============================================================


def get_connection():
    """
    Create a PostgreSQL connection using environment variables.
    """
    conn_url = os.getenv("DATABASE_URL")
    if not conn_url:
        raise RuntimeError(
            "Missing DATABASE_URL"
            "Set a Supabase PostgreSQL connection string."
        )

    return psycopg2.connect(conn_url)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():
    """
    Create the jobs table if it does not already exist.
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            work_mode TEXT,
            experience TEXT,
            skills JSONB DEFAULT '[]'::jsonb,
            salary TEXT,
            description TEXT,
            url TEXT,
            status TEXT DEFAULT 'NEW',
            notes TEXT DEFAULT '',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)

    connection.commit()
    connection.close()


# ============================================================
# NORMALIZATION HELPERS
# ============================================================

def normalize_job(row: dict[str, Any]) -> dict[str, Any]:
    """Convert stored values back into the original app format."""
    job = dict(row)

    if isinstance(job.get("skills"), str):
        try:
            job["skills"] = json.loads(job["skills"])
        except (TypeError, json.JSONDecodeError):
            job["skills"] = []
    elif job.get("skills") is None:
        job["skills"] = []

    return job



# ============================================================
# IMPORT JOBS FROM JSON
# ============================================================

def import_jobs_from_json():
    """
    Import jobs from jobs.json into Postgres.
    This only happens when the database is empty.
    """
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM jobs")
    job_count = cursor.fetchone()[0]

    if job_count > 0:
        connection.close()
        return

    if not JOBS_JSON_FILE.exists():
        connection.close()
        return

    with open(JOBS_JSON_FILE, "r", encoding="utf-8") as file:
        jobs = json.load(file)

    for job in jobs:
        cursor.execute("""
            INSERT INTO jobs (
                id,
                title,
                company,
                location,
                work_mode,
                experience,
                skills,
                salary,
                description,
                url,
                status,
                notes,
                created_at,
                updated_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """, (
            job["id"],
            job["title"],
            job["company"],
            job.get("location", ""),
            job.get("work_mode", ""),
            job.get("experience", ""),
            Json(job.get("skills", [])),
            job.get("salary", ""),
            job.get("description", ""),
            job.get("url", ""),
            "NEW",
            "",
        ))

    connection.commit()
    connection.close()


def get_job_details(job_id: int) -> dict:
    """
    Get complete information about a job using its ID.
    """
    connection = get_connection()
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
    row = cursor.fetchone()
    connection.close()

    if row is None:
        return {"error": f"Job with ID {job_id} was not found."}

    return normalize_job(dict(row))


def save_job_analysis(
    job_id: int,
    analysis
):

    query = """
        INSERT INTO job_analysis
        (
            job_id,
            match_score,
            matched_skills,
            missing_skills,
            strengths,
            interview_topics,
            recommendation,
            summary
        )

        VALUES
        (
            %s,
            %s,
            %s::jsonb,
            %s::jsonb,
            %s::jsonb,
            %s::jsonb,
            %s,
            %s
        )

        RETURNING id
    """


    values = (

        job_id,

        analysis.match_score,

        json.dumps(
            analysis.matched_skills
        ),

        json.dumps(
            analysis.missing_skills
        ),

        json.dumps(
            analysis.strengths
        ),

        json.dumps(
            analysis.interview_topics
        ),

        analysis.recommendation.value,

        analysis.summary
    )


    with get_connection() as conn:

        with conn.cursor(cursor_factory=RealDictCursor) as cursor:

            cursor.execute(
                query,
                values
            )

            result = cursor.fetchone()

            conn.commit()


    return result["id"]