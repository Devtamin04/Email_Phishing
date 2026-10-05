@echo off
REM ============================================================
REM  Thi nghiem danh gia do ben (6 kich ban x 4 bo phat hien)
REM  Can chay prepare.bat kd truoc de co mo hinh KD-BiLSTM.
REM  Mat khoang 10-20 phut tren CPU (OCR anh).
REM ============================================================
setlocal
cd /d "%~dp0\..\.."
set PYTHONUTF8=1
.venv\Scripts\python scripts\robustness_eval.py --n 30 || goto :err
echo Ket qua: results\robustness.json (xem o tab "Danh gia do ben" tren giao dien)
pause
exit /b 0

:err
echo Co loi xay ra - xem thong bao phia tren.
pause
exit /b 1
