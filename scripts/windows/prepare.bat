@echo off
REM ============================================================
REM  Chuan bi du lieu mau + huan luyen mo hinh van ban
REM    prepare.bat        -> chi mo hinh TF-IDF (vai giay)
REM    prepare.bat kd     -> them KD-BiLSTM tu MobileBERT (15-30 phut tren CPU)
REM ============================================================
setlocal
cd /d "%~dp0\..\.."
set PYTHONUTF8=1
if not exist .venv\Scripts\python.exe (
    echo Chua cai dat. Hay chay scripts\windows\setup.bat truoc.
    pause & exit /b 1
)

echo [1/2] Tao 12 email mau (samples\) ...
.venv\Scripts\python scripts\build_samples.py || goto :err

echo [2/2] Huan luyen mo hinh van ban (models\) ...
if /i "%1"=="kd" (
    .venv\Scripts\python scripts\train_text_models.py --kd || goto :err
) else (
    .venv\Scripts\python scripts\train_text_models.py || goto :err
)

echo.
echo Xong! Chay giao dien: scripts\windows\run_app.bat
pause
exit /b 0

:err
echo Co loi xay ra - xem thong bao phia tren.
pause
exit /b 1
