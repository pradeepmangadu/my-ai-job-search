import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.batch_analyzer import batch_analyze_jobs


candidate_skills = [
    "Java",
    "Spring Boot",
    "Microservices",
    "REST API",
    "SQL",
    "PostgreSQL",
    "Docker"
]


result = batch_analyze_jobs(
    candidate_skills=candidate_skills,
    max_jobs=3,
    min_score=60,
    top_n=2
)


print(
    json.dumps(
        result,
        indent=2
    )
)