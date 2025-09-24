@echo off
chcp 65001 > nul
cls

set TIMESTAMP=%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set OUTPUT_FILE=%~dp0test_ocr_output_%TIMESTAMP%.txt

echo ╔════════════════════════════════════════╗
echo ║        Test OCR i Tesseract           ║
echo ╚════════════════════════════════════════╝
echo.
echo Zapisuję wyniki do: %OUTPUT_FILE%
echo.

echo ========================================= > %OUTPUT_FILE%
echo TEST OCR - %date% %time% >> %OUTPUT_FILE%
echo ========================================= >> %OUTPUT_FILE%
echo. >> %OUTPUT_FILE%

python %~dp0test_ocr.py 2>&1 | tee -a %OUTPUT_FILE%

echo.
echo ═══════════════════════════════════════
echo Wyniki zapisane do: %OUTPUT_FILE%
echo ═══════════════════════════════════════
echo.
pause
