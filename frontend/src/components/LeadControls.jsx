import React, { useState } from 'react';
import { classifyPost, savePostAsLead, deletePost } from '../api';
import './LeadControls.css';

function LeadControls({ post, onUpdated }) {
  const [loading, setLoading] = useState(false);

  const handleClassify = async () => {
    if (loading) return;
    
    setLoading(true);
    try {
      const updatedPost = await classifyPost(post.id, false);
      // Update the post in the parent component
      if (onUpdated) {
        onUpdated();
      }
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

  const handleDelete = async () => {
    if (loading) return;
    
    if (!window.confirm('Are you sure you want to delete this post? This action cannot be undone.')) {
      return;
    }
    
    setLoading(true);
    try {
      await deletePost(post.id);
      onUpdated();
    } catch (error) {
      console.error('Error deleting post:', error);
      alert('Failed to delete post');
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
      <button
        onClick={handleDelete}
        disabled={loading}
        className="btn-action btn-delete"
        title="Delete this post"
      >
        🗑️
      </button>
    </div>
  );
}

export default LeadControls;
