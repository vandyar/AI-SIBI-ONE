@echo off
setlocal
echo AI Interview Platform Enhanced
echo ========================================
where py >nul 2>&1
if %errorlevel% equ 0 (
  py -3 -m pip install -r requirements.txt
  if errorlevel 1 exit /b 1
  py -3 run.py
) else (
  python -m pip install -r requirements.txt
  if errorlevel 1 exit /b 1
  python run.py
)
pause
