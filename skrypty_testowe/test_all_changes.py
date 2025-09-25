#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt testowy do weryfikacji zmian w aplikacji PDF-to-XML
Autor: Assistant
Data: 2025-09-24
"""

import os
import sys
import subprocess
from pathlib import Path
import importlib.util
import xml.etree.ElementTree as ET
import traceback

# Ścieżki
APP_DIR = Path(r"C:\pdf-to-xml-app")
APP_PATH = APP_DIR / "app"
INPUT_DIR = APP_DIR / "input"
OUTPUT_DIR = APP_DIR / "output"
TEST_OUTPUT_DIR = APP_DIR / "skrypty_testowe" / "test_output"

def test_imports():
    """Testuje czy wszystkie moduły można zaimportować"""
    print("\n🔍 Test 1: Sprawdzanie importów...")
    
    modules_to_test = [
        ("PyPDF2", "PyPDF2"),
        ("pdf2image", "pdf2image"),
        ("PIL", "PIL"),
        ("lxml", "lxml"),
        ("pytesseract", "pytesseract"),
        ("spacy (opcjonalnie)", "spacy"),
    ]
    
    results = []
    for name, module in modules_to_test:
        try:
            __import__(module)
            print(f"  ✅ {name}")
            results.append((name, True))
        except ImportError as e:
            if "spacy" in module:
                print(f"  ⚠️ {name} - nie zainstalowany (opcjonalny)")
            else:
                print(f"  ❌ {name} - {e}")
            results.append((name, False))
    
    required_ok = all(ok for name, ok in results if "opcjonalnie" not in name)
    return required_ok

def test_app_structure():
    """Sprawdza strukturę aplikacji"""
    print("\n📁 Test 2: Sprawdzanie struktury aplikacji...")
    
    required_files = [
        APP_PATH / "main.py",
        APP_PATH / "pdf_processor.py",
        APP_PATH / "comarch_mapper.py",
        APP_PATH / "xml_generator.py",
        APP_PATH / "parsers" / "universal_parser_v6.py",
    ]
    
    all_exist = True
    for file_path in required_files:
        if file_path.exists():
            print(f"  ✅ {file_path.relative_to(APP_DIR)}")
        else:
            print(f"  ❌ Brak: {file_path.relative_to(APP_DIR)}")
            all_exist = False
    
    return all_exist

def test_pdf_processor():
    """Testuje moduł pdf_processor"""
    print("\n⚙️ Test 3: Testowanie PDFProcessor...")
    
    try:
        # Dodaj ścieżkę do sys.path
        sys.path.insert(0, str(APP_PATH))
        
        from pdf_processor import PDFProcessor
        
        processor = PDFProcessor()
        print("  ✅ PDFProcessor zainicjalizowany")
        
        # Test metod
        if hasattr(processor, 'extract_from_pdf'):
            print("  ✅ Metoda extract_from_pdf istnieje")
        else:
            print("  ❌ Brak metody extract_from_pdf")
            return False
            
        return True
        
    except Exception as e:
        print(f"  ❌ Błąd: {e}")
        if "--verbose" in sys.argv:
            traceback.print_exc()
        return False

def test_parser():
    """Testuje parser uniwersalny"""
    print("\n📝 Test 4: Testowanie parsera...")
    
    try:
        sys.path.insert(0, str(APP_PATH))
        
        # Sprawdź który parser jest używany
        try:
            from parsers.universal_parser_v6 import UniversalParser
            parser_name = "universal_parser_v6"
        except ImportError:
            try:
                from parsers.universal_parser_v5 import UniversalParser
                parser_name = "universal_parser_v5"
            except ImportError:
                from parsers.universal_parser import UniversalParser
                parser_name = "universal_parser"
        
        print(f"  ℹ️ Używany parser: {parser_name}")
        
        parser = UniversalParser()
        print("  ✅ Parser zainicjalizowany")
        
        # Test przykładowego tekstu
        test_text = """
        Faktura VAT nr FV/2025/01/001
        Data wystawienia: 2025-01-15
        NIP: 5252822767
        Kwota brutto: 1230.00 PLN
        VAT 23%: 230.00 PLN
        """
        
        result = parser.extract_invoice_data(test_text)
        
        if result:
            print("  ✅ Parser zwrócił dane")
            if result.get('numer'):
                print(f"    - Numer faktury: {result['numer']}")
            if result.get('data_wystawienia'):
                print(f"    - Data: {result['data_wystawienia']}")
        else:
            print("  ⚠️ Parser zwrócił pusty wynik")
            
        return True
        
    except Exception as e:
        print(f"  ❌ Błąd: {e}")
        if "--verbose" in sys.argv:
            traceback.print_exc()
        return False

def test_xml_generation():
    """Testuje generowanie XML"""
    print("\n📄 Test 5: Testowanie generowania XML...")
    
    try:
        sys.path.insert(0, str(APP_PATH))
        
        from xml_generator import XMLGenerator
        from comarch_mapper import ComarchMapper
        
        # Przykładowe dane testowe
        test_invoice = {
            'numer': 'TEST/2025/001',
            'data_wystawienia': '2025-01-15',
            'data_sprzedazy': '2025-01-15',
            'kontrahent': {
                'nip': '5252822767',
                'nazwa': 'Test Company Sp. z o.o.',
                'adres': 'ul. Testowa 1, 00-001 Warszawa'
            },
            'pozycje': [
                {
                    'opis': 'Usługa testowa',
                    'ilosc': 1,
                    'cena_netto': 1000.00,
                    'vat': 23,
                    'kwota_vat': 230.00
                }
            ],
            'podsumowanie': {
                'netto': 1000.00,
                'vat': 230.00,
                'brutto': 1230.00
            }
        }
        
        # Mapowanie danych
        mapper = ComarchMapper()
        mapped_data = mapper.map_invoice_data(test_invoice)
        print("  ✅ Dane zmapowane")
        
        # Generowanie XML
        generator = XMLGenerator()
        xml_content = generator.generate_xml(mapped_data)
        
        if xml_content:
            print("  ✅ XML wygenerowany")
            
            # Sprawdź czy XML jest poprawny
            try:
                root = ET.fromstring(xml_content)
                print("  ✅ XML jest poprawnie sformatowany")
                
                # Zapisz przykładowy XML
                TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                test_xml_path = TEST_OUTPUT_DIR / "test_invoice.xml"
                with open(test_xml_path, 'w', encoding='utf-8') as f:
                    f.write(xml_content)
                print(f"  ✅ Przykładowy XML zapisany: {test_xml_path}")
                
            except ET.ParseError as e:
                print(f"  ❌ XML niepoprawny: {e}")
                return False
        else:
            print("  ❌ Brak wygenerowanego XML")
            return False
            
        return True
        
    except Exception as e:
        print(f"  ❌ Błąd: {e}")
        if "--verbose" in sys.argv:
            traceback.print_exc()
        return False

def test_main_app():
    """Testuje główną aplikację"""
    print("\n🚀 Test 6: Test głównej aplikacji...")
    
    try:
        # Test czy aplikacja się uruchamia
        result = subprocess.run(
            [sys.executable, str(APP_PATH / "main.py"), "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("  ✅ Aplikacja uruchamia się poprawnie")
            print("  ℹ️ Dostępne opcje:")
            for line in result.stdout.split('\n'):
                if '--' in line:
                    print(f"    {line.strip()}")
            return True
        else:
            print(f"  ❌ Błąd uruchomienia: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("  ❌ Timeout przy uruchamianiu aplikacji")
        return False
    except Exception as e:
        print(f"  ❌ Błąd: {e}")
        return False

def check_pdf_files():
    """Sprawdza dostępne pliki PDF"""
    print("\n📂 Test 7: Sprawdzanie plików PDF...")
    
    pdf_files = list(INPUT_DIR.glob("*.pdf"))
    
    if pdf_files:
        print(f"  ✅ Znaleziono {len(pdf_files)} plików PDF:")
        for pdf in pdf_files[:5]:  # Pokaż max 5
            print(f"    - {pdf.name}")
        if len(pdf_files) > 5:
            print(f"    ... i {len(pdf_files) - 5} więcej")
        return True
    else:
        print(f"  ⚠️ Brak plików PDF w katalogu: {INPUT_DIR}")
        print("    Umieść pliki PDF w tym katalogu przed przetwarzaniem")
        return True  # Nie jest to błąd krytyczny

def main():
    """Główna funkcja testowa"""
    print("="*60)
    print("🧪 TESTY APLIKACJI PDF-TO-XML")
    print("="*60)
    
    if "--verbose" in sys.argv:
        print("ℹ️ Tryb verbose włączony")
    
    # Uruchom testy
    tests = [
        ("Importy", test_imports),
        ("Struktura", test_app_structure),
        ("PDFProcessor", test_pdf_processor),
        ("Parser", test_parser),
        ("Generator XML", test_xml_generation),
        ("Główna aplikacja", test_main_app),
        ("Pliki PDF", check_pdf_files),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test {name} nieoczekiwanie zakończył się błędem: {e}")
            results.append((name, False))
    
    # Podsumowanie
    print("\n" + "="*60)
    print("📊 PODSUMOWANIE TESTÓW:")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {name}")
    
    print(f"\nWynik: {passed}/{total} testów zaliczonych")
    
    if passed == total:
        print("\n🎉 Wszystkie testy zaliczone! Aplikacja gotowa do użycia.")
        print("\n📌 Następne kroki:")
        print("  1. Umieść faktury PDF w: C:\\pdf-to-xml-app\\input\\")
        print("  2. Uruchom: python app\\main.py --batch")
        print("  3. Wyniki znajdziesz w: C:\\pdf-to-xml-app\\output\\")
    else:
        print("\n⚠️ Niektóre testy nie przeszły.")
        print("\n🔧 Rozwiązania:")
        if not results[0][1]:  # Test importów
            print("  1. Zainstaluj brakujące moduły:")
            print("     python skrypty_testowe\\install_missing_modules.py")
        if not results[2][1] or not results[3][1]:  # PDFProcessor lub Parser
            print("  2. Jeśli problem z spacy, wyłącz tymczasowo:")
            print("     python skrypty_testowe\\disable_spacy_temp.py")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
