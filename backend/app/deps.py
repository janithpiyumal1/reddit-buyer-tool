"""
Dependencies module for the Reddit Buyer Tool backend.
Handles environment configuration and database connection management.
"""

import os
from typing import Generator
from functools import lru_cache
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import pooling
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Reddit API credentials
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT: str = "reddit-buyer-tool/1.0"
    REDDIT_USERNAME: str = ""
    REDDIT_PASSWORD: str = ""
    
    # MySQL Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "reddit_buyer_tool"
    DB_POOL_SIZE: int = 5
    
    # LLM Integration (Optional)
    USE_LLM: bool = False
    OPENAI_API_KEY: str = ""
    LLM_MODEL: str = "gpt-3.5-turbo"
    LLM_MAX_TOKENS: int = 500
    
    # Application settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    # Fetcher settings
    FETCH_DELAY_SECONDS: float = 1.0  # Delay between network requests (RSS/HTML)
    DEFAULT_FETCH_LIMIT: int = 100
    MAX_FETCH_LIMIT: int = 1000
    
    # RSS + HTML Fetcher settings (TOS-friendly)
    USE_RSS_ONLY: bool = False  # If true, skip HTML fallback (faster but may miss full post text)
    USE_BROWSER_RENDERER: bool = False  # If true, use Playwright for JS-heavy pages (requires playwright install)
    BROWSER_RENDER_TIMEOUT: int = 10  # Timeout in seconds for browser rendering
    RSS_USER_AGENT: str = "reddit-buyer-tool/2.0 (RSS Reader; +https://github.com/janithpiyumal1/reddit-buyer-tool)"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Database connection pool
_connection_pool = None


def get_db_pool() -> pooling.MySQLConnectionPool:
    """
    Get or create database connection pool.
    Connection pooling improves performance for concurrent requests.
    """
    global _connection_pool
    
    if _connection_pool is None:
        settings = get_settings()
        
        db_config = {
            "host": settings.DB_HOST,
            "port": settings.DB_PORT,
            "user": settings.DB_USER,
            "password": settings.DB_PASSWORD,
            "database": settings.DB_NAME,
            "pool_name": "reddit_pool",
            "pool_size": settings.DB_POOL_SIZE,
            "pool_reset_session": True,
        }
        
        _connection_pool = pooling.MySQLConnectionPool(**db_config)
    
    return _connection_pool


def get_db_connection() -> Generator:
    """
    Dependency for FastAPI routes to get a database connection.
    Automatically handles connection cleanup via context manager.
    
    Usage in FastAPI route:
        @app.get("/endpoint")
        def my_route(db = Depends(get_db_connection)):
            cursor = db.cursor(dictionary=True)
            ...
    """
    pool = get_db_pool()
    connection = pool.get_connection()
    
    try:
        yield connection
    finally:
        connection.close()


def init_database():
    """
    Initialize database by running migrations if needed.
    This should be called on application startup.
    """
    settings = get_settings()
    
    # Connect without selecting database initially
    connection = mysql.connector.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD
    )
    
    cursor = connection.cursor()
    
    # Create database if it doesn't exist
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {settings.DB_NAME}")
    cursor.close()
    connection.close()
    
    # Now connect to the database and check if migrations are needed
    connection = mysql.connector.connect(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME
    )
    
    cursor = connection.cursor()
    
    # Check if reddit_posts table exists
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_schema = %s 
        AND table_name = 'reddit_posts'
    """, (settings.DB_NAME,))
    
    table_exists = cursor.fetchone()[0] > 0
    
    if not table_exists:
        print("⚠️  reddit_posts table does not exist.")
        print("📄 Please run the migration: migrations/001_init.sql")
        print(f"   mysql -u {settings.DB_USER} -p {settings.DB_NAME} < migrations/001_init.sql")
    
    cursor.close()
    connection.close()
