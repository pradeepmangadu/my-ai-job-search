import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.job_analyser import analyze_job


analysis = analyze_job(

    job_title="Senior Java Developer",

    job_description="""
    Looking for an experienced Java developer.

    Required skills:

    Java
    Spring Boot
    Microservices
    REST APIs
    PostgreSQL
    Docker
    Kubernetes
    AWS
    CI/CD
    """,

    candidate_skills=[
        "Java",
        "Spring Boot",
        "Microservices",
        "REST API",
        "PostgreSQL",
        "Docker"
    ]
)


print(
    analysis.model_dump_json(indent=2)
)