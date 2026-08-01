@echo off
setlocal
pushd "%~dp0backend"

if not exist ".venv\Scripts\python.exe" (
  echo Backend virtual environment was not found.
  echo Run the backend setup steps in README.md first.
  popd
  exit /b 1
)

".venv\Scripts\python.exe" -m uvicorn app.main:app --reload --port 8000
set "exit_code=%ERRORLEVEL%"
popd
exit /b %exit_code%
