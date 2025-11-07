import subprocess
import sys
import os
from dotenv import load_dotenv, find_dotenv

# Загрузите в runner
load_dotenv(find_dotenv(), override=True)

def run_streamlit():
    try:
        # Передайте окружение
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "src/app.py", "--server.port", "63370"],
            check=True,
            env=os.environ.copy()
        )
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при запуске Streamlit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_streamlit()