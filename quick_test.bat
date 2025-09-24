@echo off
REM ============================================
REM Szybki test systemu PDF to XML
REM ============================================

echo.
echo ############################################################
echo #              SZYBKI TEST SYSTEMU                        #
echo ############################################################
echo.

REM Przejdź do głównego katalogu
cd /d C:\pdf-to-xml-app

REM Sprawdź czy są pliki PDF
dir /b input\*.pdf >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Brak plików PDF w katalogu input\
    echo.
    echo Umieść faktury PDF w katalogu:
    echo C:\pdf-to-xml-app\input\
    echo.
    pause
    exit /b 1
)

echo Znaleziono faktury PDF w katalogu input\
echo.
echo Uruchamianie testu...
echo ============================================

python test_universal.py

echo.
echo ============================================
echo Test zakończony. Sprawdź wyniki powyżej.
echo.
echo Aby uruchomić pełne testy, użyj: run_tests.bat
echo.
pause
