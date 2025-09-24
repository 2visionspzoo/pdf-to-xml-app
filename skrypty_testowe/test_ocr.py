"""
Test funkcjonalności OCR
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

import pytesseract
from pdf2image import convert_from_path
from PIL import Image, ImageDraw, ImageFont
import tempfile
from config import get_config

def test_tesseract_installation():
    """Testuje instalację Tesseract"""
    print("="*50)
    print("TEST: Instalacja Tesseract")
    print("="*50)
    
    config = get_config()
    
    # Sprawdź ścieżkę
    if os.path.exists(config.tesseract_path):
        print(f"✓ Tesseract znaleziony: {config.tesseract_path}")
    else:
        print(f"✗ Tesseract nie znaleziony w: {config.tesseract_path}")
        return False
    
    # Sprawdź wersję
    try:
        pytesseract.pytesseract.tesseract_cmd = config.tesseract_path
        version = pytesseract.get_tesseract_version()
        print(f"✓ Wersja Tesseract: {version}")
    except Exception as e:
        print(f"✗ Błąd sprawdzania wersji: {e}")
        return False
    
    # Sprawdź języki
    try:
        languages = pytesseract.get_languages()
        print(f"✓ Dostępne języki: {', '.join(languages)}")
        
        required_langs = ['pol', 'eng']
        for lang in required_langs:
            if lang in languages:
                print(f"  ✓ {lang}: dostępny")
            else:
                print(f"  ✗ {lang}: brak (zainstaluj pakiet językowy)")
    except Exception as e:
        print(f"✗ Błąd sprawdzania języków: {e}")
    
    return True

def test_simple_ocr():
    """Testuje prosty OCR na wygenerowanym obrazie"""
    print("\n" + "="*50)
    print("TEST: Prosty OCR")
    print("="*50)
    
    try:
        config = get_config()
        pytesseract.pytesseract.tesseract_cmd = config.tesseract_path
        
        # Utwórz prosty obraz z tekstem
        img = Image.new('RGB', (800, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        # Tekst testowy
        test_text = "FAKTURA VAT NR 123/2024\nSprzedawca: Test Sp. z o.o.\nNIP: 1234567890"
        
        # Rysuj tekst (używamy domyślnej czcionki)
        draw.text((50, 50), test_text, fill='black')
        
        # Zapisz tymczasowo
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img.save(f.name)
            temp_path = f.name
        
        # OCR
        extracted_text = pytesseract.image_to_string(
            Image.open(temp_path),
            lang='pol',
            config='--psm 6'
        )
        
        print(f"Tekst oryginalny:\n{test_text}")
        print(f"\nTekst z OCR:\n{extracted_text}")
        
        # Sprawdź czy kluczowe elementy zostały rozpoznane
        if 'FAKTURA' in extracted_text.upper():
            print("✓ Słowo 'FAKTURA' rozpoznane")
        else:
            print("✗ Słowo 'FAKTURA' nie rozpoznane")
        
        if 'NIP' in extracted_text.upper():
            print("✓ Słowo 'NIP' rozpoznane")
        else:
            print("✗ Słowo 'NIP' nie rozpoznane")
        
        # Usuń tymczasowy plik
        os.unlink(temp_path)
        
        return True
        
    except Exception as e:
        print(f"✗ Błąd OCR: {e}")
        return False

def test_pdf_to_image():
    """Testuje konwersję PDF na obraz"""
    print("\n" + "="*50)
    print("TEST: Konwersja PDF na obraz")
    print("="*50)
    
    config = get_config()
    
    # Sprawdź poppler
    if config.poppler_path and os.path.exists(config.poppler_path):
        print(f"✓ Poppler skonfigurowany: {config.poppler_path}")
    else:
        print("⚠ Poppler nie skonfigurowany - używam domyślnego")
    
    # Znajdź przykładowy PDF
    pdf_path = None
    input_dir = os.path.join(os.path.dirname(__file__), '..', 'input')
    
    if os.path.exists(input_dir):
        for file in os.listdir(input_dir):
            if file.endswith('.pdf'):
                pdf_path = os.path.join(input_dir, file)
                break
    
    if not pdf_path:
        print("⚠ Brak plików PDF w katalogu input do testowania")
        return None
    
    print(f"Testuję z plikiem: {os.path.basename(pdf_path)}")
    
    try:
        # Konwersja
        kwargs = {'dpi': config.ocr_dpi}
        if config.poppler_path and os.path.exists(config.poppler_path):
            kwargs['poppler_path'] = config.poppler_path
        
        images = convert_from_path(pdf_path, **kwargs)
        
        print(f"✓ Przekonwertowano {len(images)} stron")
        
        # Test OCR na pierwszej stronie
        if images:
            print("\nTestuję OCR na pierwszej stronie...")
            text = pytesseract.image_to_string(
                images[0],
                lang=config.ocr_languages,
                config=config.get_tesseract_config()
            )
            
            # Sprawdź jakość rozpoznania
            if len(text) > 100:
                print(f"✓ Rozpoznano {len(text)} znaków")
                print(f"Pierwsze 200 znaków:\n{text[:200]}...")
            else:
                print(f"⚠ Rozpoznano tylko {len(text)} znaków")
        
        return True
        
    except Exception as e:
        print(f"✗ Błąd konwersji: {e}")
        print("Sprawdź instalację Poppler (uruchom install_poppler.bat)")
        return False

def main():
    """Główna funkcja testowa"""
    print("╔" + "="*48 + "╗")
    print("║            TESTY OCR I TESSERACT              ║")
    print("╚" + "="*48 + "╝")
    
    all_passed = True
    
    # Test 1: Instalacja Tesseract
    if not test_tesseract_installation():
        all_passed = False
    
    # Test 2: Prosty OCR
    if not test_simple_ocr():
        all_passed = False
    
    # Test 3: PDF do obrazu
    result = test_pdf_to_image()
    if result is False:
        all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("✓ WSZYSTKIE TESTY OCR PRZESZŁY POMYŚLNIE!")
    else:
        print("✗ NIEKTÓRE TESTY NIE POWIODŁY SIĘ")
        print("\nSugestie:")
        print("1. Sprawdź instalację Tesseract w C:\\Program Files\\Tesseract-OCR")
        print("2. Zainstaluj pakiety językowe (pol, eng) w Tesseract")
        print("3. Zainstaluj Poppler (uruchom install_poppler.bat)")
    print("="*50)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
