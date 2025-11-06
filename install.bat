@echo off
REM MCP-FreeCAD Installation Wrapper for Windows
REM Convenience script to run the Python installer

setlocal enabledelayedexpansion

REM Define colors using delayed expansion
for /F %%A in ('echo prompt $H ^| cmd') do set "BS=%%A"

cls

echo.
echo ╔════════════════════════════════════════╗
echo ║  MCP-FreeCAD Installation Wrapper      ║
echo ║  Version: 1.0.0                        ║
echo ╚════════════════════════════════════════╝
echo.

REM Check if Python 3 is available
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Python 3 is not installed or not in PATH
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [INFO] Using Python %PYTHON_VERSION%

REM Check Python version (3.8 or newer)
python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Python 3.8 or newer is required
    pause
    exit /b 1
)

echo [SUCCESS] Python version check passed

REM Display usage if requested
if "%1"=="-h" goto :help
if "%1"=="--help" goto :help

REM Get script directory
for %%F in ("%0") do set SCRIPT_DIR=%%~dpF

REM Check if install.py exists
if not exist "%SCRIPT_DIR%install.py" (
    echo [ERROR] install.py not found in %SCRIPT_DIR%
    pause
    exit /b 1
)

echo [SUCCESS] Found install.py at %SCRIPT_DIR%install.py

echo.
echo [INFO] Starting MCP-FreeCAD installation...
echo.

REM Run the Python installer
python "%SCRIPT_DIR%install.py" %*

if !errorlevel! equ 0 (
    echo.
    echo [SUCCESS] Installation completed successfully! 
    echo.
    echo Next steps:
    echo   1. Restart FreeCAD to load the addon
    echo   2. Restart VS Code to activate the MCP server
    echo   3. Start using FreeCAD with AI assistance!
    echo.
    pause
    exit /b 0
) else (
    echo.
    echo [ERROR] Installation failed with exit code !errorlevel!
    echo [ERROR] Please review the error messages above
    echo.
    pause
    exit /b !errorlevel!
)

goto :end

:help
echo.
echo Usage: install.bat [OPTIONS]
echo.
echo Options:
echo   (no args)        Run full installation with tests
echo   --addon-only     Install FreeCAD addon only
echo   --server-only    Install MCP server dependencies only
echo   --vscode-only    Configure VS Code only
echo   --no-test        Skip tests
echo   --verbose        Enable verbose output
echo   -h, --help       Show this help message
echo.
pause
exit /b 0

:end
