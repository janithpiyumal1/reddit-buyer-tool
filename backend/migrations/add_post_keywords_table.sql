-- Migration: Add post_keywords table to track which keywords found each post
-- Created: 2025-11-25

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

-- Add comment to table
ALTER TABLE post_keywords COMMENT = 'Stores keywords that were used to find each post';
