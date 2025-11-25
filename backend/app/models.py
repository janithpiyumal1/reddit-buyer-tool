"""
Pydantic models for request/response validation in the Reddit Buyer Tool API.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class FetchRequest(BaseModel):
    """Request model for POST /fetch endpoint."""
    keywords: List[str] = Field(..., min_length=1, description="List of keywords to search for")
    subreddits: Optional[List[str]] = Field(None, description="Optional list of subreddits to search in")
    limit: Optional[int] = Field(100, ge=1, le=1000, description="Maximum number of posts to fetch")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "keywords": ["looking for", "need help", "buying"],
                "subreddits": ["forhire", "entrepreneur"],
                "limit": 50
            }
        }
    )


class ClassifyRequest(BaseModel):
    """Request model for POST /classify/{post_id} endpoint."""
    force_llm: Optional[bool] = Field(False, description="Force LLM classification even if USE_LLM is disabled")


class PostResponse(BaseModel):
    """Response model for a single Reddit post."""
    id: int
    reddit_id: str
    subreddit: Optional[str]
    title: Optional[str]
    body: Optional[str]
    author: Optional[str]
    created_utc: Optional[datetime]
    url: Optional[str]
    fetched_at: Optional[datetime]
    is_buyer: Optional[bool]
    classification_source: Optional[str]
    classification_score: Optional[float]
    metadata: Optional[Dict[str, Any]]
    saved_as_lead: bool
    
    model_config = ConfigDict(from_attributes=True)


class PostsListResponse(BaseModel):
    """Response model for GET /posts endpoint."""
    posts: List[PostResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class PostsQueryParams(BaseModel):
    """Query parameters for GET /posts endpoint."""
    is_buyer: Optional[bool] = None
    subreddit: Optional[str] = None
    saved_as_lead: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=500)
    sort_by: Optional[str] = Field("created_utc", pattern="^(created_utc|fetched_at|classification_score)$")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$")


class ClassificationResult(BaseModel):
    """Result from classification operation."""
    is_buyer: bool
    score: float
    source: str
    reason: str


class FetchResponse(BaseModel):
    """Response model for POST /fetch endpoint."""
    message: str
    posts_fetched: int
    posts_stored: int
    duplicates_skipped: int


class SaveLeadRequest(BaseModel):
    """Request model for POST /save_lead/{post_id} endpoint."""
    saved: bool = Field(..., description="True to save as lead, False to unsave")


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
