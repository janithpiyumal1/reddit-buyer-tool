# Reddit Buyer Tool - Frontend

React-based frontend for the Reddit Buyer Tool application.

## Tech Stack

- React 18
- Vite (build tool)
- Axios (HTTP client)

## Development Setup

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

The frontend will run on `http://localhost:3000` and proxy API requests to the backend at `http://localhost:8000`.

## Build for Production

```bash
npm run build
```

The production build will be output to the `dist/` directory.

## Features

- **Search Form**: Input keywords and subreddits to fetch posts from Reddit
- **Filter Bar**: Filter posts by classification, subreddit, and saved status
- **Posts Table**: View posts with pagination and expandable details
- **Lead Controls**: Classify posts and save them as leads
- **Export**: Download saved leads as CSV

## Project Structure

```
frontend/
├── src/
│   ├── components/       # React components
│   │   ├── SearchForm.jsx
│   │   ├── FilterBar.jsx
│   │   ├── PostsTable.jsx
│   │   └── LeadControls.jsx
│   ├── App.jsx          # Main application component
│   ├── api.js           # API client wrapper
│   ├── main.jsx         # Application entry point
│   └── *.css            # Component styles
├── index.html
├── package.json
└── vite.config.js
```

## Environment Variables

The frontend uses Vite's proxy configuration for API requests in development. No additional environment variables are needed.
