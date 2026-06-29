import sys
import os

# Add project root to sys.path for Streamlit Cloud deployment path resolution
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
import pandas as pd
import plotly.express as px
import time
import json
import datetime

# Import styles and custom components
from frontend.styles import inject_cyberpunk_styles
from frontend.components import render_proctor_console

# Import backend modules directly for robust execution
from backend.database import SessionLocal, init_db
import backend.database.models as db_models
from backend.ai_provider import ProviderManager
from backend.utils.resume_parser import extract_text_from_pdf, parse_resume_with_ai
from backend.agents.assessment_agent import AssessmentAgent, AssessmentSchema
from backend.agents.evaluation_agent import EvaluationAgent
from backend.agents.task_agent import TaskAgent
from backend.agents.auto_apply_agent import AutoApplyAgent

# Initialize SQLite tables on frontend launch
init_db()

# Page Configurations
st.set_page_config(
    page_title="LevelUp AI — Career growth Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject modern cyberpunk theme styles
inject_cyberpunk_styles()

# Initialize session state variables
if "candidate_id" not in st.session_state:
    st.session_state.candidate_id = None
if "provider_name" not in st.session_state:
    st.session_state.provider_name = "openai"
if "model_name" not in st.session_state:
    st.session_state.model_name = "gpt-4o-mini"
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "active_assessment" not in st.session_state:
    st.session_state.active_assessment = None
if "test_submitted" not in st.session_state:
    st.session_state.test_submitted = False
if "simulation_mode" not in st.session_state:
    st.session_state.simulation_mode = False

# Database helper session
db = SessionLocal()

# --- SIDEBAR: SYSTEM SETTINGS & DYNAMIC LLM CONFIG ---
st.sidebar.markdown("<h2 style='text-align: center; color: #00F0FF; margin-bottom: 0;'>LEVELUP AI</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; color: #8F9FA9; font-size:11px; margin-top: 0;'>Autonomous Career growth OS</p>", unsafe_allow_html=True)
st.sidebar.markdown("---")

st.sidebar.markdown("### 🔌 AI PROVIDER GATEWAY")
provider_option = st.sidebar.selectbox(
    "Active AI Engine",
    ["OpenAI (Cloud)", "Gemini (Cloud)", "Ollama (Local Model)", "Simulation Fallback"],
    index=3  # Default to Simulation Fallback for 100% out-of-the-box workability
)

# Dynamically map and display inputs for chosen provider
if provider_option == "OpenAI (Cloud)":
    st.session_state.provider_name = "openai"
    st.session_state.model_name = st.sidebar.text_input("Model Name", value="gpt-4o-mini")
    st.session_state.api_key = st.sidebar.text_input("OpenAI API Key", type="password")
    st.session_state.simulation_mode = False
elif provider_option == "Gemini (Cloud)":
    st.session_state.provider_name = "gemini"
    st.session_state.model_name = st.sidebar.text_input("Model Name", value="gemini-1.5-flash")
    st.session_state.api_key = st.sidebar.text_input("Gemini API Key", type="password")
    st.session_state.simulation_mode = False
elif provider_option == "Ollama (Local Model)":
    st.session_state.provider_name = "ollama"
    st.session_state.model_name = st.sidebar.selectbox("Local Model", ["llama3", "mistral", "deepseek-coder", "codellama", "phi3"])
    st.session_state.api_key = ""
    st.session_state.simulation_mode = False
    st.sidebar.markdown("<p style='font-size:10px; color:#39FF14;'>Ensure local Ollama endpoint http://localhost:11434 is running.</p>", unsafe_allow_html=True)
else:
    st.session_state.provider_name = "simulation"
    st.session_state.model_name = "simulated-engine"
    st.session_state.api_key = ""
    st.session_state.simulation_mode = True
    st.sidebar.markdown("<p style='font-size:10px; color:#39FF14;'>Offline Simulation mode active. No API keys required!</p>", unsafe_allow_html=True)

# Fetch Candidate Object from DB
candidate = None
if st.session_state.candidate_id:
    candidate = db.query(db_models.Candidate).filter(db_models.Candidate.id == st.session_state.candidate_id).first()
    if candidate:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🧑‍💻 VERIFIED AGENT PROFILE")
        st.sidebar.markdown(f"**Agent Name:** `{candidate.name}`")
        st.sidebar.markdown(f"**Target Role:** `{candidate.target_role}`")
        
        # XP Badging
        st.sidebar.markdown(
            f"**Level Status:** <span class='xp-badge'>LEVEL {candidate.xp // 1000 + 1}</span>", 
            unsafe_allow_html=True
        )
        st.sidebar.markdown(
            f"**Verified XP:** <span class='xp-badge'>{candidate.xp} XP</span>", 
            unsafe_allow_html=True
        )
        
        # Lock Meter Status
        limit_text = f"{candidate.daily_apply_limit} Jobs/day" if candidate.daily_apply_limit > 0 else "LOCKED"
        st.sidebar.markdown(f"**Auto-Apply Limits:** `{limit_text}` (`{candidate.apply_level}` Tier)")

# --- MAIN PAGE ROUTING ---
if not st.session_state.candidate_id:
    # --- ONBOARDING TIER ---
    st.markdown("<h1 class='neon-title' style='text-align:center; font-size:42px;'>⚡ LEVELUP AI ⚡</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#8F9FA9;'>The Autonomous Skill-to-Internship Agent. Upload your credentials and let the AI take your career to the next level.</p>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("<div class='cyber-card'>", unsafe_allow_html=True)
        st.markdown("<h3>📁 ONBOARD CANDIDATE PROFILE</h3>", unsafe_allow_html=True)
        
        name_input = st.text_input("Candidate Full Name", placeholder="Alex Mercer")
        email_input = st.text_input("Contact Email", placeholder="alex@cybernet.io")
        role_input = st.text_input("Target Career Role", placeholder="Python Backend Developer")
        
        exp_level = st.selectbox(
            "Seniority Target Level",
            ["Beginner", "Intermediate", "Advanced"]
        )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col2:
        st.markdown("<div class='cyber-card-pink'>", unsafe_allow_html=True)
        st.markdown("<h3>📄 ANALYZE RESUME (PDF)</h3>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload your resume and the AI will extract skills automatically", type=["pdf"])
        
        if uploaded_file:
            st.success("Resume parsed successfully in buffer. Click Onboard to structure with AI.")
        else:
            st.info("You can onboarding with manual fields or let the AI extract details dynamically from your PDF resume.")
        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("🚀 ACCESS CAREER SYSTEM"):
        if not name_input or not role_input:
            st.error("Name and Target Career Role are mandatory field uploads.")
        else:
            with st.spinner("Decoding candidate coordinates with AI Agent..."):
                # 1. Parse text from upload
                resume_text = ""
                filename = None
                if uploaded_file:
                    filename = uploaded_file.name
                    file_bytes = uploaded_file.read()
                    resume_text = extract_text_from_pdf(file_bytes)

                # 2. Get active provider
                ai_provider = ProviderManager.get_provider(
                    st.session_state.provider_name,
                    st.session_state.model_name,
                    st.session_state.api_key
                )

                try:
                    parsed = parse_resume_with_ai(
                        raw_text=resume_text,
                        provider=ai_provider,
                        user_target_role=role_input,
                        user_experience_level=exp_level
                    )

                    # 3. Create candidate DB entry
                    db_candidate = db_models.Candidate(
                        name=parsed.name or name_input,
                        email=parsed.email or email_input,
                        target_role=parsed.target_role or role_input,
                        experience_level=parsed.experience_level or exp_level,
                        xp=500, # Initial onboarding XP
                        apply_level="Novice",
                        daily_apply_limit=0,
                        resume_filename=filename,
                        resume_content=resume_text if resume_text else "Manual Onboarding Profile"
                    )
                    db.add(db_candidate)
                    db.commit()
                    db.refresh(db_candidate)

                    # 4. Save parsed skills
                    for skill in parsed.skills:
                        skill_score = db_models.SkillScore(
                            candidate_id=db_candidate.id,
                            skill_name=skill,
                            score=2 # Start rating (out of 5)
                        )
                        db.add(skill_score)
                    
                    db.commit()
                    st.session_state.candidate_id = db_candidate.id
                    st.success(f"Candidate profile initialized successfully! Welcome, {db_candidate.name}.")
                    st.rerun()

                except Exception as e:
                    st.error(f"Failed to onboarding profile. Error: {str(e)}")

else:
    # --- AUTHENTICATED TABS SYSTEM ---
    st.markdown(f"<h1 class='neon-title'>⚡ LEVELUP AI OPERATING SYSTEM</h1>", unsafe_allow_html=True)
    
    tabs = st.tabs(["📊 SYSTEM DASHBOARD", "🛡️ SECURE ASSESSMENT", "🏋️ LEARNING MISSIONS", "🤖 AUTO-APPLY AGENT"])

    # ------------------ TAB 1: SYSTEM DASHBOARD ------------------
    with tabs[0]:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("<div class='cyber-card'>", unsafe_allow_html=True)
            st.markdown("<h3>🎯 DYNAMIC RADAR SKILL GRID</h3>", unsafe_allow_html=True)
            
            # Fetch skills data
            skills_data = db.query(db_models.SkillScore).filter(db_models.SkillScore.candidate_id == candidate.id).all()
            
            if skills_data:
                # Plotly radar charts rendering
                df_skills = pd.DataFrame({
                    "Skill": [s.skill_name for s in skills_data],
                    "Verified Rating": [s.score for s in skills_data]
                })
                
                fig = px.line_polar(df_skills, r='Verified Rating', theta='Skill', line_close=True)
                fig.update_traces(fill='toself', line_color='#00F0FF', fillcolor='rgba(0, 240, 255, 0.25)', line_width=2)
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 5], gridcolor='#2A2E3D', color='#8F9FA9'),
                        angularaxis=dict(gridcolor='#2A2E3D', color='#FFFFFF'),
                        bgcolor='rgba(18, 19, 28, 0.8)'
                    ),
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#FFFFFF',
                    margin=dict(t=20, b=20, l=40, r=40)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No verified skill indices. Complete the technical assessment to unlock dynamic radar plotting!")
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("<div class='cyber-card-pink'>", unsafe_allow_html=True)
            st.markdown("<h3>🧬 GAMIFIED CAREER PROGRESSION</h3>", unsafe_allow_html=True)
            
            # Show XP Level Progress
            level = (candidate.xp // 1000) + 1
            xp_in_level = candidate.xp % 1000
            
            st.markdown(f"**System Level:** `LEVEL {level}`")
            st.progress(xp_in_level / 1000.0)
            st.markdown(f"<p style='font-size:11px; text-align:right;'>{xp_in_level} / 1000 XP to LEVEL {level+1}</p>", unsafe_allow_html=True)
            st.markdown("---")

            # Show Unlocked Levels Visual Metrics
            st.markdown("#### 🚀 ARCHETYPE LOCK METER")
            
            # Novice Status
            st.markdown(
                f"🛡️ **Tier Novice (Score < 70%):** "
                f"<span style='color:{'#39FF14' if candidate.apply_level in ['Novice', 'Advanced', 'Elite'] else '#FF007F'};'>**UNLOCKED**</span>",
                unsafe_allow_html=True
            )
            st.markdown("- Manual study hub exercises active. Auto applies disabled.")

            # Advanced Status
            unlocked_adv = candidate.apply_level in ["Advanced", "Elite"]
            color_adv = "#39FF14" if unlocked_adv else "#8F9FA9"
            label_adv = "UNLOCKED" if unlocked_adv else "LOCKED (Assessment >= 70% Required)"
            st.markdown(
                f"⚡ **Tier Advanced (Score 70-89%):** "
                f"<span style='color:{color_adv};'>**{label_adv}**</span>",
                unsafe_allow_html=True
            )
            st.markdown("- Manual job searching active. Custom cover letter generations active. Limit: 1-2 applies daily.")

            # Elite Status
            unlocked_elite = candidate.apply_level == "Elite"
            color_elite = "#39FF14" if unlocked_elite else "#8F9FA9"
            label_elite = "UNLOCKED" if unlocked_elite else "LOCKED (Assessment >= 90% Required)"
            st.markdown(
                f"👾 **Tier Elite Agent (Score >= 90%):** "
                f"<span style='color:{color_elite};'>**{label_elite}**</span>",
                unsafe_allow_html=True
            )
            st.markdown("- Autonomous Cover Letter & Resume ATS Optimizer active. Limit: 5 auto-applies daily.")
            
            st.markdown("</div>", unsafe_allow_html=True)

        # Bottom Area: Application tracking grid
        st.markdown("<div class='cyber-card'>", unsafe_allow_html=True)
        st.markdown("<h3>📊 AUTONOMOUS JOB APPLICATION HUB</h3>", unsafe_allow_html=True)
        apps = db.query(db_models.JobApplication).filter(db_models.JobApplication.candidate_id == candidate.id).all()
        
        if apps:
            app_list = []
            for a in apps:
                app_list.append({
                    "Job Title": a.job_title,
                    "Company": a.company,
                    "ATS Match %": f"{a.match_score}%",
                    "Status": a.status.upper(),
                    "Applied Date": a.applied_date.strftime("%Y-%m-%d %H:%M")
                })
            st.dataframe(pd.DataFrame(app_list), use_container_width=True)
        else:
            st.markdown(
                "<div style='text-align:center; padding:30px; color:#8F9FA9;'>No active job tracker entries. "
                "Reach Advanced or Elite ranks to launch the autonomous auto-apply bots!</div>", 
                unsafe_allow_html=True
            )
        st.markdown("</div>", unsafe_allow_html=True)

    # ------------------ TAB 2: SECURE ASSESSMENT ------------------
    with tabs[1]:
        st.markdown("<div class='cyber-card'>", unsafe_allow_html=True)
        st.markdown("<h3>🛡️ SECURE ADAPTIVE TECHNICAL ASSESSMENT</h3>", unsafe_allow_html=True)
        
        # Check if assessment is currently running
        active_assessment = db.query(db_models.Assessment).filter(
            db_models.Assessment.candidate_id == candidate.id,
            db_models.Assessment.status == "pending"
        ).first()

        if not active_assessment:
            st.markdown(
                f"<p style='color:#8F9FA9;'>Prepare to initiate a fully unique, adaptive test tailored specifically "
                f"to your target role: <b>{candidate.target_role}</b>. The evaluation covers security compliance checks "
                f"and proctoring monitoring. Ensure your microphone/camera are active.</p>", 
                unsafe_allow_html=True
            )
            
            if st.button("🔌 INITIATE EXAM COMPILATION"):
                with st.spinner("Compiling technical assessment indices via LLM..."):
                    try:
                        ai_provider = ProviderManager.get_provider(
                            st.session_state.provider_name,
                            st.session_state.model_name,
                            st.session_state.api_key
                        )
                        skills_list = [s.skill_name for s in candidate.skills]
                        
                        test_schema = AssessmentAgent.generate_assessment(
                            candidate_name=candidate.name,
                            role=candidate.target_role,
                            skills=skills_list if skills_list else ["SQL", "Python"],
                            experience_level=candidate.experience_level,
                            provider=ai_provider
                        )

                        # Save assessment db entry
                        new_test = db_models.Assessment(
                            candidate_id=candidate.id,
                            role=candidate.target_role,
                            status="pending",
                            questions_json=test_schema.model_dump_json(),
                            violations=0
                        )
                        db.add(new_test)
                        db.commit()
                        st.success("Secure exam session successfully compiled! Scroll down to unlock parameters.")
                        st.rerun()

                    except Exception as e:
                        st.error(f"Failed compile. Details: {str(e)}")
        else:
            # Active test is running! Inject the HTML/JS Proctoring console in the sidebar
            render_proctor_console(time_limit_seconds=300)

            # Renders questions
            questions_data = json.loads(active_assessment.questions_json)["questions"]
            
            st.markdown("---")
            st.markdown("<p style='color:#FF007F; font-size:12px;'>⚠️ AESTHETICS PROCTOR WARNING: Tab switching or exiting fullscreen will result in exam locking warnings!</p>", unsafe_allow_html=True)
            
            # Setup Form for Submissions
            user_answers = {}
            with st.form("exam_form"):
                for q in questions_data:
                    st.markdown(f"**Question {q['id']} [Skill: {q['skill']} | Difficulty: {q['difficulty']}]:**")
                    st.markdown(f"*{q['question_text']}*")
                    
                    if q["question_type"] == "MCQ":
                        user_answers[str(q["id"])] = st.radio(
                            f"Options for Q#{q['id']}", 
                            q["options"], 
                            key=f"q_{q['id']}", 
                            label_visibility="collapsed"
                        )
                    else:
                        user_answers[str(q["id"])] = st.text_area(
                            f"Write code solution for Q#{q['id']}", 
                            placeholder="Enter SQL Query, script, or scenario answers...", 
                            key=f"q_{q['id']}", 
                            label_visibility="collapsed"
                        )
                    st.markdown("---")

                # Hidden violations count synced via Streamlit session storage or simple simulation parameter
                violations_input = st.number_input(
                    "Proctor Alert Override Tracking (Developer Test)", 
                    min_value=0, max_value=3, value=0, step=1, 
                    help="Simulates visibility tab-switching counts reported back from the Javascript bridge."
                )

                submit_btn = st.form_submit_button("📁 TRANSMIT SOLUTIONS FOR SCORING")
                
                if submit_btn:
                    with st.spinner("Verifying secure submissions and scoring answers with AI Engine..."):
                        try:
                            ai_provider = ProviderManager.get_provider(
                                st.session_state.provider_name,
                                st.session_state.model_name,
                                st.session_state.api_key
                            )
                            
                            # Parse structured schema
                            questions_obj = AssessmentSchema.model_validate_json(active_assessment.questions_json)

                            # Handle Proctored Failure Rule
                            if violations_input >= 3:
                                active_assessment.status = "terminated"
                                active_assessment.score = 0.0
                                active_assessment.violations = violations_input
                                active_assessment.answers_json = json.dumps(user_answers)
                                
                                candidate.apply_level = "Novice"
                                candidate.daily_apply_limit = 0
                                db.commit()
                                
                                st.error("🚨 ASSESSMENT AUTO-TERMINATED due to persistent proctor/tab switching violations. Score capped at 0%. Auto-apply features locked.")
                                time.sleep(2)
                                st.rerun()
                            else:
                                # Grade submission via Evaluation Agent
                                report = EvaluationAgent.evaluate_submission(
                                    assessment=questions_obj,
                                    user_answers=user_answers,
                                    provider=ai_provider
                                )

                                # Save graded details
                                active_assessment.status = "completed"
                                active_assessment.score = report.overall_score
                                active_assessment.answers_json = json.dumps(user_answers)
                                active_assessment.evaluation_json = report.model_dump_json()
                                active_assessment.violations = violations_input

                                # Dynamic limits unlocks
                                xp_earned = 50
                                if report.overall_score >= 90:
                                    candidate.apply_level = "Elite"
                                    candidate.daily_apply_limit = 5
                                    candidate.xp += 500
                                    xp_earned = 500
                                elif report.overall_score >= 70:
                                    candidate.apply_level = "Advanced"
                                    candidate.daily_apply_limit = 2
                                    candidate.xp += 250
                                    xp_earned = 250
                                else:
                                    candidate.apply_level = "Novice"
                                    candidate.daily_apply_limit = 0
                                    candidate.xp += 50

                                # Update skill rating score structures
                                for skill_name, rating in report.skills_breakdown.items():
                                    s_score = db.query(db_models.SkillScore).filter(
                                        db_models.SkillScore.candidate_id == candidate.id,
                                        db_models.SkillScore.skill_name == skill_name
                                    ).first()
                                    if s_score:
                                        s_score.score = max(s_score.score, rating)
                                    else:
                                        db.add(db_models.SkillScore(
                                            candidate_id=candidate.id,
                                            skill_name=skill_name,
                                            score=rating
                                        ))

                                db.commit()
                                st.balloons()
                                st.success(f"Grading complete! You scored {report.overall_score}%. System Rank: {candidate.apply_level} ({xp_earned} XP Awarded)")
                                time.sleep(2.5)
                                st.rerun()

                        except Exception as e:
                            st.error(f"Failed submission grading. Details: {str(e)}")

        # Print history of completed assessments
        st.markdown("---")
        st.markdown("#### 📜 ASSESSMENT HISTORY LOG")
        past_tests = db.query(db_models.Assessment).filter(
            db_models.Assessment.candidate_id == candidate.id,
            db_models.Assessment.status != "pending"
        ).all()

        if past_tests:
            for pt in past_tests:
                status_color = "#39FF14" if pt.status == "completed" else "#FF007F"
                st.markdown(f"**Assessment ID #{pt.id}** — Status: <span style='color:{status_color}; font-weight:bold;'>{pt.status.upper()}</span>", unsafe_allow_html=True)
                st.markdown(f"- **Final Grade:** `{pt.score}%` | **Tab Violations:** `{pt.violations}`")
                
                if pt.evaluation_json:
                    report_obj = json.loads(pt.evaluation_json)
                    col_str, col_wk = st.columns(2)
                    with col_str:
                        st.markdown("**Technical Strengths Verified:**")
                        for strg in report_obj.get("strengths", []):
                            st.markdown(f"✅ *{strg}*")
                    with col_wk:
                        st.markdown("**Improvement Areas Identified:**")
                        for weak in report_obj.get("weaknesses", []):
                            st.markdown(f"⚠️ *{weak}*")
                st.markdown("---")
        else:
            st.info("No historical assessment submissions logged.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ------------------ TAB 3: LEARNING HUB ------------------
    with tabs[2]:
        st.markdown("<div class='cyber-card'>", unsafe_allow_html=True)
        st.markdown("<h3>🏋️ PERSONALIZED LEARNING HUBS & MISSIONS</h3>", unsafe_allow_html=True)
        
        # Pull candidate's current tasks
        active_tasks = db.query(db_models.Task).filter(
            db_models.Task.candidate_id == candidate.id
        ).all()

        if not active_tasks:
            st.info("No active learning tasks are currently assigned to your profile.")
            if st.button("🎯 COMPILE PERSONALIZED LEARNING MISSIONS"):
                with st.spinner("Analyzing weak vectors and compiling code modules with AI..."):
                    try:
                        ai_provider = ProviderManager.get_provider(
                            st.session_state.provider_name,
                            st.session_state.model_name,
                            st.session_state.api_key
                        )
                        # Fetch lowest scoring skills
                        skills_list = db.query(db_models.SkillScore).filter(db_models.SkillScore.candidate_id == candidate.id).all()
                        weak_list = [s.skill_name for s in skills_list if s.score < 4]
                        if not weak_list:
                            weak_list = [s.skill_name for s in sorted(skills_list, key=lambda x: x.score)[:2]]
                        
                        if not weak_list:
                            weak_list = ["Python", "SQL"]

                        tasks_schema = TaskAgent.generate_learning_tasks(
                            candidate_name=candidate.name,
                            weak_skills=weak_list,
                            role=candidate.target_role,
                            provider=ai_provider
                        )

                        for t in tasks_schema.tasks:
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
                        
                        db.commit()
                        st.success("Learning Hub initialized! New tasks compiling...")
                        time.sleep(1)
                        st.rerun()

                    except Exception as e:
                        st.error(f"Failed task compile. Details: {str(e)}")
        else:
            # Render each task details
            for t in active_tasks:
                task_color_class = "cyber-card-pink" if t.status == "pending" else "cyber-card-green"
                st.markdown(f"<div class='{task_color_class}'>", unsafe_allow_html=True)
                
                status_lbl = "🟡 ACTIVE MISSION" if t.status == "pending" else "🟢 COMPLETED"
                st.markdown(f"<h4>{t.title} ({status_lbl})</h4>", unsafe_allow_html=True)
                st.markdown(f"**Targeted Skill:** `{t.skill}` | **Difficulty:** `{t.difficulty}` | **XP Reward:** `{t.xp_reward} XP`")
                st.markdown(f"*{t.description}*")
                st.markdown("---")
                
                st.markdown("**Exercise challenge prompt:**")
                st.info(t.exercise)
                
                if t.status == "pending":
                    # Input box for solutions code
                    user_sub = st.text_area(
                        "Insert script code solution below:",
                        value=t.solution_template if t.solution_template else "",
                        key=f"task_box_{t.id}",
                        height=180
                    )
                    
                    # Submit button
                    st.markdown("<div class='learn-btn'>", unsafe_allow_html=True)
                    if st.button("📤 VERIFY CODE CHALLENGE", key=f"btn_task_{t.id}"):
                        with st.spinner("Testing syntax compilation via AI review..."):
                            try:
                                ai_provider = ProviderManager.get_provider(
                                    st.session_state.provider_name,
                                    st.session_state.model_name,
                                    st.session_state.api_key
                                )
                                eval_res = TaskAgent.evaluate_task_submission(
                                    task_title=t.title,
                                    task_skill=t.skill,
                                    task_exercise=t.exercise,
                                    user_code=user_sub,
                                    xp_reward=t.xp_reward,
                                    provider=ai_provider
                                )

                                t.user_submission = user_sub
                                t.feedback = eval_res.feedback
                                
                                if eval_res.is_correct:
                                    t.status = "completed"
                                    t.score = eval_res.score
                                    candidate.xp += eval_res.xp_earned

                                    # Update specific skill ranking
                                    skill_db = db.query(db_models.SkillScore).filter(
                                        db_models.SkillScore.candidate_id == candidate.id,
                                        db_models.SkillScore.skill_name == t.skill
                                    ).first()
                                    if skill_db:
                                        skill_db.score = min(5, skill_db.score + 1)

                                    db.commit()
                                    st.balloons()
                                    st.success(f"Success! Grade: {eval_res.score}%. {eval_res.xp_earned} XP Awarded to profile.")
                                else:
                                    st.error(f"Verification Failed. Score: {eval_res.score}%. View debugger feedback below.")
                                
                                time.sleep(2)
                                st.rerun()

                            except Exception as e:
                                st.error(f"Submission compile failed: {str(e)}")
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.markdown("**Your Submission:**")
                    st.code(t.user_submission, language="python")
                    st.markdown("**AI Review Debugger Feedback:**")
                    st.markdown(t.feedback)
                
                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # ------------------ TAB 4: AUTO APPLY ------------------
    with tabs[3]:
        # Lock check
        if candidate.apply_level == "Novice":
            st.markdown("<div class='locked-overlay'>", unsafe_allow_html=True)
            st.markdown("<div class='locked-icon'>🔒</div>", unsafe_allow_html=True)
            st.markdown("<h3>AUTONOMOUS AUTO-APPLY SYSTEM TERMINATED</h3>", unsafe_allow_html=True)
            st.markdown(
                f"<p style='color:#FF007F;'>Access Level Denied (Score: below 70%). "
                f"You are restricted to Learning Mode. To unlock automatic resume applications "
                f"and headhunter submissions, achieve a minimum score of <b>70%</b> in the Technical Assessment!</p>", 
                unsafe_allow_html=True
            )
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='cyber-card'>", unsafe_allow_html=True)
            st.markdown("<h3>🤖 AUTONOMOUS AUTO-APPLY AGENT</h3>", unsafe_allow_html=True)
            st.markdown(
                f"Access Authorization Status: <span style='color:#39FF14; font-weight:bold;'>GRANTED</span> (`{candidate.apply_level}` rank active). "
                f"Your daily application limit is set to: `{candidate.daily_apply_limit} applications/day`.", 
                unsafe_allow_html=True
            )
            st.markdown("---")

            # Scan Matches
            if st.button("🔍 SCAN TARGET OPPORTUNITIES"):
                with st.spinner("Querying job gateways matching verified skill indices..."):
                    try:
                        ai_provider = ProviderManager.get_provider(
                            st.session_state.provider_name,
                            st.session_state.model_name,
                            st.session_state.api_key
                        )
                        skills_list = [s.skill_name for s in candidate.skills]
                        jobs_schema = AutoApplyAgent.search_jobs(
                            role=candidate.target_role,
                            skills=skills_list,
                            provider=ai_provider
                        )
                        # Save matches to session state to display below
                        st.session_state.job_matches = jobs_schema.jobs
                    except Exception as e:
                        st.error(f"Search failed. Error: {str(e)}")

            # Display scanned jobs
            if "job_matches" in st.session_state and st.session_state.job_matches:
                for idx, job in enumerate(st.session_state.job_matches):
                    st.markdown("<div class='cyber-card-pink'>", unsafe_allow_html=True)
                    st.markdown(f"<h4>📌 {job.title}</h4>", unsafe_allow_html=True)
                    st.markdown(f"**Company:** `{job.company}` | **Location:** `{job.location}` | **Skills Matched Index:** `{job.match_percentage}%`")
                    st.markdown(f"**Required Skillsets:** *{', '.join(job.skills_required)}*")
                    st.markdown(f"**Description:** *{job.description}*")
                    st.markdown("---")

                    # Apply Button triggering the autonomous agent simulator
                    if st.button(f"⚡ LAUNCH AUTO-APPLY BOT FOR {job.company.upper()}", key=f"apply_{idx}"):
                        
                        # Verify daily limits
                        today = datetime.datetime.utcnow().date()
                        count_today = db.query(db_models.JobApplication).filter(
                            db_models.JobApplication.candidate_id == candidate.id,
                            db_models.JobApplication.applied_date >= datetime.datetime.combine(today, datetime.time.min)
                        ).count()

                        if count_today >= candidate.daily_apply_limit:
                            st.error(f"Daily auto-apply limit of {candidate.daily_apply_limit} exceeded! Level up your XP rank to upgrade daily limits!")
                        else:
                            # 1. Simulate console logging output step-by-step
                            console = st.empty()
                            logs = [
                                "🎯 Spinning up Autonomous Application Agent...",
                                f"🔍 Parsing target job specs: {job.title} at {job.company}...",
                                "📊 Extracting candidate verified skill tags...",
                                "🧬 Executing ATS Optimization logic...",
                                "📑 Matching resume index scores with keywords...",
                                "📝 Composing personalized target cover letter using LLM...",
                                "📪 Connecting with job endpoint secure portal...",
                                "🚀 Deploying optimized resume package... SUCCESS",
                                "✅ Application verified and tracked in system database!"
                            ]
                            
                            current_log = []
                            for log in logs:
                                current_log.append(log)
                                console.markdown(
                                    f"<div style='background-color:#06070B; border:1px solid #00F0FF; padding:15px; border-radius:4px; font-family:monospace; color:#39FF14; font-size:11px; line-height:1.6;'>"
                                    + "<br>".join(current_log) + "</div>",
                                    unsafe_allow_html=True
                                )
                                time.sleep(0.6)

                            # 2. Run LLM optimization to write optimized contents
                            try:
                                ai_provider = ProviderManager.get_provider(
                                    st.session_state.provider_name,
                                    st.session_state.model_name,
                                    st.session_state.api_key
                                )
                                
                                result = AutoApplyAgent.optimize_resume_and_letter(
                                    candidate_name=candidate.name,
                                    resume_text=candidate.resume_content or "Stellar starter profile",
                                    job_title=job.title,
                                    job_company=job.company,
                                    job_desc=job.description,
                                    provider=ai_provider
                                )

                                # 3. Save application entry in database
                                new_app = db_models.JobApplication(
                                    candidate_id=candidate.id,
                                    job_title=job.title,
                                    company=job.company,
                                    match_score=job.match_percentage,
                                    cover_letter=result.cover_letter,
                                    optimized_resume=f"Optimized Summary:\n{result.optimized_summary}\n\nBullet Points:\n" + "\n".join(result.optimized_bullets),
                                    status="applied"
                                )
                                db.add(new_app)
                                db.commit()
                                
                                st.balloons()
                                st.success("Autonomous Auto-Apply Successfully Executed! View details below.")
                                
                                # Render ATS outputs
                                with st.expander("📄 VIEW DYNAMIC ATS OPTIMIZED RESUME DATA"):
                                    st.markdown(f"**Executive Summary Highlight:**\n*{result.optimized_summary}*")
                                    st.markdown("**Tailored Work Experience Bullet Points:**")
                                    for bullet in result.optimized_bullets:
                                        st.markdown(f"🎯 {bullet}")
                                
                                with st.expander("✉️ VIEW TAILORED COVER LETTER"):
                                    st.code(result.cover_letter, language="text")

                            except Exception as e:
                                st.error(f"Failed automatic applying execution. Details: {str(e)}")

                    st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("No scanned targets showing. Click 'Scan Target Opportunities' above to locate matching job indexes.")
            st.markdown("</div>", unsafe_allow_html=True)

# Close SQLite Sessions
db.close()
