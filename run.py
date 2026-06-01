import subprocess
import sys
import time
import os

def main():
    print("==================================================================")
    print("[*]                    LEVELUP AI OPERATING SYSTEM                 [*]")
    print("==================================================================")
    print("Starting system services. Initiating encrypted links...")

    # Set working directory to project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)

    # 1. Start FastAPI Backend (Uvicorn)
    backend_cmd = [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8008"]
    print("\n[SYSTEM] Launching FastAPI Backend on: http://127.0.0.1:8008")
    
    try:
        backend_process = subprocess.Popen(
            backend_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
    except Exception as e:
        print(f"[FATAL] Failed to start backend server: {str(e)}")
        sys.exit(1)

    # Give backend a moment to bind and initialize database
    time.sleep(2)

    # 2. Start Streamlit Frontend
    frontend_cmd = [sys.executable, "-m", "streamlit", "run", "frontend/app.py"]
    print("[SYSTEM] Launching Streamlit Cyberpunk UI on: http://localhost:8501")
    
    try:
        frontend_process = subprocess.Popen(
            frontend_cmd
        )
    except Exception as e:
        print(f"[FATAL] Failed to start Streamlit application: {str(e)}")
        backend_process.terminate()
        sys.exit(1)

    print("\n==================================================================")
    print("[SYSTEM] LEVELUP AI ONLINE. Cyberpunk dashboard launching in browser...")
    print("Press Ctrl+C inside the terminal to shut down all agents securely.")
    print("==================================================================")

    try:
        # Keep running and print backend output logs
        while True:
            line = backend_process.stdout.readline()
            if line:
                print(f"[BACKEND LOG] {line.strip()}")
            
            # Check if any process terminated unexpectedly
            if backend_process.poll() is not None:
                print("[FATAL] FastAPI backend terminated unexpectedly. Shutting down system.")
                break
            if frontend_process.poll() is not None:
                print("[WARNING] Streamlit frontend exited. Shutting down system.")
                break
            
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\n[SYSTEM] Shutting down autonomous agents and terminal services securely...")
    finally:
        # Secure termination of all child subprocesses
        backend_process.terminate()
        frontend_process.terminate()
        print("[SYSTEM] Services offline. Safe journey, Agent.")

if __name__ == "__main__":
    main()
