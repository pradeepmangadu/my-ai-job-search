from enum import Enum

from pydantic import BaseModel, Field


class Recommendation(str, Enum):
    STRONG_MATCH = "Strong Match"
    GOOD_MATCH = "Good Match"
    WEAK_MATCH = "Weak Match"
    NO_MATCH = "No Match"


class JobAnalysis(BaseModel):

    match_score: int = Field(
        ge=0,
        le=100
    )

    matched_skills: list[str]

    missing_skills: list[str]

    strengths: list[str]

    interview_topics: list[str]

    recommendation: Recommendation

    summary: str