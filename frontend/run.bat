@echo off
REM Answer Sheet Evaluation System - Flask Frontend Startup Script

echo ============================================
echo Answer Sheet Evaluation System - Frontend
echo ============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org
    pause
    exit /b 1
)

echo [✓] Python found
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo [✓] Virtual environment created
) else (
    echo [✓] Virtual environment exists
)

echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

echo [✓] Virtual environment activated
echo.

REM Install/Update dependencies
echo Installing dependencies...
pip install -r requirements.txt
echo [✓] Dependencies installed
echo.

REM Check for .env file
if not exist ".env" (
    echo WARNING: .env file not found
    echo Please create .env with MongoDB and API configurations
    echo.
    echo Sample .env content:
    echo MONGODB_URL=mongodb://localhost:27017
    echo OPENAI_API_KEY=your_key_here
    echo GOOGLE_API_KEY=your_key_here
    echo.
)

echo.
echo ============================================
echo Starting Flask Application...
echo ============================================
echo Application will be available at:
echo http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

REM Run Flask app
python app.py

pause
