@echo off
REM Create Desktop Shortcut for KATH

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set SHORTCUT_NAME=KATH.lnk
set TARGET=%SCRIPT_DIR%start-kath.bat
set ICON=%SystemRoot%\System32\shell32.dll,13

echo Creating desktop shortcut for KATH...

REM Create VBScript to make shortcut
set VBSCRIPT=%TEMP%\create_shortcut.vbs
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%VBSCRIPT%"
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\%SHORTCUT_NAME%" >> "%VBSCRIPT%"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%VBSCRIPT%"
echo oLink.TargetPath = "%TARGET%" >> "%VBSCRIPT%"
echo oLink.WorkingDirectory = "%SCRIPT_DIR%" >> "%VBSCRIPT%"
echo oLink.Description = "Launch KATH Genetic Analysis Tool" >> "%VBSCRIPT%"
echo oLink.IconLocation = "%ICON%" >> "%VBSCRIPT%"
echo oLink.Save >> "%VBSCRIPT%"

REM Run the script
cscript //nologo "%VBSCRIPT%"
del "%VBSCRIPT%"

echo.
echo Success! KATH shortcut created on your desktop.
echo Double-click the shortcut to start KATH.
echo.
pause
