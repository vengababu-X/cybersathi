@echo off
REM First-time setup. Run once, then use START.bat.

echo ============================================
echo   CyberSathi - first time setup
echo ============================================
echo.

cd /d %~dp0backend

echo [1/5] Creating Python environment...
python -m venv .venv || goto :err

echo [2/5] Installing Python packages...
.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
.venv\Scripts\python.exe -m pip install -r requirements.txt || goto :err

echo [3/5] Generating datasets and training models...
.venv\Scripts\python.exe ml_training\generate_datasets.py || goto :err
.venv\Scripts\python.exe ml_training\train_text_model.py || goto :err
.venv\Scripts\python.exe ml_training\train_url_model.py || goto :err
.venv\Scripts\python.exe ml_training\evaluate.py

echo [4/5] Creating and seeding the database...
.venv\Scripts\python.exe -m app.seed.run --all || goto :err

cd /d %~dp0frontend
echo [5/5] Installing frontend packages...
call npm install || goto :err

echo.
echo ============================================
echo   Setup complete. Now run START.bat
echo ============================================
pause
exit /b 0

:err
echo.
echo Setup failed. See the message above.
pause
exit /b 1
