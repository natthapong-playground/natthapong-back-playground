@echo off
setlocal EnableExtensions DisableDelayedExpansion

pushd "%~dp0" >nul || (
    echo ERROR: Cannot open the project directory.
    exit /b 1
)

set "VENV_DIR=%CD%\.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "EXPECTED_VENV=%VENV_DIR%"

if not exist "%VENV_PYTHON%" (
    echo ERROR: The project-local .venv is missing. Run setup.bat first.
    goto :error
)

"%VENV_PYTHON%" -c "import os, pathlib, sys; expected = pathlib.Path(os.environ['EXPECTED_VENV']).resolve(); actual = pathlib.Path(sys.prefix).resolve(); raise SystemExit(0 if actual == expected and sys.version_info[:2] == (3, 12) else 1)" >nul 2>&1 || (
    echo ERROR: .venv is not this project's Python 3.12 environment.
    echo Rename or remove it manually, then run setup.bat again.
    goto :error
)

if not exist "%CD%\.env" (
    echo ERROR: The private .env is missing. Run setup.bat first.
    goto :error
)

"%VENV_PYTHON%" -c "from pathlib import Path; text = Path('.env').read_text(encoding='utf-8'); raise SystemExit(1 if 'change-me' in text or 'REPLACE_WITH_A_LONG_RANDOM_SECRET' in text else 0)" >nul 2>&1 || (
    echo ERROR: .env still contains public placeholder credentials.
    echo Replace them or move .env aside and run setup.bat to generate safe local values.
    goto :error
)

where docker >nul 2>&1 || (
    echo ERROR: Docker was not found. Install and start Docker Desktop.
    goto :error
)

docker info >nul 2>&1 || (
    echo ERROR: Docker Desktop is not running or its Linux engine is unavailable.
    goto :error
)

docker compose config --quiet || goto :error

echo Starting this project's PostgreSQL and Redis containers...
docker compose up -d --wait --wait-timeout 90 postgres redis || (
    echo ERROR: PostgreSQL or Redis did not become healthy.
    docker compose ps
    goto :error
)

echo.
echo Starting the API at http://127.0.0.1:8000
echo Swagger UI: http://127.0.0.1:8000/docs
echo Press Ctrl+C to stop the API. Run stop.bat to stop PostgreSQL and Redis.
echo.
"%VENV_PYTHON%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
set "APP_EXIT=%ERRORLEVEL%"
popd
exit /b %APP_EXIT%

:error
popd
exit /b 1
