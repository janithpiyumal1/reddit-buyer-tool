"""
Database helper functions for the Reddit Buyer Tool.
Provides CRUD operations for reddit_posts table.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import json
import mysql.connector
from mysql.connector.pooling import PooledMySQLConnection


def insert_reddit_post(
    db: PooledMySQLConnection,
    reddit_id: str,
    subreddit: Optional[str],
    title: Optional[str],
    body: Optional[str],
    author: Optional[str],
    created_utc: Optional[datetime],
    url: Optional[str],
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[int]:
    """
    Insert a new Reddit post into the database.
    Returns the inserted post ID, or None if the post already exists (duplicate reddit_id).
    """
    cursor = db.cursor()
    
    # Convert metadata dict to JSON string
    metadata_json = json.dumps(metadata) if metadata else None
    
    query = """
        INSERT INTO reddit_posts 
        (reddit_id, subreddit, title, body, author, created_utc, url, metadata, fetched_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
    """
    
    try:
        cursor.execute(query, (
            reddit_id, subreddit, title, body, author, created_utc, url, metadata_json
        ))
        db.commit()
        post_id = cursor.lastrowid
        cursor.close()
        return post_id
    except mysql.connector.IntegrityError as e:
        # Duplicate reddit_id (unique constraint violation)
        db.rollback()
        cursor.close()
        return None
    except Exception as e:
        db.rollback()
        cursor.close()
        raise e


def update_classification(
    db: PooledMySQLConnection,
    post_id: int,
    is_buyer: bool,
    classification_source: str,
    classification_score: float,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Update classification fields for a post.
    Returns True if successful, False otherwise.
    """
    cursor = db.cursor()
    
    # Merge new metadata with existing if provided
    if metadata:
        metadata_json = json.dumps(metadata)
    else:
        metadata_json = None
    
    query = """
        UPDATE reddit_posts 
        SET is_buyer = %s, 
            classification_source = %s, 
            classification_score = %s
    """
    params = [is_buyer, classification_source, classification_score]
    
    if metadata_json:
        query += ", metadata = %s"
        params.append(metadata_json)
    
    query += " WHERE id = %s"
    params.append(post_id)
    
    try:
        cursor.execute(query, tuple(params))
        db.commit()
        success = cursor.rowcount > 0
        cursor.close()
        return success
    except Exception as e:
        db.rollback()
        cursor.close()
        raise e


def get_post_by_id(db: PooledMySQLConnection, post_id: int) -> Optional[Dict[str, Any]]:
    """Get a single post by its ID."""
    cursor = db.cursor(dictionary=True)
    
    query = "SELECT * FROM reddit_posts WHERE id = %s"
    cursor.execute(query, (post_id,))
    
    result = cursor.fetchone()
    cursor.close()
    
    if result and result.get('metadata'):
        try:
            result['metadata'] = json.loads(result['metadata'])
        except:
            result['metadata'] = None
    
    return result


def get_posts(
    db: PooledMySQLConnection,
    is_buyer: Optional[bool] = None,
    subreddit: Optional[str] = None,
    saved_as_lead: Optional[bool] = None,
    search: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 50,
    sort_by: str = "created_utc",
    sort_order: str = "desc"
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Get posts with optional filters and pagination.
    Returns (posts_list, total_count).
    """
    cursor = db.cursor(dictionary=True)
    
    # Build WHERE clause
    where_clauses = []
    params = []
    
    if is_buyer is not None:
        where_clauses.append("is_buyer = %s")
        params.append(is_buyer)
    
    if subreddit:
        where_clauses.append("subreddit = %s")
        params.append(subreddit)
    
    if saved_as_lead is not None:
        where_clauses.append("saved_as_lead = %s")
        params.append(saved_as_lead)
    
    if search:
        where_clauses.append("(title LIKE %s OR body LIKE %s)")
        search_pattern = f"%{search}%"
        params.append(search_pattern)
        params.append(search_pattern)
    
    if date_from:
        where_clauses.append("created_utc >= %s")
        params.append(date_from)
    
    if date_to:
        where_clauses.append("created_utc <= %s")
        params.append(date_to)
    
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    # Get total count
    count_query = f"SELECT COUNT(*) as total FROM reddit_posts WHERE {where_sql}"
    cursor.execute(count_query, tuple(params))
    total = cursor.fetchone()['total']
    
    # Validate sort_by to prevent SQL injection
    valid_sort_fields = ['created_utc', 'fetched_at', 'classification_score', 'id']
    if sort_by not in valid_sort_fields:
        sort_by = 'created_utc'
    
    # Validate sort_order
    sort_order = 'DESC' if sort_order.lower() == 'desc' else 'ASC'
    
    # Get paginated results
    offset = (page - 1) * page_size
    
    query = f"""
        SELECT * FROM reddit_posts 
        WHERE {where_sql}
        ORDER BY {sort_by} {sort_order}
        LIMIT %s OFFSET %s
    """
    
    params.extend([page_size, offset])
    cursor.execute(query, tuple(params))
    
    posts = cursor.fetchall()
    cursor.close()
    
    # Parse JSON metadata for each post
    for post in posts:
        if post.get('metadata'):
            try:
                post['metadata'] = json.loads(post['metadata'])
            except:
                post['metadata'] = None
    
    return posts, total


def get_unclassified_posts(db: PooledMySQLConnection, limit: int = 100) -> List[Dict[str, Any]]:
    """Get posts that haven't been classified yet."""
    cursor = db.cursor(dictionary=True)
    
    query = """
        SELECT * FROM reddit_posts 
        WHERE is_buyer IS NULL 
        ORDER BY fetched_at ASC
        LIMIT %s
    """
    
    cursor.execute(query, (limit,))
    posts = cursor.fetchall()
    cursor.close()
    
    # Parse JSON metadata for each post
    for post in posts:
        if post.get('metadata'):
            try:
                post['metadata'] = json.loads(post['metadata'])
            except:
                post['metadata'] = None
    
    return posts


def save_post_as_lead(db: PooledMySQLConnection, post_id: int, saved: bool) -> bool:
    """
    Mark/unmark a post as a saved lead.
    Returns True if successful, False otherwise.
    """
    cursor = db.cursor()
    
    query = "UPDATE reddit_posts SET saved_as_lead = %s WHERE id = %s"
    
    try:
        cursor.execute(query, (saved, post_id))
        db.commit()
        success = cursor.rowcount > 0
        cursor.close()
        return success
    except Exception as e:
        db.rollback()
        cursor.close()
        raise e


def get_saved_leads(db: PooledMySQLConnection) -> List[Dict[str, Any]]:
    """Get all posts marked as saved leads."""
    cursor = db.cursor(dictionary=True)
    
    query = """
        SELECT * FROM reddit_posts 
        WHERE saved_as_lead = 1
        ORDER BY created_utc DESC
    """
    
    cursor.execute(query)
    leads = cursor.fetchall()
    cursor.close()
    
    # Parse JSON metadata for each lead
    for lead in leads:
        if lead.get('metadata'):
            try:
                lead['metadata'] = json.loads(lead['metadata'])
            except:
                lead['metadata'] = None
    
    return leads


def get_subreddits_list(db: PooledMySQLConnection) -> List[str]:
    """Get list of unique subreddits in the database."""
    cursor = db.cursor()
    
    query = """
        SELECT DISTINCT subreddit 
        FROM reddit_posts 
        WHERE subreddit IS NOT NULL
        ORDER BY subreddit
    """
    
    cursor.execute(query)
    subreddits = [row[0] for row in cursor.fetchall()]
    cursor.close()
    
    return subreddits


def add_post_keyword(
    db: PooledMySQLConnection,
    post_id: int,
    keyword: str
) -> bool:
    """
    Associate a keyword with a post.
    Returns True if successful, False if already exists.
    """
    cursor = db.cursor()
    
    query = """
        INSERT IGNORE INTO post_keywords (post_id, keyword)
        VALUES (%s, %s)
    """
    
    try:
        cursor.execute(query, (post_id, keyword.lower().strip()))
        db.commit()
        rows_affected = cursor.rowcount
        cursor.close()
        return rows_affected > 0
    except Exception as e:
        db.rollback()
        cursor.close()
        raise e


def get_posts_by_keywords(
    db: PooledMySQLConnection,
    keywords: List[str],
    is_buyer: Optional[bool] = None,
    subreddit: Optional[str] = None,
    saved_as_lead: Optional[bool] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 50,
    sort_by: str = "created_utc",
    sort_order: str = "desc"
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Get posts that match ANY of the provided keywords.
    Returns (posts_list, total_count).
    """
    cursor = db.cursor(dictionary=True)
    
    # Build WHERE clause
    where_clauses = []
    params = []
    
    # Filter by keywords using the post_keywords table
    if keywords and len(keywords) > 0:
        # Create placeholders for IN clause
        keyword_placeholders = ','.join(['%s'] * len(keywords))
        where_clauses.append(f"""
            id IN (
                SELECT DISTINCT post_id 
                FROM post_keywords 
                WHERE keyword IN ({keyword_placeholders})
            )
        """)
        # Add lowercase keywords to params
        params.extend([kw.lower().strip() for kw in keywords])
    
    if is_buyer is not None:
        where_clauses.append("is_buyer = %s")
        params.append(is_buyer)
    
    if subreddit:
        where_clauses.append("subreddit = %s")
        params.append(subreddit)
    
    if saved_as_lead is not None:
        where_clauses.append("saved_as_lead = %s")
        params.append(saved_as_lead)
    
    if date_from:
        where_clauses.append("created_utc >= %s")
        params.append(date_from)
    
    if date_to:
        where_clauses.append("created_utc <= %s")
        params.append(date_to)
    
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    # Get total count
    count_query = f"SELECT COUNT(*) as total FROM reddit_posts WHERE {where_sql}"
    cursor.execute(count_query, tuple(params))
    total = cursor.fetchone()['total']
    
    # Validate sort_by
    valid_sort_fields = ['created_utc', 'fetched_at', 'classification_score', 'id']
    if sort_by not in valid_sort_fields:
        sort_by = 'created_utc'
    
    # Validate sort_order
    sort_order = 'DESC' if sort_order.lower() == 'desc' else 'ASC'
    
    # Get paginated results
    offset = (page - 1) * page_size
    
    query = f"""
        SELECT * FROM reddit_posts 
        WHERE {where_sql}
        ORDER BY {sort_by} {sort_order}
        LIMIT %s OFFSET %s
    """
    
    params.extend([page_size, offset])
    cursor.execute(query, tuple(params))
    
    posts = cursor.fetchall()
    cursor.close()
    
    # Parse JSON metadata for each post
    for post in posts:
        if post.get('metadata'):
            try:
                post['metadata'] = json.loads(post['metadata'])
            except:
                post['metadata'] = None
    
    return posts, total


def get_keywords_for_post(
    db: PooledMySQLConnection,
    post_id: int
) -> List[str]:
    """Get all keywords associated with a post."""
    cursor = db.cursor()
    
    query = """
        SELECT keyword 
        FROM post_keywords 
        WHERE post_id = %s
        ORDER BY created_at
    """
    
    cursor.execute(query, (post_id,))
    keywords = [row[0] for row in cursor.fetchall()]
    cursor.close()
    
    return keywords


def delete_post(
    db: PooledMySQLConnection,
    post_id: int
) -> bool:
    """Delete a post from the database.
    
    Returns True if successful, False otherwise.
    """
    cursor = db.cursor()
    
    try:
        # Delete associated keywords first (due to foreign key constraint)
        cursor.execute("DELETE FROM post_keywords WHERE post_id = %s", (post_id,))
        
        # Delete the post
        cursor.execute("DELETE FROM reddit_posts WHERE id = %s", (post_id,))
        
        db.commit()
        success = cursor.rowcount > 0
        cursor.close()
        return success
    except Exception as e:
        db.rollback()
        cursor.close()
        raise e


def delete_all_posts(
    db: PooledMySQLConnection
) -> int:
    """Delete all posts from the database.
    
    Returns the number of posts deleted.
    """
    cursor = db.cursor()
    
    try:
        # Delete all keywords first (due to foreign key constraint)
        cursor.execute("DELETE FROM post_keywords")
        
        # Delete all posts
        cursor.execute("DELETE FROM reddit_posts")
        
        db.commit()
        deleted_count = cursor.rowcount
        cursor.close()
        return deleted_count
    except Exception as e:
        db.rollback()
        cursor.close()
        raise e
