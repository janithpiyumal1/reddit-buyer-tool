"""
Reddit fetcher module using RSS + HTML parsing (TOS-friendly, no auth required).
Implements RSS-first approach with HTML fallback for full post content.

Why RSS + HTML instead of PRAW/API?
- No authentication or API keys required
- Simpler setup for users
- Respects Reddit's public RSS feeds (TOS-friendly)
- Avoids rate limit complexity of authenticated API
- Good for research and buyer intent analysis use cases
"""

import time
import re
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from urllib.parse import quote_plus
from html import unescape

import feedparser
import requests
from bs4 import BeautifulSoup

from app.deps import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_reddit_id_from_url(url: str) -> Optional[str]:
    """
    Extract Reddit post ID from various URL formats.
    
    Examples:
        https://www.reddit.com/r/webdev/comments/abc123/title/ -> abc123
        https://reddit.com/comments/abc123/ -> abc123
    """
    if not url:
        return None
    
    # Pattern: /comments/{id}/ or /comments/{id}?
    match = re.search(r'/comments/([a-z0-9]+)', url, re.IGNORECASE)
    if match:
        return match.group(1)
    
    return None


def parse_rss_published_date(date_str: str) -> datetime:
    """
    Parse RSS published date to datetime object.
    Handles various RSS date formats.
    """
    if not date_str:
        return datetime.now(timezone.utc)
    
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(date_str)
    except Exception as e:
        logger.warning(f"Failed to parse date '{date_str}': {e}")
        return datetime.now(timezone.utc)


def clean_html_content(html_text: str) -> str:
    """
    Clean HTML content to plain text.
    Removes tags, entities, extra whitespace.
    """
    if not html_text:
        return ""
    
    # Parse HTML and extract text
    soup = BeautifulSoup(html_text, 'html.parser')
    
    # Remove script and style elements
    for element in soup(['script', 'style']):
        element.decompose()
    
    # Get text
    text = soup.get_text(separator=' ')
    
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Unescape HTML entities
    text = unescape(text)
    
    return text


def parse_search_rss(keywords: List[str], limit: int = 100) -> List[Dict[str, Any]]:
    """
    Parse Reddit search RSS feed for given keywords.
    
    Args:
        keywords: List of search keywords (joined with OR)
        limit: Maximum number of entries to return
    
    Returns:
        List of dicts with parsed RSS entries
    """
    settings = get_settings()
    
    # Construct search query
    query = " OR ".join(keywords)
    encoded_query = quote_plus(query)
    
    # Reddit search RSS URL
    rss_url = f"https://www.reddit.com/search.rss?q={encoded_query}&sort=new"
    
    logger.info(f"Fetching RSS feed: {rss_url}")
    
    try:
        # Set custom user agent
        headers = {
            'User-Agent': settings.RSS_USER_AGENT
        }
        
        # Fetch RSS feed
        response = requests.get(rss_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parse with feedparser
        feed = feedparser.parse(response.content)
        
        entries = []
        
        for entry in feed.entries[:limit]:
            # Extract data from RSS entry
            reddit_id = extract_reddit_id_from_url(entry.get('link', ''))
            
            if not reddit_id:
                logger.warning(f"Could not extract reddit_id from: {entry.get('link')}")
                continue
            
            # Parse published date
            published = entry.get('published', entry.get('updated', ''))
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                created_utc = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            else:
                created_utc = parse_rss_published_date(published)
            
            # Extract author (format: /u/username)
            author = entry.get('author', '').replace('/u/', '').strip() or '[unknown]'
            
            # Get summary (may be truncated HTML)
            summary_html = entry.get('summary', '')
            summary_text = clean_html_content(summary_html)
            
            # Extract subreddit from category or link
            subreddit = None
            if hasattr(entry, 'tags') and entry.tags:
                # Try to find subreddit in tags
                for tag in entry.tags:
                    if tag.get('term', '').startswith('r/'):
                        subreddit = tag['term'].replace('r/', '')
                        break
            
            if not subreddit:
                # Try to extract from link
                match = re.search(r'/r/([^/]+)/', entry.get('link', ''))
                if match:
                    subreddit = match.group(1)
            
            parsed_entry = {
                'reddit_id': reddit_id,
                'title': entry.get('title', ''),
                'body': summary_text,
                'author': author,
                'url': entry.get('link', ''),
                'created_utc': created_utc,
                'subreddit': subreddit or '[unknown]',
                'raw_rss_entry': {
                    'title': entry.get('title'),
                    'link': entry.get('link'),
                    'published': published,
                    'author': entry.get('author'),
                },
                'is_truncated': len(summary_text) < 100 or '...' in summary_text or '[link]' in summary_text.lower(),
            }
            
            entries.append(parsed_entry)
        
        logger.info(f"Parsed {len(entries)} entries from RSS feed")
        return entries
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch RSS feed: {e}")
        return []
    except Exception as e:
        logger.error(f"Error parsing RSS feed: {e}")
        return []


def parse_subreddit_rss(subreddit: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Parse RSS feed for a specific subreddit's new posts.
    
    Args:
        subreddit: Subreddit name (without r/)
        limit: Maximum number of entries to return
    
    Returns:
        List of dicts with parsed RSS entries
    """
    settings = get_settings()
    
    # Subreddit RSS URL
    rss_url = f"https://www.reddit.com/r/{subreddit}/new.rss"
    
    logger.info(f"Fetching subreddit RSS: {rss_url}")
    
    try:
        headers = {
            'User-Agent': settings.RSS_USER_AGENT
        }
        
        response = requests.get(rss_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        feed = feedparser.parse(response.content)
        
        entries = []
        
        for entry in feed.entries[:limit]:
            reddit_id = extract_reddit_id_from_url(entry.get('link', ''))
            
            if not reddit_id:
                continue
            
            # Parse date
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                created_utc = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            else:
                created_utc = parse_rss_published_date(entry.get('published', ''))
            
            author = entry.get('author', '').replace('/u/', '').strip() or '[unknown]'
            summary_html = entry.get('summary', '')
            summary_text = clean_html_content(summary_html)
            
            parsed_entry = {
                'reddit_id': reddit_id,
                'title': entry.get('title', ''),
                'body': summary_text,
                'author': author,
                'url': entry.get('link', ''),
                'created_utc': created_utc,
                'subreddit': subreddit,
                'raw_rss_entry': {
                    'title': entry.get('title'),
                    'link': entry.get('link'),
                    'published': entry.get('published'),
                },
                'is_truncated': len(summary_text) < 100 or '...' in summary_text,
            }
            
            entries.append(parsed_entry)
        
        logger.info(f"Parsed {len(entries)} entries from r/{subreddit}")
        return entries
        
    except Exception as e:
        logger.error(f"Error fetching r/{subreddit} RSS: {e}")
        return []


def fetch_post_html_content(post_url: str, use_playwright: bool = False) -> Optional[str]:
    """
    Fetch full post content from Reddit HTML page.
    Used as fallback when RSS summary is truncated.
    
    Args:
        post_url: Full URL to Reddit post
        use_playwright: If True, use Playwright for JS rendering (slower but handles dynamic content)
    
    Returns:
        Extracted post body text, or None if failed
    """
    settings = get_settings()
    
    if use_playwright and settings.USE_BROWSER_RENDERER:
        return _fetch_with_playwright(post_url)
    else:
        return _fetch_with_requests(post_url)


def _fetch_with_requests(post_url: str) -> Optional[str]:
    """Fetch post HTML using requests + BeautifulSoup."""
    settings = get_settings()
    
    try:
        headers = {
            'User-Agent': settings.RSS_USER_AGENT
        }
        
        logger.info(f"Fetching HTML for: {post_url}")
        response = requests.get(post_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try multiple selectors to find post content
        # Reddit's HTML structure varies
        selectors = [
            'div[data-test-id="post-content"]',
            'div.Post div[data-click-id="text"]',
            'div.usertext-body',
            'div[data-testid="post-content"]',
            'div.md',  # Markdown content
        ]
        
        for selector in selectors:
            content_div = soup.select_one(selector)
            if content_div:
                text = clean_html_content(str(content_div))
                if text and len(text) > 20:  # Sanity check
                    logger.info(f"Extracted {len(text)} chars using selector: {selector}")
                    return text
        
        # Fallback: try to find any post-like content
        # Look for large text blocks
        for div in soup.find_all('div'):
            text = clean_html_content(str(div))
            if len(text) > 200 and 'post' in div.get('class', []):
                return text
        
        logger.warning(f"Could not extract post content from HTML: {post_url}")
        return None
        
    except Exception as e:
        logger.error(f"Error fetching HTML content: {e}")
        return None


def _fetch_with_playwright(post_url: str) -> Optional[str]:
    """Fetch post HTML using Playwright for JS-rendered content."""
    settings = get_settings()
    
    try:
        from playwright.sync_api import sync_playwright
        
        logger.info(f"Fetching with Playwright: {post_url}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_extra_http_headers({
                'User-Agent': settings.RSS_USER_AGENT
            })
            
            page.goto(post_url, timeout=settings.BROWSER_RENDER_TIMEOUT * 1000)
            page.wait_for_load_state('networkidle', timeout=settings.BROWSER_RENDER_TIMEOUT * 1000)
            
            # Get page content
            html_content = page.content()
            browser.close()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Same selectors as requests version
            selectors = [
                'div[data-test-id="post-content"]',
                'div[data-testid="post-content"]',
                'div.usertext-body',
                'div.md',
            ]
            
            for selector in selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    text = clean_html_content(str(content_div))
                    if text and len(text) > 20:
                        return text
            
            return None
            
    except ImportError:
        logger.error("Playwright not installed. Install with: pip install playwright && playwright install")
        return None
    except Exception as e:
        logger.error(f"Error with Playwright: {e}")
        return None


def enrich_posts_with_html(posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enrich truncated posts by fetching full HTML content.
    
    Args:
        posts: List of posts from RSS parsing
    
    Returns:
        Posts with full content where available
    """
    settings = get_settings()
    
    # Skip HTML fallback if disabled
    if settings.USE_RSS_ONLY:
        logger.info("USE_RSS_ONLY=True, skipping HTML fallback")
        return posts
    
    enriched_posts = []
    
    for post in posts:
        # Only fetch HTML for truncated posts
        if post.get('is_truncated', False) and post.get('url'):
            logger.info(f"Fetching full content for truncated post: {post['reddit_id']}")
            
            html_content = fetch_post_html_content(
                post['url'],
                use_playwright=settings.USE_BROWSER_RENDERER
            )
            
            if html_content:
                post['body'] = html_content
                post['fetched_html'] = True
                post['is_truncated'] = False
            else:
                post['fetched_html'] = False
                post['html_fetch_warning'] = "Failed to fetch HTML content"
            
            # Rate limiting between HTML requests
            time.sleep(settings.FETCH_DELAY_SECONDS)
        else:
            post['fetched_html'] = False
        
        enriched_posts.append(post)
    
    return enriched_posts


def search_reddit(
    keywords: List[str],
    subreddits: Optional[List[str]] = None,
    limit: int = 100,
    time_filter: str = "week"
) -> List[Dict[str, Any]]:
    """
    Search Reddit using RSS feeds.
    
    Args:
        keywords: List of search keywords
        subreddits: Optional list of specific subreddits (if None, searches all)
        limit: Maximum number of posts
        time_filter: Ignored for RSS (RSS is always recent)
    
    Returns:
        List of dicts with post data ready for database insertion
    """
    settings = get_settings()
    
    all_posts = []
    
    if subreddits and len(subreddits) > 0:
        # Fetch from specific subreddits
        for subreddit in subreddits:
            posts = parse_subreddit_rss(subreddit, limit=limit // len(subreddits))
            all_posts.extend(posts)
            time.sleep(settings.FETCH_DELAY_SECONDS)
    else:
        # Search all of Reddit
        all_posts = parse_search_rss(keywords, limit=limit)
    
    # Enrich with HTML content if needed
    all_posts = enrich_posts_with_html(all_posts)
    
    # Prepare metadata
    for post in all_posts:
        metadata = {
            'raw_rss': post.get('raw_rss_entry', {}),
            'fetched_html': post.get('fetched_html', False),
            'was_truncated': post.get('is_truncated', False),
        }
        
        if post.get('html_fetch_warning'):
            metadata['warnings'] = [post['html_fetch_warning']]
        
        post['metadata'] = metadata
    
    return all_posts


def fetch_from_subreddits_new(
    subreddits: List[str],
    limit_per_subreddit: int = 50
) -> List[Dict[str, Any]]:
    """
    Fetch new posts from specific subreddits using RSS.
    
    Args:
        subreddits: List of subreddit names
        limit_per_subreddit: Max posts per subreddit
    
    Returns:
        List of dicts with post data
    """
    settings = get_settings()
    all_posts = []
    
    for subreddit in subreddits:
        posts = parse_subreddit_rss(subreddit, limit=limit_per_subreddit)
        all_posts.extend(posts)
        
        # Rate limiting between subreddits
        time.sleep(settings.FETCH_DELAY_SECONDS)
    
    # Enrich with HTML
    all_posts = enrich_posts_with_html(all_posts)
    
    # Add metadata
    for post in all_posts:
        post['metadata'] = {
            'raw_rss': post.get('raw_rss_entry', {}),
            'fetched_html': post.get('fetched_html', False),
            'was_truncated': post.get('is_truncated', False),
        }
    
    return all_posts


def fetch_and_store(
    db_connection,
    keywords: List[str],
    subreddits: Optional[List[str]] = None,
    limit: int = 100
) -> Dict[str, int]:
    """
    Fetch posts from Reddit RSS and store in database.
    
    Args:
        db_connection: MySQL database connection
        keywords: List of keywords to search
        subreddits: Optional list of subreddits
        limit: Maximum posts to fetch
    
    Returns:
        Dict with statistics: {fetched, stored, duplicates}
    """
    from app.db import insert_reddit_post
    
    # Fetch posts via RSS
    posts_data = search_reddit(keywords, subreddits, limit)
    
    stats = {
        "fetched": len(posts_data),
        "stored": 0,
        "duplicates": 0,
    }
    
    # Store each post
    for post_data in posts_data:
        post_id = insert_reddit_post(
            db=db_connection,
            reddit_id=post_data["reddit_id"],
            subreddit=post_data["subreddit"],
            title=post_data["title"],
            body=post_data.get("body", ""),
            author=post_data["author"],
            created_utc=post_data["created_utc"],
            url=post_data["url"],
            metadata=post_data.get("metadata", {})
        )
        
        if post_id > 0:
            stats["stored"] += 1
        else:
            stats["duplicates"] += 1
    
    logger.info(f"Fetch stats: {stats}")
    return stats


# ============================================================================
# EXAMPLE USAGE (for testing/development)
# ============================================================================

if __name__ == "__main__":
    """
    Example standalone usage of the fetcher.
    Run with: python -m app.reddit_fetcher
    """
    # Example: Search for buyer intent keywords
    test_keywords = ["looking for", "need help", "where can I find"]
    test_subreddits = ["forhire", "entrepreneur"]
    
    print(f"Searching Reddit for: {test_keywords}")
    print(f"In subreddits: {test_subreddits or 'all'}")
    
    results = search_reddit(
        keywords=test_keywords,
        subreddits=test_subreddits,
        limit=5
    )
    
    print(f"\nFound {len(results)} posts:")
    for post in results:
        print(f"\n- r/{post['subreddit']}: {post['title'][:60]}...")
        print(f"  by u/{post['author']} on {post['created_utc']}")
