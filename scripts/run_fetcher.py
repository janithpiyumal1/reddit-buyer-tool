#!/usr/bin/env python3
"""
Reddit Fetcher CLI Script
Run this script manually or via cron to fetch posts from Reddit.

Usage:
    python scripts/run_fetcher.py --keywords "looking for,need help" --subreddits "forhire,entrepreneur" --limit 100

Example cron job (run every 6 hours):
    0 */6 * * * cd /path/to/reddit-buyer-tool && python scripts/run_fetcher.py --keywords "looking for,hiring" --limit 50
"""

import sys
import os
import argparse
from datetime import datetime

# Add parent directory to path to import backend modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
from backend.app.deps import get_db_pool
from backend.app.reddit_fetcher import fetch_and_store


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Fetch Reddit posts and store them in the database"
    )
    
    parser.add_argument(
        "--keywords",
        type=str,
        required=True,
        help="Comma-separated list of keywords to search for (e.g., 'looking for,need help,hiring')"
    )
    
    parser.add_argument(
        "--subreddits",
        type=str,
        default=None,
        help="Optional comma-separated list of subreddits (e.g., 'forhire,entrepreneur')"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of posts to fetch (default: 100)"
    )
    
    parser.add_argument(
        "--time-filter",
        type=str,
        default="week",
        choices=["hour", "day", "week", "month", "year", "all"],
        help="Time filter for Reddit search (default: week)"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the fetcher script."""
    # Load environment variables
    load_dotenv()
    
    # Parse arguments
    args = parse_args()
    
    # Parse keywords and subreddits
    keywords = [k.strip() for k in args.keywords.split(",")]
    subreddits = [s.strip() for s in args.subreddits.split(",")] if args.subreddits else None
    
    print("=" * 70)
    print("Reddit Buyer Tool - Fetcher")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Keywords: {keywords}")
    print(f"Subreddits: {subreddits or 'ALL'}")
    print(f"Limit: {args.limit}")
    print(f"Time filter: {args.time_filter}")
    print("-" * 70)
    
    try:
        # Get database connection
        pool = get_db_pool()
        db_connection = pool.get_connection()
        
        # Fetch and store posts
        stats = fetch_and_store(
            db_connection=db_connection,
            keywords=keywords,
            subreddits=subreddits,
            limit=args.limit
        )
        
        # Print results
        print("\n" + "=" * 70)
        print("Fetch Results:")
        print("=" * 70)
        print(f"✅ Posts fetched from Reddit: {stats['fetched']}")
        print(f"💾 Posts stored in database: {stats['stored']}")
        print(f"⏭️  Duplicates skipped: {stats['duplicates']}")
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Close connection
        db_connection.close()
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
