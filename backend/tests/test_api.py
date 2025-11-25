"""
API integration tests for the Reddit Buyer Tool backend.
Tests all endpoints with mock data.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock

from app.main import app
from app.deps import get_db_connection


# Create test client
client = TestClient(app)


# Mock database connection for testing
@pytest.fixture
def mock_db():
    """Create a mock database connection."""
    db_mock = MagicMock()
    cursor_mock = MagicMock()
    db_mock.cursor.return_value = cursor_mock
    return db_mock


@pytest.fixture
def override_db_dependency(mock_db):
    """Override the database dependency with mock."""
    def get_mock_db():
        yield mock_db
    
    app.dependency_overrides[get_db_connection] = get_mock_db
    yield
    app.dependency_overrides.clear()


class TestHealthEndpoint:
    """Test system health endpoint."""
    
    def test_health_check(self):
        """Test that health endpoint returns 200."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestRootEndpoint:
    """Test root endpoint."""
    
    def test_root(self):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Reddit Buyer Tool API"
        assert "endpoints" in data


class TestFetchEndpoint:
    """Test POST /api/fetch endpoint."""
    
    @patch("app.routes.fetch_and_store")
    def test_fetch_success(self, mock_fetch, override_db_dependency):
        """Test successful fetch operation."""
        # Mock fetch_and_store to return stats
        mock_fetch.return_value = {
            "fetched": 10,
            "stored": 8,
            "duplicates": 2
        }
        
        payload = {
            "keywords": ["looking for", "need help"],
            "subreddits": ["forhire"],
            "limit": 10
        }
        
        response = client.post("/api/fetch", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["posts_fetched"] == 10
        assert data["posts_stored"] == 8
        assert data["duplicates_skipped"] == 2
        
        # Verify fetch_and_store was called with correct params
        mock_fetch.assert_called_once()
    
    def test_fetch_missing_keywords(self, override_db_dependency):
        """Test fetch without keywords returns validation error."""
        payload = {
            "subreddits": ["forhire"],
            "limit": 10
        }
        
        response = client.post("/api/fetch", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_fetch_invalid_limit(self, override_db_dependency):
        """Test fetch with invalid limit."""
        payload = {
            "keywords": ["test"],
            "limit": 2000  # Exceeds max of 1000
        }
        
        response = client.post("/api/fetch", json=payload)
        assert response.status_code == 422


class TestPostsEndpoint:
    """Test GET /api/posts endpoint."""
    
    @patch("app.routes.get_posts")
    def test_list_posts_success(self, mock_get_posts, override_db_dependency):
        """Test listing posts with default parameters."""
        # Mock database response
        mock_posts = [
            {
                "id": 1,
                "reddit_id": "abc123",
                "subreddit": "forhire",
                "title": "Looking for web developer",
                "body": "Need help with website",
                "author": "user1",
                "created_utc": "2025-01-01 12:00:00",
                "url": "https://reddit.com/r/forhire/abc123",
                "fetched_at": "2025-01-01 12:10:00",
                "is_buyer": 1,
                "classification_source": "heuristic",
                "classification_score": 0.75,
                "metadata": {},
                "saved_as_lead": 0
            }
        ]
        
        mock_get_posts.return_value = (mock_posts, 1)
        
        response = client.get("/api/posts")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["posts"]) == 1
        assert data["posts"][0]["reddit_id"] == "abc123"
        assert data["page"] == 1
    
    @patch("app.routes.get_posts")
    def test_list_posts_with_filters(self, mock_get_posts, override_db_dependency):
        """Test listing posts with filters."""
        mock_get_posts.return_value = ([], 0)
        
        response = client.get("/api/posts?is_buyer=true&subreddit=forhire&page=2&page_size=25")
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 25


class TestClassifyEndpoint:
    """Test POST /api/classify/{post_id} endpoint."""
    
    @patch("app.routes.classify_post")
    @patch("app.routes.update_classification")
    @patch("app.routes.get_post_by_id")
    def test_classify_post_success(self, mock_get_post, mock_update, mock_classify, override_db_dependency):
        """Test successful post classification."""
        # Mock post exists
        mock_get_post.return_value = {
            "id": 1,
            "title": "Need developer",
            "body": "Looking for help",
            "metadata": {}
        }
        
        # Mock classification result
        mock_classify.return_value = (True, 0.85, "Buyer signals detected", "heuristic")
        
        # Mock update success
        mock_update.return_value = True
        
        response = client.post("/api/classify/1", json={})
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "buyer" in data["message"].lower()
    
    @patch("app.routes.get_post_by_id")
    def test_classify_nonexistent_post(self, mock_get_post, override_db_dependency):
        """Test classifying a post that doesn't exist."""
        mock_get_post.return_value = None
        
        response = client.post("/api/classify/999", json={})
        
        assert response.status_code == 404


class TestSaveLeadEndpoint:
    """Test POST /api/save_lead/{post_id} endpoint."""
    
    @patch("app.routes.save_post_as_lead")
    @patch("app.routes.get_post_by_id")
    def test_save_lead_success(self, mock_get_post, mock_save, override_db_dependency):
        """Test saving a post as lead."""
        mock_get_post.return_value = {"id": 1, "title": "Test"}
        mock_save.return_value = True
        
        payload = {"saved": True}
        response = client.post("/api/save_lead/1", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "saved" in data["message"].lower()
    
    @patch("app.routes.save_post_as_lead")
    @patch("app.routes.get_post_by_id")
    def test_unsave_lead(self, mock_get_post, mock_save, override_db_dependency):
        """Test unsaving a lead."""
        mock_get_post.return_value = {"id": 1, "title": "Test"}
        mock_save.return_value = True
        
        payload = {"saved": False}
        response = client.post("/api/save_lead/1", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "unsaved" in data["message"].lower()


class TestExportEndpoint:
    """Test GET /api/export endpoint."""
    
    @patch("app.routes.get_saved_leads")
    def test_export_leads(self, mock_get_leads, override_db_dependency):
        """Test exporting leads as CSV."""
        mock_get_leads.return_value = [
            {
                "id": 1,
                "reddit_id": "abc123",
                "subreddit": "forhire",
                "title": "Need developer",
                "author": "user1",
                "created_utc": "2025-01-01",
                "url": "https://reddit.com/r/forhire/abc123",
                "is_buyer": 1,
                "classification_score": 0.9,
                "classification_source": "heuristic",
                "body": "Looking for help with website"
            }
        ]
        
        response = client.get("/api/export")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        
        # Check CSV content
        csv_content = response.text
        assert "Reddit ID" in csv_content
        assert "abc123" in csv_content


class TestSubredditsEndpoint:
    """Test GET /api/subreddits endpoint."""
    
    @patch("app.routes.get_subreddits_list")
    def test_list_subreddits(self, mock_get_subreddits, override_db_dependency):
        """Test getting list of subreddits."""
        mock_get_subreddits.return_value = ["forhire", "entrepreneur", "startups"]
        
        response = client.get("/api/subreddits")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        assert "forhire" in data["subreddits"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
