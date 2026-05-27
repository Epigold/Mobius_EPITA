@echo off
setlocal enabledelayedexpansion
title Build Windows - Mobius

echo ============================================
echo        Build Windows du projet Mobius
echo ============================================
echo.

set "PROJECT_ROOT=%~dp0"
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

set "GAME_ROOT=%PROJECT_ROOT%\mobius"
set "BUILD_VENV=%PROJECT_ROOT%\.build-venv-win"
set "DIST_DIR=%PROJECT_ROOT%\dist"
set "BUILD_DIR=%PROJECT_ROOT%\build"
set "OUTPUT_DIR=%PROJECT_ROOT%"
set "EXECUTABLE_NAME=Mobius.exe"
set "PYTHON_CMD="

if not exist "%GAME_ROOT%\main.py" (
    echo [ERREUR] Point d'entree introuvable : "%GAME_ROOT%\main.py"
    goto :fail
)

echo Dossier du projet : %PROJECT_ROOT%
echo Dossier du jeu    : %GAME_ROOT%
echo.
echo Recherche d'une installation Python...

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
    echo [ERREUR] Python est requis pour compiler le jeu.
    echo Installez Python puis relancez le script.
    goto :fail
)

echo Python detecte : %PYTHON_CMD%
echo.
echo [1/5] Preparation de l'environnement de build
echo Creation ou mise a jour du venv : "%BUILD_VENV%"
%PYTHON_CMD% -m venv "%BUILD_VENV%"
if errorlevel 1 goto :fail

echo Activation de l'environnement virtuel...
call "%BUILD_VENV%\Scripts\activate.bat"
if errorlevel 1 goto :fail

echo.
echo [2/5] Installation des dependances de build
echo Mise a jour de pip, setuptools et wheel...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :fail
echo Installation de PyInstaller et des dependances du jeu...
python -m pip install pyinstaller pygame pillow typing_extensions
if errorlevel 1 goto :fail

echo.
echo [3/5] Nettoyage des anciens artefacts
echo Suppression des dossiers build precedents si presents...
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%OUTPUT_DIR%\%EXECUTABLE_NAME%" del /f /q "%OUTPUT_DIR%\%EXECUTABLE_NAME%" >nul 2>nul

echo.
echo [4/5] Compilation de l'executable Windows
echo Generation de "%EXECUTABLE_NAME%" avec PyInstaller...
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
if errorlevel 1 goto :fail

echo.
echo [5/5] Copie de l'executable final
copy /y "%DIST_DIR%\Mobius.exe" "%OUTPUT_DIR%\Mobius.exe" >nul
if errorlevel 1 goto :fail

echo.
echo Build terminee avec succes.
echo Executable genere : %OUTPUT_DIR%\%EXECUTABLE_NAME%
echo.
echo Lancement :
echo   %OUTPUT_DIR%\%EXECUTABLE_NAME%
echo.
pause
exit /b 0

:fail
echo.
echo Le build a echoue.
echo Consultez les messages affiches ci-dessus pour identifier l'etape en erreur.
echo.
pause
exit /b 1
