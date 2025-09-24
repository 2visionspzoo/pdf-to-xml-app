@echo off
chcp 65001 > nul
cls
echo ╔════════════════════════════════════════════════════════╗
echo ║          Instalacja Poppler dla Windows               ║
echo ║     (wymagane do konwersji PDF na obrazy)            ║
echo ╚════════════════════════════════════════════════════════╝
echo.
echo Poppler jest wymagany do konwersji PDF na obrazy (OCR).
echo.
echo INSTRUKCJA INSTALACJI:
echo ──────────────────────────────────────────────────────
echo.
echo 1. Pobierz Poppler dla Windows z:
echo    https://github.com/oschwartz10612/poppler-windows/releases
echo.
echo 2. Wybierz najnowszą wersję (np. Release-24.02.0-0.zip)
echo.
echo 3. Rozpakuj archiwum do C:\poppler
echo    (tak aby plik poppler\Library\bin\pdftoppm.exe istniał)
echo.
echo 4. Dodaj C:\poppler\Library\bin do zmiennej środowiskowej PATH:
echo    - Otwórz Panel sterowania
echo    - System i zabezpieczenia → System → Zaawansowane ustawienia
echo    - Zmienne środowiskowe → PATH → Edytuj
echo    - Dodaj nowy wpis: C:\poppler\Library\bin
echo.
echo 5. Uruchom ponownie ten skrypt aby sprawdzić instalację
echo.
echo ──────────────────────────────────────────────────────
echo.

echo Sprawdzam czy Poppler jest już zainstalowany...
echo.

if exist "C:\poppler\Library\bin\pdftoppm.exe" (
    echo ✓ Poppler znaleziony w C:\poppler
    echo.
    echo Sprawdzam wersję...
    "C:\poppler\Library\bin\pdftoppm.exe" -v
    echo.
    echo ✓ Poppler jest gotowy do użycia!
) else (
    echo ✗ Poppler nie został znaleziony w C:\poppler
    echo.
    echo Czy chcesz otworzyć stronę z pobieraniem? (T/N)
    set /p choice=
    if /i "%choice%"=="T" (
        start https://github.com/oschwartz10612/poppler-windows/releases
    )
)

echo.
echo ──────────────────────────────────────────────────────
echo.

echo Test konwersji PDF do obrazu...
python -c "from pdf2image import convert_from_path; print('✓ pdf2image działa poprawnie')" 2>nul

if errorlevel 1 (
    echo ✗ Błąd importu pdf2image
    echo Instaluję pdf2image...
    pip install pdf2image
    
    echo.
    echo Ponowny test...
    python -c "from pdf2image import convert_from_path; print('✓ pdf2image zainstalowane')"
)

echo.
pause
