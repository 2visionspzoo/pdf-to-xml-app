# -*- coding: utf-8 -*-
from lxml import etree
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class XMLGenerator:
    def generate_xml(self, comarch_data) -> str:
        """Generuje XML zgodny z formatem Comarch ERP Optima"""
        
        # Tworzenie głównego elementu bez namespace - czysty XML
        root = etree.Element("Dokumenty")
        
        # Tworzenie dokumentu typu ZAKUP
        dokument = etree.SubElement(root, "Dokument")
        dokument.set("Typ", "ZAKUP")
        
        # Nagłówek
        naglowek = etree.SubElement(dokument, "Naglowek")
        etree.SubElement(naglowek, "Numer").text = comarch_data.invoice_number
        etree.SubElement(naglowek, "DataWystawienia").text = comarch_data.issue_date
        etree.SubElement(naglowek, "DataSprzedazy").text = comarch_data.sale_date or comarch_data.issue_date
        
        # Kontrahent (sprzedawca)
        kontrahent = etree.SubElement(naglowek, "Kontrahent")
        etree.SubElement(kontrahent, "NIP").text = comarch_data.seller_nip
        etree.SubElement(kontrahent, "Nazwa").text = comarch_data.seller_name
        
        # Adres sprzedawcy (jeśli dostępny)
        if comarch_data.seller_address:
            adres_parts = []
            if comarch_data.seller_address.get('street'):
                adres_parts.append(comarch_data.seller_address.get('street'))
            if comarch_data.seller_address.get('building'):
                adres_parts.append(comarch_data.seller_address.get('building'))
            if comarch_data.seller_address.get('city'):
                city = comarch_data.seller_address.get('city')
                postal = comarch_data.seller_address.get('postal_code')
                if postal:
                    adres_parts.append(f"{postal} {city}")
                else:
                    adres_parts.append(city)
            etree.SubElement(kontrahent, "Adres").text = ", ".join(adres_parts)
        else:
            # Domyślny adres jeśli brak
            etree.SubElement(kontrahent, "Adres").text = "brak danych adresowych"
        
        # Forma płatności i termin
        etree.SubElement(naglowek, "FormaPlatnosci").text = comarch_data.payment_method
        etree.SubElement(naglowek, "TerminPlatnosci").text = comarch_data.payment_date
        
        # Pozycje faktury
        pozycje = etree.SubElement(dokument, "Pozycje")
        
        for item in comarch_data.items:
            pozycja = etree.SubElement(pozycje, "Pozycja")
            
            # Opis pozycji
            etree.SubElement(pozycja, "Opis").text = item['description']
            
            # Ilość
            etree.SubElement(pozycja, "Ilosc").text = str(item['quantity'])
            
            # Jednostka
            if 'unit' in item:
                etree.SubElement(pozycja, "Jednostka").text = item['unit']
            
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
            
            # Konto księgowe (domyślne dla usług)
            etree.SubElement(pozycja, "KontoKsiegowe").text = "402-13"
        
        # Rejestr VAT
        rejestr_vat = etree.SubElement(dokument, "RejestrVAT")
        etree.SubElement(rejestr_vat, "Typ").text = "Rejestr zakupu"
        
        # Podsumowanie VAT według stawek
        if comarch_data.vat_summary:
            for rate_str, amounts in comarch_data.vat_summary.items():
                # Usuń znak % ze stawki
                rate = rate_str.replace('%', '')
                etree.SubElement(rejestr_vat, "StawkaVAT").text = rate
                etree.SubElement(rejestr_vat, "Netto").text = f"{amounts['net']:.2f}"
                etree.SubElement(rejestr_vat, "VAT").text = f"{amounts['vat']:.2f}"
                etree.SubElement(rejestr_vat, "Brutto").text = f"{amounts['gross']:.2f}"
                break  # W podstawowej wersji tylko jedna stawka w głównym elemencie
        else:
            # Jeśli brak podsumowania, użyj sum całkowitych
            # Próba wykrycia stawki VAT
            if comarch_data.net_total > 0 and comarch_data.vat_total > 0:
                stawka_vat = round((comarch_data.vat_total / comarch_data.net_total) * 100)
            else:
                stawka_vat = 23  # domyślna stawka
                
            etree.SubElement(rejestr_vat, "StawkaVAT").text = str(stawka_vat)
            etree.SubElement(rejestr_vat, "Netto").text = f"{comarch_data.net_total:.2f}"
            etree.SubElement(rejestr_vat, "VAT").text = f"{comarch_data.vat_total:.2f}"
            etree.SubElement(rejestr_vat, "Brutto").text = f"{comarch_data.gross_total:.2f}"
        
        # Odliczalny VAT
        etree.SubElement(rejestr_vat, "Odliczalny").text = "Tak"
        
        # Płatność
        platnosc = etree.SubElement(dokument, "Platnosc")
        etree.SubElement(platnosc, "Kwota").text = f"{comarch_data.gross_total:.2f}"
        
        # Waluta - określ na podstawie kwot lub domyślnie PLN
        waluta = "PLN"  # domyślna waluta
        # Można dodać logikę wykrywania waluty jeśli potrzebna
        etree.SubElement(platnosc, "Waluta").text = waluta
        
        etree.SubElement(platnosc, "DataPlatnosci").text = comarch_data.payment_date
        etree.SubElement(platnosc, "Status").text = "rozchód"
        
        # Konwersja do stringa z pretty print
        xml_str = etree.tostring(
            root, 
            pretty_print=True, 
            xml_declaration=True,
            encoding='UTF-8'
        ).decode('utf-8')
        
        return xml_str
