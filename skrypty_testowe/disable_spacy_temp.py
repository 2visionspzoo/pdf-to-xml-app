#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt tymczasowo wyłączający spacy w parserze
Autor: Assistant
Data: 2025-09-24
"""

import os
import sys
from pathlib import Path

def create_parser_without_spacy():
    """Tworzy wersję parsera bez spacy"""
    
    parser_path = Path(r"C:\pdf-to-xml-app\app\parsers\universal_parser_v6.py")
    backup_path = Path(r"C:\pdf-to-xml-app\app\parsers\universal_parser_v6_backup.py")
    
    print("📋 Tworzenie wersji parsera bez spacy...")
    
    # Odczytaj obecny parser
    with open(parser_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Backup zapisany: {backup_path}")
    
    # Modyfikuj kod - zakomentuj spacy
    modified_content = content.replace(
        "import spacy",
        "# import spacy  # TYMCZASOWO WYŁĄCZONE"
    )
    
    # Zastąp użycie spacy prostą implementacją
    modified_content = modified_content.replace(
        "self.nlp = spacy.load('pl_core_news_sm')",
        "self.nlp = None  # TYMCZASOWO WYŁĄCZONE"
    )
    
    # Dodaj zastępczą funkcję extract_with_ner
    if "def extract_with_ner" in modified_content:
        # Znajdź funkcję i zastąp jej ciało
        lines = modified_content.split('\n')
        new_lines = []
        in_ner_function = False
        indent_level = 0
        
        for i, line in enumerate(lines):
            if "def extract_with_ner" in line:
                in_ner_function = True
                indent_level = len(line) - len(line.lstrip())
                new_lines.append(line)
                new_lines.append(" " * (indent_level + 4) + '"""Tymczasowo wyłączone - używamy prostej ekstrakcji"""')
                new_lines.append(" " * (indent_level + 4) + "# SpaCy NER tymczasowo wyłączone")
                new_lines.append(" " * (indent_level + 4) + "return self.extract_company_data_simple(text)")
                continue
            
            if in_ner_function:
                # Sprawdź czy wyszliśmy z funkcji
                if line.strip() and not line.startswith(" " * (indent_level + 4)):
                    in_ner_function = False
                    new_lines.append(line)
                # Pomijamy oryginalną zawartość funkcji
            else:
                new_lines.append(line)
        
        modified_content = '\n'.join(new_lines)
    
    # Dodaj prostą funkcję ekstrakcji jeśli nie istnieje
    if "def extract_company_data_simple" not in modified_content:
        simple_function = '''
    def extract_company_data_simple(self, text):
        """Prosta ekstrakcja danych bez NER"""
        data = {}
        
        # Ekstrakcja nazwy
        nazwa_patterns = [
            r'(?:Sprzedawca|Dostawca|Wystawca)[:\s]+([^\n]+)',
            r'(?:Nazwa|Firma)[:\s]+([^\n]+)',
        ]
        for pattern in nazwa_patterns:
            if match := re.search(pattern, text, re.IGNORECASE):
                data['nazwa'] = match.group(1).strip()
                break
        
        # Ekstrakcja adresu
        adres_patterns = [
            r'(?:ul\.|ulica)\s+([^\n]+)',
            r'(?:Adres)[:\s]+([^\n]+)',
        ]
        for pattern in adres_patterns:
            if match := re.search(pattern, text, re.IGNORECASE):
                data['adres'] = match.group(1).strip()
                break
                
        return data
'''
        # Znajdź gdzie dodać funkcję
        lines = modified_content.split('\n')
        for i, line in enumerate(lines):
            if "class UniversalParser" in line:
                # Znajdź koniec klasy i dodaj przed nim
                class_indent = len(line) - len(line.lstrip())
                # Dodaj na końcu klasy
                lines.append(simple_function)
                break
        modified_content = '\n'.join(lines)
    
    # Zapisz zmodyfikowany plik
    with open(parser_path, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    print("✅ Parser zmodyfikowany - spacy tymczasowo wyłączone")
    print("ℹ️ Backup oryginalnego pliku: universal_parser_v6_backup.py")
    
    return True

def main():
    """Główna funkcja"""
    print("="*60)
    print("🔧 TYMCZASOWE WYŁĄCZENIE SPACY")
    print("="*60)
    
    try:
        if create_parser_without_spacy():
            print("\n✅ Sukces! Możesz teraz uruchomić aplikację:")
            print("   python app\\main.py --batch")
            print("\n⚠️ UWAGA: Funkcje NER (rozpoznawanie nazw własnych)")
            print("   są tymczasowo wyłączone. Aby je włączyć:")
            print("   1. Zainstaluj spacy: pip install spacy")
            print("   2. Pobierz model: python -m spacy download pl_core_news_sm")
            print("   3. Przywróć oryginalny plik z backupu")
        return 0
    except Exception as e:
        print(f"❌ Błąd: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
