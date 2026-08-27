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

REM Build the frontend - build.spec bundles frontend\dist, so it must exist first
echo Building frontend...
where npm >nul 2>nul
if errorlevel 1 (
    echo npm not found. Node.js 18+ is required to build the frontend.
    exit /b 1
)
pushd frontend
call npm install --silent
call npm run build
if errorlevel 1 (
    echo Frontend build failed.
    popd
    exit /b 1
)
popd

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
echo 1. Run HearthAI.exe >> "dist\%APP_NAME%\README.txt"
echo 2. Open http://127.0.0.1:8080 in your browser >> "dist\%APP_NAME%\README.txt"
echo 3. On first run, Hearth AI offers to download a starter model >> "dist\%APP_NAME%\README.txt"
echo. >> "dist\%APP_NAME%\README.txt"
echo Prefer your own model? Drop a .gguf file into the "models" folder >> "dist\%APP_NAME%\README.txt"
echo before starting, then pick it in Settings. >> "dist\%APP_NAME%\README.txt"

echo.
echo Build complete!
echo Output: dist\%APP_NAME%\
echo.
echo To distribute, zip the dist\%APP_NAME% folder
pause
