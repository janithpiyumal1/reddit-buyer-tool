# 🎯 Reddit Buyer Tool

A production-ready application for finding and classifying buyer/prospect posts on Reddit. Automatically fetches posts based on keywords, filters out promotional content, and helps identify genuine buyer intent using both heuristic and optional LLM-based classification.

[![CI Tests](https://github.com/janithpiyumal1/reddit-buyer-tool/actions/workflows/ci.yml/badge.svg)](https://github.com/janithpiyumal1/reddit-buyer-tool/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Usage Guide](#usage-guide)
- [Testing](#testing)
- [Scheduling with Cron](#scheduling-with-cron)
- [API Documentation](#api-documentation)
- [Database Schema](#database-schema)
- [Security & Privacy](#security--privacy)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## 📖 Overview

The Reddit Buyer Tool is designed to help businesses and entrepreneurs find potential customers on Reddit by:

1. **Fetching** posts from Reddit based on buyer-intent keywords
2. **Classifying** posts as buyer/prospect or promotional using ML heuristics
3. **Optionally using LLM** (OpenAI GPT) for ambiguous cases
4. **Storing** posts in MySQL for analysis and tracking
5. **Providing a web UI** to review, filter, and export leads

### Use Cases

- Find clients posting "looking for developer" on r/forhire
- Identify businesses seeking services on r/entrepreneur
- Track buyer intent across multiple subreddits
- Export qualified leads for sales outreach

## 🏗️ Architecture

```
┌─────────────────┐
│   React UI      │ ← User Interface (http://localhost:3000)
│   (Vite)        │
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────┐
│  FastAPI        │ ← Backend API (http://localhost:8000)
│  Backend        │
└────────┬────────┘
         │
    ┌────┴──────┬──────────┬─────────┐
    ▼           ▼          ▼         ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ MySQL  │ │ PRAW   │ │Heuris- │ │OpenAI  │
│   DB   │ │(Reddit)│ │tic AI  │ │  LLM   │
└────────┘ └────────┘ └────────┘ └────────┘
                                  (Optional)

Scripts (Cron-schedulable):
- scripts/run_fetcher.py      ← Fetch posts periodically
- scripts/classify_pending.py ← Classify unclassified posts
```

### Key Components

- **Backend (`backend/app/`)**: FastAPI application with business logic
- **Frontend (`frontend/src/`)**: React UI with Vite build tool
- **Database**: MySQL with connection pooling
- **Classifier**: Heuristic regex-based + optional LLM
- **Fetcher**: RSS + HTML parser (TOS-friendly, no auth required)
- **Scripts**: CLI tools for automation

## ✨ Features

### Core Features

✅ **RSS-based Reddit fetching** (no API credentials needed!)  
✅ **HTML fallback** for full post content extraction  
✅ **Keyword search** across all Reddit or specific subreddits  
✅ **Heuristic classification** (regex patterns for buyer/seller signals)  
✅ **Optional LLM classification** (OpenAI GPT for low-confidence posts)  
✅ **MySQL storage** with full metadata and JSON support  
✅ **REST API** with Swagger docs (`/docs`)  
✅ **React UI** with filtering, pagination, and CSV export  
✅ **Lead management** (save/unsave posts)  
✅ **Respectful rate limiting** (configurable delays)  
✅ **Comprehensive tests** with pytest (30+ test cases)  
✅ **GitHub Actions CI** for automated testing  

### Why RSS + HTML instead of API?

🚀 **No authentication required** - Works out of the box  
📋 **TOS-compliant** - Uses public RSS feeds  
🔧 **Simpler setup** - No OAuth, tokens, or app registration  
⚡ **Fast & reliable** - Direct RSS parsing with HTML fallback  
💰 **Free** - No API quotas or rate limit concerns  

### Classification Strategy

1. **Heuristic First**: Fast, free, rule-based classification
2. **LLM Fallback**: Only for low-confidence cases (configurable)
3. **Caching**: LLM results cached in DB to avoid redundant API calls

## 🛠️ Tech Stack

### Backend
- **Python 3.11+**
- **FastAPI** - Modern async web framework
- **feedparser** - RSS feed parsing
- **BeautifulSoup4** - HTML content extraction
- **requests** - HTTP client
- **Playwright** (optional) - Browser automation for JS pages
- **MySQL** - Relational database (mysql-connector-python)
- **OpenAI** - Optional LLM integration
- **pytest** - Testing framework

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **Axios** - HTTP client

### Infrastructure
- **NO Docker** (as per requirements)
- **MySQL 8.0+** (local or remote)
- **Python venv** for isolation
- **npm** for frontend dependencies

## 📦 Prerequisites

Before installation, ensure you have:

- **Python 3.11+** ([download](https://www.python.org/downloads/))
- **Node.js 18+** and npm ([download](https://nodejs.org/))
- **MySQL 8.0+** ([download](https://dev.mysql.com/downloads/))
- **(Optional) OpenAI API key** for LLM classification ([get key](https://platform.openai.com/api-keys))
- **(Optional) Playwright** for JS-heavy page rendering (`pip install playwright && playwright install`)

**Note:** Reddit API credentials are NO LONGER REQUIRED! The new RSS + HTML fetcher works without authentication.

### Verify installations:

```bash
python --version  # Should be 3.11+
node --version    # Should be 18+
mysql --version   # Should be 8.0+
```

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/janithpiyumal1/reddit-buyer-tool.git
cd reddit-buyer-tool
```

### 2. Set Up MySQL Database

```bash
# Login to MySQL
mysql -u root -p

# Create database
CREATE DATABASE reddit_buyer_tool;
USE reddit_buyer_tool;

# Run migration
SOURCE migrations/001_init.sql;

# Verify table creation
SHOW TABLES;
DESCRIBE reddit_posts;
```

**Alternative (command line)**:
```bash
mysql -u root -p reddit_buyer_tool < migrations/001_init.sql
```

### 3. Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your credentials
# Use your favorite text editor (notepad, vim, nano, etc.)
notepad .env  # Windows
nano .env     # Linux/Mac
```

**Required credentials in `.env`**:
```bash
# Reddit API (get from https://www.reddit.com/prefs/apps)
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password

# MySQL
DB_PASSWORD=your_mysql_password

# Optional: OpenAI (only if USE_LLM=true)
USE_LLM=false
OPENAI_API_KEY=sk-...
```

### 4. Set Up Backend

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 5. Set Up Frontend

```bash
cd frontend
npm install
cd ..
```

## ⚙️ Configuration

### Reddit Fetcher (RSS + HTML)

**🎉 Good News: No API credentials required!**

The new RSS + HTML fetcher uses Reddit's public RSS feeds and HTML parsing, eliminating the need for authentication. This approach is:

✅ **TOS-friendly** - Uses publicly available RSS feeds
✅ **Simple setup** - No Reddit app creation needed  
✅ **No rate limit headaches** - Avoids complex OAuth flows  
✅ **Reliable** - Falls back to HTML when RSS content is truncated  

**How it works:**
1. **RSS First**: Queries Reddit's search RSS (`https://www.reddit.com/search.rss?q=keywords`) or subreddit RSS (`https://www.reddit.com/r/subreddit/new.rss`)
2. **HTML Fallback**: If post body is truncated in RSS, fetches full HTML and parses content
3. **Optional Browser Rendering**: For JS-heavy pages, optionally use Playwright (disabled by default)

**Configuration Options in `.env`:**

```bash
# Delay between requests (be respectful to Reddit's servers)
FETCH_DELAY_SECONDS=1.0

# Skip HTML fallback for speed (may miss full post content)
USE_RSS_ONLY=false

# Use Playwright for JS-heavy pages (requires installation)
USE_BROWSER_RENDERER=false
BROWSER_RENDER_TIMEOUT=10
```

**Sample RSS URLs:**
- Search: `https://www.reddit.com/search.rss?q=looking+for+developer&sort=new`
- Subreddit: `https://www.reddit.com/r/forhire/new.rss`
- Multiple keywords: `https://www.reddit.com/search.rss?q=hiring+OR+seeking+OR+"looking+for"`

**Optional: Enable Playwright for JS rendering:**
```bash
pip install playwright
playwright install  # Downloads browser binaries
```

Then set in `.env`:
```bash
USE_BROWSER_RENDERER=true
```

### MySQL Configuration

Default settings in `.env`:
```bash
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_NAME=reddit_buyer_tool
```

For remote MySQL, update `DB_HOST` accordingly.

### LLM Configuration (Optional)

To enable LLM classification:

1. Get OpenAI API key from https://platform.openai.com/api-keys
2. Set in `.env`:
```bash
USE_LLM=true
OPENAI_API_KEY=sk-your-key-here
LLM_MODEL=gpt-3.5-turbo  # or gpt-4
```

**Note**: LLM is only used for low-confidence posts (score < 0.4). This saves costs while improving accuracy.

## 🏃 Running the Application

### Start Backend (API Server)

```bash
# Activate venv if not already active
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Run backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at:
- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

### Start Frontend (Development Server)

In a **new terminal**:

```bash
cd frontend
npm run dev
```

Frontend will be available at:
- **UI**: http://localhost:3000

### Production Build (Frontend)

```bash
cd frontend
npm run build
# Outputs to frontend/dist/
```

Serve with any static file server (nginx, Apache, etc.)

## 📚 Usage Guide

### 1. Fetch Posts from Reddit

**Via UI**:
1. Open http://localhost:3000
2. Enter keywords (e.g., "looking for", "need help", "hiring")
3. Optionally specify subreddits (e.g., "forhire", "entrepreneur")
4. Set limit (default: 100)
5. Click "Fetch Posts"

**Via Script**:
```bash
python scripts/run_fetcher.py \
  --keywords "looking for,need help,hiring" \
  --subreddits "forhire,entrepreneur" \
  --limit 50
```

### 2. Classify Posts

**Automatic Classification**:
Posts are automatically classified when fetched. You can also run:

```bash
python scripts/classify_pending.py --limit 100
```

**Manual Re-classification** (via UI):
Click the 🔄 button on any post to re-classify.

### 3. Filter and Review Posts

Use the filter bar to:
- Show only buyer posts
- Filter by subreddit
- Show saved leads only
- Adjust page size

### 4. Save Leads

Click the ⭐ button to mark a post as a saved lead.

### 5. Export Leads

Click "Export Saved Leads" to download a CSV file with all saved leads.

## 🧪 Testing

### Run All Tests

```bash
cd backend
pytest tests/ -v
```

### Run Specific Test Files

```bash
# Classifier tests
pytest tests/test_classifier.py -v

# API tests
pytest tests/test_api.py -v
```

### Run with Coverage

```bash
pytest tests/ --cov=app --cov-report=html
# View coverage report: open htmlcov/index.html
```

### Test Results Expected

- **17+ unit tests** for classifier (labeled examples)
- **10+ API tests** for all endpoints
- **Coverage > 70%**

## ⏰ Scheduling with Cron

**Recommended: Run the fetcher periodically to discover new buyer posts**

The RSS + HTML fetcher is designed to run efficiently in scheduled jobs without API authentication concerns.

### Fetch Posts Every 6 Hours (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add this line (adjust paths):
0 */6 * * * cd /path/to/reddit-buyer-tool && /path/to/venv/bin/python scripts/run_fetcher.py --keywords "looking for,hiring,need developer" --subreddits "forhire,entrepreneur" --limit 100 >> /var/log/reddit-fetcher.log 2>&1
```

**Example cron schedules:**
```bash
# Every 4 hours
0 */4 * * * ...

# Twice daily (8 AM and 8 PM)
0 8,20 * * * ...

# Daily at midnight
0 0 * * * ...
```

### Classify Pending Posts Daily

```bash
# Run classifier on unclassified posts daily at 2 AM
0 2 * * * cd /path/to/reddit-buyer-tool && /path/to/venv/bin/python scripts/classify_pending.py --limit 200 >> /var/log/reddit-classifier.log 2>&1
```

### Windows Task Scheduler

1. Open **Task Scheduler**
2. Create **Basic Task**
3. **Trigger**: Daily at 8 AM, or every 6 hours
4. **Action**: Start a Program
   - **Program**: `C:\path\to\reddit-buyer-tool\venv\Scripts\python.exe`
   - **Arguments**: `scripts\run_fetcher.py --keywords "looking for,hiring" --subreddits "forhire" --limit 100`
   - **Start in**: `C:\path\to\reddit-buyer-tool`

**Pro tip:** Add multiple tasks with different keywords/subreddits for broader coverage:
- Task 1: `--keywords "looking for,need"` - General buyer intent
- Task 2: `--keywords "hiring,seeking developer"` - Job postings  
- Task 3: `--subreddits "startups,entrepreneur"` - Startup communities

## 📡 API Documentation

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/fetch` | Fetch posts from Reddit via RSS |
| `GET` | `/api/posts` | List posts with filters |
| `POST` | `/api/classify/{post_id}` | Re-classify a post |
| `POST` | `/api/save_lead/{post_id}` | Save/unsave as lead |
| `GET` | `/api/export` | Export leads as CSV |
| `GET` | `/api/subreddits` | List unique subreddits |
| `GET` | `/api/health` | Health check |

### Example API Calls

**Fetch Posts**:
```bash
curl -X POST http://localhost:8000/api/fetch \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["looking for", "need help"],
    "subreddits": ["forhire"],
    "limit": 10
  }'
```

**Get Posts**:
```bash
curl "http://localhost:8000/api/posts?is_buyer=true&page=1&page_size=50"
```

**Classify Post**:
```bash
curl -X POST http://localhost:8000/api/classify/123 \
  -H "Content-Type: application/json" \
  -d '{"force_llm": false}'
```

Full API documentation: http://localhost:8000/docs

## 🗄️ Database Schema

**Table: `reddit_posts`**

| Column | Type | Description |
|--------|------|-------------|
| `id` | BIGINT | Primary key |
| `reddit_id` | VARCHAR(50) | Unique Reddit post ID |
| `subreddit` | VARCHAR(100) | Subreddit name |
| `title` | TEXT | Post title |
| `body` | TEXT | Post body/selftext |
| `author` | VARCHAR(100) | Reddit username |
| `created_utc` | DATETIME | Post creation time |
| `url` | TEXT | Reddit permalink |
| `fetched_at` | DATETIME | When post was fetched |
| `is_buyer` | TINYINT(1) | Classification result |
| `classification_source` | VARCHAR(30) | 'heuristic' or 'llm' |
| `classification_score` | FLOAT | Confidence score |
| `metadata` | JSON | Additional data |
| `saved_as_lead` | TINYINT(1) | Saved lead flag |

**Indexes**:
- `reddit_id` (UNIQUE)
- `subreddit`
- `is_buyer`
- `saved_as_lead`
- `created_utc`

## 🔒 Security & Privacy

### Best Practices

✅ **Never commit `.env` file** (already in `.gitignore`)  
✅ **Use strong MySQL passwords**  
✅ **Respect Reddit's servers** (1-second minimum delay between requests)  
✅ **Use descriptive User-Agent** (helps Reddit identify your bot)  
✅ **Comply with Reddit ToS** - RSS feeds are public, but don't hammer servers  
✅ **Respect user privacy** - do not share personal data from posts  
✅ **Use HTTPS in production** (reverse proxy with nginx/Caddy)  
✅ **Optional: Enable `USE_RSS_ONLY`** to skip HTML fetching (lighter on Reddit)  

### Fetcher Rate Limiting

The RSS + HTML fetcher implements respectful throttling:

```python
# In .env
FETCH_DELAY_SECONDS=1.0  # Minimum 1 second between requests

# RSS feeds: ~1 request per search
# HTML fallback: 1 request per truncated post
# Total: ~2-10 requests for 100 posts (depending on truncation rate)
```

**Comparison:**
- **Old PRAW API**: 60 requests/minute limit, OAuth required  
- **New RSS + HTML**: No formal limit, but be respectful (~1 req/sec recommended)

### Disclaimer

This tool is for **legitimate business prospecting only**. Users must:
- Comply with Reddit's [Terms of Service](https://www.redditinc.com/policies/user-agreement)
- Use publicly available RSS feeds responsibly
- Respect user privacy and GDPR/CCPA regulations
- Not use for spam, harassment, or malicious purposes
- Set appropriate `FETCH_DELAY_SECONDS` to avoid server strain

**The authors are not responsible for misuse of this tool.**

## 🐛 Troubleshooting

### Backend won't start

**Error**: `ModuleNotFoundError: No module named 'fastapi'`
```bash
# Ensure venv is activated and dependencies installed
pip install -r backend/requirements.txt
```

**Error**: `Access denied for user 'root'@'localhost'`
```bash
# Check MySQL credentials in .env
# Verify MySQL is running: mysql -u root -p
```

**Error**: `Table 'reddit_posts' doesn't exist`
```bash
# Run migration
mysql -u root -p reddit_buyer_tool < migrations/001_init.sql
```

### Frontend won't start

**Error**: `npm ERR! Missing script: "dev"`
```bash
# Ensure you're in frontend/ directory
cd frontend
npm install
npm run dev
```

### Reddit API errors

**Error**: `401 Unauthorized`
- Check Reddit credentials in `.env`
- Verify app type is "script" not "web app"

**Error**: `429 Too Many Requests`
- Reddit rate limit exceeded
- Increase `FETCH_DELAY_SECONDS` in `.env`

### LLM not working

**Error**: `openai.AuthenticationError`
- Verify `OPENAI_API_KEY` in `.env`
- Check API key has credits

**LLM not being used**:
- Ensure `USE_LLM=true` in `.env`
- LLM only triggers for low-confidence posts (< 0.4 score)

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Commit Message Format

Use conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation update
- `test:` - Test updates
- `refactor:` - Code refactoring

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📞 Support

For issues and questions:
- **GitHub Issues**: [Create an issue](https://github.com/janithpiyumal1/reddit-buyer-tool/issues)
- **Documentation**: See `/docs` endpoint when backend is running

---

**Built with ❤️ for ethical business prospecting**

Last updated: 2025-11-25
