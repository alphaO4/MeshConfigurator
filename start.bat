@echo off
setlocal

rem Resolve repository root and switch to it
set "REPO_DIR=%~dp0"
pushd "%REPO_DIR%" >nul

set "VENV_DIR=.venv"
set "ACTIVATE_BAT=%VENV_DIR%\Scripts\activate.bat"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "DEPS_MARKER=%VENV_DIR%\.deps_installed"

if not exist "%PYTHON_EXE%" (
    echo [MeshConfigurator] Creating virtual environment...
    py -3 -m venv "%VENV_DIR%"
    if errorlevel 1 goto :error
    set "NEED_DEPS=1"
)

if not exist "%ACTIVATE_BAT%" (
    echo [MeshConfigurator] Could not find virtual environment activation script.
    goto :error
)

call "%ACTIVATE_BAT%"
if errorlevel 1 goto :error

if defined NEED_DEPS (
    echo [MeshConfigurator] Installing Python dependencies...
    python -m pip install --upgrade pip
    if errorlevel 1 goto :error
    python -m pip install -r requirements.txt
    if errorlevel 1 goto :error
    > "%DEPS_MARKER%" echo installed
) else (
    if not exist "%DEPS_MARKER%" (
        echo [MeshConfigurator] Installing Python dependencies...
        python -m pip install -r requirements.txt
        if errorlevel 1 goto :error
        > "%DEPS_MARKER%" echo installed
    )
)

echo [MeshConfigurator] Launching application...
python app.py
if errorlevel 1 goto :error

echo [MeshConfigurator] Application closed.
popd >nul
endlocal
exit /b 0

:error
echo [MeshConfigurator] Startup failed.
popd >nul
endlocal
exit /b 1
