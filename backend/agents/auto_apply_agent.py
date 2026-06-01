from typing import List, Optional
from pydantic import BaseModel
from backend.ai_provider.base_provider import BaseAIProvider

# Pydantic schemas for Job Hunting and ATS Optimization
class JobMatchSchema(BaseModel):
    title: str
    company: str
    location: str
    skills_required: List[str]
    match_percentage: int
    description: str

class JobListSchema(BaseModel):
    jobs: List[JobMatchSchema]

class ATSResultSchema(BaseModel):
    optimized_summary: str
    optimized_bullets: List[str]
    cover_letter: str

class AutoApplyAgent:
    """
    Agent responsible for matching candidates with jobs, optimizing resume ATS scores, 
    generating highly targeted cover letters, and simulating the application deployment.
    """
    @staticmethod
    def search_jobs(
        role: str,
        skills: List[str],
        provider: BaseAIProvider
    ) -> JobListSchema:
        
        skills_str = ", ".join(skills)
        system_instruction = (
            "You are a Headhunting Recruiting Agent. Your goal is to scan market demand "
            "and output suitable mock job opportunities that match the candidate's profiles."
        )

        prompt = (
            f"Candidate Role: {role}\n"
            f"Candidate Verified Skills: [{skills_str}]\n\n"
            f"Please generate exactly 3 matching job openings that a candidate with this profile can apply for.\n"
            f"Guidelines:\n"
            f"1. Create realistic job titles (e.g. Junior Backend Developer, SQL Data Analyst, React Intern).\n"
            f"2. Supply a realistic company name, location (Remote/Hybrid options), list of required skills, "
            f"   and a brief job description detailing core day-to-day work.\n"
            f"3. Calculate a dynamic `match_percentage` (between 60 and 98) based on how well their verified skills cover the job needs."
        )

        return provider.generate_json(prompt, JobListSchema, system_instruction=system_instruction)

    @staticmethod
    def optimize_resume_and_letter(
        candidate_name: str,
        resume_text: str,
        job_title: str,
        job_company: str,
        job_desc: str,
        provider: BaseAIProvider
    ) -> ATSResultSchema:
        
        system_instruction = (
            "You are an Elite ATS Resume Optimizer and Copywriter. "
            "Your objective is to optimize a candidate's resume summary and work experience bullets "
            "to maximize compatibility scanners, and write a stellar, personalized cover letter."
        )

        prompt = (
            f"Candidate Name: {candidate_name}\n"
            f"Job Details:\n"
            f"- Title: {job_title}\n"
            f"- Company: {job_company}\n"
            f"- Description: {job_desc}\n\n"
            f"Raw Candidate Resume Text:\n"
            f"```\n{resume_text[:2000] if resume_text else 'No uploaded resume. Generating optimized details from scratch.'}\n```\n\n"
            f"Tasks:\n"
            f"1. Generate an `optimized_summary`: A professional paragraph written in active voice highlighting target matching skill sets.\n"
            f"2. Generate 3 `optimized_bullets`: Formulate 3 metric-driven experience bullets aligned to the job description keywords.\n"
            f"3. Write a highly persuasive, gorgeous `cover_letter` tailored to the Hiring Manager at {job_company}."
        )

        return provider.generate_json(prompt, ATSResultSchema, system_instruction=system_instruction)
