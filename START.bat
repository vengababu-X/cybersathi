@echo off
REM One-click start for CyberSathi. Opens two windows: backend API and frontend.
REM Everything runs locally. No internet connection and no API key required.

echo ============================================
echo   CyberSathi - starting both servers
echo ============================================
echo.

if not exist "backend\.venv\Scripts\python.exe" (
  echo ERROR: Python environment missing.
  echo Run SETUP.bat first.
  pause
  exit /b 1
)

if not exist "frontend\node_modules" (
  echo ERROR: Frontend packages missing.
  echo Run SETUP.bat first.
  pause
  exit /b 1
)

start "CyberSathi API" cmd /k "cd /d %~dp0backend && .venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"
timeout /t 4 /nobreak >nul
start "CyberSathi Web" cmd /k "cd /d %~dp0frontend && npm run dev"
timeout /t 5 /nobreak >nul

echo.
echo   Web app  :  http://localhost:5173
echo   API docs :  http://127.0.0.1:8000/docs
echo.
echo   Demo login: admin@cybersathi.org / Admin@123
echo.
start http://localhost:5173
echo Close the two server windows to stop.
pause
