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


class AnalysisUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0


class AnalysisResult(BaseModel):
    analysis: JobAnalysis
    usage: AnalysisUsage



class CandidateProfile(BaseModel):
    id: int
    name: str
    skills: list[str]
    experience_years: float = 0
    preferred_role: str | None = None
    preferred_location: str | None = None


class InterviewQuestion(BaseModel):
    question: str
    topic: str
    difficulty: str
    preparation_hint: str


class InterviewPreparation(BaseModel):
    job_title: str
    preparation_topics: list[str]
    questions: list[InterviewQuestion]