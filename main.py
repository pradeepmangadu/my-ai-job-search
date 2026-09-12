import json
import os
from pathlib import Path
from typing import Any

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import Json, RealDictCursor
from mcp.server import MCPServer

load_dotenv(Path(__file__).with_name(".env"))


# ============================================================
# MCP SERVER
# ============================================================

mcp = MCPServer("AI Job Search")


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


# ============================================================
# TOOL 1: SEARCH JOBS
# ============================================================

@mcp.tool()
def search_jobs(
    keyword: str = "",
    location: str = "",
    work_mode: str = ""
) -> list:
    """
    Search jobs using keyword, location and work mode.
    """
    connection = get_connection()
    cursor = connection.cursor(cursor_factory=RealDictCursor)

    conditions = []
    params: list[Any] = []

    if keyword:
        keyword_value = f"%{keyword}%"
        conditions.append(
            "(title ILIKE %s OR company ILIKE %s OR description ILIKE %s OR skills::text ILIKE %s)"
        )
        params.extend([keyword_value, keyword_value, keyword_value, keyword_value])

    if location:
        location_value = f"%{location}%"
        conditions.append("location ILIKE %s")
        params.append(location_value)

    if work_mode:
        work_mode_value = f"%{work_mode}%"
        conditions.append("work_mode ILIKE %s")
        params.append(work_mode_value)

    query = "SELECT * FROM jobs"
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY id"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    connection.close()

    return [normalize_job(dict(row)) for row in rows]


# ============================================================
# TOOL 2: GET JOB DETAILS
# ============================================================

@mcp.tool()
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


# ============================================================
# TOOL 3: SAVE JOB
# ============================================================

@mcp.tool()
def save_job(job_id: int) -> dict:
    """
    Save a job for later application.
    """
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM jobs WHERE id = %s", (job_id,))
    job = cursor.fetchone()

    if job is None:
        connection.close()
        return {"success": False, "message": f"Job {job_id} does not exist."}

    cursor.execute(
        "UPDATE jobs SET status = 'SAVED', updated_at = NOW() WHERE id = %s",
        (job_id,),
    )
    connection.commit()
    connection.close()

    return {"success": True, "message": f"Job {job_id} has been saved."}


# ============================================================
# TOOL 4: GET SAVED JOBS
# ============================================================

@mcp.tool()
def get_tracked_jobs() -> list:
    """
    Get all jobs that are being tracked.
    """
    connection = get_connection()
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "SELECT * FROM jobs WHERE status <> 'NEW' ORDER BY updated_at DESC"
    )
    rows = cursor.fetchall()
    connection.close()

    return [normalize_job(dict(row)) for row in rows]


# ============================================================
# TOOL 5: UPDATE JOB STATUS
# ============================================================

@mcp.tool()
def update_job_status(
    job_id: int,
    status: str
) -> dict:
    """
    Update the tracking status of a job.

    Allowed statuses:
    NEW, SAVED, APPLIED, INTERVIEW, REJECTED, OFFER, ARCHIVED
    """
    allowed_statuses = {
        "NEW",
        "SAVED",
        "APPLIED",
        "INTERVIEW",
        "REJECTED",
        "OFFER",
        "ARCHIVED",
    }

    status = status.upper()

    if status not in allowed_statuses:
        return {
            "success": False,
            "message": (
                f"Invalid status '{status}'. "
                f"Allowed values: {sorted(allowed_statuses)}"
            )
        }

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM jobs WHERE id = %s", (job_id,))
    job = cursor.fetchone()

    if job is None:
        connection.close()
        return {"success": False, "message": f"Job {job_id} does not exist."}

    cursor.execute(
        "UPDATE jobs SET status = %s, updated_at = NOW() WHERE id = %s",
        (status, job_id),
    )
    connection.commit()
    connection.close()

    return {"success": True, "message": f"Job {job_id} status changed to {status}."}


# ============================================================
# TOOL 6: ADD JOB NOTE
# ============================================================

@mcp.tool()
def add_job_note(
    job_id: int,
    note: str
) -> dict:
    """
    Add a note to a job.
    """
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM jobs WHERE id = %s", (job_id,))
    job = cursor.fetchone()

    if job is None:
        connection.close()
        return {"success": False, "message": f"Job {job_id} does not exist."}

    cursor.execute(
        "UPDATE jobs SET notes = %s, updated_at = NOW() WHERE id = %s",
        (note, job_id),
    )
    connection.commit()
    connection.close()

    return {"success": True, "message": f"Note added to job {job_id}."}


# ============================================================
# TOOL 7: GET APPLICATION STATISTICS
# ============================================================

@mcp.tool()
def get_application_stats() -> dict:
    """
    Get statistics about job application tracking.
    """
    connection = get_connection()
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT status, COUNT(*) AS count FROM jobs GROUP BY status")
    rows = cursor.fetchall()
    connection.close()

    stats: dict[str, int] = {}
    for row in rows:
        stats[row["status"]] = row["count"]

    return {
        "total_jobs": sum(stats.values()),
        "status_breakdown": stats,
    }


# ============================================================
# START SERVER
# ============================================================

initialize_database()
import_jobs_from_json()


if __name__ == "__main__":
    mcp.run()
