import React, { useState } from 'react';
import './SearchForm.css';

function SearchForm({ onFetch, disabled }) {
  const [keywords, setKeywords] = useState('');
  const [subreddits, setSubreddits] = useState('');
  const [limit, setLimit] = useState(100);

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!keywords.trim()) {
      alert('Please enter at least one keyword');
      return;
    }

    const keywordList = keywords.split(',').map(k => k.trim()).filter(k => k);
    const subredditList = subreddits.split(',').map(s => s.trim()).filter(s => s);

    onFetch(keywordList, subredditList, limit);
  };

  return (
    <div className="search-form-container">
      <h2>🔍 Fetch New Posts</h2>
      <form onSubmit={handleSubmit} className="search-form">
        <div className="form-group">
          <label htmlFor="keywords">
            Keywords (comma-separated) *
          </label>
          <input
            type="text"
            id="keywords"
            value={keywords}
            onChange={(e) => setKeywords(e.target.value)}
            placeholder='e.g., "looking for", "need help", "hiring"'
            disabled={disabled}
            required
          />
          <small>Enter keywords that indicate buyer intent</small>
        </div>

        <div className="form-group">
          <label htmlFor="subreddits">
            Subreddits (comma-separated, optional)
          </label>
          <input
            type="text"
            id="subreddits"
            value={subreddits}
            onChange={(e) => setSubreddits(e.target.value)}
            placeholder='e.g., "forhire", "entrepreneur", "startups"'
            disabled={disabled}
          />
          <small>Leave empty to search all of Reddit</small>
        </div>

        <div className="form-group">
          <label htmlFor="limit">
            Limit
          </label>
          <input
            type="number"
            id="limit"
            value={limit}
            onChange={(e) => setLimit(parseInt(e.target.value))}
            min="1"
            max="1000"
            disabled={disabled}
          />
          <small>Maximum number of posts to fetch (1-1000)</small>
        </div>

        <button type="submit" className="btn-primary" disabled={disabled}>
          {disabled ? '⏳ Fetching...' : '🚀 Fetch Posts'}
        </button>
      </form>
    </div>
  );
}

export default SearchForm;
