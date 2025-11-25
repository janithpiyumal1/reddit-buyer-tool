import React, { useState, useEffect } from 'react';
import SearchForm from './components/SearchForm';
import PostsTable from './components/PostsTable';
import FilterBar from './components/FilterBar';
import { fetchPosts, getPosts, getSubreddits } from './api';
import './App.css';

function App() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [fetchProgress, setFetchProgress] = useState(null);
  const [filters, setFilters] = useState({
    is_buyer: '',
    subreddit: '',
    saved_as_lead: '',
    page: 1,
    page_size: 50,
  });
  const [pagination, setPagination] = useState({
    total: 0,
    page: 1,
    page_size: 50,
    has_next: false,
  });
  const [subreddits, setSubreddits] = useState([]);

  // Load posts on component mount and when filters change
  useEffect(() => {
    loadPosts();
  }, [filters]);

  // Load available subreddits
  useEffect(() => {
    loadSubreddits();
  }, []);

  const loadPosts = async () => {
    setLoading(true);
    try {
      const data = await getPosts(filters);
      setPosts(data.posts);
      setPagination({
        total: data.total,
        page: data.page,
        page_size: data.page_size,
        has_next: data.has_next,
      });
    } catch (error) {
      console.error('Error loading posts:', error);
      alert('Failed to load posts. Please check your backend connection.');
    } finally {
      setLoading(false);
    }
  };

  const loadSubreddits = async () => {
    try {
      const data = await getSubreddits();
      setSubreddits(data.subreddits || []);
    } catch (error) {
      console.error('Error loading subreddits:', error);
    }
  };

  const handleFetch = async (keywords, selectedSubreddits, limit) => {
    setLoading(true);
    setFetchProgress({ status: 'fetching', message: 'Fetching posts from Reddit...' });

    try {
      const result = await fetchPosts({ keywords, subreddits: selectedSubreddits, limit });
      
      setFetchProgress({
        status: 'success',
        message: `Fetched ${result.posts_fetched} posts, stored ${result.posts_stored} new posts, skipped ${result.duplicates_skipped} duplicates.`,
      });

      // Reload posts to show new data
      setTimeout(() => {
        loadPosts();
        loadSubreddits(); // Refresh subreddit list
        setFetchProgress(null);
      }, 2000);
    } catch (error) {
      console.error('Error fetching posts:', error);
      setFetchProgress({
        status: 'error',
        message: `Failed to fetch posts: ${error.response?.data?.detail || error.message}`,
      });
      setLoading(false);
    }
  };

  const handleFilterChange = (newFilters) => {
    setFilters({ ...filters, ...newFilters, page: 1 }); // Reset to page 1 when filters change
  };

  const handlePageChange = (newPage) => {
    setFilters({ ...filters, page: newPage });
  };

  const handlePostUpdated = () => {
    // Reload posts after a post is updated (classified or saved)
    loadPosts();
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🎯 Reddit Buyer Tool</h1>
        <p>Find and track buyer/prospect posts on Reddit</p>
      </header>

      <main className="App-main">
        <SearchForm onFetch={handleFetch} disabled={loading} />

        {fetchProgress && (
          <div className={`fetch-progress fetch-progress-${fetchProgress.status}`}>
            {fetchProgress.message}
          </div>
        )}

        <FilterBar
          filters={filters}
          subreddits={subreddits}
          onFilterChange={handleFilterChange}
        />

        <PostsTable
          posts={posts}
          loading={loading}
          pagination={pagination}
          onPageChange={handlePageChange}
          onPostUpdated={handlePostUpdated}
        />
      </main>

      <footer className="App-footer">
        <p>
          Reddit Buyer Tool v1.0.0 | Built with React + FastAPI
        </p>
      </footer>
    </div>
  );
}

export default App;
