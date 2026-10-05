@echo off
REM ============================================================
REM  Chay giao dien PhishLens Edu tai http://127.0.0.1:8765
REM  Dong cua so nay (hoac Ctrl+C) de tat may chu.
REM ============================================================
setlocal
cd /d "%~dp0\..\.."
set PYTHONUTF8=1
if not exist .venv\Scripts\python.exe (
    echo Chua cai dat. Hay chay scripts\windows\setup.bat truoc.
    pause & exit /b 1
)
if not exist samples\index.json .venv\Scripts\python scripts\build_samples.py
if not exist models\linear.joblib .venv\Scripts\python scripts\train_text_models.py

REM mo trinh duyet sau vai giay, khi may chu da san sang
start "" cmd /c "timeout /t 8 >nul & start http://127.0.0.1:8765"
echo Dang khoi dong may chu... (lan dau dung OCR se tai mo hinh ~100MB)
.venv\Scripts\python -m uvicorn phishlens.app:app --host 127.0.0.1 --port 8765
pause
