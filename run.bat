@echo off
chcp 65001 > nul
title PDF-to-XML Converter

:MENU
cls
echo ╔════════════════════════════════════════╗
echo ║     PDF-to-XML Converter v1.0          ║
echo ║     Konwerter Faktur PDF → XML         ║
echo ╔════════════════════════════════════════╣
echo ║                                        ║
echo ║  [1] Konwertuj pojedynczy PDF          ║
echo ║  [2] Konwertuj wszystkie PDF (batch)   ║
echo ║  [3] Uruchom testy                     ║
echo ║  [4] Instalacja/Aktualizacja           ║
echo ║  [5] Wyjście                           ║
echo ║                                        ║
echo ╚════════════════════════════════════════╝
echo.
set /p choice="Wybierz opcję (1-5): "

if "%choice%"=="1" goto SINGLE
if "%choice%"=="2" goto BATCH
if "%choice%"=="3" goto TEST
if "%choice%"=="4" goto INSTALL
if "%choice%"=="5" goto EXIT

echo Nieprawidłowa opcja!
timeout /t 2 >nul
goto MENU

:SINGLE
cls
echo =========================================
echo Konwersja pojedynczego pliku PDF
echo =========================================
echo.
echo Dostępne pliki PDF:
echo.
dir /b input\*.pdf 2>nul
if errorlevel 1 (
    echo Brak plików PDF w katalogu input\
    pause
    goto MENU
)
echo.
set /p filename="Podaj nazwę pliku (z rozszerzeniem .pdf): "

if exist "input\%filename%" (
    echo.
    echo Przetwarzanie %filename%...
    python app\main.py --input "input\%filename%" --output "output\%filename%.xml"
    echo.
    echo Konwersja zakończona!
    echo Plik XML zapisany w: output\%filename%.xml
) else (
    echo.
    echo Błąd: Plik nie istnieje!
)
pause
goto MENU

:BATCH
cls
echo =========================================
echo Konwersja wsadowa (wszystkie pliki PDF)
echo =========================================
echo.

set count=0
for %%f in (input\*.pdf) do (
    set /a count+=1
    echo Przetwarzanie: %%~nxf
    python app\main.py --input "%%f" --output "output\%%~nf.xml"
)

echo.
echo Przetworzono plików: %count%
pause
goto MENU

:TEST
cls
call skrypty_testowe\run_tests.bat
goto MENU

:INSTALL
cls
call install.bat
goto MENU

:EXIT
echo.
echo Dziękujemy za korzystanie z PDF-to-XML Converter!
timeout /t 2 >nul
exit