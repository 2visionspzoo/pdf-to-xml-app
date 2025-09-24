#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test systemu zbierającego wszystkie faktury do jednego XML
"""

import sys
import os
from pathlib import Path
import subprocess
import time

# Dodaj katalog główny do ścieżki
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_single_xml_output():
    """Testuje generowanie jednego XML ze wszystkich faktur"""
    print("=" * 60)
    print("TEST: WSZYSTKIE FAKTURY → JEDEN XML")
    print("=" * 60)
    
    # Ścieżki
    input_dir = Path(r"C:\pdf-to-xml-app\input")
    output_file = Path(r"C:\pdf-to-xml-app\output\wszystkie_faktury.xml")
    
    # Sprawdź pliki wejściowe
    pdf_files = list(input_dir.glob("*.pdf"))
    print(f"\n📁 Pliki PDF do przetworzenia: {len(pdf_files)}")
    for i, pdf in enumerate(pdf_files, 1):
        print(f"   {i}. {pdf.name}")
    
    # Usuń stary plik jeśli istnieje
    if output_file.exists():
        output_file.unlink()
        print(f"\n🧹 Usunięto stary plik: {output_file.name}")
    
    # Uruchom konwersję
    print(f"\n🚀 Uruchamiam konwersję do jednego pliku XML...")
    print("-" * 40)
    
    start_time = time.time()
    
    cmd = [
        sys.executable,
        r"C:\pdf-to-xml-app\app\main_multi.py",
        "--input-dir", str(input_dir),
        "--output", str(output_file)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - start_time
    
    # Wyświetl output
    print(result.stdout)
    if result.stderr:
        print("BŁĘDY:", result.stderr)
    
    # Sprawdź wynik
    print("\n" + "=" * 60)
    print("WYNIKI TESTU")
    print("=" * 60)
    
    if output_file.exists():
        size = output_file.stat().st_size / 1024
        print(f"\n✅ SUKCES! Wygenerowano plik XML")
        print(f"📄 Plik: {output_file.name}")
        print(f"📏 Rozmiar: {size:.1f} KB")
        print(f"⏱️ Czas: {elapsed:.2f} sekund")
        
        # Sprawdź zawartość
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Policz faktury
        invoice_count = content.count("<FakturaZakup>")
        item_count = content.count("<FakturaZakupWiersz>")
        
        print(f"\n📊 Zawartość XML:")
        print(f"   • Liczba faktur: {invoice_count}")
        print(f"   • Liczba pozycji: {item_count}")
        
        # Sprawdź kodowanie
        if "SPÓŁKA" in content:
            print(f"   • Kodowanie: ✅ Poprawne")
        else:
            print(f"   • Kodowanie: ⚠️ Sprawdź polskie znaki")
        
        # Pokaż fragment
        print(f"\n📄 Fragment XML (pierwsze 500 znaków):")
        print("-" * 40)
        print(content[:500] + "...")
        
        # Sprawdź podsumowanie
        if "<Podsumowanie>" in content:
            import re
            suma_netto = re.search(r'<SumaNetto>(.*?)</SumaNetto>', content)
            suma_vat = re.search(r'<SumaVAT>(.*?)</SumaVAT>', content)
            suma_brutto = re.search(r'<SumaBrutto>(.*?)</SumaBrutto>', content)
            
            if suma_netto and suma_vat and suma_brutto:
                print(f"\n💰 PODSUMOWANIE FINANSOWE:")
                print(f"   • Suma netto: {suma_netto.group(1)} PLN")
                print(f"   • Suma VAT: {suma_vat.group(1)} PLN")
                print(f"   • Suma brutto: {suma_brutto.group(1)} PLN")
    else:
        print(f"\n❌ NIEPOWODZENIE: Plik XML nie został utworzony")
        print(f"Sprawdź logi powyżej")

def test_direct_api():
    """Test bezpośredniego API (bez subprocess)"""
    print("\n" + "=" * 60)
    print("TEST BEZPOŚREDNIEGO API")
    print("=" * 60)
    
    try:
        from app.pdf_processor import PDFProcessor
        from app.comarch_mapper import ComarchMapper
        from app.xml_generator_multi import XMLGeneratorMulti
        
        input_dir = Path(r"C:\pdf-to-xml-app\input")
        pdf_files = list(input_dir.glob("*.pdf"))
        
        processor = PDFProcessor(parser_type='universal')
        mapper = ComarchMapper()
        generator = XMLGeneratorMulti()
        
        all_invoices = []
        
        print(f"\nPrzetwarzanie {len(pdf_files)} plików...")
        for pdf_file in pdf_files:
            try:
                invoice_data = processor.extract_from_pdf(str(pdf_file))
                comarch_data = mapper.map_invoice_data(invoice_data)
                all_invoices.append(comarch_data)
                print(f"  ✅ {pdf_file.name}")
            except Exception as e:
                print(f"  ❌ {pdf_file.name}: {e}")
        
        if all_invoices:
            print(f"\nGenerowanie XML z {len(all_invoices)} fakturami...")
            xml_content = generator.generate_multi_invoice_xml(all_invoices)
            
            output_file = Path(r"C:\pdf-to-xml-app\output\test_api.xml")
            with open(output_file, 'w', encoding='utf-8-sig') as f:
                f.write(xml_content)
            
            print(f"✅ Zapisano do: {output_file.name}")
        
    except Exception as e:
        print(f"❌ Błąd: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test 1: Przez subprocess
    test_single_xml_output()
    
    # Test 2: Bezpośrednie API
    test_direct_api()
    
    input("\nNaciśnij ENTER aby zakończyć...")
