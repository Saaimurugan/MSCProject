@echo off
REM MSC Evaluate - Quick Deployment Script for Windows CMD
REM This script runs the PowerShell deployment script

echo ==========================================
echo MSC Evaluate Deployment
echo ==========================================
echo.
echo Starting deployment using PowerShell...
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0deploy.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Deployment failed!
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ==========================================
echo Deployment completed successfully!
echo ==========================================
pause
