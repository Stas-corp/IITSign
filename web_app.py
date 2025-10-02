import subprocess
import sys

def run_streamlit():
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "src/app.py", "--server.port", "63370"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при запуске Streamlit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_streamlit()