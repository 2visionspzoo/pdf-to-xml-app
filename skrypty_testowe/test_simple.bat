@echo off
chcp 65001 > nul
cls

set TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set OUTPUT_FILE=%~dp0test_simple_output_%TIMESTAMP%.txt

echo ╔════════════════════════════════════════╗
echo ║         TEST PROSTY SYSTEMU           ║
echo ╚════════════════════════════════════════╝
echo.
echo Zapisuję wyniki do: %OUTPUT_FILE%
echo.

echo ========================================= > %OUTPUT_FILE%
echo TEST PROSTY - %date% %time% >> %OUTPUT_FILE%
echo ========================================= >> %OUTPUT_FILE%
echo. >> %OUTPUT_FILE%

echo Sprawdzanie podstawowych funkcji... | tee -a %OUTPUT_FILE%
echo. | tee -a %OUTPUT_FILE%

python %~dp0test_simple.py 2>&1 | tee -a %OUTPUT_FILE%

echo. >> %OUTPUT_FILE%
echo ========================================= >> %OUTPUT_FILE%
echo DODATKOWE INFORMACJE >> %OUTPUT_FILE%
echo ========================================= >> %OUTPUT_FILE%
echo. >> %OUTPUT_FILE%

echo Wersja Windows: >> %OUTPUT_FILE%
ver >> %OUTPUT_FILE%
echo. >> %OUTPUT_FILE%

echo Python path: >> %OUTPUT_FILE%
where python >> %OUTPUT_FILE% 2>&1
echo. >> %OUTPUT_FILE%

echo Pip version: >> %OUTPUT_FILE%
pip --version >> %OUTPUT_FILE% 2>&1
echo. >> %OUTPUT_FILE%

echo.
echo ═══════════════════════════════════════
echo Wyniki zapisane do: %OUTPUT_FILE%
echo.
echo Jeśli są błędy, sprawdź plik z wynikami.
echo ═══════════════════════════════════════
echo.
pause
