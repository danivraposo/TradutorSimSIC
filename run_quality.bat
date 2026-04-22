@echo off
setlocal

cd /d "%~dp0"

if exist "C:\ffmpeg\bin" (
	set "FFMPEG_DIR=C:\ffmpeg\bin"
)

if not exist .venv (
	echo A pasta .venv nao existe.
	echo Cria o ambiente e instala as dependencias com:
	echo   py -3 -m venv .venv
	echo   .venv\Scripts\python -m pip install -r requirements.txt
	pause
	exit /b 1
)

call .venv\Scripts\activate.bat
set "WHISPER_DEVICE=auto"
set "WHISPER_MODEL=medium"
python Tradutor_de_PT_para_ING\server.py

if errorlevel 1 (
	echo.
	echo O servidor terminou com erro.
	pause
)

