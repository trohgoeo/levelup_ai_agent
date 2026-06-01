from backend.database.connection import engine, SessionLocal, Base, get_db
from backend.database.models import Candidate, SkillScore, Assessment, Task, JobApplication

def init_db():
    Base.metadata.create_all(bind=engine)
