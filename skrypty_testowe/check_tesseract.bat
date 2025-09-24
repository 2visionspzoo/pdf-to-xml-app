@echo off
chcp 65001 > nul
cls
echo =========================================
echo Sprawdzanie instalacji Tesseract OCR
echo =========================================
echo.

echo [1] Sprawdzanie ścieżki Tesseract...
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    echo ✓ Tesseract znaleziony w: C:\Program Files\Tesseract-OCR
) else (
    echo ✗ Tesseract nie znaleziony!
    pause
    exit /b 1
)

echo.
echo [2] Sprawdzanie wersji Tesseract...
"C:\Program Files\Tesseract-OCR\tesseract.exe" --version

echo.
echo [3] Sprawdzanie dostępnych języków...
"C:\Program Files\Tesseract-OCR\tesseract.exe" --list-langs

echo.
echo [4] Dodawanie do PATH (jeśli potrzebne)...
set "tesseract_path=C:\Program Files\Tesseract-OCR"
echo %PATH% | find /i "%tesseract_path%" >nul
if errorlevel 1 (
    echo Dodaję Tesseract do PATH dla tej sesji...
    set "PATH=%PATH%;%tesseract_path%"
    echo ✓ Dodano do PATH
) else (
    echo ✓ Tesseract już jest w PATH
)

echo.
echo [5] Test OCR z pytesseract...
python -c "import pytesseract; pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'; print('✓ pytesseract skonfigurowany poprawnie')"

if errorlevel 1 (
    echo ✗ Problem z pytesseract!
    echo Instaluję pytesseract...
    pip install pytesseract
)

echo.
echo =========================================
echo Tesseract OCR jest gotowy do użycia!
echo =========================================
pause
