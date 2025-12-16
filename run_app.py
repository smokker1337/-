import subprocess
import sys
import time
import webbrowser

PYTHON = sys.executable

def main():
    print(" Запуск FastAPI + Streamlit...")

    # 1. Запуск FastAPI на 2281
    api_process = subprocess.Popen(
        [PYTHON, "-m", "uvicorn", "app:app", "--reload", "--port", "2281"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    time.sleep(3)  # ждём, чтобы API успел стартовать

    # 2. Запуск Streamlit на другом порту, например, 8501
    ui_process = subprocess.Popen(
        [PYTHON, "-m", "streamlit", "run", "ui_streamlit.py",
         "--server.port", "8501", "--server.address", "localhost"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    # Открываем браузер (UI)
    time.sleep(3)
    webbrowser.open("http://localhost:8501")

    print(" Приложение запущено")
    print("   API: http://127.0.0.1:2281/docs")
    print("   UI : http://localhost:8501")
    print(" Для остановки нажми Ctrl+C")

    try:
        api_process.wait()
        ui_process.wait()
    except KeyboardInterrupt:
        print("\n Остановка приложения...")
        api_process.terminate()
        ui_process.terminate()

if __name__ == "__main__":
    main()
