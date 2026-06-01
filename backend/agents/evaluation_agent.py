import json
from typing import List, Dict
from pydantic import BaseModel
from backend.ai_provider.base_provider import BaseAIProvider
from backend.agents.assessment_agent import AssessmentSchema

# Pydantic schema for evaluation report
class EvaluationSchema(BaseModel):
    overall_score: float                  # Final score (0.0 to 100.0)
    skills_breakdown: Dict[str, int]      # Ratings (1 to 5) for each tested skill
    strengths: List[str]                  # 2-3 specific technical strengths demonstrated
    weaknesses: List[str]                 # 2-3 weak areas requiring target study/missions
    interview_readiness: str              # "Needs Practice", "Intermediate Preparation", "Ready for Internships"
    improvement_recommendations: str     # Structured advice on learning next steps

class EvaluationAgent:
    """
    Agent responsible for scoring candidate assessments, evaluating coding / SQL logic, 
    and generating module-wise performance ratings with feedback.
    """
    @staticmethod
    def evaluate_submission(
        assessment: AssessmentSchema,
        user_answers: Dict[str, str],     # Dict mapping question_id (as str) -> user's input
        provider: BaseAIProvider
    ) -> EvaluationSchema:
        
        # Build list of Q&A blocks to feed the evaluator
        qa_blocks = []
        for q in assessment.questions:
            ans = user_answers.get(str(q.id), "")
            qa_blocks.append({
                "question_id": q.id,
                "question_type": q.question_type,
                "skill": q.skill,
                "question_text": q.question_text,
                "correct_answer": q.correct_answer,
                "user_answer": ans
            })
            
        qa_json_str = json.dumps(qa_blocks, indent=2)

        system_instruction = (
            "You are an Expert Technical Interviewer and AI Proctoring System. "
            "Your job is to thoroughly grade candidate submissions fairly. "
            "Evaluate coding syntax, logic flows, and SQL accuracy precisely."
        )

        prompt = (
            f"Please grade the following candidate test submission.\n\n"
            f"Here are the questions, reference answers, and the user's submissions:\n"
            f"{qa_json_str}\n\n"
            f"Grading Criteria:\n"
            f"1. For MCQs: If user_answer matches correct_answer exactly (ignoring spacing), they receive 100%. Otherwise 0%.\n"
            f"2. For Coding / SQL / Scenarios: Analyze the logical correctness of user_answer against correct_answer. Give partial credit for working logic or close syntax.\n"
            f"3. Calculate the cumulative average `overall_score` (between 0.0 and 100.0).\n"
            f"4. Map tested skills into a detailed `skills_breakdown` with ratings from 1 (Novice) to 5 (Expert).\n"
            f"5. Extract 2 specific technical strengths and 2 distinct weaknesses that emerged during testing.\n"
            f"6. Make an objective assessment of `interview_readiness` based on overall performance:\n"
            f"   - Score < 70%: 'Needs Practice'\n"
            f"   - Score 70%-89%: 'Intermediate Preparation'\n"
            f"   - Score >= 90%: 'Ready for Internships'\n"
            f"7. Provide clear, actionable recommendations on what weak skills to practice."
        )

        # Generate structured evaluation report via the configured provider
        return provider.generate_json(prompt, EvaluationSchema, system_instruction=system_instruction)
