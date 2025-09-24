@echo off
chcp 65001 > nul
:MENU
cls
echo ╔═══════════════════════════════════════════════════════╗
echo ║           MENU TESTÓW I DIAGNOSTYKI                  ║
echo ╚═══════════════════════════════════════════════════════╝
echo.
echo   [1] 🔧 NAPRAW PROBLEMY (zalecane na początek)
echo   [2] 📋 Test prosty - sprawdzenie instalacji
echo   [3] 🐛 Debugowanie - szczegółowa diagnostyka
echo   [4] 🖼️  Test OCR i Tesseract
echo   [5] 📄 Test rozpoznawania faktur
echo   [6] 🔄 Test kompleksowy systemu
echo   [7] 📁 Pokaż logi testów
echo   [0] ❌ Wyjście
echo.
echo ═══════════════════════════════════════════════════════
echo.

set /p choice="Wybierz opcję (0-7): "

if "%choice%"=="1" (
    call %~dp0fix_problems.bat
    pause
    goto MENU
) else if "%choice%"=="2" (
    call %~dp0test_simple.bat
    goto MENU
) else if "%choice%"=="3" (
    call %~dp0debug_test.bat
    goto MENU
) else if "%choice%"=="4" (
    call %~dp0test_ocr.bat
    goto MENU
) else if "%choice%"=="5" (
    call %~dp0test_invoice_detection.bat
    goto MENU
) else if "%choice%"=="6" (
    call %~dp0test_system_complete.bat
    goto MENU
) else if "%choice%"=="7" (
    cls
    echo ╔═══════════════════════════════════════════════════════╗
    echo ║                  LOGI TESTÓW                         ║
    echo ╚═══════════════════════════════════════════════════════╝
    echo.
    echo Dostępne logi:
    echo ───────────────────────────────────────────────────────
    dir /b %~dp0*.txt 2>nul
    echo ───────────────────────────────────────────────────────
    echo.
    echo Naciśnij dowolny klawisz aby wrócić do menu...
    pause >nul
    goto MENU
) else if "%choice%"=="0" (
    exit
) else (
    echo.
    echo ⚠️  Nieprawidłowa opcja!
    timeout /t 2 >nul
    goto MENU
)
