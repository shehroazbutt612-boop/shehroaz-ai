@echo off
title SHEHROAZ AI Setup
echo ======================================
echo       SHEHROAZ AI - First Setup
echo ======================================
echo.
where ollama >nul 2>nul
if errorlevel 1 (
  echo Ollama not found. Install it from https://ollama.com/download
  echo Then close and reopen this window and run this file again.
  pause
  exit /b 1
)
where py >nul 2>nul
if errorlevel 1 (
  echo Python not found. Install Python 3 from https://www.python.org/downloads/
  echo Tick "Add Python to PATH" during installation.
  pause
  exit /b 1
)
echo Installing Python packages...
py -m pip install -r requirements.txt
if errorlevel 1 (
  echo Package installation failed. Check your internet connection and try again.
  pause
  exit /b 1
)
echo.
echo Downloading the AI model. This may take time and use several GB of internet.
ollama pull llama3.2
if errorlevel 1 (
  echo Model download failed. Check Ollama and your internet connection.
  pause
  exit /b 1
)
echo.
echo Creating your custom SHEHROAZ AI model...
ollama create shehroaz-ai -f Modelfile
if errorlevel 1 (
  echo Custom model creation failed.
  pause
  exit /b 1
)
echo.
echo Setup complete! Run start_windows.bat next.
pause
