#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Skrypt testowy GUI po wprowadzonych poprawkach
Testuje uruchomienie GUI i podstawowe funkcjonalności
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test importów modułów"""
    print("\n=== Test importów ===")
    
    try:
        from app.gui import PDFInvoiceConverterGUI
        print("✓ Import GUI")
    except ImportError as e:
        print(f"✗ Błąd importu GUI: {e}")
        return False
    
    try:
        from app.pdf_processor import PDFProcessor
        print("✓ Import PDFProcessor")
    except ImportError as e:
        print(f"✗ Błąd importu PDFProcessor: {e}")
        return False
    
    try:
        from app.parsers.universal_parser_v6 import UniversalParser
        print("✓ Import UniversalParser")
    except ImportError as e:
        print(f"✗ Błąd importu UniversalParser: {e}")
        return False
    
    try:
        from app.comarch_mapper import ComarchMapper
        print("✓ Import ComarchMapper")
    except ImportError as e:
        print(f"✗ Błąd importu ComarchMapper: {e}")
        return False
    
    try:
        from app.xml_generator import XMLGenerator
        print("✓ Import XMLGenerator")
    except ImportError as e:
        print(f"✗ Błąd importu XMLGenerator: {e}")
        return False
    
    return True

def test_gui_initialization():
    """Test inicjalizacji GUI (bez wyświetlania okna)"""
    print("\n=== Test inicjalizacji GUI ===")
    
    try:
        import tkinter as tk
        from app.gui import PDFInvoiceConverterGUI
        
        # Utwórz root ale nie uruchamiaj mainloop
        root = tk.Tk()
        root.withdraw()  # Ukryj okno
        
        # Próba utworzenia GUI
        gui = PDFInvoiceConverterGUI(root)
        print("✓ GUI zainicjalizowane pomyślnie")
        
        # Sprawdź czy podstawowe komponenty istnieją
        if hasattr(gui, 'pdf_processor'):
            print("✓ pdf_processor dostępny")
        
        if hasattr(gui, 'parser'):
            print("✓ parser dostępny")
        
        if hasattr(gui, 'mapper'):
            print("✓ mapper dostępny")
        
        if hasattr(gui, 'xml_generator'):
            print("✓ xml_generator dostępny")
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"✗ Błąd podczas inicjalizacji GUI: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pdf_processing_flow():
    """Test przepływu przetwarzania PDF"""
    print("\n=== Test przepływu przetwarzania ===")
    
    try:
        from app.pdf_processor import PDFProcessor
        from app.parsers.universal_parser_v6 import UniversalParser
        from app.comarch_mapper import ComarchMapper
        from app.xml_generator import XMLGenerator
        
        # Znajdź przykładowy PDF
        input_dir = r"C:\pdf-to-xml-app\input"
        pdf_files = [f for f in os.listdir(input_dir) if f.endswith('.pdf')]
        
        if not pdf_files:
            print("⚠ Brak plików PDF do testowania")
            return True
        
        test_file = os.path.join(input_dir, pdf_files[0])
        print(f"Testowanie z plikiem: {pdf_files[0]}")
        
        # 1. Ekstrakcja
        processor = PDFProcessor()
        text, tables = processor.extract_text(test_file)
        print(f"✓ Ekstrahowano {len(text)} znaków")
        
        # 2. Parsowanie
        parser = UniversalParser()
        invoice_data = parser.parse(text, tables)
        print(f"✓ Sparsowano dane faktury")
        
        # 3. Mapowanie
        mapper = ComarchMapper()
        comarch_data = mapper.map_invoice_data(invoice_data)
        print(f"✓ Zmapowano do formatu Comarch")
        
        # 4. Generowanie XML (bez zapisu)
        generator = XMLGenerator()
        xml_content = generator.generate_xml(comarch_data)
        print(f"✓ Wygenerowano XML ({len(xml_content)} znaków)")
        
        return True
        
    except Exception as e:
        print(f"✗ Błąd w przepływie: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Główna funkcja testowa"""
    print("=" * 50)
    print("TEST GUI PO POPRAWKACH")
    print("=" * 50)
    
    results = []
    
    # Test 1: Importy
    results.append(("imports", test_imports()))
    
    # Test 2: Inicjalizacja GUI
    results.append(("gui_init", test_gui_initialization()))
    
    # Test 3: Przepływ przetwarzania
    results.append(("processing_flow", test_pdf_processing_flow()))
    
    # Podsumowanie
    print("\n" + "=" * 50)
    print("PODSUMOWANIE:")
    print("=" * 50)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n✅ GUI powinno działać poprawnie!")
        print("Możesz uruchomić: python app/gui.py")
    else:
        print("\n⚠️ Wykryto problemy. Sprawdź logi powyżej.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
