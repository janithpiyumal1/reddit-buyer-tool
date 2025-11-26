"""
Quick script to check the classification status of posts in the database.
"""
import sys
import os

# Add parent directory to path to import backend modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from backend.app.deps import get_db_pool

# Load environment variables
load_dotenv()

def check_classification_stats():
    """Check how many posts are classified vs unclassified."""
    db = get_db_pool().get_connection()
    cursor = db.cursor()
    
    query = """
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN is_buyer = 1 THEN 1 ELSE 0 END) as buyers,
            SUM(CASE WHEN is_buyer = 0 THEN 1 ELSE 0 END) as non_buyers,
            SUM(CASE WHEN is_buyer IS NULL THEN 1 ELSE 0 END) as unclassified
        FROM reddit_posts
    """
    
    cursor.execute(query)
    result = cursor.fetchone()
    
    print("\n📊 Database Classification Stats:")
    print("=" * 50)
    print(f"Total posts:        {result[0]}")
    print(f"✅ Buyer posts:     {result[1]}")
    print(f"❌ Non-buyer posts: {result[2]}")
    print(f"⏳ Unclassified:    {result[3]}")
    print("=" * 50)
    
    if result[3] > 0:
        print(f"\n💡 You have {result[3]} unclassified posts.")
        print("   Run: python scripts/classify_pending.py")
        print("   Or fetch with: python scripts/run_fetcher.py --auto-classify")
    
    cursor.close()
    db.close()

if __name__ == "__main__":
    check_classification_stats()
