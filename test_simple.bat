@echo off
REM =============================================
REM Test prosty - używa PDFProcessor bezpośrednio
REM =============================================

echo.
echo ############################################################
echo #                   TEST PROSTY                           #  
echo ############################################################
echo.

cd /d C:\pdf-to-xml-app

echo Sprawdzanie plików PDF...
dir /b input\*.pdf >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [!] Brak plików PDF w katalogu input\
    echo.
    echo Umieść faktury PDF w:
    echo C:\pdf-to-xml-app\input\
    echo.
    pause
    exit /b 1
)

echo [OK] Znaleziono faktury PDF
echo.
echo Uruchamianie testu...
echo ============================================
echo.

python test_simple.py

echo.
echo ============================================
echo.
pause
