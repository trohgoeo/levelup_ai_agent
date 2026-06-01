import io
from typing import List, Optional
from pydantic import BaseModel
import pypdf
from backend.ai_provider.base_provider import BaseAIProvider

# Structural Schema for Resume Outputs
class ParsedResume(BaseModel):
    name: str
    email: Optional[str] = None
    target_role: str
    experience_level: str  # Beginner, Intermediate, Advanced
    skills: List[str]
    projects: List[str]
    technologies: List[str]
    certifications: List[str]
    experience: List[str]
    strengths: List[str]
    weaknesses: List[str]

def extract_text_from_pdf(pdf_source) -> str:
    """
    Extracts text from a PDF source, which can be an absolute file path, 
    a file-like object, or bytes.
    """
    text = ""
    try:
        if isinstance(pdf_source, bytes):
            pdf_file = io.BytesIO(pdf_source)
        elif isinstance(pdf_source, str):
            pdf_file = open(pdf_source, "rb")
        else:
            pdf_file = pdf_source  # Assuming it's already a file-like object

        reader = pypdf.PdfReader(pdf_file)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        if isinstance(pdf_source, str):
            pdf_file.close()

    except Exception as e:
        print(f"Error reading PDF content: {str(e)}")
        
    return text.strip()

def parse_resume_with_ai(
    raw_text: str, 
    provider: BaseAIProvider, 
    user_target_role: Optional[str] = None, 
    user_experience_level: Optional[str] = None
) -> ParsedResume:
    """
    Takes raw resume text and uses the configured AI provider to extract skills, 
    projects, strengths, and weaknesses structurally into ParsedResume schema.
    """
    # Context injection to ensure AI maps correctly if the user specified their preferences
    context_str = ""
    if user_target_role:
        context_str += f"- User's Target Career Role: {user_target_role}\n"
    if user_experience_level:
        context_str += f"- User's Experience Level: {user_experience_level}\n"

    system_instruction = (
        "You are an Elite AI Resume Parser and Career Recruiting Expert. "
        "Your goal is to parse raw resume text and return structured JSON matching the provided schema."
    )
    
    prompt = (
        f"Please analyze the following raw resume text and extract the candidate's career details.\n"
        f"Additional User Inputs:\n{context_str}\n"
        f"--- RAW RESUME TEXT ---\n"
        f"{raw_text if raw_text else 'No resume text uploaded. Please generate a stellar starter profile matching the user inputs.'}\n"
        f"-----------------------\n"
        f"Extract:\n"
        f"1. Candidate Name (default to 'Candidate' if not found)\n"
        f"2. Contact email\n"
        f"3. Target Career Role (if not explicitly in resume, infer matching target role: {user_target_role or 'Software Engineer'})\n"
        f"4. Experience level ('Beginner', 'Intermediate', or 'Advanced')\n"
        f"5. Skills list (Extract 4-8 core technical skills, e.g. SQL, Python, Excel, React, FastAPI)\n"
        f"6. Projects (Brief descriptions or titles)\n"
        f"7. Technologies used\n"
        f"8. Certifications\n"
        f"9. Experience history\n"
        f"10. Strengths (2-3 items analyzing resume achievements)\n"
        f"11. Weaknesses (2-3 items indicating key improvement areas related to the target role)"
    )

    return provider.generate_json(prompt, ParsedResume, system_instruction=system_instruction)
