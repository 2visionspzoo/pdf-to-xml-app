#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prosty test przetwarzania wszystkich plików
"""

import sys
import os
from pathlib import Path

# Dodaj katalog główny do ścieżki
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.pdf_processor import PDFProcessor
from app.comarch_mapper import ComarchMapper
from app.xml_generator import XMLGenerator

def test_all_files():
    """Testuje przetwarzanie wszystkich plików"""
    print("=" * 60)
    print("TEST PRZETWARZANIA WSZYSTKICH PLIKÓW")
    print("=" * 60)
    
    input_dir = Path(r"C:\pdf-to-xml-app\input")
    output_dir = Path(r"C:\pdf-to-xml-app\output")
    
    # Utwórz katalog output jeśli nie istnieje
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Znajdź wszystkie pliki PDF
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ Brak plików PDF w folderze input")
        return
    
    print(f"\n📁 Znaleziono {len(pdf_files)} plików PDF:")
    print("-" * 40)
    for i, pdf in enumerate(pdf_files, 1):
        print(f"{i}. {pdf.name}")
    
    # Przetwarzaj każdy plik
    print(f"\n🚀 Rozpoczynam przetwarzanie...")
    print("-" * 40)
    
    processor = PDFProcessor(parser_type='universal')
    mapper = ComarchMapper()
    generator = XMLGenerator()
    
    successful = []
    failed = []
    
    for pdf_file in pdf_files:
        try:
            print(f"\n📄 Przetwarzanie: {pdf_file.name}")
            
            # 1. Ekstrahuj dane z PDF
            print("   → Ekstrakcja danych...")
            invoice_data = processor.extract_from_pdf(str(pdf_file))
            
            # 2. Mapuj do formatu Comarch
            print("   → Mapowanie do Comarch...")
            comarch_data = mapper.map_invoice_data(invoice_data)
            
            # 3. Generuj XML
            print("   → Generowanie XML...")
            xml_content = generator.generate_xml(comarch_data)
            
            # 4. Zapisz XML z unikalną nazwą
            output_file = output_dir / (pdf_file.stem + ".xml")
            with open(output_file, 'w', encoding='utf-8-sig') as f:
                f.write(xml_content)
            
            print(f"   ✅ Sukces! Zapisano: {output_file.name}")
            successful.append(pdf_file.name)
            
        except Exception as e:
            print(f"   ❌ Błąd: {e}")
            failed.append((pdf_file.name, str(e)))
    
    # Podsumowanie
    print("\n" + "=" * 60)
    print("PODSUMOWANIE")
    print("=" * 60)
    
    print(f"\n✅ Przetworzone pomyślnie: {len(successful)}/{len(pdf_files)}")
    if successful:
        for name in successful[:5]:
            print(f"   • {name}")
        if len(successful) > 5:
            print(f"   ... i {len(successful) - 5} więcej")
    
    if failed:
        print(f"\n❌ Niepowodzenia: {len(failed)}/{len(pdf_files)}")
        for name, error in failed[:3]:
            print(f"   • {name}")
            print(f"     {error[:100]}")
        if len(failed) > 3:
            print(f"   ... i {len(failed) - 3} więcej")
    
    # Sprawdź pliki wyjściowe
    xml_files = list(output_dir.glob("*.xml"))
    print(f"\n📁 Pliki XML w folderze output: {len(xml_files)}")
    for i, xml in enumerate(xml_files[:5], 1):
        size = xml.stat().st_size / 1024
        print(f"   {i}. {xml.name} ({size:.1f} KB)")
    if len(xml_files) > 5:
        print(f"   ... i {len(xml_files) - 5} więcej")

if __name__ == "__main__":
    test_all_files()
    input("\nNaciśnij ENTER aby zakończyć...")
