import os
from openai import OpenAI
from dotenv import load_dotenv
from enum import Enum
from pydantic import BaseModel, Field

load_dotenv()

client = OpenAI(api_key = os.getenv("OPENAI_API_KEY"))

class Recommendation(str, Enum):
    STRONG_MATCH = "Strong Match"
    GOOD_MATCH = "Good Match"
    WEAK_MATCH = "Weak Match"
    NO_MATCH = "No Match"

class JobAnalysis(BaseModel):
    match_score: int = Field(ge=0, le=100)
    matched_skills: list[str]
    missing_skills: list[str]
    recommendation: Recommendation

input_text = """
Job Requirements:


Candidate Skills:




"""

response = client.responses.parse(
    model  = "gpt-5.6-luna",
    instructions  = """
    You are an AI Job Analyzer.

    Compare the candidate technical skills alone  with the job requirements.

    Calculate a match score from 0 to 100.

    Identify:
    - skills that match
    - important required skills that are missing
    - a short recommendation for the candidate based on match score if match score is above 80, return "Strong Match", if match score is between 60 and 80, return "Good Match", if match score is between 40 and 60, return "Weak Match" if match score is 0 or below 40, return "No Match".
""",
    input  = input_text,
    text_format  = JobAnalysis,
)

result = response.output_parsed

print(result)

print("Input:", response.usage.input_tokens)
print("Output:", response.usage.output_tokens)
print("Total:", response.usage.total_tokens)


print("Match Score:", result.match_score)
print("Matched Skills:", result.matched_skills)
print("Missing Skills:", result.missing_skills)
print("Recommendation:", result.recommendation)

