@echo off
setlocal enabledelayedexpansion

set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

set "GAME_ROOT=%PROJECT_ROOT%\mobius"
set "BUILD_VENV=%PROJECT_ROOT%\.build-venv-win"
set "DIST_DIR=%PROJECT_ROOT%\dist"
set "BUILD_DIR=%PROJECT_ROOT%\build"
set "OUTPUT_DIR=%PROJECT_ROOT%\build-output"
set "EXECUTABLE_NAME=Mobius.exe"
set "PYTHON_CMD="

if not exist "%GAME_ROOT%\main.py" (
    echo Erreur: point d'entree introuvable: "%GAME_ROOT%\main.py"
    exit /b 1
)

where py >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD (
    where python >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD (
    where python3 >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=python3"
)
if not defined PYTHON_CMD (
    echo Erreur: Python est requis pour compiler le jeu. Installez Python puis relancez le script.
    exit /b 1
)

echo ==^> Preparation de l'environnement de build
%PYTHON_CMD% -m venv "%BUILD_VENV%"
if errorlevel 1 exit /b 1

call "%BUILD_VENV%\Scripts\activate.bat"
if errorlevel 1 exit /b 1

echo ==^> Installation des dependances de build
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b 1
python -m pip install pyinstaller pygame pillow typing_extensions
if errorlevel 1 exit /b 1

echo ==^> Nettoyage des anciens artefacts
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%OUTPUT_DIR%" rmdir /s /q "%OUTPUT_DIR%"

echo ==^> Compilation de l'executable Windows
pyinstaller ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --name Mobius ^
    --paths "%GAME_ROOT%" ^
    --add-data "%GAME_ROOT%\assets;assets" ^
    --add-data "%GAME_ROOT%\sons;sons" ^
    --hidden-import PIL ^
    --hidden-import PIL.Image ^
    --hidden-import PIL.ImageChops ^
    --hidden-import PIL.ImageSequence ^
    --hidden-import typing_extensions ^
    "%GAME_ROOT%\main.py"
if errorlevel 1 exit /b 1

mkdir "%OUTPUT_DIR%" >nul 2>nul
copy /y "%DIST_DIR%\Mobius.exe" "%OUTPUT_DIR%\Mobius.exe" >nul
if errorlevel 1 exit /b 1

echo.
echo Build terminee.
echo Executable : %OUTPUT_DIR%\%EXECUTABLE_NAME%
echo.
echo Lancement :
echo   %OUTPUT_DIR%\%EXECUTABLE_NAME%
