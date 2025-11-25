"""
FastAPI routes for the Reddit Buyer Tool API.
Defines all endpoints for fetching, classifying, and managing posts.
"""

import csv
import io
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from mysql.connector.pooling import PooledMySQLConnection

from app.deps import get_db_connection
from app.models import (
    FetchRequest, FetchResponse, PostResponse, PostsListResponse,
    ClassifyRequest, SaveLeadRequest, MessageResponse, ErrorResponse
)
from app.db import (
    get_posts, get_post_by_id, update_classification,
    save_post_as_lead, get_saved_leads, get_subreddits_list
)
from app.reddit_fetcher import fetch_and_store
from app.classifier import classify_post


router = APIRouter()


@router.post("/fetch", response_model=FetchResponse, tags=["Fetcher"])
async def fetch_posts(
    request: FetchRequest,
    db: PooledMySQLConnection = Depends(get_db_connection)
):
    """
    Trigger a fetch operation to retrieve posts from Reddit.
    
    - **keywords**: List of keywords to search for (required)
    - **subreddits**: Optional list of subreddit names
    - **limit**: Maximum number of posts to fetch (default: 100)
    """
    try:
        stats = fetch_and_store(
            db_connection=db,
            keywords=request.keywords,
            subreddits=request.subreddits,
            limit=request.limit or 100
        )
        
        return FetchResponse(
            message="Fetch completed successfully",
            posts_fetched=stats["fetched"],
            posts_stored=stats["stored"],
            duplicates_skipped=stats["duplicates"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fetch failed: {str(e)}")


@router.get("/posts", response_model=PostsListResponse, tags=["Posts"])
async def list_posts(
    is_buyer: Optional[bool] = Query(None, description="Filter by buyer classification"),
    subreddit: Optional[str] = Query(None, description="Filter by subreddit"),
    saved_as_lead: Optional[bool] = Query(None, description="Filter by saved lead status"),
    date_from: Optional[datetime] = Query(None, description="Filter posts created after this date"),
    date_to: Optional[datetime] = Query(None, description="Filter posts created before this date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=500, description="Posts per page"),
    sort_by: str = Query("created_utc", pattern="^(created_utc|fetched_at|classification_score)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: PooledMySQLConnection = Depends(get_db_connection)
):
    """
    List posts with optional filtering and pagination.
    
    Returns paginated list of posts with metadata.
    """
    try:
        posts, total = get_posts(
            db=db,
            is_buyer=is_buyer,
            subreddit=subreddit,
            saved_as_lead=saved_as_lead,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Convert to PostResponse models
        post_responses = [
            PostResponse(
                id=p['id'],
                reddit_id=p['reddit_id'],
                subreddit=p['subreddit'],
                title=p['title'],
                body=p['body'],
                author=p['author'],
                created_utc=p['created_utc'],
                url=p['url'],
                fetched_at=p['fetched_at'],
                is_buyer=bool(p['is_buyer']) if p['is_buyer'] is not None else None,
                classification_source=p['classification_source'],
                classification_score=p['classification_score'],
                metadata=p['metadata'],
                saved_as_lead=bool(p['saved_as_lead'])
            )
            for p in posts
        ]
        
        has_next = (page * page_size) < total
        
        return PostsListResponse(
            posts=post_responses,
            total=total,
            page=page,
            page_size=page_size,
            has_next=has_next
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch posts: {str(e)}")


@router.post("/classify/{post_id}", response_model=MessageResponse, tags=["Classification"])
async def classify_post_endpoint(
    post_id: int,
    request: ClassifyRequest = ClassifyRequest(),
    db: PooledMySQLConnection = Depends(get_db_connection)
):
    """
    Force re-classification of a specific post.
    
    - **post_id**: Database ID of the post
    - **force_llm**: Set to true to force LLM classification (optional)
    """
    try:
        # Get the post
        post = get_post_by_id(db, post_id)
        
        if not post:
            raise HTTPException(status_code=404, detail=f"Post {post_id} not found")
        
        # Classify the post
        is_buyer, confidence, reason, source = classify_post(
            title=post['title'] or "",
            body=post['body'] or "",
            metadata=post['metadata'],
            force_llm=request.force_llm
        )
        
        # Update classification in database
        success = update_classification(
            db=db,
            post_id=post_id,
            is_buyer=is_buyer,
            classification_source=source,
            classification_score=confidence
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update classification")
        
        return MessageResponse(
            message=f"Post classified as {'buyer' if is_buyer else 'not buyer'} (source: {source}, score: {confidence:.2f})",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@router.post("/save_lead/{post_id}", response_model=MessageResponse, tags=["Leads"])
async def save_lead(
    post_id: int,
    request: SaveLeadRequest,
    db: PooledMySQLConnection = Depends(get_db_connection)
):
    """
    Mark or unmark a post as a saved lead.
    
    - **post_id**: Database ID of the post
    - **saved**: true to save as lead, false to unsave
    """
    try:
        # Check if post exists
        post = get_post_by_id(db, post_id)
        
        if not post:
            raise HTTPException(status_code=404, detail=f"Post {post_id} not found")
        
        # Update saved status
        success = save_post_as_lead(db, post_id, request.saved)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update lead status")
        
        action = "saved" if request.saved else "unsaved"
        return MessageResponse(
            message=f"Post {post_id} {action} as lead",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Save lead failed: {str(e)}")


@router.get("/export", tags=["Export"])
async def export_leads(
    db: PooledMySQLConnection = Depends(get_db_connection)
):
    """
    Export all saved leads as a CSV file.
    
    Returns a downloadable CSV with all lead information.
    """
    try:
        leads = get_saved_leads(db)
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Reddit ID', 'Subreddit', 'Title', 'Author', 
            'Created UTC', 'URL', 'Is Buyer', 'Classification Score', 
            'Classification Source', 'Body Snippet'
        ])
        
        # Write data rows
        for lead in leads:
            body_snippet = (lead['body'] or '')[:200]  # First 200 chars
            writer.writerow([
                lead['id'],
                lead['reddit_id'],
                lead['subreddit'],
                lead['title'],
                lead['author'],
                lead['created_utc'],
                lead['url'],
                lead['is_buyer'],
                lead['classification_score'],
                lead['classification_source'],
                body_snippet
            ])
        
        # Prepare response
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=reddit_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/subreddits", tags=["Metadata"])
async def list_subreddits(
    db: PooledMySQLConnection = Depends(get_db_connection)
):
    """
    Get list of unique subreddits in the database.
    
    Useful for populating dropdown filters in the UI.
    """
    try:
        subreddits = get_subreddits_list(db)
        return {"subreddits": subreddits, "count": len(subreddits)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch subreddits: {str(e)}")


@router.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "reddit-buyer-tool"
    }
