#!/bin/bash
# Reddit Buyer Tool - Linux/Mac Setup Script
# Run this script to set up the project on Linux or macOS

set -e  # Exit on error

echo "========================================"
echo "Reddit Buyer Tool - Setup Script"
echo "========================================"
echo ""

# Check Python
echo "[1/5] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found! Please install Python 3.11+ from https://www.python.org/downloads/"
    exit 1
fi
python3 --version
echo ""

# Check Node
echo "[2/5] Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js not found! Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi
node --version
echo ""

# Check MySQL
echo "[3/5] Checking MySQL installation..."
if ! command -v mysql &> /dev/null; then
    echo "WARNING: MySQL not found in PATH. Make sure MySQL is installed and running."
    echo "You can download it from https://dev.mysql.com/downloads/"
    echo ""
fi

# Setup Backend
echo "[4/5] Setting up backend..."
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing backend dependencies..."
pip install -r backend/requirements.txt

echo ""

# Setup Frontend
echo "[5/5] Setting up frontend..."
cd frontend
echo "Installing frontend dependencies..."
npm install
cd ..

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Create .env file from .env.example"
echo "2. Fill in your Reddit API credentials"
echo "3. Set your MySQL password in .env"
echo "4. Run MySQL migration: mysql -u root -p reddit_buyer_tool < migrations/001_init.sql"
echo "5. Start backend: cd backend && uvicorn app.main:app --reload"
echo "6. Start frontend: cd frontend && npm run dev"
echo ""
echo "See README.md for detailed instructions."
echo ""
