@echo off
chcp 65001 > nul
cls
echo ╔════════════════════════════════════════════╗
echo ║    KOMPLEKSOWE TESTY APLIKACJI PDF-TO-XML ║
echo ╚════════════════════════════════════════════╝
echo.
echo Wybierz test do uruchomienia:
echo ────────────────────────────────────────────
echo.
echo [1] Test pełny systemu (wszystkie moduły)
echo [2] Test OCR i Tesseract
echo [3] Test rozpoznawania typów faktur
echo [4] Test kompleksowy przepływu
echo [5] Test instalacji i zależności
echo [6] Uruchom wszystkie testy
echo [0] Wyjście
echo.

set /p choice="Wybierz opcję (0-6): "

if "%choice%"=="1" (
    cls
    python %~dp0test_full.py
) else if "%choice%"=="2" (
    cls
    python %~dp0test_ocr.py
) else if "%choice%"=="3" (
    cls
    python %~dp0test_invoice_detection.py
) else if "%choice%"=="4" (
    cls
    python %~dp0test_system_complete.py
) else if "%choice%"=="5" (
    cls
    call %~dp0check_tesseract.bat
) else if "%choice%"=="6" (
    cls
    echo ══════════════════════════════════════
    echo URUCHAMIANIE WSZYSTKICH TESTÓW
    echo ══════════════════════════════════════
    echo.
    
    echo [TEST 1/4] Instalacja i zależności...
    echo ──────────────────────────────────────
    python %~dp0test_full.py
    echo.
    
    echo [TEST 2/4] OCR i Tesseract...
    echo ──────────────────────────────────────
    python %~dp0test_ocr.py
    echo.
    
    echo [TEST 3/4] Rozpoznawanie typów faktur...
    echo ──────────────────────────────────────
    python %~dp0test_invoice_detection.py
    echo.
    
    echo [TEST 4/4] Przepływ kompletny...
    echo ──────────────────────────────────────
    python %~dp0test_system_complete.py
    echo.
    
    echo ══════════════════════════════════════
    echo WSZYSTKIE TESTY ZAKOŃCZONE
    echo ══════════════════════════════════════
) else if "%choice%"=="0" (
    exit
) else (
    echo Nieprawidłowa opcja!
    timeout /t 2 >nul
    call %~dp0run_tests.bat
)

echo.
pause
