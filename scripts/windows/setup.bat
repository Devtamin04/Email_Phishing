@echo off
REM ============================================================
REM  Cai dat du an tren Windows: tao .venv + cai thu vien
REM  Yeu cau: Python 3.10 - 3.12 (tick "Add python.exe to PATH")
REM ============================================================
setlocal
cd /d "%~dp0\..\.."
set PYTHONUTF8=1

set PY=python
where py >nul 2>nul && set PY=py -3

echo [1/4] Tao moi truong ao .venv ...
if not exist .venv\Scripts\python.exe (
    %PY% -m venv .venv || goto :err
)
.venv\Scripts\python -m pip install --upgrade pip || goto :err

echo [2/4] Cai PyTorch ban CPU ...
.venv\Scripts\python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu || goto :err

echo [3/4] Cai cac thu vien con lai (requirements.txt) ...
.venv\Scripts\python -m pip install -r requirements.txt || goto :err

echo [4/4] Kiem tra cai dat ...
.venv\Scripts\python -c "import torch, transformers, gensim, fastapi, cv2, easyocr, pypdf; print('OK - torch', torch.__version__)" || goto :err

echo.
echo Hoan tat! Buoc tiep theo: scripts\windows\run_app.bat
pause
exit /b 0

:err
echo.
echo Co loi xay ra - xem thong bao phia tren.
pause
exit /b 1
