"""
Test parsera uniwersalnego v3 - test po naprawieniu importów
Testuje parser na fakturze Faktura 11_07_2025.pdf
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.parsers.universal_parser_v2 import UniversalParser  
from app.pdf_processor import PDFProcessor
import json

def test_universal_parser():
    print("=" * 60)
    print("TEST PARSERA UNIWERSALNEGO V3")
    print("=" * 60)
    
    # Testuj na fakturze
    pdf_path = r"C:\pdf-to-xml-app\input\Faktura 11_07_2025.pdf"
    print(f"\n📄 Testowanie na: {os.path.basename(pdf_path)}")
    print("-" * 60)
    
    # Użyj PDFProcessor z wymuszonym parserem uniwersalnym
    processor = PDFProcessor(parser_type='universal')
    
    # Ekstrahuj tekst i tabele
    import pdfplumber
    text = ""
    tables = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
            page_tables = page.extract_tables()
            if page_tables:
                tables.extend(page_tables)
    
    print(f"✅ Wyekstraktowano {len(text)} znaków tekstu")
    print(f"✅ Znaleziono {len(tables)} tabel\n")
    
    # Test parsera
    parser = UniversalParser()
    result = parser.parse(text, tables)
    
    # Wyświetl wyniki
    print("-" * 60)
    print("📊 WYNIKI PARSOWANIA:")
    print("-" * 60)
    
    print("\n🏢 SPRZEDAWCA:")
    if result['seller']:
        for key, value in result['seller'].items():
            if value:
                print(f"  • {key}: {value}")
    
    print("\n🏢 NABYWCA:")
    if result['buyer']:
        for key, value in result['buyer'].items():
            if value:
                print(f"  • {key}: {value}")
    
    print("\n📋 POZYCJE FAKTURY:")
    if result['items']:
        for i, item in enumerate(result['items'], 1):
            print(f"\n  Pozycja {i}:")
            for key, value in item.items():
                if value:
                    print(f"    • {key}: {value}")
    else:
        print("  ❌ Brak pozycji")
    
    print("\n💰 PODSUMOWANIE:")
    if result['summary']:
        print(f"  • Netto: {result['summary'].get('net_total', 'N/A')} zł")
        print(f"  • VAT: {result['summary'].get('vat_total', 'N/A')} zł")
        print(f"  • Brutto: {result['summary'].get('gross_total', 'N/A')} zł")
        
        if result['summary'].get('vat_breakdown'):
            print("\n  Rozbicie VAT:")
            for rate, values in result['summary']['vat_breakdown'].items():
                print(f"    • {rate}: netto={values.get('net', 'N/A')}, "
                      f"vat={values.get('vat', 'N/A')}, "
                      f"brutto={values.get('gross', 'N/A')}")
    
    # Zapisz do JSON dla analizy
    output_path = r"C:\pdf-to-xml-app\skrypty_testowe\test_output.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Wyniki zapisane do: {output_path}")
    
    # Oceń jakość parsowania
    print("\n" + "=" * 60)
    print("OCENA JAKOŚCI PARSOWANIA:")
    print("-" * 60)
    
    checks = []
    # Sprawdź kluczowe pola
    if result.get('invoice_number'):
        checks.append("✅ Numer faktury")
    else:
        checks.append("❌ Brak numeru faktury")
    
    if result.get('invoice_date'):
        checks.append("✅ Data wystawienia")
    else:
        checks.append("❌ Brak daty wystawienia")
    
    if result['seller'].get('name') and result['seller'].get('nip'):
        checks.append("✅ Dane sprzedawcy")
    else:
        checks.append("❌ Niepełne dane sprzedawcy")
    
    if result['buyer'].get('name') and result['buyer'].get('nip'):
        checks.append("✅ Dane nabywcy")
    else:
        checks.append("❌ Niepełne dane nabywcy")
    
    if len(result.get('items', [])) > 0:
        checks.append(f"✅ {len(result['items'])} pozycji faktury")
    else:
        checks.append("❌ Brak pozycji faktury")
    
    if float(result['summary'].get('gross_total', 0)) > 0:
        checks.append("✅ Kwoty podsumowania")
    else:
        checks.append("❌ Brak kwot podsumowania")
    
    for check in checks:
        print(f"  {check}")
    
    # Oblicz wynik
    success_count = sum(1 for c in checks if c.startswith("✅"))
    total_count = len(checks)
    score = (success_count / total_count) * 100
    
    print(f"\n📈 Wynik: {success_count}/{total_count} ({score:.0f}%)")
    
    if score >= 80:
        print("🎉 Parser działa bardzo dobrze!")
    elif score >= 60:
        print("⚠️ Parser działa, ale wymaga poprawek")
    else:
        print("❌ Parser wymaga znaczących poprawek")
    
    return result

if __name__ == "__main__":
    result = test_universal_parser()
    
    # Test pełnego systemu
    print("\n\n" + "=" * 60)
    print("TEST PEŁNEGO SYSTEMU (PDF -> XML)")
    print("=" * 60)
    
    print("\n🚀 Uruchamiam pełny proces konwersji...")
    
    # Uruchom główną aplikację
    import subprocess
    app_dir = r"C:\pdf-to-xml-app"
    
    cmd = [
        sys.executable,
        os.path.join(app_dir, 'app', 'main.py'),
        '--parser', 'universal'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=app_dir)
        
        if result.returncode == 0:
            print("✅ Konwersja zakończona sukcesem!")
        else:
            print("❌ Błąd podczas konwersji")
            if result.stderr:
                print(f"Błędy: {result.stderr}")
        
        # Sprawdź czy XML został wygenerowany
        xml_path = r"C:\pdf-to-xml-app\output\output.xml"
        if os.path.exists(xml_path):
            print(f"✅ XML wygenerowany: {xml_path}")
            
            # Wyświetl pierwsze 500 znaków XML
            with open(xml_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            print("\n📄 Fragment XML:")
            print("-" * 40)
            print(xml_content[:500])
            if len(xml_content) > 500:
                print("...")
        else:
            print("❌ Brak pliku XML")
            
    except Exception as e:
        print(f"❌ Błąd: {e}")
    
    print("\n" + "=" * 60)
    print("KONIEC TESTÓW")
    print("=" * 60)
