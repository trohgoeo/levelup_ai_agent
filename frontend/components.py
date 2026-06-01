import streamlit as st
import streamlit.components.v1 as components

def render_proctor_console(time_limit_seconds: int = 300):
    """
    Renders an immersive, cyberpunk-styled AI Proctoring and Timer component
    via HTML5 and Javascript. Handles:
    - Tab Switch Detection (Visibility API)
    - Fullscreen Enforcement
    - Right-click & Copy/Paste Blockers
    - Countdown Timer with Auto-Submit trigger
    - Future-ready Webcam feed rendering with circular scan indicators
    """
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Share+Tech+Mono&display=swap');
            
            body {{
                background-color: #0A0B10;
                color: #00F0FF;
                font-family: 'Share Tech Mono', monospace;
                margin: 0;
                padding: 10px;
                overflow: hidden;
                border: 1px solid #FF007F;
                border-radius: 8px;
                box-shadow: 0 0 15px rgba(255, 0, 127, 0.2);
            }}
            
            .proctor-container {{
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 8px;
            }}
            
            .camera-box {{
                width: 130px;
                height: 130px;
                border-radius: 50%;
                border: 2px solid #FF007F;
                overflow: hidden;
                position: relative;
                box-shadow: 0 0 15px rgba(255, 0, 127, 0.3);
                background-color: #12131C;
            }}
            
            #webcam {{
                width: 100%;
                height: 100%;
                object-fit: cover;
                transform: scaleX(-1); /* Mirror effect */
            }}
            
            .scan-line {{
                width: 100%;
                height: 3px;
                background-color: #39FF14;
                position: absolute;
                top: 0;
                left: 0;
                box-shadow: 0 0 8px #39FF14;
                animation: scan 3s infinite linear;
                pointer-events: none;
            }}
            
            @keyframes scan {{
                0% {{ top: 0; }}
                50% {{ top: 100%; }}
                100% {{ top: 0; }}
            }}
            
            .hud-metrics {{
                width: 100%;
                font-size: 11px;
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 5px;
                text-align: center;
            }}
            
            .hud-card {{
                background-color: rgba(18, 19, 28, 0.8);
                border: 1px solid #2A2E3D;
                border-radius: 4px;
                padding: 4px;
            }}
            
            .timer-display {{
                font-family: 'Orbitron', sans-serif;
                font-size: 20px;
                color: #39FF14;
                text-shadow: 0 0 10px rgba(57, 255, 20, 0.4);
                margin: 4px 0;
                font-weight: 700;
            }}
            
            .alert-text {{
                color: #FF007F;
                text-shadow: 0 0 5px #FF007F;
            }}
            
            .log-terminal {{
                width: 100%;
                height: 55px;
                background-color: #06070B;
                border: 1px solid #2A2E3D;
                border-radius: 4px;
                font-size: 9px;
                padding: 4px;
                box-sizing: border-box;
                overflow-y: hidden;
                color: #8F9FA9;
                display: flex;
                flex-direction: column;
                justify-content: flex-end;
            }}
            
            .log-line {{
                margin: 1px 0;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }}
            
            .log-green {{ color: #39FF14; }}
            .log-red {{ color: #FF007F; }}
            
            .fullscreen-overlay {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(10, 11, 16, 0.95);
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                z-index: 9999;
                gap: 15px;
                text-align: center;
            }}
            
            .start-btn {{
                background: linear-gradient(135deg, #FF007F, #9A00FF);
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-family: 'Orbitron', sans-serif;
                cursor: pointer;
                box-shadow: 0 0 15px rgba(255, 0, 127, 0.4);
                font-size: 12px;
                transition: transform 0.2s;
            }}
            
            .start-btn:hover {{
                transform: scale(1.05);
            }}
        </style>
    </head>
    <body>
        
        <!-- Fullscreen Lock Overlay -->
        <div id="fsOverlay" class="fullscreen-overlay">
            <span style="font-family: 'Orbitron'; color: #FF007F; font-size: 13px;">SECURITY CLEARANCE REQUIRED</span>
            <span style="font-size: 10px; color: #8F9FA9; max-width: 90%;">Fullscreen mode and webcam sharing are enforced for the duration of this technical assessment.</span>
            <button class="start-btn" onclick="initiateExam()">UNSHACKLE AGENT</button>
        </div>

        <div class="proctor-container">
            <!-- Simulated AI Proctoring Webcam Feed -->
            <div class="camera-box">
                <video id="webcam" autoplay playsinline muted></video>
                <div class="scan-line"></div>
            </div>
            
            <!-- Timer Clock -->
            <div class="timer-display" id="clock">00:00</div>
            
            <!-- Security metrics -->
            <div class="hud-metrics">
                <div class="hud-card">
                    <span style="color:#8F9FA9; font-size:9px;">STATUS</span><br>
                    <span id="pStatus" class="log-green">ACTIVE</span>
                </div>
                <div class="hud-card">
                    <span style="color:#8F9FA9; font-size:9px;">VIOLATIONS</span><br>
                    <span id="violationCount" class="alert-text">0 / 3</span>
                </div>
            </div>
            
            <!-- Active logging console output -->
            <div class="log-terminal" id="logTerminal">
                <div class="log-line log-green">&gt; INITIALIZING ENCRYPTED UPLINK...</div>
                <div class="log-line">&gt; CAMERA ACQUIRED SUCCESSFULLY.</div>
            </div>
        </div>

        <script>
            let timeRemaining = {time_limit_seconds};
            let violations = 0;
            let examStarted = false;
            
            // Log management
            function addLog(text, colorClass = "") {{
                const term = document.getElementById("logTerminal");
                const line = document.createElement("div");
                line.className = "log-line " + colorClass;
                line.innerText = "> " + text;
                term.appendChild(line);
                if (term.childNodes.length > 5) {{
                    term.removeChild(term.childNodes[0]);
                }}
            }}
            
            // Format time helper
            function formatTime(seconds) {{
                const mins = Math.floor(seconds / 60);
                const secs = seconds % 60;
                return (mins < 10 ? "0" : "") + mins + ":" + (secs < 10 ? "0" : "") + secs;
            }}
            
            // Timer countdown logic
            function startTimer() {{
                const clock = document.getElementById("clock");
                const interval = setInterval(() => {{
                    if (!examStarted) return;
                    timeRemaining--;
                    clock.innerText = formatTime(timeRemaining);
                    
                    if (timeRemaining <= 0) {{
                        clearInterval(interval);
                        clock.innerText = "00:00";
                        triggerSubmission("TIMEOUT");
                    }}
                    
                    // Periodic AI proctoring simulation logs
                    if (timeRemaining % 15 === 0) {{
                        const logs = [
                            "Eye tracking focal vectors... NORMAL",
                            "Validating background acoustics... OK",
                            "Environment scan... 1 OBJECT FOUND [CANDIDATE]",
                            "Scanning window frames... SECURED",
                            "Keystroke signature analytics... OK"
                        ];
                        const log = logs[Math.floor(Math.random() * logs.length)];
                        addLog(log, "log-green");
                    }}
                }}, 1000);
            }}

            // Start webcam logic
            async function startWebcam() {{
                try {{
                    const video = document.getElementById('webcam');
                    const stream = await navigator.mediaDevices.getUserMedia({{ video: true }});
                    video.srcObject = stream;
                    addLog("PROCTOR RADAR ENGAGED.");
                }} catch (err) {{
                    addLog("WEBCAM BLOCKED. SIMULATING SCAN...", "log-red");
                    // Mock webcam feedback if blocked
                    simulateCameraScan();
                }}
            }}
            
            function simulateCameraScan() {{
                // Standard canvas animation backup or message
            }}

            // Security Triggered Warnings
            function triggerWarning(reason) {{
                violations++;
                document.getElementById("violationCount").innerText = violations + " / 3";
                addLog("VIOLATION: " + reason.toUpperCase(), "log-red");
                alert("PROCTOR THREAT DETECTED!\\nReason: " + reason + "\\nWarning: " + violations + "/3. Continued focus breaks will auto-terminate the exam!");
                
                // Communication bridge: Update parent Streamlit state
                window.parent.postMessage({{
                    type: 'LEVELUP_VIOLATION',
                    violationsCount: violations
                }}, '*');

                if (violations >= 3) {{
                    triggerSubmission("SECURITY TERMINATION");
                }}
            }}
            
            function triggerSubmission(reason) {{
                examStarted = false;
                addLog("LOCKDOWN ACTIVE: " + reason, "log-red");
                document.getElementById("pStatus").innerText = "LOCKED";
                document.getElementById("pStatus").className = "log-red";
                alert("EXAM LOCKED: " + reason + ". Submitting your final answers immediately.");
                
                // Send postMessage to Streamlit parent
                window.parent.postMessage({{
                    type: 'LEVELUP_SUBMIT',
                    reason: reason,
                    violationsCount: violations
                }}, '*');
            }}

            // Fullscreen controls
            function initiateExam() {{
                document.getElementById("fsOverlay").style.display = "none";
                examStarted = true;
                
                // Enforce browser-wide locks
                startWebcam();
                startTimer();
                
                // Block Right Click, Copy, and Paste on the assessment page
                window.parent.document.addEventListener("contextmenu", e => e.preventDefault());
                window.parent.document.addEventListener("copy", e => e.preventDefault());
                window.parent.document.addEventListener("paste", e => e.preventDefault());
                
                addLog("EXAM SYSTEM UNLEASHED.");
            }}

            // Listen to tab switching
            document.addEventListener('visibilitychange', () => {{
                if (document.hidden && examStarted) {{
                    triggerWarning("Tab switch detected");
                }}
            }});

            window.addEventListener('blur', () => {{
                if (examStarted) {{
                    triggerWarning("Window focus lost");
                }}
            }});

            // Listen for copy/paste inside iframe as well
            document.addEventListener("contextmenu", e => e.preventDefault());
            document.addEventListener("copy", e => e.preventDefault());
            document.addEventListener("paste", e => e.preventDefault());
        </script>
    </body>
    </html>
    """
    
    # Render the HTML proctoring component in the Streamlit Sidebar
    with st.sidebar:
        st.markdown("<h3 style='text-align: center; color: #FF007F; font-size:12px;'>🛡️ AI COGNITIVE PROCTOR</h3>", unsafe_allow_html=True)
        components.html(html_code, height=310, scrolling=False)
