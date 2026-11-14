from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from profile_manager import save_candidate_profile
from utils.batch_analyzer import analyze_jobs_for_candidate
from utils.report_generator import generate_candidate_report
from utils.application_tracker import update_application_status


profile = save_candidate_profile(
    name="Demo Candidate",
    skills=[
        "Java",
        "Spring Boot",
        "Microservices",
        "REST API",
        "PostgreSQL",
        "Docker"
    ],
    experience_years=5,
    preferred_role="Senior Java Developer",
    preferred_location="Chennai"
)

candidate_id = profile["id"]

print("Candidate ID:", candidate_id)

result = analyze_jobs_for_candidate(
    candidate_id=candidate_id,
    max_jobs=3,
    min_score=60,
    top_n=3
)

print("Analysis completed.")
print("Successful:", result["successfully_analyzed"])

top_matches = result["top_matches"]

if top_matches:
    job_id = top_matches[0]["job_id"]

    application = update_application_status(
        candidate_id=candidate_id,
        job_id=job_id,
        status="Saved",
        notes="Saved for review"
    )

    print("Application:", application["status"])

report = generate_candidate_report(
    candidate_id=candidate_id,
    min_score=60
)

print("Final report:")
print(report)