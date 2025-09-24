"""
Debugowanie testów - znajdowanie problemów
"""
import sys
import os
import traceback

# Debugowanie ścieżek
print("="*60)
print("DEBUGOWANIE ŚCIEŻEK")
print("="*60)
print(f"Python: {sys.executable}")
print(f"Wersja: {sys.version}")
print(f"Bieżący katalog: {os.getcwd()}")
print(f"__file__: {__file__}")

# Dodanie ścieżki do app
app_path = os.path.join(os.path.dirname(__file__), '..', 'app')
app_path = os.path.abspath(app_path)
print(f"Ścieżka app: {app_path}")
sys.path.insert(0, app_path)
print(f"sys.path: {sys.path[:3]}")

# Test 1: Import modułów podstawowych
print("\n" + "="*60)
print("TEST 1: Import modułów podstawowych")
print("="*60)

try:
    import pdfplumber
    print("✓ pdfplumber zaimportowany")
except ImportError as e:
    print(f"✗ Błąd importu pdfplumber: {e}")
    print("  Instalacja: pip install pdfplumber")

try:
    import pytesseract
    print("✓ pytesseract zaimportowany")
except ImportError as e:
    print(f"✗ Błąd importu pytesseract: {e}")
    print("  Instalacja: pip install pytesseract")

try:
    from pdf2image import convert_from_path
    print("✓ pdf2image zaimportowany")
except ImportError as e:
    print(f"✗ Błąd importu pdf2image: {e}")
    print("  Instalacja: pip install pdf2image")

try:
    from PIL import Image
    print("✓ PIL (Pillow) zaimportowany")
except ImportError as e:
    print(f"✗ Błąd importu PIL: {e}")
    print("  Instalacja: pip install Pillow")

# Test 2: Import modułów aplikacji
print("\n" + "="*60)
print("TEST 2: Import modułów aplikacji")
print("="*60)

# Sprawdź strukturę katalogów
print("\nStruktura app/:")
if os.path.exists(app_path):
    for file in os.listdir(app_path):
        print(f"  - {file}")
else:
    print(f"✗ Katalog nie istnieje: {app_path}")

# Test importu config
try:
    from config import get_config
    config = get_config()
    print("✓ config zaimportowany")
    print(f"  Tesseract: {config.tesseract_path}")
    print(f"  Poppler: {config.poppler_path}")
except Exception as e:
    print(f"✗ Błąd importu config: {e}")
    traceback.print_exc()

# Test importu invoice_detector
try:
    from invoice_detector import InvoiceDetector, InvoiceType
    print("✓ invoice_detector zaimportowany")
except Exception as e:
    print(f"✗ Błąd importu invoice_detector: {e}")
    traceback.print_exc()

# Test importu base_parser
try:
    from base_parser import BaseInvoiceParser, InvoiceItem
    print("✓ base_parser zaimportowany")
except Exception as e:
    print(f"✗ Błąd importu base_parser: {e}")
    traceback.print_exc()

# Test 3: Sprawdzenie Tesseract
print("\n" + "="*60)
print("TEST 3: Sprawdzenie Tesseract")
print("="*60)

tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(tesseract_path):
    print(f"✓ Tesseract istnieje: {tesseract_path}")
    
    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        version = pytesseract.get_tesseract_version()
        print(f"✓ Wersja: {version}")
        
        languages = pytesseract.get_languages()
        print(f"✓ Języki: {', '.join(languages)}")
    except Exception as e:
        print(f"✗ Błąd Tesseract: {e}")
else:
    print(f"✗ Tesseract nie istnieje: {tesseract_path}")

# Test 4: Sprawdzenie Poppler
print("\n" + "="*60)
print("TEST 4: Sprawdzenie Poppler")
print("="*60)

poppler_paths = [
    r"C:\poppler\Library\bin",
    r"C:\poppler",
    r"C:\Program Files\poppler\Library\bin",
    r"C:\Program Files\poppler"
]

poppler_found = False
for path in poppler_paths:
    if os.path.exists(path):
        print(f"✓ Poppler znaleziony: {path}")
        
        # Sprawdź pliki wykonywalne
        executables = ['pdftoppm.exe', 'pdfinfo.exe', 'pdftocairo.exe']
        for exe in executables:
            exe_path = os.path.join(path, exe)
            if os.path.exists(exe_path):
                print(f"  ✓ {exe} znaleziony")
            else:
                print(f"  ✗ {exe} brak")
        
        poppler_found = True
        break

if not poppler_found:
    print("✗ Poppler nie znaleziony!")
    print("  Sprawdzone ścieżki:")
    for path in poppler_paths:
        print(f"    - {path}")

# Test 5: Test konwersji PDF
print("\n" + "="*60)
print("TEST 5: Test konwersji PDF")
print("="*60)

try:
    from pdf2image import convert_from_path
    
    # Znajdź przykładowy PDF
    input_dir = os.path.join(os.path.dirname(__file__), '..', 'input')
    pdf_found = False
    
    if os.path.exists(input_dir):
        for file in os.listdir(input_dir):
            if file.endswith('.pdf'):
                pdf_path = os.path.join(input_dir, file)
                print(f"Znaleziono PDF: {file}")
                
                try:
                    # Próba konwersji z różnymi opcjami
                    print("\nPróba 1: Bez poppler_path...")
                    try:
                        images = convert_from_path(pdf_path, dpi=150)
                        print(f"✓ Sukces! Przekonwertowano {len(images)} stron")
                    except Exception as e1:
                        print(f"✗ Błąd: {str(e1)[:100]}")
                        
                        print("\nPróba 2: Z poppler_path=C:\\poppler\\Library\\bin...")
                        try:
                            images = convert_from_path(pdf_path, dpi=150, poppler_path=r"C:\poppler\Library\bin")
                            print(f"✓ Sukces! Przekonwertowano {len(images)} stron")
                        except Exception as e2:
                            print(f"✗ Błąd: {str(e2)[:100]}")
                            
                            print("\nPróba 3: Z poppler_path=C:\\poppler...")
                            try:
                                images = convert_from_path(pdf_path, dpi=150, poppler_path=r"C:\poppler")
                                print(f"✓ Sukces! Przekonwertowano {len(images)} stron")
                            except Exception as e3:
                                print(f"✗ Błąd: {str(e3)[:100]}")
                
                except Exception as e:
                    print(f"✗ Błąd ogólny: {e}")
                    traceback.print_exc()
                
                pdf_found = True
                break
    
    if not pdf_found:
        print("⚠ Brak plików PDF w katalogu input/")
        print(f"  Ścieżka: {input_dir}")
        
except Exception as e:
    print(f"✗ Błąd testu konwersji: {e}")
    traceback.print_exc()

# Test 6: Import parserów
print("\n" + "="*60)
print("TEST 6: Import parserów")
print("="*60)

parsers_path = os.path.join(app_path, 'parsers')
print(f"Ścieżka parsers: {parsers_path}")

if os.path.exists(parsers_path):
    print("Pliki w parsers/:")
    for file in os.listdir(parsers_path):
        print(f"  - {file}")
    
    # Dodaj ścieżkę parsers
    sys.path.insert(0, parsers_path)
    
    # Test importu parserów
    try:
        # Najpierw spróbuj importować base_parser z głównego katalogu app
        sys.path.insert(0, app_path)
        from base_parser import BaseInvoiceParser, InvoiceItem
        print("✓ base_parser zaimportowany z app/")
    except Exception as e:
        print(f"✗ Błąd importu base_parser: {e}")
    
    try:
        from atut_parser import ATUTParser
        print("✓ atut_parser zaimportowany")
    except Exception as e:
        print(f"✗ Błąd importu atut_parser: {e}")
        traceback.print_exc()
    
    try:
        from universal_parser import UniversalParser
        print("✓ universal_parser zaimportowany")
    except Exception as e:
        print(f"✗ Błąd importu universal_parser: {e}")
else:
    print(f"✗ Katalog parsers nie istnieje!")

# Podsumowanie
print("\n" + "="*60)
print("PODSUMOWANIE DEBUGOWANIA")
print("="*60)
print("Sprawdź powyższe wyniki i napraw problemy:")
print("1. Zainstaluj brakujące moduły: pip install pdfplumber pytesseract pdf2image pillow")
print("2. Upewnij się że Tesseract jest w: C:\\Program Files\\Tesseract-OCR")
print("3. Upewnij się że Poppler jest w: C:\\poppler\\Library\\bin")
print("4. Sprawdź strukturę katalogów app/ i app/parsers/")
print("="*60)
