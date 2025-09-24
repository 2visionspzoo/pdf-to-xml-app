#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test nowego systemu przetwarzania wsadowego
"""

import sys
import os
from pathlib import Path
import subprocess
import time

def test_batch_processing():
    """Testuje przetwarzanie wsadowe"""
    print("=" * 60)
    print("TEST PRZETWARZANIA WSADOWEGO")
    print("=" * 60)
    
    # Sprawdź pliki wejściowe
    input_dir = Path(r"C:\pdf-to-xml-app\input")
    output_dir = Path(r"C:\pdf-to-xml-app\output")
    
    pdf_files = list(input_dir.glob("*.pdf"))
    print(f"\n📁 Pliki PDF do przetworzenia: {len(pdf_files)}")
    for i, pdf in enumerate(pdf_files[:5], 1):
        print(f"   {i}. {pdf.name}")
    if len(pdf_files) > 5:
        print(f"   ... i {len(pdf_files) - 5} więcej")
    
    # Wyczyść folder output
    print(f"\n🧹 Czyszczenie folderu output...")
    for xml_file in output_dir.glob("*.xml"):
        xml_file.unlink()
    print("   ✓ Wyczyszczono")
    
    # Uruchom nowy system
    print(f"\n🚀 Uruchamiam przetwarzanie wsadowe...")
    print("-" * 40)
    
    start_time = time.time()
    
    cmd = [
        sys.executable,
        r"C:\pdf-to-xml-app\app\main.py",
        "--input-dir", str(input_dir),
        "--output-dir", str(output_dir)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    elapsed = time.time() - start_time
    
    # Sprawdź wyniki
    print(result.stdout)
    if result.stderr:
        print("BŁĘDY:", result.stderr)
    
    # Sprawdź pliki wyjściowe
    xml_files = list(output_dir.glob("*.xml"))
    
    print("\n" + "=" * 60)
    print("WYNIKI TESTU")
    print("=" * 60)
    
    print(f"\n📊 Statystyki:")
    print(f"   • Plików PDF: {len(pdf_files)}")
    print(f"   • Plików XML: {len(xml_files)}")
    print(f"   • Czas: {elapsed:.2f} sekund")
    print(f"   • Skuteczność: {len(xml_files)}/{len(pdf_files)} ({100*len(xml_files)/len(pdf_files):.0f}%)")
    
    if len(xml_files) == len(pdf_files):
        print("\n✅ SUKCES! Wszystkie pliki przetworzone!")
    elif len(xml_files) > 0:
        print(f"\n⚠️ CZĘŚCIOWY SUKCES: Przetworzone {len(xml_files)} z {len(pdf_files)} plików")
    else:
        print("\n❌ NIEPOWODZENIE: Żaden plik nie został przetworzony")
    
    # Lista wygenerowanych plików
    if xml_files:
        print(f"\n📄 Wygenerowane pliki XML:")
        for i, xml in enumerate(xml_files[:5], 1):
            size = xml.stat().st_size / 1024
            print(f"   {i}. {xml.name} ({size:.1f} KB)")
        if len(xml_files) > 5:
            print(f"   ... i {len(xml_files) - 5} więcej")
    
    # Sprawdź kodowanie
    if xml_files:
        print(f"\n🔤 Test kodowania pierwszego pliku:")
        first_xml = xml_files[0]
        with open(first_xml, 'r', encoding='utf-8') as f:
            content = f.read()
            if "SPÓŁKA" in content:
                print("   ✅ Kodowanie poprawne (zawiera 'SPÓŁKA')")
            elif "2VISION" in content:
                # Sprawdź czy są polskie znaki w innych miejscach
                polish_chars = ['Ą', 'Ć', 'Ę', 'Ł', 'Ń', 'Ó', 'Ś', 'Ź', 'Ż']
                has_polish = any(char in content for char in polish_chars)
                if has_polish:
                    print("   ✅ Kodowanie wygląda poprawnie")
                else:
                    print("   ⚠️ Możliwy problem z kodowaniem")
                    print("   💡 Sprawdź plik XML ręcznie")
            else:
                print("   ℹ️ Nie znaleziono tekstu testowego")

if __name__ == "__main__":
    test_batch_processing()
    input("\nNaciśnij ENTER aby zakończyć...")
