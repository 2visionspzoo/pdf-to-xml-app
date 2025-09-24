@echo off
chcp 65001 > nul
echo =========================================
echo Instalator PDF-to-XML Converter v1.0
echo =========================================
echo.

echo [1] Sprawdzanie wersji Python...
python --version 2>nul
if errorlevel 1 (
    echo BŁĄD: Python nie jest zainstalowany!
    echo Pobierz z: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [2] Instalacja pakietów Python...
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo BŁĄD: Nie udało się zainstalować pakietów!
    pause
    exit /b 1
)

echo.
echo [3] Sprawdzanie Tesseract OCR...
tesseract --version 2>nul
if errorlevel 1 (
    echo.
    echo UWAGA: Tesseract OCR nie jest zainstalowany!
    echo.
    echo Pobierz i zainstaluj z:
    echo https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    echo Wybierz wersję: tesseract-ocr-w64-setup-5.3.3.20231005.exe
    echo Podczas instalacji ZAZNACZ język polski (pol)!
    echo.
    echo Po instalacji dodaj do PATH:
    echo C:\Program Files\Tesseract-OCR
    echo.
    pause
)

echo.
echo [4] Tworzenie struktury katalogów...
if not exist "input" mkdir input
if not exist "output" mkdir output
if not exist "processed" mkdir processed
if not exist "logs" mkdir logs
if not exist "skrypty_testowe" mkdir skrypty_testowe

echo.
echo =========================================
echo Instalacja zakończona!
echo =========================================
echo.
echo Umieść pliki PDF w katalogu: input\
echo Wyniki XML znajdziesz w: output\
echo.
pause