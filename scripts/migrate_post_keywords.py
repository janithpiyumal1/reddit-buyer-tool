"""
Migration script to create the post_keywords table.
Run this to add the new table for tracking which keywords found each post.
"""
import sys
import os

# Add parent directory to path to import backend modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from backend.app.deps import get_db_pool

# Load environment variables
load_dotenv()

def run_migration():
    """Create the post_keywords table."""
    db = get_db_pool().get_connection()
    cursor = db.cursor()
    
    migration_sql = """
    -- Create post_keywords table to store the many-to-many relationship between posts and keywords
    CREATE TABLE IF NOT EXISTS post_keywords (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        post_id BIGINT NOT NULL,
        keyword VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        -- Foreign key to reddit_posts table
        FOREIGN KEY (post_id) REFERENCES reddit_posts(id) ON DELETE CASCADE,
        
        -- Index for faster lookups
        INDEX idx_post_id (post_id),
        INDEX idx_keyword (keyword),
        
        -- Prevent duplicate keyword-post combinations
        UNIQUE KEY unique_post_keyword (post_id, keyword)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    try:
        print("🔄 Running migration: Creating post_keywords table...")
        cursor.execute(migration_sql)
        db.commit()
        print("✅ Migration successful! post_keywords table created.")
        
        # Check if table was created
        cursor.execute("SHOW TABLES LIKE 'post_keywords'")
        result = cursor.fetchone()
        if result:
            print("✅ Verified: post_keywords table exists")
            
            # Show table structure
            cursor.execute("DESCRIBE post_keywords")
            columns = cursor.fetchall()
            print("\n📋 Table Structure:")
            print("-" * 60)
            for col in columns:
                print(f"  {col[0]:<15} {col[1]:<20} {col[2]:<5}")
            print("-" * 60)
        else:
            print("⚠️  Warning: Table creation might have failed")
            
    except Exception as e:
        db.rollback()
        print(f"❌ Migration failed: {str(e)}")
        raise
    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Post Keywords Table Migration")
    print("=" * 60)
    run_migration()
    print("\n✨ You can now track which keywords found each post!")
    print("   Posts will be associated with their search keywords.")
