/**
 * API client module for Reddit Buyer Tool
 * Wraps axios for API communication with the backend
 */

import axios from 'axios';

// Base API URL - uses Vite proxy in development
const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Fetch posts from Reddit
 * @param {Object} params - Fetch parameters
 * @param {string[]} params.keywords - Array of keywords
 * @param {string[]} [params.subreddits] - Optional array of subreddits
 * @param {number} [params.limit] - Max posts to fetch
 * @param {boolean} [params.auto_classify] - Auto-classify posts after fetching
 */
export const fetchPosts = async ({ keywords, subreddits, limit, auto_classify }) => {
  const response = await api.post('/fetch', {
    keywords,
    subreddits: subreddits && subreddits.length > 0 ? subreddits : undefined,
    limit: limit || 100,
    auto_classify: auto_classify !== undefined ? auto_classify : false,
  });
  return response.data;
};

/**
 * Get list of posts with filters
 * @param {Object} filters - Filter parameters
 */
export const getPosts = async (filters = {}) => {
  const params = new URLSearchParams();
  
  if (filters.search && filters.search.trim() !== '') {
    params.append('search', filters.search.trim());
  }
  if (filters.is_buyer !== undefined && filters.is_buyer !== null && filters.is_buyer !== '') {
    // Convert string "true"/"false" to actual boolean
    const isBuyerValue = filters.is_buyer === 'true' ? true : filters.is_buyer === 'false' ? false : filters.is_buyer;
    params.append('is_buyer', isBuyerValue);
  }
  if (filters.subreddit) {
    params.append('subreddit', filters.subreddit);
  }
  if (filters.saved_as_lead !== undefined && filters.saved_as_lead !== null && filters.saved_as_lead !== '') {
    // Convert string "true"/"false" to actual boolean
    const savedAsLeadValue = filters.saved_as_lead === 'true' ? true : filters.saved_as_lead === 'false' ? false : filters.saved_as_lead;
    params.append('saved_as_lead', savedAsLeadValue);
  }
  if (filters.page) {
    params.append('page', filters.page);
  }
  if (filters.page_size) {
    params.append('page_size', filters.page_size);
  }
  
  const url = `/posts?${params.toString()}`;
  console.log('API Request URL:', url);
  console.log('Filters:', filters);
  
  const response = await api.get(url);
  console.log('API Response:', response.data);
  return response.data;
};

/**
 * Classify a post
 * @param {number} postId - Post ID
 * @param {boolean} [forceLlm] - Force LLM classification
 */
export const classifyPost = async (postId, forceLlm = false) => {
  const response = await api.post(`/classify/${postId}`, {
    force_llm: forceLlm,
  });
  return response.data;
};

/**
 * Save or unsave a post as lead
 * @param {number} postId - Post ID
 * @param {boolean} saved - True to save, false to unsave
 */
export const savePostAsLead = async (postId, saved) => {
  const response = await api.post(`/save_lead/${postId}`, {
    saved,
  });
  return response.data;
};

/**
 * Delete a post
 * @param {number} postId - Post ID
 */
export const deletePost = async (postId) => {
  const response = await api.delete(`/posts/${postId}`);
  return response.data;
};

/**
 * Delete all posts
 */
export const deleteAllPosts = async () => {
  const response = await api.delete('/posts');
  return response.data;
};

/**
 * Export saved leads as CSV
 */
export const exportLeads = async () => {
  const response = await api.get('/export', {
    responseType: 'blob',
  });
  
  // Create download link
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `reddit_leads_${Date.now()}.csv`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  
  return true;
};

/**
 * Get list of subreddits
 */
export const getSubreddits = async () => {
  const response = await api.get('/subreddits');
  return response.data;
};

/**
 * Health check
 */
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;
