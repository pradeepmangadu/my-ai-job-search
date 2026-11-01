from database import (
    get_jobs_for_analysis,
    save_batch_job_analysis
)

from utils.job_analyser import analyze_job


def batch_analyze_jobs(
    candidate_skills: list[str],
    max_jobs: int = 5,
    min_score: int = 60,
    top_n: int = 5
) -> dict:

    # Validate inputs before spending API credits
    if not candidate_skills:
        raise ValueError("Candidate skills cannot be empty.")

    if not 1 <= max_jobs <= 20:
        raise ValueError("max_jobs must be between 1 and 20.")

    if not 0 <= min_score <= 100:
        raise ValueError("min_score must be 0 to 100.")

    if not 1 <= top_n <= 20:
        raise ValueError("top_n must be between 1 and 20.")

    # STEP 1: Fetch jobs from Supabase
    jobs = get_jobs_for_analysis(max_jobs)

    results = []
    failed_jobs = []

    total_input_tokens = 0
    total_output_tokens = 0
    total_cost = 0.0

    # STEP 2: Analyze each job
    for job in jobs:

        print(f"Analyzing job ID: {job['id']}")

        try:
            result = analyze_job(
                job_title=job["title"],
                job_description=job["description"],
                candidate_skills=candidate_skills
            )

            analysis = result.analysis
            usage = result.usage

            # Record API usage before database saving.
            total_input_tokens += usage.input_tokens
            total_output_tokens += usage.output_tokens
            total_cost += usage.estimated_cost_usd

            # STEP 3: Save to Supabase
            analysis_id = save_batch_job_analysis(
                job_id=job["id"],
                result=result
            )

            # STEP 4: Collect result
            results.append({
                "job_id": job["id"],
                "title": job["title"],
                "company": job["company"],
                "analysis_id": analysis_id,
                "match_score": analysis.match_score,
                "recommendation": analysis.recommendation.value,
                "matched_skills": analysis.matched_skills,
                "missing_skills": analysis.missing_skills,
                "summary": analysis.summary
            })

        except Exception as error:

            # Continue processing other jobs
            failed_jobs.append({
                "job_id": job["id"],
                "error": type(error).__name__
            })

            print(
                f"Failed job {job['id']}: "
                f"{type(error).__name__}"
            )

    # STEP 5: Sort by match score
    ranked_jobs = sorted(
        results,
        key=lambda job: job["match_score"],
        reverse=True
    )

    # STEP 6: Filter by minimum score
    filtered_jobs = [
        job for job in ranked_jobs
        if job["match_score"] >= min_score
    ]

    # STEP 7: Return only top N
    top_jobs = filtered_jobs[:top_n]

    return {
        "total_jobs_fetched": len(jobs),
        "successfully_analyzed": len(results),
        "failed_count": len(failed_jobs),
        "jobs_above_threshold": len(filtered_jobs),
        "minimum_match_score": min_score,
        "top_matches": top_jobs,
        "failed_jobs": failed_jobs,
        "api_usage": {
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "total_tokens": (
                total_input_tokens + total_output_tokens
            ),
            "estimated_cost_usd": round(
                total_cost, 6
            )
        }
    }
	