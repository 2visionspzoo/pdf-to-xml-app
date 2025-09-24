#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Konwerter wszystkich faktur PDF do jednego pliku XML
"""

import sys
import os
from pathlib import Path

# Dodaj katalog główny do ścieżki
sys.path.insert(0, str(Path(__file__).parent))

from app.main_multi import main

if __name__ == "__main__":
    print("=" * 60)
    print("  KONWERTER FAKTUR PDF → JEDEN PLIK XML")
    print("=" * 60)
    print()
    
    # Sprawdź pliki
    input_dir = Path(r"C:\pdf-to-xml-app\input")
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ Brak plików PDF w folderze 'input'")
        print(f"   Umieść faktury PDF w: {input_dir}")
        input("\nNaciśnij ENTER aby zakończyć...")
        sys.exit(1)
    
    print(f"📁 Znaleziono {len(pdf_files)} plików PDF:")
    print("-" * 40)
    for i, pdf in enumerate(pdf_files, 1):
        print(f"   {i}. {pdf.name}")
    
    print()
    response = input("Czy przetworzyć wszystkie do jednego XML? (T/n): ")
    if response.lower() == 'n':
        print("Anulowano.")
        sys.exit(0)
    
    print("\n🚀 Rozpoczynam konwersję...")
    print("-" * 40)
    
    # Uruchom konwerter
    try:
        sys.argv = ['main_multi.py']  # Reset argumentów
        result = main()
        
        if result == 0:
            print("\n✅ SUKCES!")
            print(f"📄 Plik XML: C:\\pdf-to-xml-app\\output\\wszystkie_faktury.xml")
        else:
            print("\n⚠️ Konwersja zakończona z błędami")
            
    except Exception as e:
        print(f"\n❌ Błąd: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nNaciśnij ENTER aby zakończyć...")
