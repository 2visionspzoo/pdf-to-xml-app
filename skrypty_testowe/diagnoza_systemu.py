#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt diagnostyczny - sprawdza dlaczego nie wszystkie pliki są przetwarzane
"""

import sys
import os
from pathlib import Path
import pdfplumber

# Dodaj katalog główny do ścieżki
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.pdf_processor import PDFProcessor
from app.comarch_mapper import ComarchMapper
from app.xml_generator import XMLGenerator

def diagnose_system():
    """Diagnozuje problemy z konwersją"""
    print("=" * 60)
    print("DIAGNOSTYKA SYSTEMU PDF-TO-XML")
    print("=" * 60)
    
    # 1. Sprawdź pliki w input
    input_dir = Path(r"C:\pdf-to-xml-app\input")
    pdf_files = list(input_dir.glob("*.pdf"))
    
    print(f"\n📁 PLIKI W FOLDERZE INPUT:")
    print("-" * 40)
    if not pdf_files:
        print("❌ Brak plików PDF!")
        return
    
    for i, pdf in enumerate(pdf_files, 1):
        size = pdf.stat().st_size / 1024
        print(f"{i}. {pdf.name} ({size:.1f} KB)")
    
    print(f"\nZnaleziono: {len(pdf_files)} plików PDF")
    
    # 2. Sprawdź pliki w output
    output_dir = Path(r"C:\pdf-to-xml-app\output")
    xml_files = list(output_dir.glob("*.xml"))
    
    print(f"\n📁 PLIKI W FOLDERZE OUTPUT:")
    print("-" * 40)
    if not xml_files:
        print("❌ Brak plików XML!")
    else:
        for xml in xml_files:
            size = xml.stat().st_size / 1024
            print(f"• {xml.name} ({size:.1f} KB)")
    
    print(f"\nZnaleziono: {len(xml_files)} plików XML")
    
    # 3. Test konwersji każdego pliku
    print(f"\n🧪 TEST KONWERSJI KAŻDEGO PLIKU:")
    print("-" * 40)
    
    successful = []
    failed = []
    
    processor = PDFProcessor(parser_type='universal')
    mapper = ComarchMapper()
    generator = XMLGenerator()
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n{i}. Testuję: {pdf_file.name}")
        
        try:
            # Sprawdź czy plik się otwiera
            with pdfplumber.open(pdf_file) as pdf:
                pages = len(pdf.pages)
                print(f"   ✓ PDF ma {pages} stron")
            
            # Spróbuj przetworzyć
            print(f"   → Ekstrakcja danych...")
            invoice_data = processor.extract_from_pdf(str(pdf_file))
            
            print(f"   → Mapowanie do Comarch...")
            comarch_data = mapper.map_invoice_data(invoice_data)
            
            print(f"   → Generowanie XML...")
            xml_content = generator.generate_xml(comarch_data)
            
            # Zapisz XML z unikalną nazwą
            output_name = pdf_file.stem + ".xml"
            output_path = output_dir / output_name
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            print(f"   ✅ SUKCES! XML zapisany jako: {output_name}")
            successful.append(pdf_file.name)
            
        except Exception as e:
            print(f"   ❌ BŁĄD: {str(e)[:100]}")
            failed.append((pdf_file.name, str(e)))
    
    # 4. Podsumowanie
    print("\n" + "=" * 60)
    print("PODSUMOWANIE DIAGNOSTYKI")
    print("=" * 60)
    
    print(f"\n✅ Przetworzone pomyślnie: {len(successful)}/{len(pdf_files)}")
    if successful:
        for name in successful:
            print(f"   • {name}")
    
    if failed:
        print(f"\n❌ Niepowodzenia: {len(failed)}/{len(pdf_files)}")
        for name, error in failed:
            print(f"   • {name}")
            print(f"     Powód: {error[:100]}")
    
    # 5. Problem z kodowaniem
    print("\n📝 TEST KODOWANIA:")
    print("-" * 40)
    test_text = "SPÓŁKA Z OGRANICZONĄ ODPOWIEDZIALNOŚCIĄ"
    print(f"Tekst testowy: {test_text}")
    
    # Sprawdź XML
    if xml_files:
        first_xml = xml_files[0]
        with open(first_xml, 'r', encoding='utf-8') as f:
            content = f.read()[:500]
            # Sprawdzamy obecność poprawnych polskich znaków
            if "SPÓŁKA" in content or "OGRANICZONĄ" in content:
                print("✅ Kodowanie XML wygląda OK")
            elif "SP" in content and "KA" in content:
                print("⚠️ Możliwy problem z kodowaniem")
                print("   Sprawdź plik XML ręcznie")
            else:
                print("ℹ️ Nie można określić stanu kodowania")


if __name__ == "__main__":
    diagnose_system()
    input("\nNaciśnij ENTER aby zakończyć...")
