"""
Moduł do rozpoznawania typu faktury na podstawie zawartości PDF
"""
import re
from typing import Dict, Optional, List
from enum import Enum

class InvoiceType(Enum):
    """Typy faktur obsługiwane przez system"""
    ATUT = "ATUT"
    SANFILM = "Sanfilm"
    FIRMAO = "Firmao"
    BOLT = "Bolt"
    TERG = "TERG"
    ORLEN = "Orlen"
    MY_MUSIC = "My Music"
    PMH = "PMH"
    UNKNOWN = "Unknown"

class InvoiceDetector:
    """Klasa do rozpoznawania typu faktury"""
    
    def __init__(self):
        # Wzorce do rozpoznawania typów faktur
        self.patterns = {
            InvoiceType.ATUT: {
                'keywords': ['ATUT', 'Atut Sp. z o.o.', 'ATUT SP. Z O.O.'],
                'nip': '5252374228',
                'regex_patterns': [r'ATUT\s+SP.*Z\s*O\.O\.']
            },
            InvoiceType.SANFILM: {
                'keywords': ['Sanfilm', 'SANFILM', 'Sanfilm sp. z o.o.'],
                'nip': None,  # Uzupełnić NIP jeśli znany
                'regex_patterns': [r'Sanfilm\s+sp.*z\s*o\.o\.']
            },
            InvoiceType.FIRMAO: {
                'keywords': ['Firmao', 'FIRMAO', 'Firmao.pl'],
                'nip': None,
                'regex_patterns': [r'Firmao\.pl', r'FIRMAO']
            },
            InvoiceType.BOLT: {
                'keywords': ['Bolt', 'BOLT', 'Bolt Operations'],
                'nip': None,
                'regex_patterns': [r'Bolt\s+Operations', r'BOLT']
            },
            InvoiceType.TERG: {
                'keywords': ['TERG', 'Terg S.A.'],
                'nip': '5272630491',
                'regex_patterns': [r'TERG\s+S\.A\.']
            },
            InvoiceType.ORLEN: {
                'keywords': ['ORLEN', 'PKN ORLEN', 'Orlen Paliwa'],
                'nip': '7740001454',
                'regex_patterns': [r'PKN\s+ORLEN', r'ORLEN\s+PALIWA']
            },
            InvoiceType.MY_MUSIC: {
                'keywords': ['My Music', 'MyMusic', 'MY MUSIC'],
                'nip': None,
                'regex_patterns': [r'My\s+Music', r'MyMusic']
            },
            InvoiceType.PMH: {
                'keywords': ['PMH', 'P.M.H.'],
                'nip': None,
                'regex_patterns': [r'P\.M\.H\.', r'PMH']
            }
        }
    
    def detect_type(self, text: str) -> InvoiceType:
        """
        Wykrywa typ faktury na podstawie tekstu
        
        Args:
            text: Tekst wyekstrahowany z PDF
            
        Returns:
            Typ faktury
        """
        text_upper = text.upper()
        text_lower = text.lower()
        
        # Sprawdzanie każdego typu
        for invoice_type, patterns in self.patterns.items():
            # Sprawdzanie słów kluczowych
            for keyword in patterns['keywords']:
                if keyword.upper() in text_upper:
                    return invoice_type
            
            # Sprawdzanie NIP jeśli zdefiniowany
            if patterns['nip'] and patterns['nip'] in text:
                return invoice_type
            
            # Sprawdzanie wyrażeń regularnych
            for regex in patterns['regex_patterns']:
                if re.search(regex, text, re.IGNORECASE):
                    return invoice_type
        
        return InvoiceType.UNKNOWN
    
    def get_confidence_score(self, text: str, invoice_type: InvoiceType) -> float:
        """
        Zwraca poziom pewności wykrycia typu faktury
        
        Args:
            text: Tekst do analizy
            invoice_type: Wykryty typ faktury
            
        Returns:
            Poziom pewności (0.0 - 1.0)
        """
        if invoice_type == InvoiceType.UNKNOWN:
            return 0.0
        
        patterns = self.patterns.get(invoice_type, {})
        score = 0.0
        max_score = 0.0
        
        # Sprawdzanie słów kluczowych
        max_score += len(patterns.get('keywords', []))
        for keyword in patterns.get('keywords', []):
            if keyword.upper() in text.upper():
                score += 1.0
        
        # Sprawdzanie NIP
        if patterns.get('nip'):
            max_score += 2.0  # NIP ma większą wagę
            if patterns['nip'] in text:
                score += 2.0
        
        # Sprawdzanie regex
        max_score += len(patterns.get('regex_patterns', []))
        for regex in patterns.get('regex_patterns', []):
            if re.search(regex, text, re.IGNORECASE):
                score += 1.0
        
        return score / max_score if max_score > 0 else 0.0
    
    def detect_multiple_invoices(self, text: str) -> List[Dict]:
        """
        Wykrywa wiele faktur w jednym dokumencie
        
        Args:
            text: Tekst całego dokumentu
            
        Returns:
            Lista słowników z informacjami o znalezionych fakturach
        """
        invoices = []
        
        # Wzorce do wykrywania granic faktur
        invoice_markers = [
            r'FAKTURA\s+(?:VAT\s+)?(?:NR|Nr\.?)\s*[:\s]?\s*([A-Za-z0-9\-/]+)',
            r'INVOICE\s+(?:NUMBER|NO\.?)\s*[:\s]?\s*([A-Za-z0-9\-/]+)',
            r'Faktura\s+nr\s*[:\s]?\s*([A-Za-z0-9\-/]+)',
            r'Strona\s+\d+\s+z\s+\d+',
            r'Page\s+\d+\s+of\s+\d+'
        ]
        
        # Znajdowanie pozycji faktur
        for pattern in invoice_markers:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                start_pos = match.start()
                invoice_number = match.group(1) if match.lastindex else None
                
                # Wyodrębnianie fragmentu tekstu dla tej faktury
                # (zakładamy, że następna faktura zaczyna się od kolejnego dopasowania)
                end_pos = len(text)
                for next_match in re.finditer(pattern, text[start_pos+1:], re.IGNORECASE):
                    end_pos = start_pos + 1 + next_match.start()
                    break
                
                invoice_text = text[start_pos:end_pos]
                invoice_type = self.detect_type(invoice_text)
                
                invoices.append({
                    'number': invoice_number,
                    'type': invoice_type,
                    'start_pos': start_pos,
                    'end_pos': end_pos,
                    'confidence': self.get_confidence_score(invoice_text, invoice_type),
                    'text_fragment': invoice_text[:500]  # Pierwsze 500 znaków
                })
        
        # Deduplikacja i sortowanie
        unique_invoices = []
        seen_numbers = set()
        
        for invoice in sorted(invoices, key=lambda x: x['start_pos']):
            if invoice['number'] and invoice['number'] not in seen_numbers:
                seen_numbers.add(invoice['number'])
                unique_invoices.append(invoice)
            elif not invoice['number']:
                # Jeśli nie ma numeru, sprawdź czy nie jest to duplikat po pozycji
                is_duplicate = False
                for ui in unique_invoices:
                    if abs(ui['start_pos'] - invoice['start_pos']) < 100:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    unique_invoices.append(invoice)
        
        return unique_invoices
