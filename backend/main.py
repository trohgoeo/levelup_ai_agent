import os
from fastapi import FastAPI, Depends, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Optional

# Database imports
from backend.database import init_db, get_db
import backend.database.models as db_models

# AI Agent and Provider imports
from backend.ai_provider import ProviderManager
from backend.utils.resume_parser import extract_text_from_pdf, parse_resume_with_ai
from backend.agents.assessment_agent import AssessmentAgent
from backend.agents.evaluation_agent import EvaluationAgent
from backend.agents.task_agent import TaskAgent
from backend.agents.auto_apply_agent import AutoApplyAgent

app = FastAPI(
    title="LevelUp AI Backend",
    description="REST API for LevelUp AI — Autonomous Skill-to-Internship Agent",
    version="1.0.0"
)

# Enable CORS for frontend integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Run database creation on startup
@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/")
def read_root():
    return {"message": "Welcome to LevelUp AI REST API server. System Online."}

# --- CANDIDATE ENDPOINTS ---

@app.post("/candidates/register")
async def register_candidate(
    name: str = Form(...),
    email: Optional[str] = Form(None),
    target_role: str = Form(...),
    experience_level: str = Form("Beginner"),
    provider_name: str = Form("openai"),
    model_name: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    resume_file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    try:
        # 1. Handle Resume text extraction
        resume_text = ""
        filename = None
        if resume_file:
            filename = resume_file.filename
            file_bytes = await resume_file.read()
            resume_text = extract_text_from_pdf(file_bytes)

        # 2. Parse resume details using chosen AI provider
        ai_provider = ProviderManager.get_provider(provider_name, model_name, api_key)
        parsed = parse_resume_with_ai(
            raw_text=resume_text, 
            provider=ai_provider, 
            user_target_role=target_role, 
            user_experience_level=experience_level
        )

        # 3. Create database entry
        candidate = db_models.Candidate(
            name=parsed.name or name,
            email=parsed.email or email,
            target_role=parsed.target_role or target_role,
            experience_level=parsed.experience_level or experience_level,
            xp=100, # Starter XP
            apply_level="Novice",
            daily_apply_limit=0, # Locked until assessment taken
            resume_filename=filename,
            resume_content=resume_text if resume_text else "No raw resume parsed"
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)

        # 4. Save extracted Skills
        for skill in parsed.skills:
            # Default skill rating starts at 1
            skill_score = db_models.SkillScore(
                candidate_id=candidate.id,
                skill_name=skill,
                score=2 # Default starting score
            )
            db.add(skill_score)
        
        db.commit()
        db.refresh(candidate)

        return {
            "status": "success",
            "candidate_id": candidate.id,
            "parsed_profile": {
                "name": candidate.name,
                "email": candidate.email,
                "target_role": candidate.target_role,
                "experience_level": candidate.experience_level,
                "skills": [s.skill_name for s in candidate.skills],
                "strengths": parsed.strengths,
                "weaknesses": parsed.weaknesses
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to register candidate: {str(e)}")


@app.get("/candidates/{candidate_id}")
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.query(db_models.Candidate).filter(db_models.Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    return {
        "id": candidate.id,
        "name": candidate.name,
        "email": candidate.email,
        "target_role": candidate.target_role,
        "experience_level": candidate.experience_level,
        "xp": candidate.xp,
        "apply_level": candidate.apply_level,
        "daily_apply_limit": candidate.daily_apply_limit,
        "skills": {s.skill_name: s.score for s in candidate.skills},
        "created_at": candidate.created_at
    }


# --- ASSESSMENT ENDPOINTS ---

@app.post("/candidates/{candidate_id}/generate-assessment")
def generate_assessment(
    candidate_id: int,
    provider_name: str = Form("openai"),
    model_name: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    candidate = db.query(db_models.Candidate).filter(db_models.Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    try:
        skills = [s.skill_name for s in candidate.skills]
        if not skills:
            skills = ["Python", "SQL", "APIs"] # Default backup

        ai_provider = ProviderManager.get_provider(provider_name, model_name, api_key)
        assessment_data = AssessmentAgent.generate_assessment(
            candidate_name=candidate.name,
            role=candidate.target_role,
            skills=skills,
            experience_level=candidate.experience_level,
            provider=ai_provider
        )

        # Store assessment in database
        db_assessment = db_models.Assessment(
            candidate_id=candidate.id,
            role=candidate.target_role,
            status="pending",
            questions_json=assessment_data.model_dump_json(),
            violations=0
        )
        db.add(db_assessment)
        db.commit()
        db.refresh(db_assessment)

        return {
            "assessment_id": db_assessment.id,
            "role": db_assessment.role,
            "questions": assessment_data.questions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate assessment: {str(e)}")


@app.post("/assessments/{assessment_id}/submit")
def submit_assessment(
    assessment_id: int,
    answers: Dict[str, str], # Maps question ID as string to answer text
    violations: int = Form(0),
    provider_name: str = Form("openai"),
    model_name: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    db_assessment = db.query(db_models.Assessment).filter(db_models.Assessment.id == assessment_id).first()
    if not db_assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    try:
        # Load structured questions
        from backend.agents.assessment_agent import AssessmentSchema
        questions_obj = AssessmentSchema.model_validate_json(db_assessment.questions_json)

        # Evaluate answers using AI provider
        ai_provider = ProviderManager.get_provider(provider_name, model_name, api_key)
        
        # Grade cheating logic: if violations exceed 2, score is capped or terminated
        if violations >= 3:
            db_assessment.status = "terminated"
            db_assessment.score = 0.0
            db_assessment.violations = violations
            db_assessment.answers_json = json.dumps(answers)
            db.commit()
            return {
                "status": "terminated",
                "score": 0.0,
                "message": "Assessment auto-terminated due to multiple tab-switching proctor violations."
            }

        eval_report = EvaluationAgent.evaluate_submission(
            assessment=questions_obj,
            user_answers=answers,
            provider=ai_provider
        )

        # Update assessment fields
        db_assessment.status = "completed"
        db_assessment.score = eval_report.overall_score
        db_assessment.answers_json = json.dumps(answers)
        db_assessment.evaluation_json = eval_report.model_dump_json()
        db_assessment.violations = violations

        # Update candidate scores and limits based on Unlock Rules
        candidate = db_assessment.candidate
        
        # 1. Update individual Skill Ratings
        for skill_name, new_rating in eval_report.skills_breakdown.items():
            skill_score = db.query(db_models.SkillScore).filter(
                db_models.SkillScore.candidate_id == candidate.id,
                db_models.SkillScore.skill_name == skill_name
            ).first()
            if skill_score:
                skill_score.score = max(skill_score.score, new_rating)
            else:
                db.add(db_models.SkillScore(
                    candidate_id=candidate.id,
                    skill_name=skill_name,
                    score=new_rating
                ))

        # 2. Gamification and Unlock Rules
        if eval_report.overall_score >= 90.0:
            candidate.apply_level = "Elite"
            candidate.daily_apply_limit = 5
            candidate.xp += 500  # Bonus XP
        elif eval_report.overall_score >= 70.0:
            candidate.apply_level = "Advanced"
            candidate.daily_apply_limit = 2
            candidate.xp += 250  # Medium XP
        else:
            candidate.apply_level = "Novice"
            candidate.daily_apply_limit = 0  # Learning mode locked
            candidate.xp += 50   # Completion XP

        db.commit()
        db.refresh(db_assessment)
        db.refresh(candidate)

        return {
            "status": "success",
            "overall_score": db_assessment.score,
            "apply_level": candidate.apply_level,
            "daily_limit": candidate.daily_apply_limit,
            "xp_earned": 500 if db_assessment.score >= 90 else (250 if db_assessment.score >= 70 else 50),
            "report": eval_report
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to evaluate submission: {str(e)}")


# --- LEARNING ENDPOINTS ---

@app.post("/candidates/{candidate_id}/generate-tasks")
def generate_tasks(
    candidate_id: int,
    provider_name: str = Form("openai"),
    model_name: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    candidate = db.query(db_models.Candidate).filter(db_models.Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    try:
        # Find weak skills (score < 4)
        weak_skills = [s.skill_name for s in candidate.skills if s.score < 4]
        if not weak_skills:
            # If no weak skills, choose 2 lowest ones or default
            sorted_skills = sorted(candidate.skills, key=lambda s: s.score)
            weak_skills = [s.skill_name for s in sorted_skills[:2]]
        
        if not weak_skills:
            weak_skills = ["Python", "SQL"]

        ai_provider = ProviderManager.get_provider(provider_name, model_name, api_key)
        task_data = TaskAgent.generate_learning_tasks(
            candidate_name=candidate.name,
            weak_skills=weak_skills,
            role=candidate.target_role,
            provider=ai_provider
        )

        created_tasks = []
        for t in task_data.tasks:
            db_task = db_models.Task(
                candidate_id=candidate.id,
                title=t.title,
                skill=t.skill,
                description=t.description,
                difficulty=t.difficulty,
                exercise=t.exercise,
                solution_template=t.solution_template,
                status="pending",
                xp_reward=t.xp_reward
            )
            db.add(db_task)
            created_tasks.append(db_task)

        db.commit()
        return {"status": "success", "count": len(created_tasks)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate tasks: {str(e)}")


@app.post("/tasks/{task_id}/submit")
def submit_task(
    task_id: int,
    user_code: str = Form(...),
    provider_name: str = Form("openai"),
    model_name: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    db_task = db.query(db_models.Task).filter(db_models.Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    try:
        ai_provider = ProviderManager.get_provider(provider_name, model_name, api_key)
        eval_result = TaskAgent.evaluate_task_submission(
            task_title=db_task.title,
            task_skill=db_task.skill,
            task_exercise=db_task.exercise,
            user_code=user_code,
            xp_reward=db_task.xp_reward,
            provider=ai_provider
        )

        db_task.user_submission = user_code
        db_task.feedback = eval_result.feedback
        
        if eval_result.is_correct:
            db_task.status = "completed"
            db_task.score = eval_result.score
            
            # Award XP to Candidate
            candidate = db_task.candidate
            candidate.xp += eval_result.xp_earned

            # Increment Candidate's skill rating score slightly in database
            skill_score = db.query(db_models.SkillScore).filter(
                db_models.SkillScore.candidate_id == candidate.id,
                db_models.SkillScore.skill_name == db_task.skill
            ).first()
            if skill_score:
                skill_score.score = min(5, skill_score.score + 1) # Cap rating at 5

        db.commit()
        db.refresh(db_task)

        return {
            "is_correct": eval_result.is_correct,
            "score": eval_result.score,
            "feedback": eval_result.feedback,
            "xp_earned": eval_result.xp_earned
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to grade task: {str(e)}")


# --- JOB APPLY ENDPOINTS ---

@app.get("/candidates/{candidate_id}/job-matches")
def search_jobs(
    candidate_id: int,
    provider_name: str = Form("openai"),
    model_name: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    candidate = db.query(db_models.Candidate).filter(db_models.Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    try:
        skills = [s.skill_name for s in candidate.skills]
        ai_provider = ProviderManager.get_provider(provider_name, model_name, api_key)
        job_matches = AutoApplyAgent.search_jobs(
            role=candidate.target_role,
            skills=skills,
            provider=ai_provider
        )
        return {"jobs": job_matches.jobs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to match jobs: {str(e)}")


@app.post("/candidates/{candidate_id}/auto-apply")
def auto_apply(
    candidate_id: int,
    job_title: str = Form(...),
    company: str = Form(...),
    job_description: str = Form(...),
    provider_name: str = Form("openai"),
    model_name: Optional[str] = Form(None),
    api_key: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    candidate = db.query(db_models.Candidate).filter(db_models.Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Enforce Unlock Rules limits
    if candidate.apply_level == "Novice":
        raise HTTPException(status_code=403, detail="Auto Apply is locked. Candidates scoring below 70% must enter Learning Mode.")
    
    # Check if candidate has reached their daily limit
    today = datetime.datetime.utcnow().date()
    applied_today = db.query(db_models.JobApplication).filter(
        db_models.JobApplication.candidate_id == candidate.id,
        db_models.JobApplication.applied_date >= datetime.datetime.combine(today, datetime.time.min)
    ).count()

    if applied_today >= candidate.daily_apply_limit:
        raise HTTPException(status_code=429, detail=f"Daily auto-apply limit of {candidate.daily_apply_limit} reached for your '{candidate.apply_level}' status. Complete learning tasks to upgrade your levels!")

    try:
        # ATS Optimization and Cover Letter Generation
        ai_provider = ProviderManager.get_provider(provider_name, model_name, api_key)
        ats_result = AutoApplyAgent.optimize_resume_and_letter(
            candidate_name=candidate.name,
            resume_text=candidate.resume_content or "No Resume Text",
            job_title=job_title,
            job_company=company,
            job_desc=job_description,
            provider=ai_provider
        )

        # Create Job Application Tracker
        job_app = db_models.JobApplication(
            candidate_id=candidate.id,
            job_title=job_title,
            company=company,
            match_score=85, # Simulated ATS Match Score
            cover_letter=ats_result.cover_letter,
            optimized_resume=f"ATS Optimizations:\n{ats_result.optimized_summary}\n\nKey Experience Targets:\n" + "\n".join(ats_result.optimized_bullets),
            status="applied"
        )
        db.add(job_app)
        db.commit()
        db.refresh(job_app)

        return {
            "status": "success",
            "application_id": job_app.id,
            "optimized_summary": ats_result.optimized_summary,
            "optimized_bullets": ats_result.optimized_bullets,
            "cover_letter": ats_result.cover_letter
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to auto apply: {str(e)}")
