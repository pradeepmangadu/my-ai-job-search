from psycopg2.extras import Json, RealDictCursor
from database import get_connection


def save_candidate_profile(
    name: str,
    skills: list[str],
    experience_years: float = 0,
    preferred_role: str = "",
    preferred_location: str = ""
) -> dict:

    if not name.strip() or not skills:
        raise ValueError("Name and skills are required.")

    if experience_years < 0:
        raise ValueError("Experience cannot be negative.")

    query = """
        INSERT INTO candidate_profiles (
            name, skills, experience_years,
            preferred_role, preferred_location
        )
        VALUES (%s, %s, %s, %s, %s)
        RETURNING *
    """

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (
                name.strip(),
                Json(skills),
                experience_years,
                preferred_role,
                preferred_location
            ))
            return cursor.fetchone()


def get_candidate_profile(candidate_id: int):

    query = """
        SELECT *
        FROM candidate_profiles
        WHERE id = %s
    """

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (candidate_id,))
            return cursor.fetchone()


def update_candidate_skills(
    candidate_id: int,
    skills: list[str]
):

    if not skills:
        raise ValueError("Skills cannot be empty.")

    query = """
        UPDATE candidate_profiles
        SET skills = %s,
            updated_at = NOW()
        WHERE id = %s
        RETURNING *
    """

    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                query,
                (Json(skills), candidate_id)
            )
            return cursor.fetchone()