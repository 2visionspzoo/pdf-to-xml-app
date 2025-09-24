@echo off
chcp 65001 > nul
cls
echo ╔════════════════════════════════════════╗
echo ║         DEBUGOWANIE TESTÓW             ║
echo ╚════════════════════════════════════════╝
echo.

set TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set OUTPUT_FILE=%~dp0debug_output_%TIMESTAMP%.txt

echo Zapisuję wyniki do: %OUTPUT_FILE%
echo.

echo ========================================= > %OUTPUT_FILE%
echo DEBUG TEST - %date% %time% >> %OUTPUT_FILE%
echo ========================================= >> %OUTPUT_FILE%
echo. >> %OUTPUT_FILE%

echo Uruchamiam test debugowania...
python %~dp0debug_test.py 2>&1 | tee -a %OUTPUT_FILE%

echo. >> %OUTPUT_FILE%
echo ========================================= >> %OUTPUT_FILE%
echo INFORMACJE O SYSTEMIE >> %OUTPUT_FILE%
echo ========================================= >> %OUTPUT_FILE%
echo. >> %OUTPUT_FILE%

echo PATH: >> %OUTPUT_FILE%
echo %PATH% >> %OUTPUT_FILE%
echo. >> %OUTPUT_FILE%

echo Python version: >> %OUTPUT_FILE%
python --version >> %OUTPUT_FILE% 2>&1
echo. >> %OUTPUT_FILE%

echo Pip list: >> %OUTPUT_FILE%
pip list >> %OUTPUT_FILE% 2>&1
echo. >> %OUTPUT_FILE%

echo Tesseract version: >> %OUTPUT_FILE%
"C:\Program Files\Tesseract-OCR\tesseract.exe" --version >> %OUTPUT_FILE% 2>&1
echo. >> %OUTPUT_FILE%

echo Poppler check: >> %OUTPUT_FILE%
if exist "C:\poppler\Library\bin\pdftoppm.exe" (
    echo Poppler found at C:\poppler\Library\bin >> %OUTPUT_FILE%
    "C:\poppler\Library\bin\pdftoppm.exe" -v >> %OUTPUT_FILE% 2>&1
) else (
    echo Poppler NOT found at C:\poppler\Library\bin >> %OUTPUT_FILE%
)
echo. >> %OUTPUT_FILE%

echo.
echo ═══════════════════════════════════════
echo Wyniki zapisane do: %OUTPUT_FILE%
echo ═══════════════════════════════════════
echo.
pause
