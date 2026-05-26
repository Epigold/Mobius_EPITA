@echo off
setlocal

set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"
for %%I in ("%PROJECT_ROOT%") do set "PARENT_DIR=%%~dpI"
if "%PARENT_DIR:~-1%"=="\" set "PARENT_DIR=%PARENT_DIR:~0,-1%"

echo Ce script va supprimer completement le dossier du projet :
echo   %PROJECT_ROOT%
echo.
echo Cela inclut le code source, les assets, les executables compiles et les environnements virtuels.
echo.
set /p CONFIRM=Tapez SUPPRIMER pour confirmer : 

if /I not "%CONFIRM%"=="SUPPRIMER" (
    echo Desinstallation annulee.
    exit /b 0
)

set "TMP_BAT=%TEMP%\mobius_uninstall_%RANDOM%%RANDOM%.bat"
> "%TMP_BAT%" echo @echo off
>>"%TMP_BAT%" echo ping 127.0.0.1 -n 3 ^>nul
>>"%TMP_BAT%" echo rmdir /s /q "%PROJECT_ROOT%"
>>"%TMP_BAT%" echo rmdir "%PARENT_DIR%" ^>nul 2^>^&1
>>"%TMP_BAT%" echo del "%%~f0" ^>nul 2^>^&1

start "" /min cmd /c "%TMP_BAT%"

echo Desinstallation lancee.
echo Le dossier sera supprime : %PROJECT_ROOT%
