@echo off
echo ============================================================
echo           KONWERTER FAKTUR PDF DO XML (Comarch)
echo ============================================================
echo.

REM Przejdź do katalogu aplikacji
cd /d C:\pdf-to-xml-app

REM Sprawdź czy są pliki do przetworzenia
if not exist "input\*.pdf" (
    echo [BŁĄD] Brak plików PDF w folderze input\
    echo Umieść faktury PDF w: C:\pdf-to-xml-app\input\
    pause
    exit /b 1
)

echo Znalezione pliki PDF:
echo ---------------------
dir /b input\*.pdf
echo.

echo Rozpoczynam konwersję...
echo ---------------------

REM Uruchom konwerter
python app\main.py

echo.
echo ============================================================
echo                    KONWERSJA ZAKOŃCZONA
echo ============================================================
echo.
echo Wygenerowane pliki XML znajdują się w folderze:
echo C:\pdf-to-xml-app\output\
echo.
dir /b output\*.xml 2>nul

echo.
pause
