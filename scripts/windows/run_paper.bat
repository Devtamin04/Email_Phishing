@echo off
REM ============================================================
REM  Tai hien bai bao (phishkd): du lieu + cac mo hinh baseline
REM    run_paper.bat        -> LSTM, BiLSTM, +SH, +MH (1 fold, nhanh)
REM    run_paper.bat full   -> them MobileBERT + KD-BiLSTM, 5 fold (rat lau tren CPU)
REM ============================================================
setlocal
cd /d "%~dp0\..\.."
set PYTHONUTF8=1

echo [1/2] Chuan bi corpus (data\corpus.csv) ...
.venv\Scripts\python scripts\prepare_data.py || goto :err

echo [2/2] Chay thi nghiem 5 kich ban ...
if /i "%1"=="full" (
    .venv\Scripts\python scripts\run_experiments.py --bert-max-len 128 || goto :err
) else (
    .venv\Scripts\python scripts\run_experiments.py --models lstm,bilstm,bilstm_sh,bilstm_mh --max-folds 1 || goto :err
)
echo Ket qua: results\results_summary.csv
pause
exit /b 0

:err
echo Co loi xay ra - xem thong bao phia tren.
pause
exit /b 1
