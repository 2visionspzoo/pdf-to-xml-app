@echo off
REM Skrypt testowy dla PDF to XML konwertera - wersja Windows
REM Zapisz jako test_pdf_converter.bat

echo === Test PDF to XML Converter ===

REM Sprawdź czy plik PDF istnieje
echo 1. Sprawdzanie pliku PDF...
if not exist "C:\pdf-to-xml-app\faktura.pdf\input.pdf" (
    echo    BŁĄD: Plik PDF nie istnieje!
    pause
    exit /b 1
)
echo    OK: Plik PDF znaleziony

REM Sprawdź czy katalog output istnieje
echo 2. Sprawdzanie katalogu output...
if not exist "C:\pdf-to-xml-app\app\output" (
    echo    Tworzenie katalogu output...
    mkdir "C:\pdf-to-xml-app\app\output"
)
echo    OK: Katalog output gotowy

REM Przejdź do katalogu głównego
echo 3. Przygotowanie do uruchomienia...
cd /d "C:\pdf-to-xml-app"

REM Zaktualizuj config.txt z poprawną ścieżką
echo 4. Aktualizacja konfiguracji...
echo [PATHS] > config.txt
echo input_pdf = /app/input/input.pdf >> config.txt
echo output_xml = /app/output/output-test1.xml >> config.txt

REM Uruchom Docker z poprawioną komendą
echo 5. Uruchamianie konwersji...
docker run --rm -v "C:\pdf-to-xml-app\config.txt:/app/config.txt" -v "C:\pdf-to-xml-app\faktura.pdf:/app/input" -v "C:\pdf-to-xml-app\app\output:/app/output" pdf-to-xml

REM Sprawdź wynik
echo 6. Sprawdzanie wyniku...
if exist "C:\pdf-to-xml-app\app\output\output-test1.xml" (
    echo    OK: Plik XML został wygenerowany
    for %%A in ("C:\pdf-to-xml-app\app\output\output-test1.xml") do echo    Rozmiar pliku: %%~zA bajtów
    echo    Zawartość pliku XML:
    type "C:\pdf-to-xml-app\app\output\output-test1.xml"
) else (
    echo    BŁĄD: Plik XML nie został wygenerowany!
    pause
    exit /b 1
)

echo === Test zakończony ===
pause
