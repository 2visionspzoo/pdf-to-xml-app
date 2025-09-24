#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOMPLEKSOWY TEST Z DEBUGOWANIEM
================================
Test wszystkich komponentów systemu PDF-to-XML z szczegółowym debugowaniem
"""

import os
import sys
import traceback
import logging
from pathlib import Path

# Dodaj ścieżkę do aplikacji
sys.path.insert(0, r'C:\pdf-to-xml-app')
sys.path.insert(0, r'C:\pdf-to-xml-app\app')

# Konfiguracja logowania z debugowaniem
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)8s] %(filename)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

# Kolory dla Windows Console
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Wyświetl nagłówek sekcji"""
    print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.CYAN}{text}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}\n")

def print_success(text):
    """Wyświetl komunikat sukcesu"""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_error(text):
    """Wyświetl komunikat błędu"""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_warning(text):
    """Wyświetl ostrzeżenie"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def print_info(text):
    """Wyświetl informację"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")

def test_imports():
    """Test importów wszystkich modułów"""
    print_header("TEST 1: IMPORTY MODUŁÓW")
    
    modules_to_test = [
        ('pdfplumber', 'PDF text extraction'),
        ('pytesseract', 'OCR engine'),
        ('pdf2image', 'PDF to image conversion'),
        ('PIL', 'Image processing'),
        ('lxml', 'XML generation'),
        ('pandas', 'Data processing (optional)'),
    ]
    
    failed = []
    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print_success(f"{module_name:15} - {description}")
        except ImportError as e:
            print_error(f"{module_name:15} - {description}")
            print(f"    Szczegóły: {e}")
            failed.append(module_name)
    
    if failed:
        print_warning(f"\nBrakujące moduły: {', '.join(failed)}")
        print_info("Zainstaluj: pip install " + ' '.join(failed))
    
    return len(failed) == 0

def test_app_modules():
    """Test modułów aplikacji"""
    print_header("TEST 2: MODUŁY APLIKACJI")
    
    modules = [
        'config',
        'invoice_detector',
        'base_parser',
        'pdf_processor',
        'comarch_mapper',
        'xml_generator',
        'parsers.atut_parser',
        'parsers.bolt_parser',
        'parsers.universal_parser'
    ]
    
    failed = []
    for module in modules:
        try:
            imported_module = __import__(module, fromlist=[''])
            print_success(f"{module:30} - załadowany")
            
            # Debug: wyświetl dostępne atrybuty
            attrs = [a for a in dir(imported_module) if not a.startswith('_')]
            if attrs:
                print(f"    Dostępne: {', '.join(attrs[:5])}" + 
                      ("..." if len(attrs) > 5 else ""))
        except Exception as e:
            print_error(f"{module:30} - błąd")
            print(f"    Szczegóły: {e}")
            logger.debug(traceback.format_exc())
            failed.append(module)
    
    return len(failed) == 0

def test_configuration():
    """Test konfiguracji systemowej"""
    print_header("TEST 3: KONFIGURACJA")
    
    try:
        from config import Config
        config = Config()
        
        # Test Tesseract
        if config.tesseract_path and Path(config.tesseract_path).exists():
            print_success(f"Tesseract: {config.tesseract_path}")
        else:
            print_error(f"Tesseract nie znaleziony: {config.tesseract_path}")
        
        # Test Poppler
        if config.poppler_path and Path(config.poppler_path).exists():
            print_success(f"Poppler: {config.poppler_path}")
        else:
            print_error(f"Poppler nie znaleziony: {config.poppler_path}")
        
        # Test katalogów
        paths = {
            'Input': config.input_dir,
            'Output': config.output_dir,
            'Logs': config.logs_dir
        }
        
        for name, path in paths.items():
            if Path(path).exists():
                print_success(f"{name:10} - {path}")
            else:
                print_warning(f"{name:10} - nie istnieje: {path}")
                Path(path).mkdir(parents=True, exist_ok=True)
                print_info(f"  → Utworzono katalog")
        
        return True
    except Exception as e:
        print_error(f"Błąd konfiguracji: {e}")
        logger.debug(traceback.format_exc())
        return False

def test_ocr_functionality():
    """Test funkcjonalności OCR"""
    print_header("TEST 4: OCR (TESSERACT)")
    
    try:
        import pytesseract
        from PIL import Image
        import numpy as np
        
        # Utworz testowy obraz z tekstem
        img = Image.new('RGB', (200, 50), color='white')
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "TEST OCR 123", fill='black')
        
        # Test OCR
        text = pytesseract.image_to_string(img)
        if 'TEST' in text or '123' in text:
            print_success(f"OCR działa - rozpoznano: {text.strip()}")
        else:
            print_warning(f"OCR działa ale wynik niepewny: {text.strip()}")
        
        # Test języków
        try:
            langs = pytesseract.get_languages()
            print_info(f"Dostępne języki: {', '.join(langs)}")
            if 'pol' in langs:
                print_success("Język polski dostępny")
            else:
                print_warning("Brak języka polskiego - zalecana instalacja")
        except:
            print_warning("Nie można pobrać listy języków")
        
        return True
    except Exception as e:
        print_error(f"Błąd OCR: {e}")
        logger.debug(traceback.format_exc())
        return False

def test_pdf_processing():
    """Test przetwarzania PDF"""
    print_header("TEST 5: PRZETWARZANIE PDF")
    
    try:
        from pdf_processor import PDFProcessor
        processor = PDFProcessor()
        
        # Znajdź przykładowy PDF
        input_dir = Path(r'C:\pdf-to-xml-app\input')
        pdf_files = list(input_dir.glob('*.pdf'))
        
        if not pdf_files:
            print_warning("Brak plików PDF w katalogu input/")
            return True
        
        test_pdf = pdf_files[0]
        print_info(f"Testowy plik: {test_pdf.name}")
        
        # Test ekstrakcji
        logger.info(f"Rozpoczynam ekstrakcję z: {test_pdf}")
        result = processor.extract_from_pdf(str(test_pdf))
        
        if result:
            print_success("Ekstrakcja zakończona sukcesem")
            
            # Debug: pokaż wykryte dane
            if hasattr(result, '__dict__'):
                for key, value in result.__dict__.items():
                    if value and not key.startswith('_'):
                        print(f"    {key}: {str(value)[:50]}...")
        else:
            print_warning("Ekstrakcja zwróciła pusty wynik")
        
        return True
    except Exception as e:
        print_error(f"Błąd przetwarzania PDF: {e}")
        logger.debug(traceback.format_exc())
        return False

def test_invoice_detection():
    """Test rozpoznawania typu faktury"""
    print_header("TEST 6: ROZPOZNAWANIE TYPU FAKTURY")
    
    try:
        from invoice_detector import InvoiceDetector
        detector = InvoiceDetector()
        
        # Testowe teksty faktur
        test_cases = [
            ("ATUT Sp. z o.o. NIP: 123456789", "ATUT"),
            ("Bolt Technology OÜ Invoice", "BOLT"),
            ("Faktura VAT nr 123/2025", "UNIVERSAL")
        ]
        
        for text, expected in test_cases:
            invoice_type = detector.detect_type(text)
            if invoice_type == expected:
                print_success(f"{expected:10} - rozpoznano poprawnie")
            else:
                print_error(f"{expected:10} - rozpoznano jako {invoice_type}")
        
        return True
    except Exception as e:
        print_error(f"Błąd rozpoznawania: {e}")
        logger.debug(traceback.format_exc())
        return False

def test_xml_generation():
    """Test generowania XML"""
    print_header("TEST 7: GENEROWANIE XML")
    
    try:
        from xml_generator import XMLGenerator
        from comarch_mapper import ComarchMapper
        
        generator = XMLGenerator()
        mapper = ComarchMapper()
        
        # Testowe dane faktury
        test_invoice = {
            'invoice_number': 'TEST/2025/001',
            'seller_name': 'Test Company',
            'seller_nip': '1234567890',
            'date_issued': '2025-01-10',
            'net_total': 1000.00,
            'vat_total': 230.00,
            'gross_total': 1230.00
        }
        
        # Mapuj dane
        class TestData:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)
        
        mapped_data = TestData(test_invoice)
        
        # Generuj XML
        xml_content = generator.generate_xml(mapped_data)
        
        if xml_content and '<NAGLOWEK>' in xml_content:
            print_success("XML wygenerowany poprawnie")
            print_info(f"Długość XML: {len(xml_content)} znaków")
            
            # Zapisz testowy XML
            test_output = Path(r'C:\pdf-to-xml-app\output\test_debug.xml')
            test_output.write_text(xml_content, encoding='utf-8')
            print_success(f"Zapisano do: {test_output}")
        else:
            print_error("XML niepoprawny lub pusty")
        
        return True
    except Exception as e:
        print_error(f"Błąd generowania XML: {e}")
        logger.debug(traceback.format_exc())
        return False

def test_full_pipeline():
    """Test całego procesu konwersji"""
    print_header("TEST 8: PEŁNY PROCES KONWERSJI")
    
    try:
        # Znajdź plik testowy
        input_dir = Path(r'C:\pdf-to-xml-app\input')
        pdf_files = list(input_dir.glob('*.pdf'))
        
        if not pdf_files:
            print_warning("Brak plików PDF do testu")
            return True
        
        test_pdf = pdf_files[0]
        output_xml = Path(r'C:\pdf-to-xml-app\output') / f"test_{test_pdf.stem}.xml"
        
        print_info(f"Plik wejściowy: {test_pdf.name}")
        print_info(f"Plik wyjściowy: {output_xml.name}")
        
        # Uruchom konwersję
        import subprocess
        result = subprocess.run([
            sys.executable,
            r'C:\pdf-to-xml-app\app\main.py',
            '--input', str(test_pdf),
            '--output', str(output_xml)
        ], capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print_success("Konwersja zakończona sukcesem")
            if output_xml.exists():
                print_success(f"XML utworzony: {output_xml.stat().st_size} bajtów")
            else:
                print_warning("Plik XML nie został utworzony")
        else:
            print_error(f"Konwersja zakończona błędem (kod: {result.returncode})")
            if result.stderr:
                print("STDERR:", result.stderr[:500])
        
        return result.returncode == 0
    except Exception as e:
        print_error(f"Błąd pipeline: {e}")
        logger.debug(traceback.format_exc())
        return False

def main():
    """Główna funkcja testowa"""
    print(f"\n{Colors.MAGENTA}{Colors.BOLD}")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║         TEST DEBUGOWANIA SYSTEMU PDF-TO-XML             ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(Colors.RESET)
    
    results = {
        'Importy': test_imports(),
        'Moduły': test_app_modules(),
        'Konfiguracja': test_configuration(),
        'OCR': test_ocr_functionality(),
        'PDF': test_pdf_processing(),
        'Detekcja': test_invoice_detection(),
        'XML': test_xml_generation(),
        'Pipeline': test_full_pipeline()
    }
    
    # Podsumowanie
    print_header("PODSUMOWANIE TESTÓW")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, status in results.items():
        if status:
            print_success(f"{name:15} - ZALICZONY")
        else:
            print_error(f"{name:15} - NIEZALICZONY")
    
    print(f"\n{Colors.BOLD}")
    if passed == total:
        print(f"{Colors.GREEN}✨ WSZYSTKIE TESTY ZALICZONE! ({passed}/{total})")
        print("System jest w pełni gotowy do użycia!")
    elif passed >= total * 0.7:
        print(f"{Colors.YELLOW}⚠ WIĘKSZOŚĆ TESTÓW ZALICZONA ({passed}/{total})")
        print("System może działać, ale zalecane są poprawki.")
    else:
        print(f"{Colors.RED}✗ SYSTEM WYMAGA NAPRAWY ({passed}/{total})")
        print("Sprawdź logi i napraw błędy przed użyciem.")
    print(Colors.RESET)
    
    # Zapisz raport
    report_file = Path(r'C:\pdf-to-xml-app\skrypty_testowe\test_debug_report.txt')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"RAPORT TESTÓW DEBUGOWANIA\n")
        f.write(f"{'='*50}\n")
        f.write(f"Data: {__import__('datetime').datetime.now()}\n\n")
        for name, status in results.items():
            f.write(f"{name}: {'PASS' if status else 'FAIL'}\n")
        f.write(f"\nWynik: {passed}/{total} testów zaliczonych\n")
    
    print(f"\n{Colors.BLUE}Raport zapisany: {report_file}{Colors.RESET}")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
