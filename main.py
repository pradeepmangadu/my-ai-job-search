import json
import os
from pathlib import Path
from typing import Any

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import Json, RealDictCursor
from mcp.server.mcpserver import MCPServer
from database import get_candidate_top_jobs, get_connection, get_top_matching_jobs, initialize_database, import_jobs_from_json, normalize_job
from profile_manager import get_candidate_profile, save_candidate_profile, update_candidate_skills
from utils.application_tracker import list_applications, update_application_status
from utils.batch_analyzer import analyze_jobs_for_candidate, batch_analyze_jobs
from utils.interview_preparation import prepare_for_interview
from utils.job_analyser import analyze_saved_job
from utils.report_generator import generate_candidate_report, get_skill_gap_report

load_dotenv(Path(__file__).with_name(".env"))


# ============================================================
# MCP SERVER
# ============================================================

mcp = MCPServer("AI Job Search")

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

    return get_job_details(job_id)


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
    status: str,
    notes: str = ""
) -> dict:
    """
    Update the tracking status of a job.

    Allowed statuses:
    Saved, Applied, Interviewing, Rejected, Offered
    """
    allowed_statuses = {
        "Saved",
        "Applied",
        "Interviewing",
        "Rejected",
        "Offered"
    }

    status_by_key = {
        allowed_status.casefold(): allowed_status
        for allowed_status in allowed_statuses
    }
    normalized_status = status_by_key.get(status.strip().casefold())

    if normalized_status is None:
        return {
            "success": False,
            "message": (
                f"Invalid status '{status}'. "
                f"Allowed values: {sorted(allowed_statuses)}"
            )
        }
    status = normalized_status

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM jobs WHERE id = %s", (job_id,))
    job = cursor.fetchone()

    if job is None:
        connection.close()
        return {"success": False, "message": f"Job {job_id} does not exist."}

    cursor.execute(
        """
        UPDATE jobs
        SET status = %s,
            notes = CASE WHEN %s = '' THEN notes ELSE %s END,
            updated_at = NOW()
        WHERE id = %s
        """,
        (status, notes, notes, job_id),
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
# TOOL: ANALYSE JOB WITH SKILLS
# ============================================================


@mcp.tool()
def analyze_job_with_ai(
    job_id: int,
    candidate_skills: list[str]
) -> dict:
    """
    Analyze a saved job using AI.

    Fetches the job from PostgreSQL,
    compares the job requirements against
    candidate skills using OpenAI,
    saves the analysis in PostgreSQL,
    and returns the result.
    """

    return analyze_saved_job(
        job_id=job_id,
        candidate_skills=candidate_skills
    )


# ============================================================
# TOOL: GET ALL JOBS
# ============================================================

@mcp.tool()
def get_all_jobs() -> list:
    """
    Get all jobs stored in the database.
    """
    connection = get_connection()
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM jobs ORDER BY id")
    rows = cursor.fetchall()
    connection.close()

    return [normalize_job(dict(row)) for row in rows]


@mcp.tool()
def get_previously_analyzed_jobs(
    min_score: int = 60,
    limit: int = 10
) -> list[dict[str, Any]]:
    """
    Get the latest saved analysis for each job scoring at least min_score.

    Returns jobs ordered by match score, highest first. Does not call the AI API.
    """
    return get_top_matching_jobs(
        min_score=min_score,
        limit=limit
    )



@mcp.tool()
def find_best_matching_jobs(
    candidate_skills: list[str],
    max_jobs: int = 5,
    min_score: int = 60,
    top_n: int = 3
) -> dict:
    """
    Analyze multiple stored jobs using the OpenAI API.

    Compares jobs against candidate skills,
    saves AI analysis to Supabase PostgreSQL,
    ranks jobs by skill match score,
    and returns the best matching opportunities.

    This tool makes paid API calls.
    Default batch size is five jobs.
    """

    return batch_analyze_jobs(
        candidate_skills=candidate_skills,
        max_jobs=max_jobs,
        min_score=min_score,
        top_n=top_n
    )



@mcp.tool()
def create_profile(
    name: str,
    skills: list[str],
    experience_years: float = 0,
    preferred_role: str = "",
    preferred_location: str = ""
) -> dict:
    """Create a saved candidate profile."""

    return save_candidate_profile(
        name,
        skills,
        experience_years,
        preferred_role,
        preferred_location
    )


@mcp.tool()
def view_profile(candidate_id: int) -> dict:
    """Retrieve a saved candidate profile."""

    return get_candidate_profile(candidate_id)


@mcp.tool()
def change_candidate_skills(
    candidate_id: int,
    skills: list[str]
) -> dict:
    """Update skills in a candidate profile."""

    return update_candidate_skills(
        candidate_id,
        skills
    )


@mcp.tool()
def find_personalized_jobs(
    candidate_id: int,
    max_jobs: int = 5,
    min_score: int = 60,
    top_n: int = 3
) -> dict:
    """
    Analyze stored jobs using a saved candidate profile.

    Makes paid OpenAI API calls.
    Saves candidate-specific results to Supabase.
    """

    return analyze_jobs_for_candidate(
        candidate_id,
        max_jobs,
        min_score,
        top_n
    )


@mcp.tool()
def view_personalized_jobs(
    candidate_id: int,
    min_score: int = 60,
    limit: int = 5
) -> list[dict]:
    """
    View previously analyzed jobs for a candidate.
    Does not call the OpenAI API.
    """

    return get_candidate_top_jobs(
        candidate_id,
        min_score,
        limit
    )


@mcp.tool()
def analyze_candidate_skill_gaps(
    candidate_id: int,
    min_score: int = 0
) -> dict:
    """Identify common missing skills in analyzed jobs."""

    return get_skill_gap_report(
        candidate_id,
        min_score
    )


@mcp.tool()
def generate_interview_questions(
    candidate_id: int,
    job_id: int,
    question_count: int = 5
) -> dict:
    """
    Generate technical interview questions using OpenAI.
    Makes a paid API call.
    """

    return prepare_for_interview(
        candidate_id,
        job_id,
        question_count
    )


@mcp.tool()
def track_job_application(
    candidate_id: int,
    job_id: int,
    status: str,
    notes: str = ""
) -> dict:
    """Create or update a tracked job application."""

    return update_application_status(
        candidate_id,
        job_id,
        status,
        notes
    )


@mcp.tool()
def view_job_applications(
    candidate_id: int
) -> list[dict]:
    """Retrieve tracked job applications."""

    return list_applications(candidate_id)


@mcp.tool()
def create_final_job_report(
    candidate_id: int,
    min_score: int = 60
) -> dict:
    """
    Generate a consolidated report from stored data.
    No new OpenAI API call is made.
    """

    return generate_candidate_report(
        candidate_id,
        min_score
    )


# ============================================================
# START SERVER
# ============================================================

initialize_database()
import_jobs_from_json()


if __name__ == "__main__":
    mcp.run()
