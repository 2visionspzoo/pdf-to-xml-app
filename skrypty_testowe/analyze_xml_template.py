#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANALIZA WZORU XML Z COMARCH OPTIMA
"""

import xml.etree.ElementTree as ET
from pathlib import Path

def analyze_xml_template():
    """Analizuj wzór XML od księgowej"""
    
    xml_path = Path(r'C:\pdf-to-xml-app\wzór_xml\plik od ksiegowej wzór zaimportowanych faktur.xml')
    
    print("\n" + "="*60)
    print("ANALIZA WZORU XML COMARCH OPTIMA")
    print("="*60 + "\n")
    
    try:
        # Odczytaj pierwsze linie
        with open(xml_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        print("Pierwsze 50 linii wzoru:")
        print("-"*40)
        for i, line in enumerate(lines[:50], 1):
            print(f"{i:3}: {line.rstrip()}")
        print("-"*40)
        
        # Parsuj XML
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        print(f"\nRoot element: {root.tag}")
        print(f"Atrybuty: {root.attrib}")
        
        # Analiza struktury
        print("\nStruktura głównych elementów:")
        for child in root:
            print(f"  • {child.tag}")
            for subchild in child:
                print(f"    - {subchild.tag}")
                for subsubchild in subchild:
                    print(f"      · {subsubchild.tag}: {subsubchild.text[:30] if subsubchild.text else 'brak'}")
                if len(list(child)) > 3:
                    print(f"      ... (i {len(list(child)) - 3} więcej)")
                    break
        
        # Znajdź przykładową fakturę
        print("\nPrzykładowa faktura:")
        print("-"*40)
        
        # Szukaj pierwszej faktury
        for elem in root.iter():
            if 'DOKUMENT' in elem.tag or 'FAKTURA' in elem.tag:
                print(f"\nElement: {elem.tag}")
                for child in elem:
                    text = child.text[:50] if child.text else 'brak'
                    print(f"  {child.tag}: {text}")
                break
        
        return True
        
    except Exception as e:
        print(f"Błąd analizy: {e}")
        return False

if __name__ == "__main__":
    analyze_xml_template()
