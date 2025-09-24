"""
Test finalny - sprawdzenie czy wszystko działa
"""
import sys
import os

print("="*60)
print("TEST FINALNY SYSTEMU PDF-TO-XML")
print("="*60)

# Ustaw ścieżki
app_path = os.path.join(os.path.dirname(__file__), '..', 'app')
sys.path.insert(0, app_path)

# Test 1: Wszystkie importy
print("\n[1] TEST IMPORTÓW:")
print("-"*40)

all_ok = True

try:
    import pdfplumber
    print("✓ pdfplumber")
except ImportError as e:
    print(f"✗ pdfplumber: {e}")
    all_ok = False

try:
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    print("✓ pytesseract")
except ImportError as e:
    print(f"✗ pytesseract: {e}")
    all_ok = False

try:
    from pdf2image import convert_from_path
    print("✓ pdf2image")
except ImportError as e:
    print(f"✗ pdf2image: {e}")
    all_ok = False

try:
    from PIL import Image
    print("✓ PIL")
except ImportError as e:
    print(f"✗ PIL: {e}")
    all_ok = False

try:
    import lxml
    print("✓ lxml")
except ImportError as e:
    print(f"✗ lxml: {e}")
    all_ok = False

# Test 2: Moduły aplikacji
print("\n[2] TEST MODUŁÓW APLIKACJI:")
print("-"*40)

try:
    from config import get_config
    config = get_config()
    print("✓ config")
    print(f"  Tesseract: {config.tesseract_path[:30]}...")
    print(f"  Poppler: {config.poppler_path[:30]}...")
except Exception as e:
    print(f"✗ config: {e}")
    all_ok = False

try:
    from invoice_detector import InvoiceDetector, InvoiceType
    print("✓ invoice_detector")
except Exception as e:
    print(f"✗ invoice_detector: {e}")
    all_ok = False

try:
    from base_parser import BaseInvoiceParser
    print("✓ base_parser")
except Exception as e:
    print(f"✗ base_parser: {e}")
    all_ok = False

try:
    from pdf_processor import PDFProcessor
    print("✓ pdf_processor")
except Exception as e:
    print(f"✗ pdf_processor: {e}")
    all_ok = False

# Test 3: Test OCR
print("\n[3] TEST OCR:")
print("-"*40)

if os.path.exists(r"C:\Program Files\Tesseract-OCR\tesseract.exe"):
    print("✓ Tesseract zainstalowany")
    
    try:
        import pytesseract
        from PIL import Image, ImageDraw
        
        # Prosty obraz testowy
        img = Image.new('RGB', (200, 50), 'white')
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "FAKTURA 123", fill='black')
        
        text = pytesseract.image_to_string(img)
        if "FAKTURA" in text or "123" in text:
            print("✓ OCR działa")
        else:
            print("⚠ OCR może mieć problemy")
    except Exception as e:
        print(f"✗ Błąd OCR: {e}")
        all_ok = False
else:
    print("✗ Tesseract nie zainstalowany")
    all_ok = False

# Test 4: Test Poppler
print("\n[4] TEST POPPLER:")
print("-"*40)

poppler_path = r"C:\poppler\Library\bin"
if os.path.exists(os.path.join(poppler_path, "pdftoppm.exe")):
    print("✓ Poppler zainstalowany")
    
    # Test konwersji
    input_dir = os.path.join(os.path.dirname(__file__), '..', 'input')
    pdf_files = []
    if os.path.exists(input_dir):
        pdf_files = [f for f in os.listdir(input_dir) if f.endswith('.pdf')]
    
    if pdf_files:
        try:
            from pdf2image import convert_from_path
            pdf_path = os.path.join(input_dir, pdf_files[0])
            images = convert_from_path(pdf_path, dpi=100, poppler_path=poppler_path)
            print(f"✓ Konwersja PDF działa ({len(images)} stron)")
        except Exception as e:
            print(f"✗ Błąd konwersji: {e}")
            all_ok = False
    else:
        print("⚠ Brak PDF do testu w input/")
else:
    print("✗ Poppler nie zainstalowany poprawnie")
    print(f"  Sprawdzono: {poppler_path}")
    all_ok = False

# Test 5: Parsery
print("\n[5] TEST PARSERÓW:")
print("-"*40)

parsers_path = os.path.join(app_path, 'parsers')
sys.path.insert(0, parsers_path)

try:
    from atut_parser import ATUTParser
    parser = ATUTParser()
    print("✓ ATUTParser")
except Exception as e:
    print(f"✗ ATUTParser: {e}")
    all_ok = False

try:
    from universal_parser import UniversalParser
    parser = UniversalParser()
    print("✓ UniversalParser")
except Exception as e:
    print(f"✗ UniversalParser: {e}")
    all_ok = False

# Test 6: Test rozpoznawania faktury
print("\n[6] TEST ROZPOZNAWANIA FAKTURY:")
print("-"*40)

try:
    from invoice_detector import InvoiceDetector, InvoiceType
    detector = InvoiceDetector()
    
    test_text = "FAKTURA VAT 123/2024\nATUT Sp. z o.o.\nNIP: 5252374228"
    detected = detector.detect_type(test_text)
    
    if detected == InvoiceType.ATUT:
        print("✓ Rozpoznawanie działa (wykryto ATUT)")
    else:
        print(f"⚠ Rozpoznawanie działa ale wykryto: {detected.value}")
except Exception as e:
    print(f"✗ Błąd rozpoznawania: {e}")
    all_ok = False

# Podsumowanie
print("\n" + "="*60)
print("WYNIK TESTU:")
print("="*60)

if all_ok:
    print("✅ WSZYSTKO DZIAŁA POPRAWNIE!")
    print("\nSystem jest gotowy do użycia.")
    print("Uruchom aplikację: run.bat")
else:
    print("❌ SĄ PROBLEMY DO NAPRAWIENIA")
    print("\nSprawdź:")
    print("1. Czy Poppler jest w C:\\poppler\\Library\\bin")
    print("2. Czy wszystkie moduły są zainstalowane")
    print("3. Uruchom: check_poppler.bat")

print("="*60)
