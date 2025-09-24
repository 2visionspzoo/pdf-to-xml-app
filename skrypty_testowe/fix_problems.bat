@echo off
chcp 65001 > nul
cls
echo ╔════════════════════════════════════════════════╗
echo ║    AUTOMATYCZNA NAPRAWA PROBLEMÓW             ║
echo ╚════════════════════════════════════════════════╝
echo.

set OUTPUT_FILE=%~dp0fix_problems_log.txt
echo Log naprawy: %OUTPUT_FILE% > %OUTPUT_FILE%
echo ========================================= >> %OUTPUT_FILE%
echo %date% %time% >> %OUTPUT_FILE%
echo ========================================= >> %OUTPUT_FILE%
echo. >> %OUTPUT_FILE%

echo [1] Instalacja/aktualizacja modułów Python...
echo ───────────────────────────────────────────
echo.

echo Aktualizacja pip... | tee -a %OUTPUT_FILE%
python -m pip install --upgrade pip >> %OUTPUT_FILE% 2>&1

echo.
echo Instalacja modułów podstawowych... | tee -a %OUTPUT_FILE%
echo.

set MODULES=pdfplumber pytesseract pdf2image Pillow lxml PyPDF2 python-dateutil openpyxl pandas

for %%m in (%MODULES%) do (
    echo Instaluję %%m... | tee -a %OUTPUT_FILE%
    python -m pip install %%m >> %OUTPUT_FILE% 2>&1
    if errorlevel 1 (
        echo   ✗ Błąd instalacji %%m | tee -a %OUTPUT_FILE%
    ) else (
        echo   ✓ %%m zainstalowany | tee -a %OUTPUT_FILE%
    )
)

echo.
echo [2] Konfiguracja Tesseract...
echo ───────────────────────────────────────────
echo.

if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    echo ✓ Tesseract znaleziony | tee -a %OUTPUT_FILE%
    
    REM Dodaj do PATH jeśli nie ma
    echo %PATH% | find /i "Tesseract-OCR" >nul
    if errorlevel 1 (
        echo Dodaję Tesseract do PATH... | tee -a %OUTPUT_FILE%
        setx PATH "%PATH%;C:\Program Files\Tesseract-OCR" >> %OUTPUT_FILE% 2>&1
        set "PATH=%PATH%;C:\Program Files\Tesseract-OCR"
        echo ✓ Dodano do PATH | tee -a %OUTPUT_FILE%
    ) else (
        echo ✓ Tesseract już jest w PATH | tee -a %OUTPUT_FILE%
    )
) else (
    echo ✗ Tesseract nie znaleziony! | tee -a %OUTPUT_FILE%
    echo   Pobierz z: https://github.com/UB-Mannheim/tesseract/wiki | tee -a %OUTPUT_FILE%
)

echo.
echo [3] Konfiguracja Poppler...
echo ───────────────────────────────────────────
echo.

if exist "C:\poppler\Library\bin\pdftoppm.exe" (
    echo ✓ Poppler znaleziony w C:\poppler | tee -a %OUTPUT_FILE%
    
    REM Dodaj do PATH jeśli nie ma
    echo %PATH% | find /i "poppler" >nul
    if errorlevel 1 (
        echo Dodaję Poppler do PATH... | tee -a %OUTPUT_FILE%
        setx PATH "%PATH%;C:\poppler\Library\bin" >> %OUTPUT_FILE% 2>&1
        set "PATH=%PATH%;C:\poppler\Library\bin"
        echo ✓ Dodano do PATH | tee -a %OUTPUT_FILE%
    ) else (
        echo ✓ Poppler już jest w PATH | tee -a %OUTPUT_FILE%
    )
) else (
    echo ✗ Poppler nie znaleziony w C:\poppler! | tee -a %OUTPUT_FILE%
    echo   Pobierz z: https://github.com/oschwartz10612/poppler-windows/releases | tee -a %OUTPUT_FILE%
    echo   Rozpakuj do C:\poppler | tee -a %OUTPUT_FILE%
)

echo.
echo [4] Tworzenie brakujących katalogów...
echo ───────────────────────────────────────────
echo.

set DIRS=input output processed logs app\parsers skrypty_testowe

for %%d in (%DIRS%) do (
    if not exist "%~dp0..\%%d" (
        echo Tworzę katalog %%d... | tee -a %OUTPUT_FILE%
        mkdir "%~dp0..\%%d" >> %OUTPUT_FILE% 2>&1
        echo ✓ Utworzono %%d | tee -a %OUTPUT_FILE%
    ) else (
        echo ✓ Katalog %%d już istnieje | tee -a %OUTPUT_FILE%
    )
)

echo.
echo [5] Test końcowy...
echo ───────────────────────────────────────────
echo.

python -c "import pdfplumber, pytesseract, pdf2image; print('✓ Wszystkie moduły działają!')" 2>&1 | tee -a %OUTPUT_FILE%

if errorlevel 1 (
    echo ✗ Nadal są problemy z modułami | tee -a %OUTPUT_FILE%
) else (
    echo ✓ System gotowy do pracy! | tee -a %OUTPUT_FILE%
)

echo.
echo ════════════════════════════════════════════
echo NAPRAWA ZAKOŃCZONA
echo ════════════════════════════════════════════
echo.
echo Log zapisany w: %OUTPUT_FILE%
echo.
echo Jeśli nadal są problemy:
echo 1. Sprawdź log: %OUTPUT_FILE%
echo 2. Uruchom: test_simple.bat
echo 3. Może być konieczny restart komputera (zmienne PATH)
echo.
pause
