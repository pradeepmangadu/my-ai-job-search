import os

from dotenv import load_dotenv
from openai import OpenAI

from database import save_job_analysis
from database import get_job_details
from models import JobAnalysis


load_dotenv()


client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-5.6-luna"
)


def analyze_job(
    job_title: str,
    job_description: str,
    candidate_skills: list[str]
) -> JobAnalysis:

    skills = ", ".join(candidate_skills)

    user_prompt = f"""
Job Title:
{job_title}

Job Description:
{job_description}

Candidate Skills:
{skills}

Analyze the candidate's skill alignment with this job.

Identify:

1. Matching skills
2. Important missing skills
3. Candidate strengths
4. Topics to prepare for the interview
5. Overall skill match score from 0 to 100

Only use information explicitly provided above.

Do not invent candidate skills or experience.
"""

    response = client.responses.parse(

        model=MODEL,

        instructions="""
You are an AI job analysis assistant.

Compare the candidate's explicitly provided skills
against the supplied job description.

Return a practical analysis.

Do not assume skills or experience that have not
been provided.
""",

        input=user_prompt,

        text_format=JobAnalysis
    )

    return response.output_parsed


def analyze_saved_job(
    job_id: int,
    candidate_skills: list[str]
):

    # Step 1:
    # Get job from Supabase PostgreSQL

    job = get_job_details(job_id)

    if not job:

        return {
            "success": False,
            "message": f"Job ID {job_id} not found."
        }


    # Step 2:
    # Send job to ChatGPT

    analysis = analyze_job(

        job_title=job["title"],

        job_description=job["description"],

        candidate_skills=candidate_skills
    )


     # -------------------------
    # 3. SAVE ANALYSIS
    # -------------------------

    analysis_id = save_job_analysis(
        job_id,
        analysis
    )


    # -------------------------
    # 4. RETURN RESULT
    # -------------------------

    return {

        "success": True,

        "job": {

            "id": job["id"],

            "title": job["title"],

            "company": job["company"]
        },

        "analysis_id": analysis_id,

        "analysis": analysis.model_dump()
    }

