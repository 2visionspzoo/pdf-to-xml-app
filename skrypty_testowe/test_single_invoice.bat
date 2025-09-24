@echo off
chcp 65001 > nul
title Test Pojedynczej Faktury z Debugowaniem

cd /d C:\pdf-to-xml-app\skrypty_testowe
python test_single_invoice_debug.py

pause
