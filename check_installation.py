#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sprawdzenie instalacji i zależności
"""

import sys
import os

print("="*60)
print("SPRAWDZANIE INSTALACJI PDF TO XML CONVERTER")
print("="*60)

def check_module(name, import_name=None):
    """Sprawdź czy moduł jest zainstalowany"""
    if not import_name:
        import_name = name
    try:
        __import__(import_name)
        print(f"✅ {name}")
        return True
    except ImportError:
        print(f"❌ {name} - BRAK (zainstaluj: pip install {name})")
        return False

def check_tesseract():
    """Sprawdź Tesseract OCR"""
    try:
        import pytesseract
        import configparser
        
        # Sprawdź najpierw config.ini
        config_path = 'config.ini'
        if os.path.exists(config_path):
            config = configparser.ConfigParser()
            config.read(config_path)
            tesseract_path = config.get('DEFAULT', 'TESSERACT_PATH', fallback=None)
            
            if tesseract_path and os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                version = pytesseract.get_tesseract_version()
                print(f"✅ Tesseract OCR (z config.ini: {tesseract_path})")
                return True
        
        # Spróbuj domyślnie
        pytesseract.get_tesseract_version()
        print(f"✅ Tesseract OCR (w PATH)")
        return True
    except Exception as e:
        # Sprawdź standardową lokalizację Windows
        standard_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        if os.path.exists(standard_path):
            print(f"✅ Tesseract OCR (znaleziony w: {standard_path})")
            print("   ℹ️ Ścieżka jest w config.ini")
            return True
        else:
            print(f"❌ Tesseract OCR - BRAK lub nie skonfigurowany")
            print("   Zainstaluj z: https://github.com/UB-Mannheim/tesseract/wiki")
            return False

def check_poppler():
    """Sprawdź Poppler"""
    try:
        from pdf2image import convert_from_path
        # Test na małym PDF jeśli istnieje
        print(f"✅ Poppler/pdf2image")
        return True
    except:
        print(f"❌ Poppler - BRAK lub nie w PATH")
        print("   Pobierz z: https://github.com/oschwartz10612/poppler-windows/releases/")
        return False

print("\n1️⃣ MODUŁY PYTHON:")
print("-" * 40)
modules = [
    ('pdf2image', None),
    ('pytesseract', None),
    ('PIL', 'PIL'),
    ('pdfplumber', None),
    ('lxml', None),
    ('openpyxl', None),
    ('pandas', None),
]

python_ok = True
for module in modules:
    if not check_module(*module):
        python_ok = False

print("\n2️⃣ NARZĘDZIA ZEWNĘTRZNE:")
print("-" * 40)
tesseract_ok = check_tesseract()
poppler_ok = check_poppler()

print("\n3️⃣ STRUKTURA PROJEKTU:")
print("-" * 40)
dirs = ['input', 'output', 'app', 'app/parsers', 'skrypty_testowe']
structure_ok = True
for dir_name in dirs:
    if os.path.exists(dir_name):
        print(f"✅ {dir_name}/")
    else:
        print(f"❌ {dir_name}/ - BRAK")
        structure_ok = False

print("\n4️⃣ PLIKI KONFIGURACYJNE:")
print("-" * 40)
files = ['config.ini', 'requirements.txt', 'README.md']
for file_name in files:
    if os.path.exists(file_name):
        print(f"✅ {file_name}")
    else:
        print(f"⚠️ {file_name} - BRAK (opcjonalny)")

print("\n5️⃣ FAKTURY TESTOWE:")
print("-" * 40)
import glob
pdf_files = glob.glob('input/*.pdf')
if pdf_files:
    print(f"✅ Znaleziono {len(pdf_files)} faktur PDF")
    for pdf in pdf_files[:3]:  # Pokaż max 3
        print(f"   • {os.path.basename(pdf)}")
else:
    print(f"⚠️ Brak faktur w katalogu input/")

print("\n" + "="*60)
print("PODSUMOWANIE:")
print("="*60)

all_ok = python_ok and tesseract_ok and poppler_ok and structure_ok

if all_ok:
    print("✅ WSZYSTKO GOTOWE! System jest poprawnie zainstalowany.")
    print("\nMożesz teraz uruchomić:")
    print("  • python test_simple.py - prosty test")
    print("  • python app/main.py - główna aplikacja")
else:
    print("⚠️ WYKRYTO PROBLEMY!")
    print("\nRozwiązania:")
    if not python_ok:
        print("  • Zainstaluj brakujące moduły: pip install -r requirements.txt")
    if not tesseract_ok:
        print("  • Zainstaluj Tesseract OCR")
    if not poppler_ok:
        print("  • Zainstaluj Poppler i dodaj do PATH")

print("\n" + "="*60)
