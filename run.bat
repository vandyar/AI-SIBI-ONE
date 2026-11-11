@echo off
setlocal
echo AI Interview Platform
echo ========================================
echo.

set "PYEXE="
where py >nul 2>&1 && set "PYEXE=py -3"
if not defined PYEXE (
  python --version >nul 2>&1 && set "PYEXE=python"
)
if not defined PYEXE (
  echo Python tidak ditemukan. Install Python 3.10+ dari https://www.python.org/downloads/
  echo Centang "Add Python to PATH" saat instalasi.
  pause
  exit /b 1
)

echo Menggunakan: %PYEXE%
echo Menginstall dependensi...
%PYEXE% -m pip install -r requirements.txt
if errorlevel 1 (
  echo Gagal pip install.
  pause
  exit /b 1
)

echo.
echo Server: http://127.0.0.1:8000
echo Tekan Ctrl+C untuk berhenti.
echo ========================================
echo.

%PYEXE% run.py

pause
