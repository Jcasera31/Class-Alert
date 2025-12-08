@echo off
echo ======================================
echo   ClassAlert - Starting Application
echo ======================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created.
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies if needed
if not exist "venv\Lib\site-packages\flask" (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo.
)

REM Initialize database if it doesn't exist
if not exist "classalert.db" (
    echo Initializing database...
    python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
    echo Database initialized.
    echo.
)

REM Create necessary directories
if not exist "uploads" mkdir uploads
if not exist "instance" mkdir instance

REM Clear any PostgreSQL DATABASE_URL that might be set
set DATABASE_URL=

echo ======================================
echo   Application Starting...
echo   Access at: http://localhost:5000
echo   Press Ctrl+C to stop
echo ======================================
echo.

REM Run the application
python run.py

pause
