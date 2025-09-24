@echo off
REM ============================================
REM Instalator systemu PDF to XML Converter
REM ============================================

echo.
echo ############################################################
echo #         PDF to XML Converter - INSTALATOR               #
echo ############################################################
echo.

REM Sprawdź Python
echo [1/5] Sprawdzanie Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Python nie jest zainstalowany lub nie jest w PATH!
    echo     Pobierz z: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python znaleziony

REM Sprawdź pip
echo [2/5] Sprawdzanie pip...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] pip nie jest zainstalowany!
    echo     Instalowanie pip...
    python -m ensurepip --default-pip
)
echo [OK] pip dostępny

REM Instaluj zależności Python
echo [3/5] Instalowanie zależności Python...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [!] Niektóre pakiety mogły się nie zainstalować
    echo     Spróbuj: pip install -r requirements.txt --user
) else (
    echo [OK] Zależności zainstalowane
)

REM Sprawdź Tesseract
echo [4/5] Sprawdzanie Tesseract OCR...
tesseract --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Tesseract nie jest zainstalowany lub nie jest w PATH
    echo.
    echo     Opcje instalacji:
    echo     1. Uruchom instalator: tesseract-ocr-w64-setup-5.5.0.20241111.exe
    echo     2. Lub pobierz z: https://github.com/UB-Mannheim/tesseract/wiki
    echo     3. Dodaj do PATH: C:\Program Files\Tesseract-OCR
    echo.
    choice /C YN /M "Czy chcesz uruchomić instalator Tesseract teraz?"
    if errorlevel 2 goto skip_tesseract
    if errorlevel 1 (
        if exist "tesseract-ocr-w64-setup-5.5.0.20241111.exe" (
            start tesseract-ocr-w64-setup-5.5.0.20241111.exe
            echo Poczekaj na zakończenie instalacji Tesseract...
            pause
        ) else (
            echo [!] Instalator nie znaleziony
        )
    )
) else (
    echo [OK] Tesseract zainstalowany
)
:skip_tesseract

REM Sprawdź Poppler
echo [5/5] Sprawdzanie Poppler...
where pdftoppm >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Poppler nie jest zainstalowany lub nie jest w PATH
    echo.
    echo     Instrukcja instalacji:
    echo     1. Pobierz z: https://github.com/oschwartz10612/poppler-windows/releases/
    echo     2. Rozpakuj do C:\poppler
    echo     3. Dodaj do PATH: C:\poppler\Library\bin
    echo.
) else (
    echo [OK] Poppler zainstalowany
)

REM Tworzenie katalogów
echo.
echo Tworzenie struktury katalogów...
if not exist "input" mkdir input
if not exist "output" mkdir output
if not exist "logs" mkdir logs
echo [OK] Katalogi utworzone

REM Test instalacji
echo.
echo ============================================
echo TESTOWANIE INSTALACJI
echo ============================================
python -c "import pytesseract; import pdf2image; print('[OK] Moduły Python działają')"
if %errorlevel% neq 0 (
    echo [!] Problem z modułami Python
)

REM Podsumowanie
echo.
echo ############################################################
echo #                    INSTALACJA ZAKOŃCZONA                #
echo ############################################################
echo.
echo Następne kroki:
echo 1. Umieść faktury PDF w katalogu 'input'
echo 2. Uruchom: python app/main.py
echo    lub: python skrypty_testowe/test_quick.py
echo.
echo Aby przetestować system:
echo   python skrypty_testowe/test_parser_fixes_part1.py
echo.
pause
