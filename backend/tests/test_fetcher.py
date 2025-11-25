"""
Tests for the RSS + HTML fetcher module.
Tests RSS parsing, HTML fallback, edge cases, and error handling.
"""

import pytest
import os
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

import feedparser
from bs4 import BeautifulSoup

from app.reddit_fetcher import (
    extract_reddit_id_from_url,
    parse_rss_published_date,
    clean_html_content,
    parse_search_rss,
    parse_subreddit_rss,
    fetch_post_html_content,
    enrich_posts_with_html,
    search_reddit,
    _fetch_with_requests,
)


# Fixtures directory path
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_rss_xml():
    """Load sample RSS XML fixture."""
    with open(FIXTURES_DIR / "sample_search_rss.xml", "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def sample_post_html():
    """Load sample post HTML fixture."""
    with open(FIXTURES_DIR / "sample_post_html.html", "r", encoding="utf-8") as f:
        return f.read()


class TestRedditIdExtraction:
    """Test Reddit ID extraction from various URL formats."""
    
    def test_extract_id_from_standard_url(self):
        url = "https://www.reddit.com/r/forhire/comments/abc123/title_here/"
        assert extract_reddit_id_from_url(url) == "abc123"
    
    def test_extract_id_from_short_url(self):
        url = "https://reddit.com/comments/def456/"
        assert extract_reddit_id_from_url(url) == "def456"
    
    def test_extract_id_with_query_params(self):
        url = "https://www.reddit.com/r/webdev/comments/xyz789/post/?utm_source=share"
        assert extract_reddit_id_from_url(url) == "xyz789"
    
    def test_extract_id_none_for_invalid_url(self):
        assert extract_reddit_id_from_url("") is None
        assert extract_reddit_id_from_url(None) is None
        assert extract_reddit_id_from_url("https://example.com") is None


class TestHtmlCleaning:
    """Test HTML content cleaning."""
    
    def test_clean_simple_html(self):
        html = "<p>Hello <b>world</b>!</p>"
        result = clean_html_content(html)
        assert result == "Hello world !"
    
    def test_clean_html_with_entities(self):
        html = "I&amp;#39;m looking for help &amp;amp; support"
        result = clean_html_content(html)
        assert "I'm" in result or "I&#39;m" in result
        assert "&" in result or "&amp;" in result
    
    def test_clean_html_removes_scripts(self):
        html = "<div>Content<script>alert('xss')</script>More</div>"
        result = clean_html_content(html)
        assert "alert" not in result
        assert "Content" in result
        assert "More" in result
    
    def test_clean_html_collapses_whitespace(self):
        html = "<p>Text    with\n\nmultiple\twhitespace</p>"
        result = clean_html_content(html)
        assert "  " not in result  # No double spaces
        assert "\n" not in result
    
    def test_clean_empty_html(self):
        assert clean_html_content("") == ""
        assert clean_html_content(None) == ""


class TestRssDateParsing:
    """Test RSS date parsing."""
    
    def test_parse_valid_rfc2822_date(self):
        date_str = "Mon, 25 Nov 2025 10:30:00 +0000"
        result = parse_rss_published_date(date_str)
        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 11
        assert result.day == 25
    
    def test_parse_invalid_date_returns_current(self):
        result = parse_rss_published_date("invalid date")
        assert isinstance(result, datetime)
        # Should return current time
        assert (datetime.now(timezone.utc) - result).total_seconds() < 5
    
    def test_parse_empty_date(self):
        result = parse_rss_published_date("")
        assert isinstance(result, datetime)


class TestRssParsing:
    """Test RSS feed parsing."""
    
    @patch('requests.get')
    def test_parse_search_rss_success(self, mock_get, sample_rss_xml):
        """Test successful RSS parsing with sample fixture."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.content = sample_rss_xml.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Parse RSS
        results = parse_search_rss(["looking for developer"], limit=10)
        
        # Verify results
        assert len(results) == 3  # Sample has 3 entries
        
        # Check first entry (buyer intent)
        assert results[0]['reddit_id'] == 'abc123'
        assert '[Hiring]' in results[0]['title']
        assert results[0]['subreddit'] == 'forhire'
        assert results[0]['author'] == 'test_buyer_123'
        
        # Check second entry (buyer intent)
        assert results[1]['reddit_id'] == 'def456'
        assert 'Need help' in results[1]['title']
        assert results[1]['subreddit'] == 'entrepreneur'
        
        # Check third entry (seller/promotional)
        assert results[2]['reddit_id'] == 'ghi789'
        assert 'Selling' in results[2]['title']
    
    @patch('requests.get')
    def test_parse_rss_network_error(self, mock_get):
        """Test RSS parsing handles network errors gracefully."""
        import requests
        mock_get.side_effect = requests.RequestException("Network error")
        
        results = parse_search_rss(["test"], limit=10)
        
        assert results == []  # Should return empty list on error
    
    @patch('requests.get')
    def test_parse_subreddit_rss(self, mock_get, sample_rss_xml):
        """Test subreddit-specific RSS parsing."""
        mock_response = Mock()
        mock_response.content = sample_rss_xml.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        results = parse_subreddit_rss("forhire", limit=10)
        
        assert len(results) > 0
        assert all(result.get('subreddit') == 'forhire' for result in results)


class TestHtmlFallback:
    """Test HTML content fetching fallback."""
    
    @patch('requests.get')
    def test_fetch_post_html_success(self, mock_get, sample_post_html):
        """Test successful HTML content extraction."""
        mock_response = Mock()
        mock_response.text = sample_post_html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        content = _fetch_with_requests("https://reddit.com/r/forhire/comments/abc123/test/")
        
        assert content is not None
        assert len(content) > 100  # Should have substantial content
        assert "fullstack developer" in content.lower()
        assert "react" in content.lower()
    
    @patch('requests.get')
    def test_fetch_html_network_error(self, mock_get):
        """Test HTML fetching handles errors gracefully."""
        import requests
        mock_get.side_effect = requests.RequestException("Network error")
        
        content = _fetch_with_requests("https://reddit.com/test/")
        
        assert content is None  # Should return None on error
    
    @patch('requests.get')
    def test_fetch_html_no_content_found(self, mock_get):
        """Test HTML parsing when no post content found."""
        mock_response = Mock()
        mock_response.text = "<html><body><div>Unrelated content</div></body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        content = _fetch_with_requests("https://reddit.com/test/")
        
        # May return None or minimal content
        assert content is None or len(content) < 50


class TestPostEnrichment:
    """Test post enrichment with HTML fallback."""
    
    def test_enrich_truncated_posts(self):
        """Test that truncated posts trigger HTML fetch."""
        posts = [
            {
                'reddit_id': 'test123',
                'title': 'Test Post',
                'body': 'Short truncated text...',
                'url': 'https://reddit.com/r/test/comments/test123/',
                'is_truncated': True,
            }
        ]
        
        with patch('app.reddit_fetcher.fetch_post_html_content') as mock_fetch:
            mock_fetch.return_value = "Full HTML content here with much more detail"
            
            enriched = enrich_posts_with_html(posts)
            
            assert len(enriched) == 1
            assert enriched[0]['body'] == "Full HTML content here with much more detail"
            assert enriched[0]['fetched_html'] is True
            assert enriched[0]['is_truncated'] is False
    
    def test_skip_enrichment_for_complete_posts(self):
        """Test that non-truncated posts are not re-fetched."""
        posts = [
            {
                'reddit_id': 'test456',
                'title': 'Test Post',
                'body': 'This is complete content that is long enough and does not need HTML fallback',
                'url': 'https://reddit.com/r/test/comments/test456/',
                'is_truncated': False,
            }
        ]
        
        with patch('app.reddit_fetcher.fetch_post_html_content') as mock_fetch:
            enriched = enrich_posts_with_html(posts)
            
            # Should NOT call HTML fetch
            mock_fetch.assert_not_called()
            assert enriched[0]['fetched_html'] is False
    
    @patch('app.reddit_fetcher.get_settings')
    def test_skip_enrichment_when_rss_only(self, mock_settings):
        """Test that USE_RSS_ONLY flag skips HTML fallback."""
        mock_settings.return_value.USE_RSS_ONLY = True
        
        posts = [
            {
                'reddit_id': 'test789',
                'title': 'Test',
                'body': 'Truncated...',
                'url': 'https://reddit.com/test/',
                'is_truncated': True,
            }
        ]
        
        with patch('app.reddit_fetcher.fetch_post_html_content') as mock_fetch:
            enriched = enrich_posts_with_html(posts)
            
            # Should skip HTML fetch when USE_RSS_ONLY=True
            mock_fetch.assert_not_called()


class TestIntegration:
    """Integration tests for complete fetch workflow."""
    
    @patch('requests.get')
    def test_search_reddit_workflow(self, mock_get, sample_rss_xml):
        """Test complete search workflow from RSS to enrichment."""
        mock_response = Mock()
        mock_response.content = sample_rss_xml.encode('utf-8')
        mock_response.text = sample_rss_xml
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        results = search_reddit(
            keywords=["looking for", "need help"],
            subreddits=None,
            limit=10
        )
        
        assert len(results) > 0
        
        # Verify metadata structure
        for post in results:
            assert 'metadata' in post
            assert 'raw_rss' in post['metadata']
            assert 'fetched_html' in post['metadata']
            assert 'was_truncated' in post['metadata']
    
    @patch('requests.get')
    @patch('app.reddit_fetcher.get_settings')
    def test_search_with_html_fallback_disabled(self, mock_settings, mock_get, sample_rss_xml):
        """Test search respects USE_RSS_ONLY setting."""
        mock_settings.return_value.USE_RSS_ONLY = True
        mock_settings.return_value.FETCH_DELAY_SECONDS = 0
        
        mock_response = Mock()
        mock_response.content = sample_rss_xml.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        results = search_reddit(keywords=["test"], limit=5)
        
        # All posts should have fetched_html=False when USE_RSS_ONLY=True
        assert all(post['metadata']['fetched_html'] is False for post in results)


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_extract_id_from_malformed_urls(self):
        """Test ID extraction from malformed URLs."""
        urls = [
            "not a url",
            "https://example.com/random/path",
            "https://reddit.com/",
            "https://reddit.com/r/test/",
        ]
        
        for url in urls:
            result = extract_reddit_id_from_url(url)
            assert result is None, f"Should return None for: {url}"
    
    def test_clean_html_with_nested_tags(self):
        """Test HTML cleaning with deeply nested tags."""
        html = """
        <div>
            <article>
                <section>
                    <p>Nested <span>content <b>here</b></span></p>
                </section>
            </article>
        </div>
        """
        result = clean_html_content(html)
        assert "Nested" in result
        assert "content" in result
        assert "here" in result
        assert "<" not in result
    
    @patch('requests.get')
    def test_parse_rss_empty_feed(self, mock_get):
        """Test parsing an empty RSS feed."""
        empty_feed = """<?xml version="1.0"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <title>Empty Feed</title>
        </feed>"""
        
        mock_response = Mock()
        mock_response.content = empty_feed.encode('utf-8')
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        results = parse_search_rss(["test"], limit=10)
        
        assert results == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
