"""
Moduł konfiguracji aplikacji
"""
import os
import configparser
from pathlib import Path

class Config:
    """Klasa przechowująca konfigurację aplikacji"""
    
    def __init__(self, config_file='config.ini'):
        self.config = configparser.ConfigParser()
        config_path = Path(__file__).parent.parent / config_file
        
        if config_path.exists():
            self.config.read(config_path, encoding='utf-8')
            self._load_settings()
        else:
            self._set_defaults()
    
    def _load_settings(self):
        """Wczytuje ustawienia z pliku konfiguracyjnego"""
        # Tesseract
        self.tesseract_path = self.config.get('DEFAULT', 'TESSERACT_PATH', 
                                              fallback=r'C:\Program Files\Tesseract-OCR\tesseract.exe')
        self.ocr_languages = self.config.get('DEFAULT', 'OCR_LANGUAGES', fallback='pol+eng')
        self.ocr_dpi = self.config.getint('DEFAULT', 'OCR_DPI', fallback=300)
        self.ocr_psm = self.config.getint('DEFAULT', 'OCR_PSM', fallback=6)
        
        # Poppler
        self.poppler_path = self.config.get('DEFAULT', 'POPPLER_PATH', fallback=None)
        
        # Domyślny nabywca
        self.default_buyer_name = self.config.get('DEFAULT', 'DEFAULT_BUYER_NAME', 
                                                  fallback='2Vision Sp. z o.o.')
        self.default_buyer_nip = self.config.get('DEFAULT', 'DEFAULT_BUYER_NIP', 
                                                 fallback='6751781780')
        self.default_buyer_address = self.config.get('DEFAULT', 'DEFAULT_BUYER_ADDRESS', 
                                                     fallback='ul. Dąbska 20A/17')
        self.default_buyer_city = self.config.get('DEFAULT', 'DEFAULT_BUYER_CITY', 
                                                  fallback='Kraków')
        self.default_buyer_postal_code = self.config.get('DEFAULT', 'DEFAULT_BUYER_POSTAL_CODE', 
                                                         fallback='31-572')
        
        # Katalogi
        self.input_dir = self.config.get('DEFAULT', 'INPUT_DIR', fallback='input')
        self.output_dir = self.config.get('DEFAULT', 'OUTPUT_DIR', fallback='output')
        self.processed_dir = self.config.get('DEFAULT', 'PROCESSED_DIR', fallback='processed')
        self.logs_dir = self.config.get('DEFAULT', 'LOGS_DIR', fallback='logs')
        
        # Logowanie
        self.log_level = self.config.get('DEFAULT', 'LOG_LEVEL', fallback='INFO')
        
        # XML
        self.xml_encoding = self.config.get('DEFAULT', 'XML_ENCODING', fallback='UTF-8')
        self.xml_indent = self.config.getboolean('DEFAULT', 'XML_INDENT', fallback=True)
        self.xml_version = self.config.get('DEFAULT', 'XML_VERSION', fallback='1.0')
    
    def _set_defaults(self):
        """Ustawia domyślne wartości"""
        self.tesseract_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        self.ocr_languages = 'pol+eng'
        self.ocr_dpi = 300
        self.ocr_psm = 6
        self.poppler_path = None
        
        self.default_buyer_name = '2Vision Sp. z o.o.'
        self.default_buyer_nip = '6751781780'
        self.default_buyer_address = 'ul. Dąbska 20A/17'
        self.default_buyer_city = 'Kraków'
        self.default_buyer_postal_code = '31-572'
        
        self.input_dir = 'input'
        self.output_dir = 'output'
        self.processed_dir = 'processed'
        self.logs_dir = 'logs'
        
        self.log_level = 'INFO'
        
        self.xml_encoding = 'UTF-8'
        self.xml_indent = True
        self.xml_version = '1.0'
    
    def get_default_buyer(self):
        """Zwraca słownik z danymi domyślnego nabywcy"""
        return {
            'name': self.default_buyer_name,
            'nip': self.default_buyer_nip,
            'address': self.default_buyer_address,
            'city': self.default_buyer_city,
            'postal_code': self.default_buyer_postal_code,
            'country': 'Polska'
        }
    
    def get_tesseract_config(self):
        """Zwraca konfigurację dla Tesseract"""
        return f'--psm {self.ocr_psm} --oem 3'

# Singleton konfiguracji
_config = None

def get_config():
    """Zwraca instancję konfiguracji"""
    global _config
    if _config is None:
        _config = Config()
    return _config
