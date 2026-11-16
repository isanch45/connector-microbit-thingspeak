@echo off
setlocal
cd /d "%~dp0"
echo Compilant Connector Microbit-ThingSpeak-Serial (reconstruccio v5.1.4)
py -3.12 -m pip install -r requirements.txt -r requirements-build.txt
if errorlevel 1 exit /b 1
py -3.12 -m unittest discover -s tests -v
if errorlevel 1 exit /b 1
py -3.12 -m PyInstaller --noconfirm --clean --onefile --windowed --name Connector_Microbit-ThingSpeak-Serial_v5.1.4_rebuild --icon assets\app_icon.ico --add-data "assets\app_icon.png;assets" microbit_thingspeak_gateway.py
if errorlevel 1 exit /b 1
echo EXE reconstruït: dist\Connector_Microbit-ThingSpeak-Serial_v5.1.4_rebuild.exe
exit /b 0
