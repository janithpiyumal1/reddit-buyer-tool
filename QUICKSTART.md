# Quick Start Guide

This guide will help you get the Reddit Buyer Tool running locally in under 10 minutes.

## Prerequisites Checklist

- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed
- [ ] MySQL 8.0+ installed and running
- [ ] Reddit account and API credentials
- [ ] (Optional) OpenAI API key

## Step-by-Step Setup

### 1. Database Setup (2 minutes)

```bash
# Login to MySQL
mysql -u root -p

# Run these commands in MySQL shell:
CREATE DATABASE reddit_buyer_tool;
USE reddit_buyer_tool;
SOURCE migrations/001_init.sql;
EXIT;
```

### 2. Environment Configuration (2 minutes)

```bash
# Copy example file
cp .env.example .env

# Edit .env and set these required values:
# - REDDIT_CLIENT_ID
# - REDDIT_CLIENT_SECRET
# - REDDIT_USERNAME
# - REDDIT_PASSWORD
# - DB_PASSWORD
```

**Get Reddit credentials**:
1. Visit https://www.reddit.com/prefs/apps
2. Click "Create App" → Select "script"
3. Copy client_id and secret

### 3. Backend Setup (2 minutes)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 4. Frontend Setup (2 minutes)

```bash
cd frontend
npm install
cd ..
```

### 5. Run the Application (1 minute)

**Terminal 1 - Backend**:
```bash
cd backend
uvicorn app.main:app --reload
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm run dev
```

### 6. Verify Installation

1. Open http://localhost:3000 (frontend UI)
2. Open http://localhost:8000/docs (API docs)
3. Try fetching some posts!

## Test the Setup

```bash
# Run tests to verify everything works
cd backend
pytest tests/ -v
```

## First Fetch Example

In the UI (http://localhost:3000):

1. **Keywords**: `looking for, need help, hiring`
2. **Subreddits**: `forhire, entrepreneur`
3. **Limit**: `10`
4. Click **Fetch Posts**

You should see posts appear in the table below!

## Common Issues

**"Access denied for user"**: Check `DB_PASSWORD` in `.env`

**"PRAW 401 Unauthorized"**: Check Reddit credentials in `.env`

**"Module not found"**: Activate venv and run `pip install -r backend/requirements.txt`

**"Port already in use"**: Change `API_PORT` in `.env` or kill existing process

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the API at http://localhost:8000/docs
- Set up cron jobs for automated fetching (see README)
- Enable LLM classification (see README)

## Getting Help

- Check [README.md](README.md) Troubleshooting section
- Open an issue on GitHub
- Review logs in terminal output

Happy prospecting! 🎯
