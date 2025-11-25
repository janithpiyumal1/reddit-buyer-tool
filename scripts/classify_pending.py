#!/usr/bin/env python3
"""
Classify Pending Posts Script
Runs classification on all unclassified posts in the database.

Usage:
    python scripts/classify_pending.py --limit 100 --use-llm

Example cron job (run daily at 2 AM):
    0 2 * * * cd /path/to/reddit-buyer-tool && python scripts/classify_pending.py --limit 200
"""

import sys
import os
import argparse
from datetime import datetime

# Add parent directory to path to import backend modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
from backend.app.deps import get_db_pool
from backend.app.db import get_unclassified_posts, update_classification
from backend.app.classifier import classify_post


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Classify unclassified Reddit posts"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of posts to classify (default: 100)"
    )
    
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Enable LLM classification for low-confidence posts"
    )
    
    parser.add_argument(
        "--force-llm",
        action="store_true",
        help="Force LLM classification for all posts (ignores USE_LLM env var)"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the classifier script."""
    # Load environment variables
    load_dotenv()
    
    # Parse arguments
    args = parse_args()
    
    print("=" * 70)
    print("Reddit Buyer Tool - Classifier")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Limit: {args.limit}")
    print(f"Use LLM: {args.use_llm or args.force_llm}")
    print("-" * 70)
    
    try:
        # Get database connection
        pool = get_db_pool()
        db_connection = pool.get_connection()
        
        # Get unclassified posts
        posts = get_unclassified_posts(db_connection, limit=args.limit)
        
        if not posts:
            print("\n✅ No unclassified posts found.")
            db_connection.close()
            return 0
        
        print(f"\nFound {len(posts)} unclassified post(s). Classifying...\n")
        
        # Classify each post
        stats = {
            "total": len(posts),
            "buyer": 0,
            "not_buyer": 0,
            "heuristic": 0,
            "llm": 0,
            "errors": 0
        }
        
        for i, post in enumerate(posts, 1):
            try:
                # Classify the post
                is_buyer, confidence, reason, source = classify_post(
                    title=post.get('title') or "",
                    body=post.get('body') or "",
                    metadata=post.get('metadata'),
                    force_llm=args.force_llm
                )
                
                # Update classification in database
                success = update_classification(
                    db=db_connection,
                    post_id=post['id'],
                    is_buyer=is_buyer,
                    classification_source=source,
                    classification_score=confidence
                )
                
                if success:
                    # Update stats
                    if is_buyer:
                        stats["buyer"] += 1
                    else:
                        stats["not_buyer"] += 1
                    
                    if source == "llm":
                        stats["llm"] += 1
                    else:
                        stats["heuristic"] += 1
                    
                    # Print progress
                    result_emoji = "✅" if is_buyer else "❌"
                    print(f"[{i}/{len(posts)}] {result_emoji} Post {post['id']}: "
                          f"{'BUYER' if is_buyer else 'NOT BUYER'} "
                          f"(score: {confidence:.2f}, source: {source})")
                else:
                    print(f"[{i}/{len(posts)}] ⚠️  Failed to update post {post['id']}")
                    stats["errors"] += 1
                    
            except Exception as e:
                print(f"[{i}/{len(posts)}] ❌ Error classifying post {post['id']}: {e}")
                stats["errors"] += 1
        
        # Print summary
        print("\n" + "=" * 70)
        print("Classification Results:")
        print("=" * 70)
        print(f"Total posts processed: {stats['total']}")
        print(f"✅ Buyer posts: {stats['buyer']}")
        print(f"❌ Not buyer posts: {stats['not_buyer']}")
        print(f"🤖 Heuristic classifications: {stats['heuristic']}")
        print(f"🧠 LLM classifications: {stats['llm']}")
        print(f"⚠️  Errors: {stats['errors']}")
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
