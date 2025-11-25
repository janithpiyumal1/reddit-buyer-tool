import React, { useState } from 'react';
import LeadControls from './LeadControls';
import { exportLeads } from '../api';
import './PostsTable.css';

function PostsTable({ posts, loading, pagination, onPageChange, onPostUpdated }) {
  const [expandedPost, setExpandedPost] = useState(null);

  const toggleExpand = (postId) => {
    setExpandedPost(expandedPost === postId ? null : postId);
  };

  const handleExport = async () => {
    try {
      await exportLeads();
      alert('Leads exported successfully!');
    } catch (error) {
      console.error('Error exporting leads:', error);
      alert('Failed to export leads');
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  const getBuyerBadge = (isBuyer, score) => {
    if (isBuyer === null || isBuyer === undefined) {
      return <span className="badge badge-unclassified">Unclassified</span>;
    }
    if (isBuyer) {
      const confidence = score ? ` (${(score * 100).toFixed(0)}%)` : '';
      return <span className="badge badge-buyer">✅ Buyer{confidence}</span>;
    }
    return <span className="badge badge-not-buyer">❌ Not Buyer</span>;
  };

  if (loading) {
    return <div className="loading">⏳ Loading posts...</div>;
  }

  if (!posts || posts.length === 0) {
    return (
      <div className="no-posts">
        <p>📭 No posts found. Try fetching some posts or adjusting your filters.</p>
      </div>
    );
  }

  return (
    <div className="posts-table-container">
      <div className="table-header">
        <h2>📊 Posts ({pagination.total} total)</h2>
        <button onClick={handleExport} className="btn-export">
          📥 Export Saved Leads
        </button>
      </div>

      <div className="table-responsive">
        <table className="posts-table">
          <thead>
            <tr>
              <th>Subreddit</th>
              <th>Title</th>
              <th>Author</th>
              <th>Created</th>
              <th>Classification</th>
              <th>Saved</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {posts.map((post) => (
              <React.Fragment key={post.id}>
                <tr className={expandedPost === post.id ? 'expanded' : ''}>
                  <td>
                    <a
                      href={`https://reddit.com/r/${post.subreddit}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="subreddit-link"
                    >
                      r/{post.subreddit}
                    </a>
                  </td>
                  <td>
                    <div className="title-cell">
                      <a
                        href={post.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="post-title"
                      >
                        {post.title}
                      </a>
                      <button
                        onClick={() => toggleExpand(post.id)}
                        className="btn-expand"
                      >
                        {expandedPost === post.id ? '▼' : '▶'}
                      </button>
                    </div>
                  </td>
                  <td>u/{post.author}</td>
                  <td className="date-cell">
                    {formatDate(post.created_utc)}
                  </td>
                  <td>
                    {getBuyerBadge(post.is_buyer, post.classification_score)}
                    {post.classification_source && (
                      <small className="source-tag">
                        {post.classification_source}
                      </small>
                    )}
                  </td>
                  <td>
                    {post.saved_as_lead ? (
                      <span className="badge badge-saved">⭐ Saved</span>
                    ) : (
                      <span className="badge badge-not-saved">-</span>
                    )}
                  </td>
                  <td>
                    <LeadControls post={post} onUpdated={onPostUpdated} />
                  </td>
                </tr>
                {expandedPost === post.id && (
                  <tr className="expanded-row">
                    <td colSpan="7">
                      <div className="post-details">
                        <h4>Post Body:</h4>
                        <p className="post-body">
                          {post.body || <em>No body text</em>}
                        </p>
                        <div className="post-meta">
                          <span>Reddit ID: {post.reddit_id}</span>
                          <span>Fetched: {formatDate(post.fetched_at)}</span>
                          {post.classification_score && (
                            <span>Score: {post.classification_score.toFixed(3)}</span>
                          )}
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="pagination">
        <button
          onClick={() => onPageChange(pagination.page - 1)}
          disabled={pagination.page === 1}
          className="btn-page"
        >
          ← Previous
        </button>
        <span className="page-info">
          Page {pagination.page} of {Math.ceil(pagination.total / pagination.page_size)}
        </span>
        <button
          onClick={() => onPageChange(pagination.page + 1)}
          disabled={!pagination.has_next}
          className="btn-page"
        >
          Next →
        </button>
      </div>
    </div>
  );
}

export default PostsTable;
