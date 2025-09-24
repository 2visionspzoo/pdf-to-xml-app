@echo off
echo ===================================
echo Test aplikacji PDF-to-XML
echo ===================================
echo.
echo [1] Testowanie lokalne (Python)
echo.

cd C:\pdf-to-xml-app

echo Instalacja wymaganych pakietów...
pip install -r requirements.txt

echo.
echo Uruchamianie aplikacji...
cd app
python main.py

echo.
echo ===================================
echo Test zakończony!
echo Sprawdź plik: C:\pdf-to-xml-app\output\output-test1.xml
echo ===================================
pause
