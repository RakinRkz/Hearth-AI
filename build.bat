@echo off
REM Build script for Hearth AI (Windows)
REM Usage: build.bat

set APP_NAME=HearthAI
set VERSION=1.0.0

echo Building %APP_NAME% v%VERSION%

REM Activate virtual environment
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Run: python -m venv venv
    exit /b 1
)

REM Install PyInstaller if not present
pip install pyinstaller --quiet

REM Clean previous builds
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

REM Build
echo Running PyInstaller...
pyinstaller build.spec --noconfirm

REM Create necessary directories in dist
mkdir "dist\%APP_NAME%\models" 2>nul
mkdir "dist\%APP_NAME%\data\conversations" 2>nul
mkdir "dist\%APP_NAME%\data\vectorstore" 2>nul
mkdir "dist\%APP_NAME%\documents" 2>nul

REM Create README
echo Hearth AI - Local AI Chat Application > "dist\%APP_NAME%\README.txt"
echo ==================================== >> "dist\%APP_NAME%\README.txt"
echo. >> "dist\%APP_NAME%\README.txt"
echo Quick Start: >> "dist\%APP_NAME%\README.txt"
echo 1. Download a GGUF model from HuggingFace >> "dist\%APP_NAME%\README.txt"
echo 2. Place the .gguf file in the "models" folder >> "dist\%APP_NAME%\README.txt"
echo 3. Run HearthAI.exe >> "dist\%APP_NAME%\README.txt"
echo 4. Go to Settings, Browse, Select your model, Load >> "dist\%APP_NAME%\README.txt"

echo.
echo Build complete!
echo Output: dist\%APP_NAME%\
echo.
echo To distribute, zip the dist\%APP_NAME% folder
pause
