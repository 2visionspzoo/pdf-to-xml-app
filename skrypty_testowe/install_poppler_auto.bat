@echo off
echo ========================================
echo INSTALACJA POPPLER
echo ========================================
echo.

echo Sprawdzam czy Poppler jest zainstalowany...
if exist "C:\poppler\Library\bin\pdftoppm.exe" (
    echo Poppler jest juz zainstalowany!
    "C:\poppler\Library\bin\pdftoppm.exe" -v
    echo.
    pause
    exit /b 0
)

echo Poppler nie jest zainstalowany.
echo.
echo Znaleziono skrypt PowerShell: C:\poppler\Install-Poppler.ps1
echo.
echo Uruchamiam instalator...
echo ========================================
echo.

powershell -ExecutionPolicy Bypass -File "C:\poppler\Install-Poppler.ps1"

echo.
echo ========================================
echo.

if exist "C:\poppler\Library\bin\pdftoppm.exe" (
    echo SUKCES! Poppler zostal zainstalowany.
    echo.
    echo Test:
    "C:\poppler\Library\bin\pdftoppm.exe" -v
) else (
    echo BLAD: Instalacja nie powiodla sie.
    echo.
    echo Sprobuj uruchomic PowerShell jako Administrator i wykonac:
    echo powershell -ExecutionPolicy Bypass -File "C:\poppler\Install-Poppler.ps1"
)

echo.
pause
