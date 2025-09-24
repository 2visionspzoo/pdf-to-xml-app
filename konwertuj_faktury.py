#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do szybkiego przetwarzania wszystkich faktur PDF
"""

import sys
import os
from pathlib import Path

# Dodaj katalog główny do ścieżki
sys.path.insert(0, str(Path(__file__).parent))

from app.main import main

if __name__ == "__main__":
    print("=" * 60)
    print("    KONWERTER FAKTUR PDF → XML (Comarch Optima)")
    print("=" * 60)
    print()
    
    # Sprawdź czy są pliki do przetworzenia
    input_dir = Path(r"C:\pdf-to-xml-app\input")
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ Brak plików PDF w folderze 'input'")
        print(f"   Umieść faktury PDF w: {input_dir}")
        input("\nNaciśnij ENTER aby zakończyć...")
        sys.exit(1)
    
    print(f"📁 Znaleziono {len(pdf_files)} plików PDF:")
    print("-" * 40)
    for pdf in pdf_files:
        print(f"   • {pdf.name}")
    print()
    
    response = input("Czy chcesz przetworzyć wszystkie pliki? (T/n): ")
    if response.lower() == 'n':
        print("Anulowano.")
        sys.exit(0)
    
    print("\n🚀 Rozpoczynam konwersję...")
    print("-" * 40)
    
    # Uruchom konwerter
    try:
        # Przekaż argumenty do main
        sys.argv = ['main.py']  # Reset argumentów
        main()
        
        print("\n" + "=" * 60)
        print("         ✅ KONWERSJA ZAKOŃCZONA!")
        print("=" * 60)
        
        output_dir = Path(r"C:\pdf-to-xml-app\output")
        xml_files = list(output_dir.glob("*.xml"))
        
        print(f"\n📁 Wygenerowano {len(xml_files)} plików XML:")
        print("-" * 40)
        for xml in xml_files[:5]:  # Pokaż pierwsze 5
            print(f"   • {xml.name}")
        if len(xml_files) > 5:
            print(f"   ... i {len(xml_files) - 5} więcej")
        
        print(f"\n📂 Pliki XML znajdują się w: {output_dir}")
        
    except Exception as e:
        print(f"\n❌ Błąd podczas konwersji: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nNaciśnij ENTER aby zakończyć...")
