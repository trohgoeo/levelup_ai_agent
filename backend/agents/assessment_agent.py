import random
from typing import List, Optional
from pydantic import BaseModel
from backend.ai_provider.base_provider import BaseAIProvider

# Pydantic Schemas for structural enforcement
class QuestionSchema(BaseModel):
    id: int
    question_type: str  # MCQ, Coding, Scenario, Debugging, SQL
    skill: str
    difficulty: str     # Easy, Medium, Hard
    question_text: str
    options: List[str]  # Empty array if coding / SQL / free text
    correct_answer: str # The correct option or sample solution code

class AssessmentSchema(BaseModel):
    questions: List[QuestionSchema]

class AssessmentAgent:
    """
    Agent responsible for generating dynamic, customized, unique assessments
    for candidates based on their role, skill set, and experience level.
    """
    @staticmethod
    def generate_assessment(
        candidate_name: str,
        role: str,
        skills: List[str],
        experience_level: str,
        provider: BaseAIProvider
    ) -> AssessmentSchema:
        skills_str = ", ".join(skills)
        
        # Inject entropy using a randomized key to guarantee that static cache is broken
        # and assessments are completely unique and dynamic.
        seed_value = random.randint(1000, 9999)
        
        system_instruction = (
            "You are an Elite Technical Assessment Architect. Your objective is to compile unique, "
            "highly relevant, role-specific assessment questions. "
            "Do NOT return generic questions. Focus on practical, real-world industry interview-level quality."
        )

        prompt = (
            f"Generate a customized technical assessment for a candidate named {candidate_name} with seed ID: #{seed_value}.\n\n"
            f"Candidate Specifications:\n"
            f"- Target Career Role: {role}\n"
            f"- Extracted Core Skills: [{skills_str}]\n"
            f"- Seniority/Experience level: {experience_level}\n\n"
            f"Task Guidelines:\n"
            f"Compile a structured assessment consisting of exactly 5 distinct, unique questions.\n"
            f"1. Adaptive Difficulty: Tune the question complexity to fit a {experience_level} level.\n"
            f"2. Balanced Question Types:\n"
            f"   - Question 1: MCQ covering foundational theory or concepts of {skills[0] if len(skills) > 0 else 'Core Technical Skills'}\n"
            f"   - Question 2: A practical scenario-based problem or dashboard interpretation (e.g. for {skills[1] if len(skills) > 1 else 'Core Skill'})\n"
            f"   - Question 3: A coding debugging puzzle or database SQL query writing question\n"
            f"   - Question 4: An intermediate programming challenge or API schema construction\n"
            f"   - Question 5: A hard problem testing algorithmic design, optimization, or architecture specs\n"
            f"3. Make questions immersive, involving practical snippets. Do not generate repetitive static queries.\n"
            f"4. For coding or query writing questions, set `options` to an empty array `[]` and specify a reference "
            f"correct answer or standard syntax script in `correct_answer`."
        )

        # Generate structured questions JSON via configured provider
        return provider.generate_json(prompt, AssessmentSchema, system_instruction=system_instruction)
