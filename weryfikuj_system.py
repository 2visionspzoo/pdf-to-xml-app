#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Weryfikacja systemu PDF to XML Converter
Sprawdza czy wszystkie komponenty działają poprawnie
"""

import os
import sys
import importlib
from datetime import datetime
from pathlib import Path

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def check_module(module_name, path=None):
    """Sprawdza czy moduł można zaimportować"""
    try:
        if path:
            sys.path.insert(0, path)
        importlib.import_module(module_name)
        return True, "OK"
    except ImportError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)

def check_file(filepath):
    """Sprawdza czy plik istnieje"""
    return Path(filepath).exists()

def main():
    print("\n" + "="*60)
    print("  🔍 WERYFIKACJA SYSTEMU PDF TO XML CONVERTER")
    print(f"  Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Sprawdź strukturę katalogów
    print_section("📁 Struktura katalogów")
    dirs = [
        "C:\\pdf-to-xml-app",
        "C:\\pdf-to-xml-app\\app",
        "C:\\pdf-to-xml-app\\app\\parsers",
        "C:\\pdf-to-xml-app\\input",
        "C:\\pdf-to-xml-app\\output",
        "C:\\pdf-to-xml-app\\skrypty_testowe"
    ]
    
    for dir_path in dirs:
        exists = os.path.exists(dir_path)
        status = "✅" if exists else "❌"
        print(f"  {status} {dir_path}")
    
    # Sprawdź kluczowe pliki
    print_section("📄 Kluczowe pliki")
    files = [
        ("Instrukcja XML", "C:\\pdf-to-xml-app\\instrukcja wzoru xml.txt"),
        ("README", "C:\\pdf-to-xml-app\\README.md"),
        ("Requirements", "C:\\pdf-to-xml-app\\requirements.txt"),
        ("Main script", "C:\\pdf-to-xml-app\\app\\main.py"),
        ("XML Generator", "C:\\pdf-to-xml-app\\app\\xml_generator.py"),
        ("XML Multi Generator", "C:\\pdf-to-xml-app\\app\\xml_generator_multi.py"),
        ("Comarch Mapper", "C:\\pdf-to-xml-app\\app\\comarch_mapper.py"),
        ("PDF Processor", "C:\\pdf-to-xml-app\\app\\pdf_processor.py"),
    ]
    
    for name, filepath in files:
        exists = check_file(filepath)
        status = "✅" if exists else "❌"
        print(f"  {status} {name:20} {filepath}")
    
    # Sprawdź moduły Python
    print_section("🐍 Moduły aplikacji")
    
    sys.path.insert(0, "C:\\pdf-to-xml-app")
    
    modules = [
        "app.xml_generator",
        "app.xml_generator_multi",
        "app.comarch_mapper",
        "app.pdf_processor",
        "app.invoice_detector"
    ]
    
    all_ok = True
    for module in modules:
        ok, error = check_module(module)
        status = "✅" if ok else "❌"
        print(f"  {status} {module}")
        if not ok:
            print(f"      Błąd: {error}")
            all_ok = False
    
    # Sprawdź testy
    print_section("🧪 Skrypty testowe")
    test_scripts = [
        "test_comarch_format.py",
        "test_mapper_fix.py",
        "quick_test_format.py"
    ]
    
    test_dir = Path("C:\\pdf-to-xml-app\\skrypty_testowe")
    for script in test_scripts:
        filepath = test_dir / script
        exists = filepath.exists()
        status = "✅" if exists else "❌"
        print(f"  {status} {script}")
    
    # Sprawdź pliki PDF do testów
    print_section("📑 Pliki PDF w input")
    input_dir = Path("C:\\pdf-to-xml-app\\input")
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if pdf_files:
        print(f"  ✅ Znaleziono {len(pdf_files)} plików PDF:")
        for pdf in pdf_files[:5]:  # Pokaż max 5 plików
            print(f"     • {pdf.name}")
        if len(pdf_files) > 5:
            print(f"     ... i {len(pdf_files)-5} więcej")
    else:
        print("  ⚠️ Brak plików PDF do przetworzenia")
    
    # Sprawdź zewnętrzne zależności
    print_section("📦 Zewnętrzne pakiety")
    packages = [
        "lxml",
        "pytesseract",
        "pdf2image",
        "PIL",
        "pandas"
    ]
    
    for package in packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - nie zainstalowany")
    
    # Podsumowanie
    print_section("📊 PODSUMOWANIE")
    
    if all_ok and pdf_files:
        print("  ✅ System gotowy do pracy!")
        print("\n  Możesz teraz uruchomić:")
        print("  1. python skrypty_testowe\\test_comarch_format.py")
        print("  2. python konwertuj_wszystkie_do_xml.py")
    else:
        print("  ⚠️ System wymaga dodatkowej konfiguracji")
        if not all_ok:
            print("  • Sprawdź błędy importu modułów")
        if not pdf_files:
            print("  • Dodaj pliki PDF do katalogu input")
    
    print("\n" + "="*60)
    print("  Weryfikacja zakończona")
    print("="*60)

if __name__ == "__main__":
    main()
