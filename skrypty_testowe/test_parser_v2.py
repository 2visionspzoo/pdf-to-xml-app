"""
Skrypt testowy dla ulepszonego parsera uniwersalnego
Testuje nową wersję parsera na fakturze
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.parsers.universal_parser_v2 import UniversalParserV2
from app.pdf_processor import PDFProcessor
import json

def test_improved_parser():
    print("=" * 60)
    print("TEST ULEPSZONEGO PARSERA UNIWERSALNEGO V2")
    print("=" * 60)
    
    # Ścieżka do testowego pliku
    pdf_path = r"C:\pdf-to-xml-app\input\Faktura 11_07_2025.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ Nie znaleziono pliku: {pdf_path}")
        return
    
    print(f"📄 Testowany plik: {os.path.basename(pdf_path)}\n")
    
    # Ekstrakcja tekstu i tabel
    processor = PDFProcessor()
    text = processor.extract_text(pdf_path)
    tables = processor.extract_tables(pdf_path)
    
    print(f"✅ Wyekstraktowano {len(text)} znaków tekstu")
    print(f"✅ Znaleziono {len(tables)} tabel\n")
    
    # Test parsera
    parser = UniversalParserV2()
    result = parser.parse(text, tables)
    
    # Wyświetl wyniki
    print("-" * 60)
    print("WYNIKI PARSOWANIA:")
    print("-" * 60)
    
    # Podstawowe dane
    print("\n📌 DANE PODSTAWOWE:")
    print(f"  Numer faktury: {result['invoice_number']}")
    print(f"  Data wystawienia: {result['invoice_date']}")
    print(f"  Data sprzedaży: {result['sale_date']}")
    print(f"  Termin płatności: {result['payment_date']}")
    print(f"  Metoda płatności: {result['payment_method']}")
    
    # Sprzedawca
    print("\n👤 SPRZEDAWCA:")
    seller = result['seller']
    print(f"  Nazwa: {seller['name']}")
    print(f"  NIP: {seller['nip']}")
    print(f"  Adres: {seller['address']}")
    print(f"  Miasto: {seller['postal_code']} {seller['city']}")
    
    # Nabywca
    print("\n👤 NABYWCA:")
    buyer = result['buyer']
    print(f"  Nazwa: {buyer['name']}")
    print(f"  NIP: {buyer['nip']}")
    print(f"  Adres: {buyer['address']}")
    print(f"  Miasto: {buyer['postal_code']} {buyer['city']}")
    
    # Pozycje
    print("\n📦 POZYCJE FAKTURY:")
    if result['items']:
        print(f"  Znaleziono {len(result['items'])} pozycji:\n")
        for i, item in enumerate(result['items'], 1):
            print(f"  [{i}] {item['name']}")
            print(f"      Ilość: {item['quantity']} {item['unit']}")
            print(f"      Cena jedn.: {item['unit_price_net']} zł")
            print(f"      Netto: {item['net_amount']} zł")
            print(f"      VAT ({item['vat_rate']}): {item['vat_amount']} zł")
            print(f"      Brutto: {item['gross_amount']} zł")
            print()
    else:
        print("  ❌ Brak pozycji")
    
    # Podsumowanie
    print("\n💰 PODSUMOWANIE:")
    summary = result['summary']
    print(f"  Razem netto: {summary['net_total']} zł")
    print(f"  Razem VAT: {summary['vat_total']} zł")
    print(f"  Razem brutto: {summary['gross_total']} zł")
    
    if summary.get('vat_breakdown'):
        print("\n  Zestawienie VAT:")
        for rate, values in summary['vat_breakdown'].items():
            print(f"    {rate}: netto={values.get('net', '0')} zł, "
                  f"VAT={values.get('vat', '0')} zł, "
                  f"brutto={values.get('gross', '0')} zł")
    
    # Sprawdzenie poprawności
    print("\n" + "=" * 60)
    print("SPRAWDZENIE POPRAWNOŚCI:")
    print("-" * 60)
    
    checks = []
    
    # Sprawdź numer faktury
    if result['invoice_number']:
        checks.append(("✅", "Numer faktury wykryty"))
    else:
        checks.append(("❌", "Brak numeru faktury"))
    
    # Sprawdź daty
    if result['invoice_date']:
        checks.append(("✅", "Data wystawienia wykryta"))
    else:
        checks.append(("❌", "Brak daty wystawienia"))
    
    # Sprawdź sprzedawcę
    if result['seller']['name'] and result['seller']['nip']:
        checks.append(("✅", f"Sprzedawca: {result['seller']['name'][:30]}..."))
    else:
        checks.append(("❌", "Niepełne dane sprzedawcy"))
    
    # Sprawdź nabywcę
    if result['buyer']['name'] and result['buyer']['nip']:
        checks.append(("✅", f"Nabywca: {result['buyer']['name'][:30]}..."))
    else:
        checks.append(("❌", "Niepełne dane nabywcy"))
    
    # Sprawdź pozycje
    if len(result['items']) > 0:
        checks.append(("✅", f"Wykryto {len(result['items'])} pozycji"))
    else:
        checks.append(("❌", "Brak pozycji faktury"))
    
    # Sprawdź kwoty
    if float(result['summary']['gross_total']) > 0:
        checks.append(("✅", f"Kwota brutto: {result['summary']['gross_total']} zł"))
    else:
        checks.append(("❌", "Brak kwoty brutto"))
    
    for status, msg in checks:
        print(f"  {status} {msg}")
    
    # Zapisz wyniki do pliku
    output_file = r"C:\pdf-to-xml-app\skrypty_testowe\test_parser_v2_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Wyniki zapisano do: {output_file}")
    
    print("\n" + "=" * 60)
    print("KONIEC TESTU")
    print("=" * 60)

if __name__ == "__main__":
    test_improved_parser()
