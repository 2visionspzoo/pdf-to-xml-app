#!/bin/bash

# Skrypt testowy dla PDF to XML konwertera
# Zapisz jako test_pdf_converter.bat w katalogu C:\pdf-to-xml-app\skrypty_testowe

echo "=== Test PDF to XML Converter ==="

# Sprawdź czy plik PDF istnieje
echo "1. Sprawdzanie pliku PDF..."
if [ ! -f "C:\pdf-to-xml-app\faktura.pdf\input.pdf" ]; then
    echo "   BŁĄD: Plik PDF nie istnieje!"
    exit 1
fi
echo "   OK: Plik PDF znaleziony"

# Sprawdź czy katalog output istnieje
echo "2. Sprawdzanie katalogu output..."
if [ ! -d "C:\pdf-to-xml-app\app\output" ]; then
    echo "   Tworzenie katalogu output..."
    mkdir -p "C:\pdf-to-xml-app\app\output"
fi
echo "   OK: Katalog output gotowy"

# Uruchom Docker z poprawioną komendą
echo "3. Uruchamianie konwersji..."
cd "C:\pdf-to-xml-app"

# POPRAWIONA komenda Docker - mapowanie katalogu zamiast pliku
docker run --rm \
    -v "C:\pdf-to-xml-app\config.txt:/app/config.txt" \
    -v "C:\pdf-to-xml-app\faktura.pdf:/app/input" \
    -v "C:\pdf-to-xml-app\app\output:/app/output" \
    pdf-to-xml

# Sprawdź wynik
echo "4. Sprawdzanie wyniku..."
if [ -f "C:\pdf-to-xml-app\app\output\output-test1.xml" ]; then
    echo "   OK: Plik XML został wygenerowany"
    echo "   Rozmiar pliku: $(stat --printf="%s" "C:\pdf-to-xml-app\app\output\output-test1.xml") bajtów"
    echo "   Pierwsze 500 znaków pliku XML:"
    head -c 500 "C:\pdf-to-xml-app\app\output\output-test1.xml"
else
    echo "   BŁĄD: Plik XML nie został wygenerowany!"
    exit 1
fi

echo "=== Test zakończony ==="
