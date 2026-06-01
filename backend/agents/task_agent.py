from typing import List, Dict, Optional
from pydantic import BaseModel
from backend.ai_provider.base_provider import BaseAIProvider

# Pydantic schemas for tasks
class TaskSchema(BaseModel):
    title: str
    skill: str
    description: str
    difficulty: str            # Easy, Medium, Hard
    exercise: str              # Practical exercise instructions/problem
    solution_template: str     # Boilerplate code to start with
    xp_reward: int             # e.g., 100, 150, 200

class TaskListSchema(BaseModel):
    tasks: List[TaskSchema]

class TaskEvaluationSchema(BaseModel):
    is_correct: bool
    score: float               # Percentage grade (0-100)
    feedback: str              # Step-by-step guidance or code corrections
    xp_earned: int             # XP awarded if correct (otherwise 0)

class TaskAgent:
    """
    Agent responsible for generating hyper-personalized hands-on learning tasks 
    for weak skills, and evaluating their subsequent practice submissions.
    """
    @staticmethod
    def generate_learning_tasks(
        candidate_name: str,
        weak_skills: List[str],
        role: str,
        provider: BaseAIProvider
    ) -> TaskListSchema:
        
        weak_str = ", ".join(weak_skills)
        system_instruction = (
            "You are a Legendary Tech Mentor. Your goal is to design engaging, high-yield, "
            "practical learning tasks/missions that help students master their weak engineering concepts."
        )

        prompt = (
            f"Candidate: {candidate_name}\n"
            f"Target Role: {role}\n"
            f"Weak Skills Detected: [{weak_str}]\n\n"
            f"Please generate exactly 2 personalized, hands-on learning tasks tailored to improve their weak skills.\n"
            f"Guidelines:\n"
            f"1. Make exercises highly interactive and realistic. Avoid boilerplate questions. (e.g. write API endpoints, optimize complex database joins, debug asynchronous logic).\n"
            f"2. Provide a clear `solution_template` (e.g. Python function headers with comments, SQL template queries) for the student to write their code in.\n"
            f"3. Assign an appropriate `xp_reward` based on difficulty (e.g., Easy: 100 XP, Medium: 150 XP, Hard: 200 XP)."
        )

        return provider.generate_json(prompt, TaskListSchema, system_instruction=system_instruction)

    @staticmethod
    def evaluate_task_submission(
        task_title: str,
        task_skill: str,
        task_exercise: str,
        user_code: str,
        xp_reward: int,
        provider: BaseAIProvider
    ) -> TaskEvaluationSchema:
        
        system_instruction = (
            "You are an AI Automated Coding Grader. Your goal is to carefully run code review "
            "and verify if the user's submission correctly solves the technical challenge."
        )

        prompt = (
            f"Verify the user's solution for the following learning task:\n"
            f"- Task Title: {task_title}\n"
            f"- Targeted Skill: {task_skill}\n"
            f"- Problem Exercise: {task_exercise}\n"
            f"- User's Submission:\n"
            f"```python\n{user_code}\n```\n\n"
            f"Evaluation Tasks:\n"
            f"1. Determine `is_correct` (True if the logical solution is correct and solves the task, False otherwise).\n"
            f"2. Calculate the coding `score` (0.0 to 100.0).\n"
            f"3. Draft detailed, motivating technical `feedback` explaining what they did well and how they can improve.\n"
            f"4. Assign `xp_earned` (If `is_correct` is True, award the full `{xp_reward}` XP, otherwise award 0 XP)."
        )

        return provider.generate_json(prompt, TaskEvaluationSchema, system_instruction=system_instruction)
