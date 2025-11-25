@echo off
REM Reddit Buyer Tool - Windows Setup Script
REM Run this script to set up the project on Windows

echo ========================================
echo Reddit Buyer Tool - Setup Script
echo ========================================
echo.

REM Check Python
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found! Please install Python 3.11+ from https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.

REM Check Node
echo [2/5] Checking Node.js installation...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js not found! Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)
node --version
echo.

REM Check MySQL
echo [3/5] Checking MySQL installation...
mysql --version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: MySQL not found in PATH. Make sure MySQL is installed and running.
    echo You can download it from https://dev.mysql.com/downloads/
    echo.
)

REM Setup Backend
echo [4/5] Setting up backend...
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing backend dependencies...
pip install -r backend\requirements.txt

echo.

REM Setup Frontend
echo [5/5] Setting up frontend...
cd frontend
echo Installing frontend dependencies...
call npm install
cd ..

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Create .env file from .env.example
echo 2. Fill in your Reddit API credentials
echo 3. Set your MySQL password in .env
echo 4. Run MySQL migration: mysql -u root -p reddit_buyer_tool ^< migrations\001_init.sql
echo 5. Start backend: cd backend ^&^& uvicorn app.main:app --reload
echo 6. Start frontend: cd frontend ^&^& npm run dev
echo.
echo See README.md for detailed instructions.
echo.

pause
