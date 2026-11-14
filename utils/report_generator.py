from collections import Counter
from utils.application_tracker import list_applications
from database import (
    get_connection,
    get_candidate_top_jobs
)
from profile_manager import get_candidate_profile


def get_skill_gap_report(
    candidate_id: int,
    min_score: int = 0,
    limit: int = 10
) -> dict:

    jobs = get_candidate_top_jobs(
        candidate_id,
        min_score,
        limit
    )

    counts = Counter()
    display_names = {}

    for job in jobs:
        # Count each missing skill once per job.
        unique_skills = {
            skill.strip()
            for skill in job["missing_skills"] or []
            if skill.strip()
        }

        for skill in unique_skills:
            key = skill.casefold()
            counts[key] += 1
            display_names.setdefault(key, skill)

    gaps = [
        {
            "skill": display_names[key],
            "missing_in_jobs": count
        }
        for key, count in counts.most_common()
    ]

    return {
        "candidate_id": candidate_id,
        "jobs_considered": len(jobs),
        "skill_gaps": gaps
    }



def generate_candidate_report(
    candidate_id: int,
    min_score: int = 60
) -> dict:

    profile = get_candidate_profile(candidate_id)

    if profile is None:
        raise ValueError("Candidate not found.")

    top_jobs = get_candidate_top_jobs(
        candidate_id=candidate_id,
        min_score=min_score,
        limit=5
    )

    skill_gaps = get_skill_gap_report(
        candidate_id=candidate_id,
        min_score=min_score,
        limit=10
    )

    applications = list_applications(candidate_id)

    return {
        "candidate": {
            "id": profile["id"],
            "name": profile["name"],
            "skills": profile["skills"],
            "preferred_role": profile["preferred_role"],
            "preferred_location": profile["preferred_location"]
        },
        "top_matching_jobs": top_jobs,
        "skill_gap_analysis": skill_gaps,
        "applications": applications,
        "summary": {
            "top_jobs_count": len(top_jobs),
            "tracked_applications": len(applications)
        }
    }