import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.database.connection import Base

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, nullable=True)
    target_role = Column(String, nullable=True)
    experience_level = Column(String, default="Beginner")
    xp = Column(Integer, default=0)
    apply_level = Column(String, default="Novice")  # Novice, Advanced, Elite
    daily_apply_limit = Column(Integer, default=0)    # 0, 2, 5, 10
    resume_filename = Column(String, nullable=True)
    resume_content = Column(Text, nullable=True)     # Extracted text from PDF
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    skills = relationship("SkillScore", back_populates="candidate", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="candidate", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="candidate", cascade="all, delete-orphan")
    applications = relationship("JobApplication", back_populates="candidate", cascade="all, delete-orphan")


class SkillScore(Base):
    __tablename__ = "skill_scores"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"))
    skill_name = Column(String, index=True)
    score = Column(Integer, default=1)  # 1 to 5

    candidate = relationship("Candidate", back_populates="skills")


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"))
    role = Column(String)
    status = Column(String, default="pending")  # pending, completed, terminated
    questions_json = Column(Text, nullable=True)  # List of unique questions in JSON
    answers_json = Column(Text, nullable=True)    # User's responses in JSON
    score = Column(Float, default=0.0)            # Final score percentage (0-100)
    evaluation_json = Column(Text, nullable=True) # AI detailed scoring breakdown
    violations = Column(Integer, default=0)       # Tab-switching warnings triggered
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    candidate = relationship("Candidate", back_populates="assessments")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"))
    title = Column(String)
    skill = Column(String)
    description = Column(Text)
    difficulty = Column(String, default="Medium")
    exercise = Column(Text)                       # The coding problem / scenario prompt
    solution_template = Column(Text, nullable=True)
    user_submission = Column(Text, nullable=True)
    status = Column(String, default="pending")    # pending, completed
    score = Column(Float, nullable=True)
    xp_reward = Column(Integer, default=100)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    candidate = relationship("Candidate", back_populates="tasks")


class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"))
    job_title = Column(String)
    company = Column(String)
    match_score = Column(Integer, default=80)     # ATS match percentage
    cover_letter = Column(Text, nullable=True)
    optimized_resume = Column(Text, nullable=True)
    status = Column(String, default="applied")    # applied, pending, interview, rejected
    applied_date = Column(DateTime, default=datetime.datetime.utcnow)

    candidate = relationship("Candidate", back_populates="applications")
