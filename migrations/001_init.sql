-- Reddit Buyer Tool - Initial Schema Migration
-- Description: Creates the reddit_posts table to store fetched Reddit posts and classification data
-- Version: 001
-- Date: 2025-11-25

CREATE TABLE IF NOT EXISTS reddit_posts (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  reddit_id VARCHAR(50) NOT NULL UNIQUE,
  subreddit VARCHAR(100),
  title TEXT,
  body TEXT,
  author VARCHAR(100),
  created_utc DATETIME,
  url TEXT,
  fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  is_buyer TINYINT(1) DEFAULT NULL,
  classification_source VARCHAR(30),
  classification_score FLOAT DEFAULT NULL,
  metadata JSON,
  saved_as_lead TINYINT(1) DEFAULT 0,
  
  INDEX idx_subreddit (subreddit),
  INDEX idx_is_buyer (is_buyer),
  INDEX idx_saved_as_lead (saved_as_lead),
  INDEX idx_created_utc (created_utc),
  INDEX idx_fetched_at (fetched_at)
);

-- Add a comment to document the table
ALTER TABLE reddit_posts COMMENT = 'Stores Reddit posts with buyer/prospect classification metadata';
