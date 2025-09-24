@echo off
echo ============================================================
echo     KONWERTER FAKTUR PDF - JEDEN PLIK XML
echo ============================================================
echo.

REM Przejdź do katalogu aplikacji
cd /d C:\pdf-to-xml-app

REM Sprawdź czy są pliki do przetworzenia
if not exist "input\*.pdf" (
    echo [BLAD] Brak plikow PDF w folderze input\
    echo Umiesc faktury PDF w: C:\pdf-to-xml-app\input\
    pause
    exit /b 1
)

echo Znalezione pliki PDF:
echo ---------------------
dir /b input\*.pdf
echo.

echo Wszystkie faktury zostana zebrane do jednego pliku XML
echo.
set /p confirm=Czy kontynuowac? (T/N): 
if /i "%confirm%" neq "T" (
    echo Anulowano
    pause
    exit /b 0
)

echo.
echo Rozpoczynam konwersje...
echo ---------------------

REM Uruchom konwerter
python app\main_multi.py --output output\wszystkie_faktury.xml

echo.
echo ============================================================
echo                    KONWERSJA ZAKONCZONA
echo ============================================================
echo.

if exist "output\wszystkie_faktury.xml" (
    echo SUKCES! Wygenerowano plik:
    echo C:\pdf-to-xml-app\output\wszystkie_faktury.xml
    echo.
    echo Plik zawiera wszystkie faktury w jednym XML
) else (
    echo BLAD! Plik XML nie zostal utworzony
    echo Sprawdz logi powyzej
)

echo.
pause
