@echo off
echo ======================================================================
echo   INICIANDO SERVIDOR LOCAL DO PAINEL DICOM
echo ======================================================================
echo.
echo Iniciando servidor Python HTTP na porta 8000...
start "" "http://localhost:8000/index.html"
python -m http.server 8000
