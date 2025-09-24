@echo off
chcp 65001 > nul
title Test Debugowania PDF-to-XML

echo ╔══════════════════════════════════════════╗
echo ║    KOMPLEKSOWY TEST Z DEBUGOWANIEM      ║
echo ╚══════════════════════════════════════════╝
echo.

cd /d C:\pdf-to-xml-app\skrypty_testowe
python test_debug_full.py

echo.
echo ════════════════════════════════════════════
echo Test zakończony. Sprawdź raport w:
echo test_debug_report.txt
echo ════════════════════════════════════════════
pause
