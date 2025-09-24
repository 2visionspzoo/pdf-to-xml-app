# -*- coding: utf-8 -*-
"""
Generator XML dla wielu faktur w jednym pliku - format Comarch ERP Optima
"""
from lxml import etree
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class XMLGeneratorMulti:
    def generate_multi_invoice_xml(self, invoice_list) -> str:
        """Generuje XML z wieloma fakturami zgodny z formatem Comarch ERP Optima"""
        
        # Tworzenie głównego elementu bez namespace - czysty XML
        root = etree.Element("Dokumenty")
        
        # Dodaj każdą fakturę jako osobny dokument
        for idx, comarch_data in enumerate(invoice_list, 1):
            # Tworzenie dokumentu typu ZAKUP
            dokument = etree.SubElement(root, "Dokument")
            dokument.set("Typ", "ZAKUP")
            
            # Nagłówek
            naglowek = etree.SubElement(dokument, "Naglowek")
            etree.SubElement(naglowek, "Numer").text = comarch_data.invoice_number
            etree.SubElement(naglowek, "DataWystawienia").text = comarch_data.issue_date
            etree.SubElement(naglowek, "DataSprzedazy").text = comarch_data.sale_date or comarch_data.issue_date
            
            # Opcjonalne: Data księgowania (jeśli inna niż wystawienia)
            etree.SubElement(naglowek, "DataKsiegowania").text = datetime.now().strftime('%Y-%m-%d')
            
            # Kontrahent (sprzedawca)
            kontrahent = etree.SubElement(naglowek, "Kontrahent")
            
            # NIP - upewnij się że jest wartość
            seller_nip = comarch_data.seller_nip if comarch_data.seller_nip else ""
            etree.SubElement(kontrahent, "NIP").text = seller_nip
            
            # Nazwa sprzedawcy
            seller_name = comarch_data.seller_name if comarch_data.seller_name else "NIEZNANY DOSTAWCA"
            etree.SubElement(kontrahent, "Nazwa").text = seller_name
            
            # Adres sprzedawcy
            if comarch_data.seller_address:
                adres_parts = []
                if comarch_data.seller_address.get('street'):
                    street = comarch_data.seller_address.get('street')
                    building = comarch_data.seller_address.get('building', '')
                    adres_parts.append(f"{street} {building}".strip())
                if comarch_data.seller_address.get('city'):
                    city = comarch_data.seller_address.get('city')
                    postal = comarch_data.seller_address.get('postal_code')
                    if postal:
                        adres_parts.append(f"{postal} {city}")
                    else:
                        adres_parts.append(city)
                adres_text = ", ".join(adres_parts) if adres_parts else "brak danych adresowych"
            else:
                adres_text = "brak danych adresowych"
            
            etree.SubElement(kontrahent, "Adres").text = adres_text
            
            # Kod kraju (opcjonalny)
            etree.SubElement(kontrahent, "KodKraju").text = "PL"
            
            # Forma płatności i termin
            etree.SubElement(naglowek, "FormaPlatnosci").text = comarch_data.payment_method
            etree.SubElement(naglowek, "TerminPlatnosci").text = comarch_data.payment_date
            
            # Waluta - sprawdź czy mamy informację o walucie
            waluta = "PLN"  # domyślna waluta
            etree.SubElement(naglowek, "Waluta").text = waluta
            
            # Pozycje faktury
            pozycje = etree.SubElement(dokument, "Pozycje")
            
            for item in comarch_data.items:
                pozycja = etree.SubElement(pozycje, "Pozycja")
                
                # Opis pozycji
                etree.SubElement(pozycja, "Opis").text = item['description']
                
                # Ilość
                etree.SubElement(pozycja, "Ilosc").text = str(item['quantity'])
                
                # Jednostka
                jednostka = item.get('unit', 'szt.')
                etree.SubElement(pozycja, "Jednostka").text = jednostka
                
                # Cena netto jednostkowa
                etree.SubElement(pozycja, "CenaNetto").text = f"{item['unit_price']:.2f}"
                
                # Wartość netto
                etree.SubElement(pozycja, "WartoscNetto").text = f"{item['net_value']:.2f}"
                
                # Stawka VAT (bez znaku %)
                etree.SubElement(pozycja, "StawkaVAT").text = str(item['vat_rate'])
                
                # Kwota VAT
                etree.SubElement(pozycja, "KwotaVAT").text = f"{item['vat_amount']:.2f}"
                
                # Wartość brutto
                etree.SubElement(pozycja, "WartoscBrutto").text = f"{item['gross_value']:.2f}"
                
                # Kategoria księgowa - można dostosować według typu
                kategoria = "402-13"  # domyślnie dla usług
                if 'towar' in item['description'].lower():
                    kategoria = "401-05"  # dla towarów
                etree.SubElement(pozycja, "KategoriaKsiegowa").text = kategoria
                
                # Konto księgowe
                etree.SubElement(pozycja, "KontoKsiegowe").text = kategoria
            
            # Rejestr VAT
            rejestr_vat = etree.SubElement(dokument, "RejestrVAT")
            etree.SubElement(rejestr_vat, "Typ").text = "Rejestr zakupu"
            
            # Jeśli mamy podsumowanie VAT według stawek
            if comarch_data.vat_summary:
                # Dla każdej stawki VAT dodaj osobny wpis
                for rate_str, amounts in comarch_data.vat_summary.items():
                    # W podstawowej strukturze używamy tylko jednej głównej stawki
                    # Dla pełnej zgodności można by utworzyć osobne elementy dla każdej stawki
                    rate = rate_str.replace('%', '')
                    etree.SubElement(rejestr_vat, "StawkaVAT").text = rate
                    etree.SubElement(rejestr_vat, "Netto").text = f"{amounts['net']:.2f}"
                    etree.SubElement(rejestr_vat, "VAT").text = f"{amounts['vat']:.2f}"
                    etree.SubElement(rejestr_vat, "Brutto").text = f"{amounts['gross']:.2f}"
                    break  # Użyjemy tylko pierwszej stawki jako głównej
            else:
                # Jeśli brak podsumowania, użyj sum całkowitych
                if comarch_data.net_total > 0 and comarch_data.vat_total > 0:
                    stawka_vat = round((comarch_data.vat_total / comarch_data.net_total) * 100)
                else:
                    stawka_vat = 23
                    
                etree.SubElement(rejestr_vat, "StawkaVAT").text = str(stawka_vat)
                etree.SubElement(rejestr_vat, "Netto").text = f"{comarch_data.net_total:.2f}"
                etree.SubElement(rejestr_vat, "VAT").text = f"{comarch_data.vat_total:.2f}"
            
            # Brutto - oblicz jeśli nie ma
            brutto = comarch_data.gross_total
            if brutto == 0:
                brutto = comarch_data.net_total + comarch_data.vat_total
            etree.SubElement(rejestr_vat, "Brutto").text = f"{brutto:.2f}"
            
            # VAT odliczalny
            etree.SubElement(rejestr_vat, "Odliczalny").text = "Tak"
            
            # Sekcja płatności
            platnosc = etree.SubElement(dokument, "Platnosc")
            etree.SubElement(platnosc, "Kwota").text = f"{brutto:.2f}"
            etree.SubElement(platnosc, "Waluta").text = waluta
            etree.SubElement(platnosc, "DataPlatnosci").text = comarch_data.payment_date
            etree.SubElement(platnosc, "Status").text = "rozchód"
            
            # Opcjonalne: Rachunek bankowy
            # etree.SubElement(platnosc, "RachunekBankowy").text = "PL12345678901234567890123456"
            
            # Opcjonalne dodatkowe elementy
            # Notatki
            if hasattr(comarch_data, 'notes') and comarch_data.notes:
                etree.SubElement(dokument, "Notatki").text = comarch_data.notes
            
            # Załączniki
            if hasattr(comarch_data, 'attachments') and comarch_data.attachments:
                zalaczniki = etree.SubElement(dokument, "Zalaczniki")
                for attachment in comarch_data.attachments:
                    etree.SubElement(zalaczniki, "Zalacznik").text = attachment
            
            # Wersja schematu
            etree.SubElement(dokument, "Wersja").text = "2.00"
        
        # Konwersja do stringa z pretty print i prawidłowym kodowaniem UTF-8
        xml_str = etree.tostring(
            root, 
            pretty_print=True, 
            xml_declaration=True,
            encoding='UTF-8'
        )
        
        # Dekoduj do stringa UTF-8
        return xml_str.decode('utf-8')
