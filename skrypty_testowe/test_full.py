#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt testowy dla PDF-to-XML Converter
Testuje podstawowe funkcjonalności aplikacji
"""

import os
import sys
import traceback
from pathlib import Path

# Dodaj ścieżkę do modułów aplikacji
sys.path.insert(0, r'C:\pdf-to-xml-app\app')

def test_imports():
    """Test importu modułów"""
    print("[TEST 1] Sprawdzanie importów...")
    try:
        import pdfplumber
        print("✓ pdfplumber")
        
        import pytesseract
        print("✓ pytesseract")
        
        import pdf2image
        print("✓ pdf2image")
        
        import lxml
        print("✓ lxml")
        
        from pdf_processor import PDFProcessor
        print("✓ pdf_processor")
        
        from comarch_mapper import ComarchMapper
        print("✓ comarch_mapper")
        
        from xml_generator import XMLGenerator
        print("✓ xml_generator")
        
        return True
    except ImportError as e:
        print(f"✗ Błąd importu: {e}")
        return False

def test_tesseract():
    """Test instalacji Tesseract OCR"""
    print("\n[TEST 2] Sprawdzanie Tesseract OCR...")
    try:
        import pytesseract
        import subprocess
        
        # Próba uruchomienia tesseract
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Tesseract zainstalowany")
            
            # Sprawdź język polski
            result = subprocess.run(['tesseract', '--list-langs'], 
                                  capture_output=True, text=True)
            if 'pol' in result.stdout:
                print("✓ Język polski dostępny")
            else:
                print("⚠ Brak języka polskiego - OCR może działać gorzej")
            return True
    except:
        print("✗ Tesseract nie jest zainstalowany lub nie jest w PATH")
        print("  Pobierz z: https://github.com/UB-Mannheim/tesseract/wiki")
        return False

def test_pdf_processing():
    """Test przetwarzania przykładowego PDF"""
    print("\n[TEST 3] Test przetwarzania PDF...")
    
    input_dir = Path(r"C:\pdf-to-xml-app\input")
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("⚠ Brak plików PDF w katalogu input/")
        print("  Umieść plik PDF w: C:\\pdf-to-xml-app\\input\\")
        return False
    
    try:
        from pdf_processor import PDFProcessor
        from comarch_mapper import ComarchMapper
        from xml_generator import XMLGenerator
        
        pdf_file = pdf_files[0]
        print(f"  Przetwarzanie: {pdf_file.name}")
        
        # Test ekstrakcji
        processor = PDFProcessor()
        invoice_data = processor.extract_from_pdf(str(pdf_file))
        
        if invoice_data.invoice_number:
            print(f"✓ Numer faktury: {invoice_data.invoice_number}")
        else:
            print("⚠ Nie znaleziono numeru faktury")
            
        if invoice_data.seller_name:
            print(f"✓ Sprzedawca: {invoice_data.seller_name}")
        else:
            print("⚠ Nie znaleziono sprzedawcy")
            
        if invoice_data.gross_total:
            print(f"✓ Kwota brutto: {invoice_data.gross_total:.2f} PLN")
        else:
            print("⚠ Nie znaleziono kwoty")
        
        # Test mapowania
        mapper = ComarchMapper()
        comarch_data = mapper.map_invoice_data(invoice_data)
        
        # Test generowania XML
        generator = XMLGenerator()
        xml_content = generator.generate_xml(comarch_data)
        
        if xml_content:
            output_file = Path(r"C:\pdf-to-xml-app\output") / f"test_{pdf_file.stem}.xml"
            output_file.write_text(xml_content, encoding='utf-8')
            print(f"✓ XML wygenerowany: {output_file}")
            return True
            
    except Exception as e:
        print(f"✗ Błąd: {e}")
        traceback.print_exc()
        return False

def test_structure():
    """Test struktury katalogów"""
    print("\n[TEST 4] Sprawdzanie struktury katalogów...")
    
    required_dirs = [
        r"C:\pdf-to-xml-app\input",
        r"C:\pdf-to-xml-app\output",
        r"C:\pdf-to-xml-app\app",
        r"C:\pdf-to-xml-app\skrypty_testowe"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✓ {dir_path}")
        else:
            print(f"✗ Brak: {dir_path}")
            all_exist = False
    
    return all_exist

def main():
    """Główna funkcja testowa"""
    print("="*50)
    print("PDF-to-XML Converter - Testy")
    print("="*50)
    
    results = {
        "Importy": test_imports(),
        "Tesseract": test_tesseract(),
        "Struktura": test_structure(),
        "Przetwarzanie": test_pdf_processing()
    }
    
    print("\n" + "="*50)
    print("PODSUMOWANIE TESTÓW:")
    print("="*50)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:20} {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✓ Wszystkie testy zaliczone!")
    else:
        print("\n⚠ Niektóre testy nie powiodły się.")
        print("  Uruchom install.bat aby naprawić problemy.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
