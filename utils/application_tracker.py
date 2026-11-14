from database import get_connection
from profile_manager import get_candidate_profile
from psycopg2.extras import RealDictCursor


VALID_STATUSES = {
    "Saved",
    "Applied",
    "Interviewing",
    "Rejected",
    "Offered"
}


def update_application_status(
    candidate_id: int,
    job_id: int,
    status: str,
    notes: str = ""
) -> dict:

    status_by_key = {
        valid_status.casefold(): valid_status
        for valid_status in VALID_STATUSES
    }
    normalized_status = status_by_key.get(status.strip().casefold())

    if normalized_status is None:
        raise ValueError(
            f"Invalid status: {status}"
        )

    status = normalized_status

    if get_candidate_profile(candidate_id) is None:
        raise ValueError("Candidate not found.")

    query = """
        INSERT INTO job_applications (
            candidate_id,
            job_id,
            status,
            notes,
            applied_at
        )
        VALUES (
            %s, %s, %s, %s,
            CASE
                WHEN %s = 'Applied'
                THEN NOW()
                ELSE NULL
            END
        )
        ON CONFLICT (candidate_id, job_id)
        DO UPDATE SET
            status = EXCLUDED.status,
            notes = EXCLUDED.notes,
            updated_at = NOW(),
            applied_at = CASE
                WHEN EXCLUDED.status = 'Applied'
                THEN COALESCE(
                    job_applications.applied_at,
                    NOW()
                )
                ELSE job_applications.applied_at
            END
        RETURNING *
    """

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                query,
                (
                    candidate_id,
                    job_id,
                    status,
                    notes,
                    status
                )
            )
            return cursor.fetchone()


def list_applications(candidate_id: int):

    query = """
        SELECT
            a.id,
            a.job_id,
            j.title,
            j.company,
            a.status,
            a.notes,
            a.applied_at,
            a.updated_at
        FROM job_applications a
        JOIN jobs j ON j.id = a.job_id
        WHERE a.candidate_id = %s
        ORDER BY a.updated_at DESC
    """

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                query,
                (candidate_id,)
            )
            return cursor.fetchall()
