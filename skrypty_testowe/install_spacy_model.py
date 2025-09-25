#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Skrypt do instalacji i weryfikacji modułu spaCy z modelem polskim
"""

import subprocess
import sys

def install_spacy():
    """Instaluje spaCy i model języka polskiego"""
    print("="*60)
    print("INSTALACJA SPACY I MODELU JĘZYKA POLSKIEGO")
    print("="*60)
    
    try:
        # Sprawdź czy spaCy jest zainstalowane
        import spacy
        print("✓ spaCy jest już zainstalowane")
    except ImportError:
        print("⚠ spaCy nie jest zainstalowane. Instaluję...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "spacy"])
        print("✓ spaCy zainstalowane")
    
    # Sprawdź czy model polski jest dostępny
    try:
        import spacy
        nlp = spacy.load("pl_core_news_sm")
        print("✓ Model pl_core_news_sm jest już zainstalowany")
        return True
    except:
        print("⚠ Model pl_core_news_sm nie jest zainstalowany. Instaluję...")
        
    try:
        # Pobierz model
        subprocess.check_call([sys.executable, "-m", "spacy", "download", "pl_core_news_sm"])
        print("✓ Model pl_core_news_sm zainstalowany")
        
        # Weryfikuj instalację
        import spacy
        nlp = spacy.load("pl_core_news_sm")
        print("✓ Model działa poprawnie")
        
        # Test na przykładowym tekście
        doc = nlp("Faktura VAT nr 123/2025 z dnia 15 stycznia 2025")
        print(f"✓ Test NLP: znaleziono {len(doc.ents)} encji")
        
        return True
        
    except Exception as e:
        print(f"✗ Błąd podczas instalacji modelu: {e}")
        print("\nMożesz spróbować zainstalować ręcznie:")
        print("  python -m spacy download pl_core_news_sm")
        return False

def verify_all_dependencies():
    """Weryfikuje wszystkie wymagane moduły"""
    print("\n" + "="*60)
    print("WERYFIKACJA ZALEŻNOŚCI")
    print("="*60)
    
    required_modules = [
        'pdfplumber',
        'pytesseract',
        'pdf2image',
        'lxml',
        'requests',
        'tkinter',
        'spacy'
    ]
    
    all_ok = True
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError:
            print(f"✗ {module} - BRAK")
            all_ok = False
            
    return all_ok

def main():
    """Główna funkcja"""
    print("INSTALATOR MODUŁÓW DLA PDF-TO-XML-APP")
    print("="*60)
    
    # Weryfikuj zależności
    deps_ok = verify_all_dependencies()
    
    if not deps_ok:
        print("\n⚠ Niektóre moduły nie są zainstalowane.")
        print("Zainstaluj je używając:")
        print("  pip install -r C:\\pdf-to-xml-app\\requirements.txt")
        
    # Instaluj spaCy
    spacy_ok = install_spacy()
    
    print("\n" + "="*60)
    if deps_ok and spacy_ok:
        print("✅ WSZYSTKO GOTOWE DO PRACY")
    else:
        print("⚠️  WYMAGANA INTERWENCJA")
        
if __name__ == "__main__":
    main()
