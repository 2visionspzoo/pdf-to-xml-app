"""
Test kompletnego przetwarzania faktury
Testuje cały proces: PDF -> parsowanie -> XML
"""
import sys
import os
import subprocess
import json
from pathlib import Path

# Dodaj ścieżkę do modułów
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_full_processing():
    print("=" * 60)
    print("TEST KOMPLETNEGO PRZETWARZANIA FAKTURY")
    print("=" * 60)
    
    # Ścieżki
    input_pdf = r"C:\pdf-to-xml-app\input\Faktura 11_07_2025.pdf"
    app_dir = r"C:\pdf-to-xml-app"
    output_dir = r"C:\pdf-to-xml-app\app\output"
    
    # Sprawdź czy plik istnieje
    if not os.path.exists(input_pdf):
        print(f"❌ Nie znaleziono pliku: {input_pdf}")
        return
    
    print(f"📄 Plik wejściowy: {os.path.basename(input_pdf)}")
    print(f"📁 Katalog wyjściowy: {output_dir}\n")
    
    # Usuń stare pliki wyjściowe
    print("🧹 Czyszczenie katalogu wyjściowego...")
    for file in Path(output_dir).glob("*"):
        if file.is_file():
            file.unlink()
    
    # Uruchom główną aplikację
    print("\n🚀 Uruchamiam aplikację...")
    print("-" * 40)
    
    try:
        # Zmień katalog roboczy
        os.chdir(app_dir)
        
        # Uruchom aplikację
        result = subprocess.run(
            [sys.executable, "app/main.py"],
            capture_output=True,
            text=True,
            cwd=app_dir
        )
        
        # Wyświetl output
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print("-" * 40)
        
        # Sprawdź wyniki
        print("\n📊 SPRAWDZENIE WYNIKÓW:")
        print("-" * 40)
        
        # Szukaj wygenerowanych plików
        xml_files = list(Path(output_dir).glob("*.xml"))
        json_files = list(Path(output_dir).glob("*.json"))
        
        if xml_files:
            print(f"✅ Znaleziono {len(xml_files)} plików XML:")
            for xml_file in xml_files:
                print(f"   - {xml_file.name}")
                
                # Sprawdź zawartość XML
                with open(xml_file, 'r', encoding='utf-8') as f:
                    xml_content = f.read()
                
                # Podstawowe sprawdzenia
                checks = []
                if '<Dokument>' in xml_content:
                    checks.append("✅ Zawiera tag <Dokument>")
                else:
                    checks.append("❌ Brak tagu <Dokument>")
                
                if '<Naglowek>' in xml_content:
                    checks.append("✅ Zawiera tag <Naglowek>")
                else:
                    checks.append("❌ Brak tagu <Naglowek>")
                
                if '<Pozycje>' in xml_content:
                    checks.append("✅ Zawiera tag <Pozycje>")
                else:
                    checks.append("❌ Brak tagu <Pozycje>")
                
                if '11/07/2025' in xml_content:
                    checks.append("✅ Zawiera numer faktury")
                else:
                    checks.append("❌ Brak numeru faktury")
                
                print("\n   Sprawdzenie zawartości:")
                for check in checks:
                    print(f"   {check}")
                
                # Wyświetl fragment XML
                print("\n   Fragment XML (pierwsze 500 znaków):")
                print("   " + "-" * 35)
                lines = xml_content[:500].split('\n')
                for line in lines[:10]:
                    print(f"   {line}")
                if len(xml_content) > 500:
                    print("   ...")
        else:
            print("❌ Nie znaleziono plików XML")
        
        if json_files:
            print(f"\n✅ Znaleziono {len(json_files)} plików JSON:")
            for json_file in json_files:
                print(f"   - {json_file.name}")
                
                # Załaduj i sprawdź JSON
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                print(f"\n   Analiza danych JSON:")
                if 'invoice_number' in data:
                    print(f"   • Numer faktury: {data['invoice_number']}")
                if 'seller' in data and data['seller'].get('name'):
                    print(f"   • Sprzedawca: {data['seller']['name']}")
                if 'buyer' in data and data['buyer'].get('name'):
                    print(f"   • Nabywca: {data['buyer']['name']}")
                if 'items' in data:
                    print(f"   • Liczba pozycji: {len(data['items'])}")
                if 'summary' in data:
                    print(f"   • Kwota brutto: {data['summary'].get('gross_total', 'N/A')} zł")
        
        # Podsumowanie
        print("\n" + "=" * 60)
        print("PODSUMOWANIE TESTU:")
        print("-" * 40)
        
        success = len(xml_files) > 0
        if success:
            print("✅ TEST ZAKOŃCZONY SUKCESEM")
            print(f"   Wygenerowano {len(xml_files)} plików XML")
            print(f"   Wygenerowano {len(json_files)} plików JSON")
        else:
            print("❌ TEST ZAKOŃCZONY NIEPOWODZENIEM")
            print("   Nie udało się wygenerować plików XML")
        
    except Exception as e:
        print(f"❌ Błąd podczas uruchamiania aplikacji: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("KONIEC TESTU")
    print("=" * 60)

if __name__ == "__main__":
    test_full_processing()
