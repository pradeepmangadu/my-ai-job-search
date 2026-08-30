import json
from pathlib import Path

from mcp.server import MCPServer


# Create MCP server
mcp = MCPServer("AI Job Search")


# Location of our local job dataset
JOBS_FILE = Path(__file__).parent / "jobs.json"


def load_jobs():
    """Load jobs from the local JSON file."""
    with open(JOBS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


@mcp.tool()
def search_jobs(
    keyword: str = "",
    location: str = "",
    work_mode: str = ""
) -> list:
    """
    Search jobs using keyword, location and work mode.

    Args:
        keyword: Search term such as Java, Python, Spring Boot or AWS.
        location: City such as Chennai, Bangalore or Hyderabad.
        work_mode: Remote, Hybrid or On-site.
    """

    jobs = load_jobs()

    keyword = keyword.lower().strip()
    location = location.lower().strip()
    work_mode = work_mode.lower().strip()

    results = []

    for job in jobs:

        searchable_text = (
            job["title"]
            + " "
            + job["company"]
            + " "
            + job["description"]
            + " "
            + " ".join(job["skills"])
        ).lower()

        keyword_match = (
            not keyword
            or keyword in searchable_text
        )

        location_match = (
            not location
            or location in job["location"].lower()
        )

        work_mode_match = (
            not work_mode
            or work_mode in job["work_mode"].lower()
        )

        if keyword_match and location_match and work_mode_match:
            results.append(job)

    return results


@mcp.tool()
def get_job_details(job_id: int) -> dict:
    """
    Get complete information about a job using its ID.
    """

    jobs = load_jobs()

    for job in jobs:
        if job["id"] == job_id:
            return job

    return {
        "error": f"Job with ID {job_id} was not found."
    }


@mcp.tool()
def get_job_stats() -> dict:
    """
    Get basic statistics about the available jobs.
    """

    jobs = load_jobs()

    locations = {}

    for job in jobs:
        location = job["location"]

        locations[location] = locations.get(location, 0) + 1

    return {
        "total_jobs": len(jobs),
        "locations": locations
    }



# --- Resources: data the client can read ---
@mcp.resource("config://app-version")
def get_version() -> str:
    """Return the app version."""
    return "1.0.0"


# --- Prompts: reusable templates ---
@mcp.prompt()
def job_recommendation_prompt(skills: str, experience: str, location: str) -> str:
    """Generate a prompt to recommend jobs based on candidate profile."""
    return f"""You are a career advisor. Based on the following candidate profile, 
recommend suitable job opportunities and career growth strategies:

Skills: {skills}
Experience Level: {experience}
Preferred Location: {location}

Provide specific job recommendations and explain why they're a good fit."""


if __name__ == "__main__":
    mcp.run()