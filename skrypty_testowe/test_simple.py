"""
Test prosty - sprawdzenie podstawowych funkcji
"""
import sys
import os

print("="*60)
print("TEST PROSTY - SPRAWDZENIE PODSTAWOWYCH FUNKCJI")
print("="*60)

# Test 1: Import podstawowych modułów
print("\n1. IMPORTY PODSTAWOWE:")
print("-"*40)

modules_to_test = [
    ('pdfplumber', 'pip install pdfplumber'),
    ('pytesseract', 'pip install pytesseract'),
    ('pdf2image', 'pip install pdf2image'),
    ('PIL', 'pip install Pillow'),
    ('lxml', 'pip install lxml'),
]

failed_imports = []
for module_name, install_cmd in modules_to_test:
    try:
        if module_name == 'pdf2image':
            from pdf2image import convert_from_path
        elif module_name == 'PIL':
            from PIL import Image
        else:
            __import__(module_name)
        print(f"✓ {module_name}")
    except ImportError:
        print(f"✗ {module_name} - uruchom: {install_cmd}")
        failed_imports.append((module_name, install_cmd))

# Test 2: Sprawdzenie Tesseract
print("\n2. TESSERACT OCR:")
print("-"*40)

tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(tesseract_path):
    print(f"✓ Tesseract znaleziony: {tesseract_path}")
    
    if 'pytesseract' not in [m[0] for m in failed_imports]:
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            
            # Prosty test OCR
            from PIL import Image, ImageDraw
            
            # Tworzenie prostego obrazu
            img = Image.new('RGB', (200, 50), color='white')
            draw = ImageDraw.Draw(img)
            draw.text((10, 10), "TEST 123", fill='black')
            
            # OCR
            text = pytesseract.image_to_string(img)
            if "TEST" in text or "123" in text:
                print("✓ OCR działa poprawnie")
            else:
                print("⚠ OCR działa, ale może być problem z rozpoznawaniem")
                
        except Exception as e:
            print(f"✗ Błąd OCR: {e}")
else:
    print(f"✗ Tesseract nie znaleziony w: {tesseract_path}")
    print("  Zainstaluj Tesseract OCR ze strony:")
    print("  https://github.com/UB-Mannheim/tesseract/wiki")

# Test 3: Sprawdzenie Poppler
print("\n3. POPPLER (do konwersji PDF):")
print("-"*40)

poppler_path = r"C:\poppler\Library\bin"
if os.path.exists(poppler_path):
    print(f"✓ Poppler znaleziony: {poppler_path}")
    
    # Sprawdź kluczowe pliki
    pdftoppm = os.path.join(poppler_path, "pdftoppm.exe")
    if os.path.exists(pdftoppm):
        print("✓ pdftoppm.exe znaleziony")
        
        # Test konwersji jeśli pdf2image działa
        if 'pdf2image' not in [m[0] for m in failed_imports]:
            try:
                from pdf2image import convert_from_path
                
                # Znajdź przykładowy PDF
                input_dir = os.path.join(os.path.dirname(__file__), '..', 'input')
                pdf_found = False
                
                if os.path.exists(input_dir):
                    for file in os.listdir(input_dir):
                        if file.endswith('.pdf'):
                            pdf_path = os.path.join(input_dir, file)
                            try:
                                images = convert_from_path(
                                    pdf_path, 
                                    dpi=100,
                                    poppler_path=poppler_path
                                )
                                print(f"✓ Konwersja PDF działa ({len(images)} stron)")
                                pdf_found = True
                            except Exception as e:
                                print(f"✗ Błąd konwersji: {str(e)[:80]}")
                            break
                
                if not pdf_found:
                    print("⚠ Brak plików PDF do testowania w input/")
                    
            except Exception as e:
                print(f"✗ Problem z pdf2image: {e}")
    else:
        print("✗ pdftoppm.exe nie znaleziony")
else:
    print(f"✗ Poppler nie znaleziony w: {poppler_path}")
    print("  Pobierz Poppler z:")
    print("  https://github.com/oschwartz10612/poppler-windows/releases")
    print("  Rozpakuj do C:\\poppler")

# Test 4: Struktura katalogów
print("\n4. STRUKTURA PROJEKTU:")
print("-"*40)

base_dir = os.path.dirname(os.path.dirname(__file__))
required_dirs = ['app', 'input', 'output', 'skrypty_testowe']

for dir_name in required_dirs:
    dir_path = os.path.join(base_dir, dir_name)
    if os.path.exists(dir_path):
        print(f"✓ {dir_name}/")
    else:
        print(f"✗ {dir_name}/ - brak katalogu!")

# Test 5: Pliki aplikacji
print("\n5. PLIKI APLIKACJI:")
print("-"*40)

app_dir = os.path.join(base_dir, 'app')
required_files = [
    'pdf_processor.py',
    'xml_generator.py',
    'invoice_detector.py',
    'base_parser.py',
    'config.py'
]

for file_name in required_files:
    file_path = os.path.join(app_dir, file_name)
    if os.path.exists(file_path):
        print(f"✓ {file_name}")
    else:
        print(f"✗ {file_name} - brak pliku!")

# Podsumowanie
print("\n" + "="*60)
print("PODSUMOWANIE:")
print("="*60)

if failed_imports:
    print("\n⚠ BRAKUJĄCE MODUŁY PYTHON:")
    print("Zainstaluj je używając poniższych komend:")
    for module, cmd in failed_imports:
        print(f"  {cmd}")

print("\n📋 KOLEJNE KROKI:")
print("1. Zainstaluj brakujące moduły Python")
print("2. Upewnij się że Tesseract jest zainstalowany")
print("3. Upewnij się że Poppler jest w C:\\poppler")
print("4. Umieść przykładowy PDF w folderze input/")
print("5. Uruchom ponownie testy")

print("\n" + "="*60)
