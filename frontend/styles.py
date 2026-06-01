import streamlit as st

def inject_cyberpunk_styles():
    cyberpunk_css = """
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@500;700&family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
    
    <style>
    /* Global Styles */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0A0B10 !important;
        color: #E2E8F0 !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Header fonts */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Orbitron', sans-serif !important;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        font-weight: 700 !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #0E0F17 !important;
        border-right: 2px solid #9A00FF !important;
        box-shadow: 0 0 15px rgba(154, 0, 255, 0.25) !important;
    }
    
    /* Neon glow cards */
    .cyber-card {
        background: rgba(18, 19, 28, 0.8) !important;
        border: 1px solid #00F0FF !important;
        border-radius: 12px !important;
        padding: 24px !important;
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.15) !important;
        margin-bottom: 20px !important;
        position: relative;
        overflow: hidden;
    }
    
    .cyber-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background: linear-gradient(90deg, #00F0FF, #9A00FF, #FF007F);
    }
    
    .cyber-card-pink {
        background: rgba(18, 19, 28, 0.8) !important;
        border: 1px solid #FF007F !important;
        border-radius: 12px !important;
        padding: 24px !important;
        box-shadow: 0 0 15px rgba(255, 0, 127, 0.15) !important;
        margin-bottom: 20px !important;
    }
    
    .cyber-card-green {
        background: rgba(18, 19, 28, 0.8) !important;
        border: 1px solid #39FF14 !important;
        border-radius: 12px !important;
        padding: 24px !important;
        box-shadow: 0 0 15px rgba(57, 255, 20, 0.15) !important;
        margin-bottom: 20px !important;
    }
    
    /* Neon header gradients */
    .neon-title {
        background: linear-gradient(45deg, #00F0FF, #9A00FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 32px !important;
        font-weight: 900 !important;
        text-shadow: 0 0 30px rgba(0, 240, 255, 0.3);
    }
    
    .neon-pink-title {
        background: linear-gradient(45deg, #FF007F, #9A00FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(255, 0, 127, 0.3);
    }

    /* Buttons styling override */
    div.stButton > button {
        background: linear-gradient(135deg, #00F0FF 0%, #9A00FF 100%) !important;
        color: #FFFFFF !important;
        font-family: 'Orbitron', sans-serif !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        transition: all 0.3s ease-in-out !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.5);
        box-shadow: 0 0 15px rgba(0, 240, 255, 0.3) !important;
        letter-spacing: 1px;
    }
    
    div.stButton > button:hover {
        transform: scale(1.05) !important;
        box-shadow: 0 0 25px rgba(0, 240, 255, 0.6) !important;
        color: #FFFFFF !important;
        border: none !important;
    }
    
    /* Secondary/learning mode button styling */
    .learn-btn div.stButton > button {
        background: linear-gradient(135deg, #FF007F 0%, #9A00FF 100%) !important;
        box-shadow: 0 0 15px rgba(255, 0, 127, 0.3) !important;
    }
    
    .learn-btn div.stButton > button:hover {
        box-shadow: 0 0 25px rgba(255, 0, 127, 0.6) !important;
    }

    /* Input focus colors */
    input, textarea, select {
        background-color: #12131C !important;
        color: white !important;
        border: 1px solid #2A2E3D !important;
    }
    
    input:focus, textarea:focus {
        border-color: #00F0FF !important;
        box-shadow: 0 0 10px rgba(0, 240, 255, 0.4) !important;
    }
    
    /* XP display badge */
    .xp-badge {
        font-family: 'Orbitron', sans-serif;
        color: #39FF14;
        border: 1px solid #39FF14;
        background: rgba(57, 255, 20, 0.1);
        padding: 4px 12px;
        border-radius: 20px;
        display: inline-block;
        font-weight: bold;
        box-shadow: 0 0 10px rgba(57, 255, 20, 0.2);
    }
    
    /* Streaks glowing indicator */
    .streak-badge {
        font-family: 'Orbitron', sans-serif;
        color: #FF9F00;
        border: 1px solid #FF9F00;
        background: rgba(255, 159, 0, 0.1);
        padding: 4px 12px;
        border-radius: 20px;
        display: inline-block;
        font-weight: bold;
        box-shadow: 0 0 10px rgba(255, 159, 0, 0.2);
    }
    
    /* Lock elements visually overlay */
    .locked-overlay {
        background: rgba(10, 11, 16, 0.85);
        border: 2px dashed #FF007F;
        border-radius: 12px;
        padding: 40px;
        text-align: center;
        box-shadow: 0 0 20px rgba(255, 0, 127, 0.15);
        color: #8C98A9;
    }
    
    .locked-icon {
        font-size: 48px;
        color: #FF007F;
        text-shadow: 0 0 20px rgba(255, 0, 127, 0.5);
        margin-bottom: 15px;
    }
    </style>
    """
    st.markdown(cyberpunk_css, unsafe_allow_html=True)
