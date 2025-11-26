"""
Test script to verify the post_keywords functionality.
"""
import sys
import os

# Add parent directory to path to import backend modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from backend.app.deps import get_db_pool
from backend.app.db import get_posts_by_keywords

# Load environment variables
load_dotenv()

def test_keyword_search():
    """Test searching posts by keywords."""
    db = get_db_pool().get_connection()
    
    print("\n" + "=" * 60)
    print("Testing Post Keywords Functionality")
    print("=" * 60)
    
    # First, check how many posts have keywords
    cursor = db.cursor()
    cursor.execute("""
        SELECT COUNT(DISTINCT post_id) as posts_with_keywords,
               COUNT(*) as total_keyword_associations
        FROM post_keywords
    """)
    result = cursor.fetchone()
    print(f"\n📊 Database Stats:")
    print(f"   Posts with keywords: {result[0]}")
    print(f"   Total keyword associations: {result[1]}")
    
    # Get some sample keywords
    cursor.execute("""
        SELECT keyword, COUNT(*) as post_count
        FROM post_keywords
        GROUP BY keyword
        ORDER BY post_count DESC
        LIMIT 10
    """)
    keywords_stats = cursor.fetchall()
    
    if keywords_stats:
        print(f"\n🔑 Top Keywords:")
        for kw, count in keywords_stats:
            print(f"   '{kw}': {count} posts")
        
        # Test search with first keyword
        test_keyword = keywords_stats[0][0]
        print(f"\n🔍 Searching for posts with keyword: '{test_keyword}'")
        
        posts, total = get_posts_by_keywords(
            db=db,
            keywords=[test_keyword],
            page=1,
            page_size=5
        )
        
        print(f"\n✅ Found {total} posts matching '{test_keyword}'")
        if posts:
            print(f"\n📝 Sample Posts:")
            for i, post in enumerate(posts[:3], 1):
                print(f"\n   Post {i}:")
                print(f"   Title: {post['title'][:60]}...")
                print(f"   Subreddit: r/{post['subreddit']}")
                print(f"   URL: {post['url'][:50]}...")
    else:
        print("\n⚠️  No keywords found in database yet.")
        print("   Fetch some posts using:")
        print("   python scripts/run_fetcher.py --keywords 'hiring' --limit 10")
    
    cursor.close()
    db.close()
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_keyword_search()
