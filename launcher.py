import subprocess
import webbrowser
import time
import sys
import os

def run_desktop_app():
    # Jalankan streamlit server
    streamlit_cmd = [sys.executable, "-m", "streamlit", "run", "app.py", "--server.headless", "true", "--server.port", "8501"]
    process = subprocess.Popen(streamlit_cmd, cwd=os.getcwd())

    # Tunggu server start
    time.sleep(3)

    # Buka browser
    webbrowser.open("http://localhost:8501")

    # Tunggu process selesai
    process.wait()

if __name__ == "__main__":
    run_desktop_app()