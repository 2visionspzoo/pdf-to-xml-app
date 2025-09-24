@echo off
chcp 65001 > nul
cls
echo ╔════════════════════════════════════════════════════════╗
echo ║     SPRAWDZENIE I INSTALACJA POPPLER                  ║
echo ╚════════════════════════════════════════════════════════╝
echo.

echo [1] Sprawdzanie obecnej instalacji Poppler...
echo ──────────────────────────────────────────────────────

if exist "C:\poppler" (
    echo ✓ Folder C:\poppler istnieje
    echo.
    echo Sprawdzanie struktury katalogów...
    
    if exist "C:\poppler\Library\bin" (
        echo ✓ Folder Library\bin istnieje
        
        if exist "C:\poppler\Library\bin\pdftoppm.exe" (
            echo ✓ pdftoppm.exe znaleziony
        ) else (
            echo ✗ pdftoppm.exe BRAK!
        )
        
        if exist "C:\poppler\Library\bin\pdfinfo.exe" (
            echo ✓ pdfinfo.exe znaleziony
        ) else (
            echo ✗ pdfinfo.exe BRAK!
        )
    ) else (
        echo ✗ Folder Library\bin NIE istnieje!
        echo.
        echo Struktura powinna wyglądać tak:
        echo C:\poppler\
        echo  └── Library\
        echo       └── bin\
        echo            ├── pdftoppm.exe
        echo            ├── pdfinfo.exe
        echo            └── ... (inne pliki)
    )
) else (
    echo ✗ Folder C:\poppler NIE istnieje!
)

echo.
echo ════════════════════════════════════════════════════════
echo INSTRUKCJA INSTALACJI POPPLER:
echo ════════════════════════════════════════════════════════
echo.
echo 1. Otwórz stronę: https://github.com/oschwartz10612/poppler-windows/releases
echo.
echo 2. Pobierz najnowszą wersję (np. Release-24.08.0-0.zip)
echo    Kliknij na "Assets" i pobierz plik ZIP
echo.
echo 3. Rozpakuj archiwum ZIP
echo.
echo 4. Skopiuj folder "Library" do C:\poppler\
echo    tak aby struktura wyglądała:
echo    C:\poppler\Library\bin\pdftoppm.exe
echo.
echo 5. Uruchom ponownie ten skrypt aby sprawdzić instalację
echo.
echo ────────────────────────────────────────────────────────

set /p open="Czy otworzyć stronę z pobieraniem? (T/N): "
if /i "%open%"=="T" (
    start https://github.com/oschwartz10612/poppler-windows/releases
)

echo.
echo [2] Test konwersji PDF (jeśli Poppler jest zainstalowany)...
echo ──────────────────────────────────────────────────────

if exist "C:\poppler\Library\bin\pdftoppm.exe" (
    python -c "from pdf2image import convert_from_path; print('Test pdf2image...')"
    
    python -c "import os; from pdf2image import convert_from_path; input_dir = os.path.join('..', 'input'); pdfs = [f for f in os.listdir(input_dir) if f.endswith('.pdf')] if os.path.exists(input_dir) else []; print(f'Znaleziono {len(pdfs)} plików PDF w input/') if pdfs else print('Brak plików PDF w input/')"
    
    echo.
    echo Próba konwersji z poppler_path...
    python -c "import os; from pdf2image import convert_from_path; poppler_path = r'C:\poppler\Library\bin'; input_dir = os.path.join('..', 'input'); pdfs = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.endswith('.pdf')] if os.path.exists(input_dir) else []; images = convert_from_path(pdfs[0], dpi=150, poppler_path=poppler_path) if pdfs else None; print(f'✓ Konwersja działa! {len(images)} stron') if images else print('Brak PDF do testu')" 2>&1
) else (
    echo ✗ Poppler nie jest zainstalowany - pomiń test
)

echo.
pause
