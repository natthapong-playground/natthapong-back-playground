@echo off
setlocal EnableExtensions DisableDelayedExpansion

pushd "%~dp0" >nul || (
    echo ERROR: Cannot open the project directory.
    exit /b 1
)

set "VENV_DIR=%CD%\.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "EXPECTED_VENV=%VENV_DIR%"

where py >nul 2>&1 || (
    echo ERROR: The Python launcher was not found.
    echo Install 64-bit Python 3.12 from https://www.python.org/downloads/
    goto :error
)

py -3.12 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>&1 || (
    echo ERROR: Python 3.12 is required but was not found.
    echo Install it, then run setup.bat again.
    goto :error
)

where docker >nul 2>&1 || (
    echo ERROR: Docker was not found.
    echo Install Docker Desktop and enable Docker Compose v2.
    goto :error
)

docker compose version >nul 2>&1 || (
    echo ERROR: Docker Compose v2 is not available.
    goto :error
)

if not exist "%VENV_PYTHON%" (
    if exist "%VENV_DIR%" (
        echo ERROR: .venv exists but does not contain a usable Python environment.
        echo Rename or remove "%VENV_DIR%" manually, then run setup.bat again.
        goto :error
    )

    echo Creating the project-local Python 3.12 environment...
    py -3.12 -m venv "%VENV_DIR%" || goto :error
)

"%VENV_PYTHON%" -c "import os, pathlib, sys; expected = pathlib.Path(os.environ['EXPECTED_VENV']).resolve(); actual = pathlib.Path(sys.prefix).resolve(); raise SystemExit(0 if actual == expected and sys.version_info[:2] == (3, 12) else 1)" >nul 2>&1 || (
    echo ERROR: .venv is not this project's Python 3.12 environment.
    echo Rename or remove "%VENV_DIR%" manually, then run setup.bat again.
    goto :error
)

set "PIP_REQUIRE_VIRTUALENV=true"
set "PIP_DISABLE_PIP_VERSION_CHECK=1"
set "PIP_NO_CACHE_DIR=true"

echo Installing dependencies into .venv only...
"%VENV_PYTHON%" -m pip install --upgrade pip || goto :error
"%VENV_PYTHON%" -m pip install -r "%CD%\requirements.txt" || goto :error
"%VENV_PYTHON%" -m pip check || goto :error

if not exist "%CD%\.env" (
    echo Creating a private .env with random local secrets...
    copy /y "%CD%\.env.example" "%CD%\.env" >nul || goto :error
    "%VENV_PYTHON%" -c "from pathlib import Path; import secrets; path = Path('.env'); text = path.read_text(encoding='utf-8'); password = secrets.token_urlsafe(24); text = text.replace('change-me', password).replace('REPLACE_WITH_A_LONG_RANDOM_SECRET', secrets.token_urlsafe(48)); path.write_text(text, encoding='utf-8')" || goto :env_error
) else (
    echo Keeping the existing private .env unchanged.
)

docker compose config --quiet || (
    echo ERROR: docker-compose.yml or .env is invalid.
    goto :error
)

echo.
echo Setup complete. Dependencies are installed only in:
echo   %VENV_DIR%
echo.
echo Start Docker Desktop, then run start.bat.
popd
exit /b 0

:env_error
del /q "%CD%\.env" >nul 2>&1
echo ERROR: Could not generate .env. No partial .env was kept.

:error
popd
exit /b 1
