@echo off
chcp 65001 > nul
title Konwersja Wszystkich Faktur

echo ╔══════════════════════════════════════════╗
echo ║    KONWERSJA WSZYSTKICH FAKTUR PDF      ║
echo ╚══════════════════════════════════════════╝
echo.

cd /d C:\pdf-to-xml-app

echo Dostępne faktury w katalogu input:
echo ────────────────────────────────────
dir /b input\*.pdf
echo ────────────────────────────────────
echo.

set /p confirm="Czy chcesz przetworzyć wszystkie pliki? (T/N): "
if /i not "%confirm%"=="T" goto END

echo.
echo Rozpoczynam konwersję...
echo ════════════════════════════════════

set count=0
set success=0
set failed=0

for %%f in (input\*.pdf) do (
    set /a count+=1
    echo.
    echo [!count!] Przetwarzanie: %%~nxf
    echo ────────────────────────────────────
    
    python app\main.py --input "%%f" --output "output\%%~nf.xml" 2>nul
    
    if exist "output\%%~nf.xml" (
        set /a success+=1
        echo ✓ Sukces: output\%%~nf.xml
    ) else (
        set /a failed+=1
        echo ✗ Błąd podczas konwersji
    )
)

echo.
echo ════════════════════════════════════
echo PODSUMOWANIE:
echo ════════════════════════════════════
echo Plików przetworzonych: %count%
echo Sukcesy: %success%
echo Błędy: %failed%
echo ════════════════════════════════════
echo.
echo Pliki XML znajdują się w: C:\pdf-to-xml-app\output\
echo.

:END
pause
