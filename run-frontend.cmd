@echo off
setlocal
pushd "%~dp0frontend"

if not exist "node_modules" (
  echo Frontend dependencies were not found.
  echo Run npm install in the frontend directory first.
  popd
  exit /b 1
)

call npm run dev
set "exit_code=%ERRORLEVEL%"
popd
exit /b %exit_code%
