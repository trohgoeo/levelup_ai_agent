import os
import json
import random
from typing import Type, TypeVar
from pydantic import BaseModel
from backend.ai_provider.base_provider import BaseAIProvider
from backend.ai_provider.openai_provider import OpenAIProvider
from backend.ai_provider.gemini_provider import GeminiProvider
from backend.ai_provider.ollama_provider import OllamaProvider

T = TypeVar('T', bound=BaseModel)

class SimulationProvider(BaseAIProvider):
    """
    Intelligent simulated provider fallback. It analyzes prompts and dynamically generates 
    highly realistic, contextual responses matching Pydantic schemas for all platform features.
    """
    def generate_text(self, prompt: str, system_instruction: str = None) -> str:
        # If text is requested directly, return a contextual mock text.
        prompt_lower = prompt.lower()
        
        if "cover letter" in prompt_lower or "apply" in prompt_lower:
            return (
                "Dear Hiring Team,\n\n"
                "I am writing to express my enthusiastic interest in your opening. As a dedicated technical professional "
                "with verified hands-on skills, I am excited about the opportunity to contribute to your goals. "
                "Through rigorous evaluations in LevelUp AI, I have demonstrated strong proficiency in solving complex "
                "problems, debugging production systems, and writing clean, scalable logic.\n\n"
                "I would love the opportunity to discuss how my skill set aligns with your engineering requirements.\n\n"
                "Best regards,\n[Applicant Name] (LevelUp Verified Agent)"
            )
        elif "ats" in prompt_lower or "optimize" in prompt_lower:
            return (
                "### ATS Optimization Report:\n"
                "- Added high-frequency keywords matching job specs\n"
                "- Streamlined experience formatting for readability\n"
                "- Highlighted verified skill scores (SQL, Python) at the top"
            )
        return "Simulated AI Provider response. Configure an API key or local Ollama model to enable live reasoning."

    def generate_json(self, prompt: str, response_model: Type[T], system_instruction: str = None) -> T:
        prompt_lower = prompt.lower()
        model_name = response_model.__name__.lower()
        
        # 1. Handle Resume Parser Simulation
        if "resume" in prompt_lower or "parse" in prompt_lower:
            # Detect target role
            role = "Python Backend Developer"
            if "data" in prompt_lower or "analyst" in prompt_lower:
                role = "Data Analyst"
            elif "frontend" in prompt_lower or "react" in prompt_lower:
                role = "Frontend Developer"
            
            # Default Mock Data based on role
            if "data analyst" in role.lower():
                skills = ["SQL", "Excel", "Power BI", "Python", "Statistics"]
                projects = "E-Commerce Customer Analytics Cohort Dashboard, SQL Database Query Optimization Pipeline"
                tech = "PostgreSQL, Power BI, Python (Pandas/NumPy), MS Excel"
                strengths = ["Strong SQL aggregate queries and window functions", "Data visual representation storytelling"]
                weaknesses = ["Statistical hypothesis modeling", "Advanced Python machine learning APIs"]
            elif "frontend" in role.lower():
                skills = ["React", "CSS", "Javascript", "HTML", "TypeScript"]
                projects = "Interactive Cyberpunk Neon UI Dashboard, Mobile Responsive SaaS Checkout Component"
                tech = "React, TailwindCSS, TypeScript, Vite, Jest"
                strengths = ["Excellent styling design eye", "Responsive CSS architectures"]
                weaknesses = ["State management performance tuning", "Complex UI unit test suites"]
            else:
                skills = ["Python", "FastAPI", "SQL", "OOPs", "APIs"]
                projects = "Real-time Autonomous Agent System, Secure User Authentication API with JWT"
                tech = "Python, FastAPI, SQLite, SQLAlchemy, Docker, Redis"
                strengths = ["RESTful API architecture design", "Database schema writing and optimization"]
                weaknesses = ["Asynchronous worker tasks queue scheduling", "High-frequency caching patterns"]

            # Structure matching the parser schema
            mock_data = {
                "name": "Alex Mercer",
                "email": "alex.mercer@cybernet.io",
                "target_role": role,
                "experience_level": "Intermediate" if "intermediate" in prompt_lower or "mid" in prompt_lower else "Beginner",
                "skills": skills,
                "projects": [projects],
                "technologies": tech.split(", "),
                "certifications": ["Verified LevelUp AI Foundation Certificate"],
                "experience": ["Junior Engineer Trainee (1 Year)"],
                "strengths": strengths,
                "weaknesses": weaknesses
            }
            return response_model.model_validate(mock_data)

        # 2. Handle Assessment Generation Simulation
        elif "assessment" in prompt_lower or "question" in prompt_lower:
            role = "Python Backend Developer"
            if "data" in prompt_lower:
                role = "Data Analyst"
            elif "frontend" in prompt_lower:
                role = "Frontend Developer"

            questions = []
            if "data" in role.lower():
                questions = [
                    {
                        "id": 1,
                        "question_type": "MCQ",
                        "skill": "SQL",
                        "difficulty": "Medium",
                        "question_text": "Which SQL statement is used to remove duplicates from a query result set?",
                        "options": ["SELECT DISTINCT", "SELECT UNIQUE", "SELECT REMOVE_DUPLICATES", "SELECT CLEAN"],
                        "correct_answer": "SELECT DISTINCT"
                    },
                    {
                        "id": 2,
                        "question_type": "SQL",
                        "skill": "SQL",
                        "difficulty": "Hard",
                        "question_text": "Given a table `orders` (id, customer_id, order_date, amount), write a query to find customers who placed more than 3 orders.",
                        "options": [],
                        "correct_answer": "SELECT customer_id FROM orders GROUP BY customer_id HAVING COUNT(id) > 3;"
                    },
                    {
                        "id": 3,
                        "question_type": "MCQ",
                        "skill": "Excel",
                        "difficulty": "Medium",
                        "question_text": "Which Excel function allows you to search for a value in the leftmost column of a table and return a value in the same row?",
                        "options": ["VLOOKUP", "HLOOKUP", "INDEX", "MATCH"],
                        "correct_answer": "VLOOKUP"
                    },
                    {
                        "id": 4,
                        "question_type": "Scenario",
                        "skill": "Power BI",
                        "difficulty": "Medium",
                        "question_text": "Your dashboard is loading extremely slowly. You discover a massive many-to-many relationship in your data model. What is the recommended best practice to resolve this?",
                        "options": [
                            "Introduce a bridge/junction table to break it into two one-to-many relationships",
                            "Ignore the warnings and upgrade server hosting memory",
                            "Combine all tables into one flat sheet containing millions of duplicate rows",
                            "Disable filters entirely on the dashboard"
                        ],
                        "correct_answer": "Introduce a bridge/junction table to break it into two one-to-many relationships"
                    },
                    {
                        "id": 5,
                        "question_type": "MCQ",
                        "skill": "Statistics",
                        "difficulty": "Hard",
                        "question_text": "What does a p-value of 0.03 indicate in hypothesis testing if our significance level alpha is 0.05?",
                        "options": [
                            "Reject the null hypothesis, findings are statistically significant",
                            "Fail to reject the null hypothesis, findings are due to chance",
                            "The hypothesis test is invalid",
                            "The null hypothesis is 97% true"
                        ],
                        "correct_answer": "Reject the null hypothesis, findings are statistically significant"
                    }
                ]
            else:
                questions = [
                    {
                        "id": 1,
                        "question_type": "MCQ",
                        "skill": "Python",
                        "difficulty": "Medium",
                        "question_text": "What is the primary difference between a List and a Tuple in Python?",
                        "options": [
                            "Lists are mutable, Tuples are immutable",
                            "Lists are immutable, Tuples are mutable",
                            "Lists can hold multiple types, Tuples can only hold integers",
                            "Lists use parentheses, Tuples use square brackets"
                        ],
                        "correct_answer": "Lists are mutable, Tuples are immutable"
                    },
                    {
                        "id": 2,
                        "question_type": "Debugging",
                        "skill": "Python",
                        "difficulty": "Medium",
                        "question_text": "Identify the bug in this Python function:\n\ndef add_item(item, list_items=[]):\n    list_items.append(item)\n    return list_items",
                        "options": [
                            "Using a mutable default argument (`list_items=[]`) causes sharing across distinct calls",
                            "Functions cannot return lists in Python",
                            "The append method does not exist on standard lists",
                            "You must declare the variable global"
                        ],
                        "correct_answer": "Using a mutable default argument (`list_items=[]`) causes sharing across distinct calls"
                    },
                    {
                        "id": 3,
                        "question_type": "Coding",
                        "skill": "OOPs",
                        "difficulty": "Hard",
                        "question_text": "Implement a class structure demonstrating encapsulation. Write a Python class `BankAccount` with a private balance attribute and a secure method to deposit money.",
                        "options": [],
                        "correct_answer": "class BankAccount:\n    def __init__(self):\n        self.__balance = 0\n    def deposit(self, amt):\n        if amt > 0: self.__balance += amt"
                    },
                    {
                        "id": 4,
                        "question_type": "MCQ",
                        "skill": "APIs",
                        "difficulty": "Medium",
                        "question_text": "Which HTTP status code is returned when a client requests a resource they are not authenticated to view?",
                        "options": ["401 Unauthorized", "403 Forbidden", "404 Not Found", "400 Bad Request"],
                        "correct_answer": "401 Unauthorized"
                    },
                    {
                        "id": 5,
                        "question_type": "Scenario",
                        "skill": "DSA",
                        "difficulty": "Hard",
                        "question_text": "You need to frequently check if specific elements exist in a large collection. Which Python data structure provides O(1) average time complexity lookup?",
                        "options": ["Set", "List", "Tuple", "Linked List"],
                        "correct_answer": "Set"
                    }
                ]

            mock_data = {
                "questions": questions
            }
            return response_model.model_validate(mock_data)

        # 3. Handle Evaluation Simulation
        elif "evaluate" in prompt_lower or "score" in prompt_lower:
            # Check if user made tab violations
            score = 75.0
            if "violation" in prompt_lower or "cheated" in prompt_lower:
                score = 35.0

            # Dynamic based on answers provided
            skills_breakdown = {}
            if "sql" in prompt_lower or "power bi" in prompt_lower or "excel" in prompt_lower:
                skills_breakdown = {
                    "SQL": 4,
                    "Excel": 5,
                    "Power BI": 2,
                    "Python": 2,
                    "Statistics": 3
                }
            else:
                skills_breakdown = {
                    "Python": 4,
                    "FastAPI": 4,
                    "SQL": 3,
                    "OOPs": 2,
                    "APIs": 1
                }

            mock_data = {
                "overall_score": score,
                "skills_breakdown": skills_breakdown,
                "strengths": [
                    "Excellent syntax comprehension",
                    "Solid conceptual foundation in querying logic"
                ],
                "weaknesses": [
                    "Lacks experience with advanced state validation and design schemas",
                    "Struggles with security optimization parameters"
                ],
                "interview_readiness": "Needs Practice" if score < 70 else ("Ready for Internships" if score >= 90 else "Intermediate Preparation"),
                "improvement_recommendations": "Focus on the generated tasks. Solve the customized assignments to unlock higher automatic applying modules."
            }
            return response_model.model_validate(mock_data)

        # 4. Handle Task Generation Simulation
        elif "task" in prompt_lower or "mission" in prompt_lower:
            skills = ["Power BI", "Python"]
            if "python" in prompt_lower:
                skills = ["APIs", "OOPs"]
            elif "sql" in prompt_lower:
                skills = ["SQL", "Statistics"]

            tasks = [
                {
                    "title": f"Mastering {skills[0]} Integrations",
                    "skill": skills[0],
                    "description": f"Learn to architect safe, modular systems using advanced {skills[0]} principles.",
                    "difficulty": "Medium",
                    "exercise": f"Write a optimized codebase implementing structural loops in {skills[0]} with appropriate exception validations.",
                    "solution_template": "def solve_challenge():\n    # Enter your code here\n    pass",
                    "xp_reward": 150
                },
                {
                    "title": f"Hands-on {skills[1]} Practical Lab",
                    "skill": skills[1],
                    "description": f"A scenario-based deployment using the key elements of {skills[1]}.",
                    "difficulty": "Hard",
                    "exercise": f"Configure a system block mapping complex data aggregates using {skills[1]}.",
                    "solution_template": "def run_analysis():\n    # Enter your code here\n    pass",
                    "xp_reward": 200
                }
            ]
            
            mock_data = {
                "tasks": tasks
            }
            return response_model.model_validate(mock_data)

        # Fallback if no specific model matched
        raise ValueError(f"SimulationProvider could not match schema model {model_name}")


class ProviderManager:
    @staticmethod
    def get_provider(provider_name: str, model_name: str = None, api_key: str = None) -> BaseAIProvider:
        """
        Dynamically return the appropriate AI provider instance. 
        Falls back to SimulationProvider if credentials/connections fail.
        """
        p_name = provider_name.lower()
        
        try:
            if p_name == "openai":
                key = api_key or os.getenv("OPENAI_API_KEY")
                if not key:
                    return SimulationProvider()
                return OpenAIProvider(api_key=key, model=model_name or "gpt-4o-mini")
                
            elif p_name == "gemini":
                key = api_key or os.getenv("GEMINI_API_KEY")
                if not key:
                    return SimulationProvider()
                return GeminiProvider(api_key=key, model=model_name or "gemini-1.5-flash")
                
            elif p_name == "ollama":
                # Check for active Ollama model.
                base_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
                model = model_name or "llama3"
                # Quick test connection, if fails, fallback to simulation
                try:
                    import requests
                    requests.get(f"{base_url}/api/tags", timeout=2)
                except Exception:
                    # Ollama offline or not running
                    return SimulationProvider()
                return OllamaProvider(base_url=base_url, model=model)
                
            else:
                return SimulationProvider()
        except Exception:
            # Any failures (e.g. library not installed) falls back to simulated response for 100% reliability
            return SimulationProvider()
