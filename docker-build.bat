@echo off
REM Docker Build and Run Script for Retinopathy Backend (Windows)
REM Usage: docker-build.bat [dev|prod] [build|run|stop|logs]

setlocal enabledelayedexpansion

REM Default values
set ENVIRONMENT=%1
set ACTION=%2
set IMAGE_NAME=retinopathy-backend
set CONTAINER_NAME=retinopathy-api

if "%ENVIRONMENT%"=="" set ENVIRONMENT=dev
if "%ACTION%"=="" set ACTION=build

echo [INFO] Retinopathy Backend Docker Script
echo [INFO] Environment: %ENVIRONMENT%
echo [INFO] Action: %ACTION%

REM Check if .env file exists
if not exist .env (
    echo [WARNING] .env file not found. Creating from template...
    (
        echo MONGODB_URI=mongodb://localhost:27017/retinopathy
        echo JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
        echo FLASK_ENV=%ENVIRONMENT%
    ) > .env
    echo [WARNING] Please edit .env file with your actual values
)

if "%ACTION%"=="build" goto build
if "%ACTION%"=="run" goto run
if "%ACTION%"=="stop" goto stop
if "%ACTION%"=="logs" goto logs
if "%ACTION%"=="restart" goto restart

echo [ERROR] Unknown action: %ACTION%
echo Usage: %0 [dev^|prod] [build^|run^|stop^|logs^|restart]
exit /b 1

:build
echo [INFO] Building Docker image for %ENVIRONMENT% environment...
if "%ENVIRONMENT%"=="prod" (
    docker build -f Dockerfile.prod -t %IMAGE_NAME%:%ENVIRONMENT% .
) else (
    docker build -t %IMAGE_NAME%:%ENVIRONMENT% .
)
echo [SUCCESS] Docker image built successfully: %IMAGE_NAME%:%ENVIRONMENT%
goto end

:run
call :build
echo [INFO] Running Docker container for %ENVIRONMENT% environment...

REM Stop existing container if running
for /f %%i in ('docker ps -q -f name=%CONTAINER_NAME%-%ENVIRONMENT% 2^>nul') do (
    echo [WARNING] Stopping existing container...
    docker stop %CONTAINER_NAME%-%ENVIRONMENT%
    docker rm %CONTAINER_NAME%-%ENVIRONMENT%
)

REM Run new container
if "%ENVIRONMENT%"=="prod" (
    docker run -d --name %CONTAINER_NAME%-%ENVIRONMENT% -p 5000:5000 --env-file .env --restart unless-stopped %IMAGE_NAME%:%ENVIRONMENT%
) else (
    docker run -d --name %CONTAINER_NAME%-%ENVIRONMENT% -p 5000:5000 -v %cd%:/app --env-file .env %IMAGE_NAME%:%ENVIRONMENT%
)

echo [SUCCESS] Container started: %CONTAINER_NAME%-%ENVIRONMENT%
echo [INFO] API available at: http://localhost:5000
goto end

:stop
echo [INFO] Stopping Docker container...
for /f %%i in ('docker ps -q -f name=%CONTAINER_NAME%-%ENVIRONMENT% 2^>nul') do (
    docker stop %CONTAINER_NAME%-%ENVIRONMENT%
    docker rm %CONTAINER_NAME%-%ENVIRONMENT%
    echo [SUCCESS] Container stopped and removed
    goto end
)
echo [WARNING] No running container found
goto end

:logs
echo [INFO] Showing logs for %CONTAINER_NAME%-%ENVIRONMENT%...
docker logs -f %CONTAINER_NAME%-%ENVIRONMENT%
goto end

:restart
call :stop
call :run
goto end

:end
endlocal