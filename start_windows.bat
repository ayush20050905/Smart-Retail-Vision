@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Create the environment and install requirements using README.md first.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m streamlit run app.py
pause
