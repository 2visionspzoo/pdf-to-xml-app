#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt naprawczy - naprawia kodowanie w istniejących plikach XML
"""

import os
from pathlib import Path

def fix_encoding_in_xml(file_path):
    """Naprawia kodowanie w pliku XML"""
    try:
        # Odczytaj plik z różnymi kodowaniami
        content = None
        encodings = ['utf-8', 'latin-1', 'cp1250', 'iso-8859-2']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    break
            except:
                continue
        
        if not content:
            print(f"   ❌ Nie można odczytać pliku")
            return False
        
        original_content = content
        
        # Napraw znane problemy z kodowaniem
        replacements = {
            'SPÃ"ÅKA': 'SPÓŁKA',
            'OGRANICZONÄ„': 'OGRANICZONĄ',
            'ODPOWIEDZIALNOÅšCIÄ„': 'ODPOWIEDZIALNOŚCIĄ',
            'Ã"': 'Ó',
            'Å': 'Ł',
            'Ä„': 'Ą',
            'Åš': 'Ś',
            'Ã³': 'ó',
            'Ä™': 'ę',
            'Ä‡': 'ć',
            'Å¼': 'ż',
            'Åº': 'ź',
            'Å„': 'ń'
        }
        
        for wrong, correct in replacements.items():
            content = content.replace(wrong, correct)
        
        # Zapisz poprawiony plik
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8-sig') as f:
                f.write(content)
            print(f"   ✅ Naprawiono kodowanie")
            return True
        else:
            print(f"   ℹ️ Kodowanie już poprawne")
            return False
            
    except Exception as e:
        print(f"   ❌ Błąd: {e}")
        return False

def main():
    """Główna funkcja"""
    print("=" * 60)
    print("NAPRAWA KODOWANIA W PLIKACH XML")
    print("=" * 60)
    
    output_dir = Path(r"C:\pdf-to-xml-app\output")
    xml_files = list(output_dir.glob("*.xml"))
    
    if not xml_files:
        print("\n❌ Brak plików XML w folderze output")
        return
    
    print(f"\n📁 Znaleziono {len(xml_files)} plików XML")
    print("-" * 40)
    
    fixed = 0
    for xml_file in xml_files:
        print(f"\n{xml_file.name}:")
        if fix_encoding_in_xml(xml_file):
            fixed += 1
    
    print("\n" + "=" * 60)
    print("PODSUMOWANIE")
    print("=" * 60)
    print(f"✅ Naprawiono: {fixed}/{len(xml_files)} plików")
    
    if fixed > 0:
        print("\n💡 Wskazówka: Sprawdź pliki XML w folderze output")

if __name__ == "__main__":
    main()
    input("\nNaciśnij ENTER aby zakończyć...")
