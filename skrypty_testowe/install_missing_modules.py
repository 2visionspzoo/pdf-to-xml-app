#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt instalujący brakujące moduły dla aplikacji PDF-to-XML
Autor: Assistant
Data: 2025-09-24
"""

import subprocess
import sys
import os

def install_package(package):
    """Instaluje pakiet przez pip"""
    try:
        print(f"📦 Instaluję: {package}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Zainstalowano: {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Błąd instalacji {package}: {e}")
        return False

def main():
    """Główna funkcja instalująca wszystkie wymagane pakiety"""
    
    print("="*60)
    print("🚀 INSTALACJA BRAKUJĄCYCH MODUŁÓW DLA PDF-TO-XML")
    print("="*60)
    
    # Lista pakietów do zainstalowania
    packages = [
        "spacy",  # Dla NLP i NER
        "requests",  # Dla walidacji zewnętrznej
        "lxml",  # Dla walidacji XSD
        "multiprocessing-logging",  # Dla lepszego logowania w multiprocessing
    ]
    
    # Instalacja pakietów
    print("\n📋 Instalowanie pakietów podstawowych...")
    failed = []
    for package in packages:
        if not install_package(package):
            failed.append(package)
    
    # Instalacja modelu spaCy dla języka polskiego
    if "spacy" not in failed:
        print("\n🇵🇱 Instalowanie modelu języka polskiego dla spaCy...")
        try:
            # Najpierw sprawdzamy czy model już jest zainstalowany
            import spacy
            try:
                nlp = spacy.load("pl_core_news_sm")
                print("✅ Model pl_core_news_sm już zainstalowany")
            except OSError:
                # Model nie jest zainstalowany, instalujemy
                print("📥 Pobieranie modelu pl_core_news_sm...")
                subprocess.check_call([sys.executable, "-m", "spacy", "download", "pl_core_news_sm"])
                print("✅ Model języka polskiego zainstalowany")
        except Exception as e:
            print(f"⚠️ Uwaga: Nie udało się zainstalować modelu spaCy: {e}")
            print("Możesz zainstalować ręcznie: python -m spacy download pl_core_news_sm")
            failed.append("pl_core_news_sm")
    
    # Podsumowanie
    print("\n" + "="*60)
    print("📊 PODSUMOWANIE INSTALACJI:")
    print("="*60)
    
    if not failed:
        print("✅ Wszystkie moduły zainstalowane pomyślnie!")
        print("\n🎯 Możesz teraz uruchomić aplikację:")
        print("   python app\\main.py --batch")
    else:
        print(f"⚠️ Nie udało się zainstalować: {', '.join(failed)}")
        print("\n🔧 Spróbuj zainstalować ręcznie:")
        for package in failed:
            if package == "pl_core_news_sm":
                print(f"   python -m spacy download {package}")
            else:
                print(f"   pip install {package}")
    
    print("\n💡 Wskazówka: Jeśli występują problemy z instalacją, spróbuj:")
    print("   1. Uruchomić jako administrator")
    print("   2. Zaktualizować pip: python -m pip install --upgrade pip")
    print("   3. Użyć wirtualnego środowiska")
    
    return 0 if not failed else 1

if __name__ == "__main__":
    sys.exit(main())
