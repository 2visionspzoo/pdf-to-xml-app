# -*- coding: utf-8 -*-
"""
Skrypt testowy do weryfikacji poprawek w generatorach XML
Test formatu Comarch ERP Optima
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.xml_generator import XMLGenerator
from app.xml_generator_multi import XMLGeneratorMulti
from app.comarch_mapper import ComarchMapper
from lxml import etree
import logging
from datetime import datetime

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def print_header(text):
    """Wyświetla nagłówek"""
    print(f"\n{'='*80}")
    print(f"🧪 {text}")
    print('='*80)

def test_xml_structure(xml_string):
    """Testuje strukturę XML zgodną z Comarch ERP Optima"""
    try:
        # Parsuj XML
        root = etree.fromstring(xml_string.encode('utf-8'))
        
        # Sprawdź główny element
        if root.tag != "Dokumenty":
            return False, f"❌ Błędny element główny: {root.tag} (powinno być: Dokumenty)"
        
        # Sprawdź dokumenty
        dokumenty = root.findall("Dokument")
        if not dokumenty:
            return False, "❌ Brak elementów Dokument"
        
        # Sprawdź strukturę pierwszego dokumentu
        dokument = dokumenty[0]
        
        # Sprawdź typ dokumentu
        typ = dokument.get("Typ")
        if typ != "ZAKUP":
            return False, f"❌ Błędny typ dokumentu: {typ} (powinno być: ZAKUP)"
        
        # Sprawdź wymagane sekcje
        required_sections = {
            "Naglowek": False,
            "Pozycje": False,
            "RejestrVAT": False,
            "Platnosc": False
        }
        
        for child in dokument:
            if child.tag in required_sections:
                required_sections[child.tag] = True
        
        missing = [k for k, v in required_sections.items() if not v]
        if missing:
            return False, f"❌ Brakujące sekcje: {', '.join(missing)}"
        
        # Sprawdź nagłówek
        naglowek = dokument.find("Naglowek")
        required_header_fields = ["Numer", "DataWystawienia", "Kontrahent", "FormaPlatnosci"]
        
        for field in required_header_fields:
            if naglowek.find(field) is None:
                return False, f"❌ Brak pola {field} w Naglowek"
        
        # Sprawdź kontrahenta
        kontrahent = naglowek.find("Kontrahent")
        if kontrahent.find("NIP") is None:
            return False, "❌ Brak NIP w Kontrahent"
        if kontrahent.find("Nazwa") is None:
            return False, "❌ Brak Nazwa w Kontrahent"
        
        # Sprawdź pozycje
        pozycje = dokument.find("Pozycje")
        pozycja_list = pozycje.findall("Pozycja")
        if not pozycja_list:
            return False, "❌ Brak pozycji faktury"
        
        # Sprawdź pierwszą pozycję
        pozycja = pozycja_list[0]
        required_item_fields = ["Opis", "Ilosc", "CenaNetto", "StawkaVAT", "KwotaVAT"]
        
        for field in required_item_fields:
            if pozycja.find(field) is None:
                return False, f"❌ Brak pola {field} w Pozycja"
        
        # Sprawdź rejestr VAT
        rejestr = dokument.find("RejestrVAT")
        if rejestr.find("Typ") is None:
            return False, "❌ Brak Typ w RejestrVAT"
        if rejestr.find("StawkaVAT") is None:
            return False, "❌ Brak StawkaVAT w RejestrVAT"
        
        # Sprawdź płatność
        platnosc = dokument.find("Platnosc")
        if platnosc.find("Kwota") is None:
            return False, "❌ Brak Kwota w Platnosc"
        
        return True, f"✅ Struktura XML zgodna z Comarch ERP Optima! Znaleziono {len(dokumenty)} dokument(ów)"
        
    except Exception as e:
        return False, f"❌ Błąd parsowania XML: {str(e)}"

def test_single_invoice():
    """Test pojedynczej faktury"""
    print_header("TEST POJEDYNCZEJ FAKTURY")
    
    # Przykładowe dane testowe
    test_data = {
        'invoice_number': 'FA/123/2025',
        'invoice_date': '2025-08-01',
        'sale_date': '2025-08-01',
        'seller': {
            'name': 'Google Cloud Poland Sp. Z O.O.',
            'nip': '5252822767'
        },
        'payment': {
            'method': 'przelew',
            'due_date': '2025-08-08'
        },
        'items': [{
            'name': 'Usługi dozoru, transportu, informatyczne, pozostałe',
            'quantity': 1,
            'unit': 'szt.',
            'unit_price_net': 511.42,
            'net_amount': 511.42,
            'vat_rate': 23,
            'vat_amount': 117.63,
            'gross_amount': 629.05
        }],
        'summary': {
            'net_total': 511.42,
            'vat_total': 117.63,
            'gross_total': 629.05
        }
    }
    
    try:
        # Mapuj dane
        mapper = ComarchMapper()
        comarch_data = mapper.map_invoice_data(test_data)
        
        print("📋 Dane zmapowane:")
        print(f"   • Numer faktury: {comarch_data.invoice_number}")
        print(f"   • Sprzedawca: {comarch_data.seller_name}")
        print(f"   • NIP: {comarch_data.seller_nip}")
        print(f"   • Kwota netto: {comarch_data.net_total:.2f}")
        print(f"   • VAT: {comarch_data.vat_total:.2f}")
        print(f"   • Brutto: {comarch_data.gross_total:.2f}")
        
        # Generuj XML
        generator = XMLGenerator()
        xml_str = generator.generate_xml(comarch_data)
        
        print(f"\n📄 XML wygenerowany ({len(xml_str)} znaków)")
        
        # Testuj strukturę
        valid, message = test_xml_structure(xml_str)
        print(f"\n{message}")
        
        # Zapisz do pliku testowego
        output_file = os.path.join(os.path.dirname(__file__), 'test_single_output.xml')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xml_str)
        print(f"💾 XML zapisany do: {output_file}")
        
        # Wyświetl fragment XML
        lines = xml_str.split('\n')[:20]
        print("\n📝 Pierwsze 20 linii XML:")
        for line in lines:
            print(f"   {line}")
        
        return valid
        
    except Exception as e:
        print(f"❌ Błąd: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_invoices():
    """Test wielu faktur"""
    print_header("TEST WIELU FAKTUR")
    
    # Przykładowe dane dla 3 faktur
    invoices_data = []
    
    for i in range(1, 4):
        invoice = {
            'invoice_number': f'FA/{i}/2025',
            'invoice_date': f'2025-08-0{i}',
            'seller': {
                'name': f'Dostawca {i} Sp. z o.o.',
                'nip': f'525282276{i}'
            },
            'payment': {
                'method': 'przelew',
                'due_date': f'2025-08-1{i}'
            },
            'items': [{
                'name': f'Towar/Usługa {i}',
                'quantity': i,
                'unit_price_net': 100.00 * i,
                'net_amount': 100.00 * i * i,
                'vat_rate': 23,
                'vat_amount': 23.00 * i * i,
                'gross_amount': 123.00 * i * i
            }],
            'summary': {
                'net_total': 100.00 * i * i,
                'vat_total': 23.00 * i * i,
                'gross_total': 123.00 * i * i
            }
        }
        invoices_data.append(invoice)
    
    try:
        mapper = ComarchMapper()
        comarch_list = []
        
        for inv_data in invoices_data:
            comarch_data = mapper.map_invoice_data(inv_data)
            comarch_list.append(comarch_data)
        
        print(f"📋 Zmapowano {len(comarch_list)} faktur")
        
        # Generuj XML
        generator = XMLGeneratorMulti()
        xml_str = generator.generate_multi_invoice_xml(comarch_list)
        
        print(f"📄 XML wygenerowany ({len(xml_str)} znaków)")
        
        # Testuj strukturę
        valid, message = test_xml_structure(xml_str)
        print(f"\n{message}")
        
        # Zapisz do pliku
        output_file = os.path.join(os.path.dirname(__file__), 'test_multi_output.xml')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xml_str)
        print(f"💾 XML zapisany do: {output_file}")
        
        return valid
        
    except Exception as e:
        print(f"❌ Błąd: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Główna funkcja testowa"""
    print("\n" + "="*80)
    print("🚀 START TESTÓW FORMATU COMARCH ERP OPTIMA")
    print(f"Data testu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    results = []
    
    # Test 1: Pojedyncza faktura
    results.append(("Pojedyncza faktura", test_single_invoice()))
    
    # Test 2: Wiele faktur
    results.append(("Wiele faktur", test_multiple_invoices()))
    
    # Podsumowanie
    print("\n" + "="*80)
    print("📊 PODSUMOWANIE TESTÓW")
    print("="*80)
    
    all_passed = all(result for _, result in results)
    
    for test_name, passed in results:
        status = "✅ ZALICZONY" if passed else "❌ NIEZALICZONY"
        print(f"   {test_name}: {status}")
    
    if all_passed:
        print("\n✅ WSZYSTKIE TESTY ZALICZONE!")
        print("🎉 Generatory XML działają poprawnie z formatem Comarch ERP Optima!")
    else:
        print("\n⚠️ Niektóre testy nie przeszły. Sprawdź logi powyżej.")
    
    print("\n💡 WSKAZÓWKA: Sprawdź pliki XML w katalogu skrypty_testowe:")
    print("   • test_single_output.xml - pojedyncza faktura")
    print("   • test_multi_output.xml - wiele faktur")

if __name__ == "__main__":
    main()
