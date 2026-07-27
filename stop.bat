@echo off
setlocal EnableExtensions

pushd "%~dp0" >nul || (
    echo ERROR: Cannot open the project directory.
    exit /b 1
)

where docker >nul 2>&1 || (
    echo ERROR: Docker was not found.
    goto :error
)

docker info >nul 2>&1 || (
    echo ERROR: Docker Desktop is not running or its Linux engine is unavailable.
    goto :error
)

echo Stopping this project's PostgreSQL and Redis containers...
docker compose stop postgres redis || goto :error

echo Project services stopped. Container data was kept.
popd
exit /b 0

:error
popd
exit /b 1
