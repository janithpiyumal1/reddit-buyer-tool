import React from 'react';
import './FilterBar.css';

function FilterBar({ filters, subreddits, onFilterChange }) {
  const handleFilterChange = (key, value) => {
    onFilterChange({ [key]: value });
  };

  return (
    <div className="filter-bar">
      <h3>🔎 Filters</h3>
      <div className="filter-controls">
        <div className="filter-group">
          <label htmlFor="filter-is-buyer">Classification:</label>
          <select
            id="filter-is-buyer"
            value={filters.is_buyer}
            onChange={(e) => handleFilterChange('is_buyer', e.target.value)}
          >
            <option value="">All Posts</option>
            <option value="true">Buyer Posts Only</option>
            <option value="false">Non-Buyer Posts Only</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="filter-subreddit">Subreddit:</label>
          <select
            id="filter-subreddit"
            value={filters.subreddit}
            onChange={(e) => handleFilterChange('subreddit', e.target.value)}
          >
            <option value="">All Subreddits</option>
            {subreddits.map((sub) => (
              <option key={sub} value={sub}>
                r/{sub}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="filter-saved">Saved Leads:</label>
          <select
            id="filter-saved"
            value={filters.saved_as_lead}
            onChange={(e) => handleFilterChange('saved_as_lead', e.target.value)}
          >
            <option value="">All</option>
            <option value="true">Saved Only</option>
            <option value="false">Not Saved</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="filter-page-size">Per Page:</label>
          <select
            id="filter-page-size"
            value={filters.page_size}
            onChange={(e) => handleFilterChange('page_size', parseInt(e.target.value))}
          >
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </div>
      </div>
    </div>
  );
}

export default FilterBar;
