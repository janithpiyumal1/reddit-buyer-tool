import React, { useState } from 'react';
import { classifyPost, savePostAsLead } from '../api';
import './LeadControls.css';

function LeadControls({ post, onUpdated }) {
  const [loading, setLoading] = useState(false);

  const handleClassify = async () => {
    if (loading) return;
    
    setLoading(true);
    try {
      await classifyPost(post.id, false);
      alert('Post re-classified successfully!');
      onUpdated();
    } catch (error) {
      console.error('Error classifying post:', error);
      alert('Failed to classify post');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleSave = async () => {
    if (loading) return;
    
    setLoading(true);
    try {
      await savePostAsLead(post.id, !post.saved_as_lead);
      onUpdated();
    } catch (error) {
      console.error('Error saving post:', error);
      alert('Failed to save post');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="lead-controls">
      <button
        onClick={handleClassify}
        disabled={loading}
        className="btn-action btn-classify"
        title="Re-classify this post"
      >
        🔄
      </button>
      <button
        onClick={handleToggleSave}
        disabled={loading}
        className={`btn-action ${post.saved_as_lead ? 'btn-unsave' : 'btn-save'}`}
        title={post.saved_as_lead ? 'Remove from saved leads' : 'Save as lead'}
      >
        {post.saved_as_lead ? '⭐' : '☆'}
      </button>
    </div>
  );
}

export default LeadControls;
