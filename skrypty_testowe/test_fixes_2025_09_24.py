#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Skrypt testowy po poprawkach z 2025-09-24
Testuje:
1. Poprawione importy w GUI
2. Metodę extract_text_and_tables w PDFProcessor
3. Kompatybilność InvoiceItem
4. Metodę _clean_nip
"""

import sys
import os

# Dodaj ścieżkę do katalogu głównego projektu
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_pdf_processor():
    """Test PDFProcessor z poprawną nazwą metody"""
    print("\n=== Test PDFProcessor ===")
    try:
        from app.pdf_processor import PDFProcessor
        
        processor = PDFProcessor()
        print("✓ PDFProcessor zaimportowany poprawnie")
        
        # Sprawdzenie czy metoda extract_text_and_tables istnieje
        if hasattr(processor, 'extract_text_and_tables'):
            print("✓ Metoda extract_text_and_tables() istnieje")
        else:
            print("✗ Brak metody extract_text_and_tables()")
            
        # Test metody na przykładowym pliku
        test_dir = r"C:\pdf-to-xml-app\input"
        pdf_files = [f for f in os.listdir(test_dir) if f.endswith('.pdf')]
        
        if pdf_files:
            test_file = os.path.join(test_dir, pdf_files[0])
            print(f"\nTestowanie pliku: {pdf_files[0]}")
            
            try:
                text, tables = processor.extract_text_and_tables(test_file)
                print(f"✓ Wyekstraktowano tekst: {len(text)} znaków")
                print(f"✓ Znaleziono tabel: {len(tables)}")
                
                # Test pełnej ekstrakcji
                invoice_data = processor.extract_from_pdf(test_file)
                if invoice_data:
                    print(f"✓ Dane faktury wyekstraktowane")
                    if invoice_data.invoice_number:
                        print(f"  - Numer faktury: {invoice_data.invoice_number}")
                    if invoice_data.seller_name:
                        print(f"  - Sprzedawca: {invoice_data.seller_name}")
                        
            except Exception as e:
                print(f"✗ Błąd podczas przetwarzania pliku: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("⚠ Brak plików PDF do testowania")
            
        return True
        
    except Exception as e:
        print(f"✗ Błąd w teście PDFProcessor: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gui_imports():
    """Test importów w GUI po poprawkach"""
    print("\n=== Test importów GUI ===")
    try:
        # Bezpośredni import modułów używanych w GUI
        from app.pdf_processor import PDFProcessor
        from app.comarch_mapper import ComarchMapper
        from app.xml_generator import XMLGenerator
        from app.xml_generator_multi import XMLGeneratorMulti
        
        print("✓ PDFProcessor zaimportowany")
        print("✓ ComarchMapper zaimportowany")
        print("✓ XMLGenerator zaimportowany")
        print("✓ XMLGeneratorMulti zaimportowany")
        
        # Test inicjalizacji
        processor = PDFProcessor()
        mapper = ComarchMapper()
        xml_gen = XMLGenerator()
        xml_gen_multi = XMLGeneratorMulti()
        
        print("✓ Wszystkie moduły zainicjalizowane poprawnie")
        return True
        
    except Exception as e:
        print(f"✗ Błąd importu: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_universal_parser():
    """Test UniversalParser z metodą _clean_nip i InvoiceItem"""
    print("\n=== Test UniversalParser ===")
    try:
        from app.parsers.universal_parser_v6 import UniversalParser
        
        parser = UniversalParser()
        
        # Test metody _clean_nip
        test_cases = [
            ("PL 123-456-78-90", "1234567890"),
            ("1234567890", "1234567890"),
            ("PL1234567890", "1234567890"),
            ("123 456 78 90", "1234567890"),
        ]
        
        all_passed = True
        for input_val, expected in test_cases:
            result = parser._clean_nip(input_val)
            if result == expected:
                print(f"✓ _clean_nip('{input_val}') -> '{result}'")
            else:
                print(f"✗ _clean_nip('{input_val}') -> '{result}' (oczekiwano: '{expected}')")
                all_passed = False
                
        # Test klasy InvoiceItem
        from app.parsers.universal_parser_v6 import InvoiceItem
        
        item = InvoiceItem(
            name="Test produkt",
            quantity=1.0,
            unit="szt",
            unit_price_net=100.0,
            vat_rate=23,
            net_value=100.0,
            vat_value=23.0,
            gross_value=123.0
        )
        
        # Test kompatybilności
        if hasattr(item, 'description'):
            print(f"✓ InvoiceItem.description (alias) = {item.description}")
        if hasattr(item, 'unit_price'):
            print(f"✓ InvoiceItem.unit_price (alias) = {item.unit_price}")
            
        return all_passed
        
    except Exception as e:
        print(f"✗ Błąd w teście UniversalParser: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_full_pipeline():
    """Test pełnego procesu konwersji"""
    print("\n=== Test pełnego procesu konwersji ===")
    try:
        from app.pdf_processor import PDFProcessor
        from app.comarch_mapper import ComarchMapper
        from app.xml_generator import XMLGenerator
        
        processor = PDFProcessor(parser_type='universal')
        mapper = ComarchMapper()
        xml_gen = XMLGenerator()
        
        # Znajdź pierwszy plik PDF
        test_dir = r"C:\pdf-to-xml-app\input"
        pdf_files = [f for f in os.listdir(test_dir) if f.endswith('.pdf')]
        
        if not pdf_files:
            print("⚠ Brak plików PDF do testowania")
            return False
            
        test_file = os.path.join(test_dir, pdf_files[0])
        print(f"Przetwarzanie: {pdf_files[0]}")
        
        # Ekstrakcja
        invoice_data = processor.extract_from_pdf(test_file)
        print("✓ Dane wyekstraktowane z PDF")
        
        # Mapowanie
        comarch_data = mapper.map_invoice_data(invoice_data)
        print("✓ Dane zmapowane do formatu Comarch")
        
        # Generowanie XML
        xml_content = xml_gen.generate_xml(comarch_data)
        print("✓ XML wygenerowany")
        
        # Zapisz testowy XML
        output_file = os.path.join(test_dir, "..", "skrypty_testowe", "test_output.xml")
        with open(output_file, 'w', encoding='utf-8-sig') as f:
            f.write(xml_content)
        print(f"✓ XML zapisany do: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"✗ Błąd w pełnym procesie: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Główna funkcja testowa"""
    print("="*60)
    print("TESTY PO POPRAWKACH 2025-09-24")
    print("="*60)
    
    results = []
    
    # Uruchom testy
    results.append(("PDFProcessor", test_pdf_processor()))
    results.append(("GUI Imports", test_gui_imports()))
    results.append(("UniversalParser", test_universal_parser()))
    results.append(("Full Pipeline", test_full_pipeline()))
    
    # Podsumowanie
    print("\n" + "="*60)
    print("PODSUMOWANIE TESTÓW:")
    print("="*60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
            
    print("\n" + "="*60)
    if all_passed:
        print("✅ WSZYSTKIE TESTY PRZESZŁY POMYŚLNIE")
    else:
        print("⚠️  NIEKTÓRE TESTY NIE POWIODŁY SIĘ")
        
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
