# Post Keywords Feature - Implementation Summary

## ✅ What Was Created

### 1. **New Database Table: `post_keywords`**
   - Stores the many-to-many relationship between posts and keywords
   - Schema:
     ```sql
     - id (BIGINT): Primary key
     - post_id (BIGINT): Foreign key to reddit_posts table
     - keyword (VARCHAR 255): The keyword that found this post
     - created_at (TIMESTAMP): When the association was created
     ```
   - Indexes: On `post_id` and `keyword` for fast lookups
   - Unique constraint: Prevents duplicate keyword-post pairs

### 2. **Database Functions Added** (`backend/app/db.py`)
   - `add_post_keyword(db, post_id, keyword)`: Associate a keyword with a post
   - `get_posts_by_keywords(db, keywords, ...)`: Get posts matching ANY of the keywords
   - `get_keywords_for_post(db, post_id)`: Get all keywords for a specific post

### 3. **Updated Fetcher** (`backend/app/reddit_fetcher.py`)
   - Now automatically stores keywords when fetching posts
   - When you fetch with keywords like `["hiring", "looking for"]`, those keywords are saved with each post

### 4. **Updated API** (`backend/app/routes.py`)
   - `/posts` endpoint now uses keyword-based search
   - When `search` parameter is provided, it searches in the `post_keywords` table
   - Supports comma-separated keywords: `?search=hiring,freelance`

## 🎯 How It Works

### Fetching Posts (Stores Keywords):
```bash
python scripts/run_fetcher.py --keywords "hiring" "freelance" --limit 10
```
- Fetches posts matching those keywords
- Stores each post in `reddit_posts` table
- **NEW**: Stores keyword associations in `post_keywords` table
  - Post #123 → "hiring"
  - Post #123 → "freelance"

### Searching Posts (Uses Keywords):
```
GET /posts?search=hiring
GET /posts?search=hiring,freelance
```
- Searches `post_keywords` table for posts with those exact keywords
- Only shows posts that were found using those specific keywords
- Much faster than text search in title/body

## 📊 Example Workflow

1. **Fetch posts with keywords:**
   ```bash
   # Fetch posts about hiring
   python scripts/run_fetcher.py --keywords "hiring" --limit 20
   
   # Fetch posts about freelancing  
   python scripts/run_fetcher.py --keywords "freelance" --limit 20
   ```

2. **Search in frontend:**
   - Type "hiring" in Search Keywords → Shows only posts fetched with "hiring" keyword
   - Type "freelance" → Shows only posts fetched with "freelance" keyword
   - Type "hiring,freelance" → Shows posts fetched with EITHER keyword

3. **Benefits:**
   - **Accurate**: Shows exactly what you searched for
   - **Fast**: Indexed keyword lookup instead of full-text search
   - **Traceable**: Know which keywords found each post
   - **No duplicates**: Can't associate same keyword twice with a post

## 🚀 Testing

### Test 1: Check Current State
```bash
python scripts/test_keywords.py
```
Shows how many posts have keywords and what the top keywords are.

### Test 2: Fetch New Posts
```bash
python scripts/run_fetcher.py --keywords "hiring" --limit 5
python scripts/test_keywords.py
```
Should now show 5 posts with "hiring" keyword.

### Test 3: Search via API
```bash
# Using curl or browser
GET http://localhost:8000/posts?search=hiring
```

### Test 4: Search via Frontend
1. Open frontend in browser
2. Type "hiring" in "Search Keywords" field
3. Should show only posts fetched with "hiring" keyword

## 🔧 Migration

Run this once to create the table:
```bash
python scripts/migrate_post_keywords.py
```

## 📝 Notes

- **Existing posts** (fetched before this update) won't have keywords
  - They won't show up in keyword searches
  - Solution: Re-fetch them or add keywords manually

- **Frontend behavior**: 
  - Empty by default (no posts shown)
  - Only shows posts when you enter keywords
  - Exactly what you requested!

- **Backward compatible**:
  - Old posts without keywords still accessible via direct DB queries
  - New posts automatically get keywords

## 🎉 Summary

You now have a **keyword-tracking system** where:
1. ✅ Posts are tagged with the keywords used to find them
2. ✅ Searches only return posts matching those specific keywords
3. ✅ No more seeing all 52 random posts - only what you search for!
4. ✅ Fast, indexed lookups in dedicated `post_keywords` table
