"""
FastAPI main application for Reddit Buyer Tool.
Entry point for the backend API server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.deps import get_settings, init_database
from app.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    print("🚀 Starting Reddit Buyer Tool API...")
    
    # Initialize database (check if migrations are needed)
    try:
        init_database()
        print("✅ Database connection verified")
    except Exception as e:
        print(f"⚠️  Database initialization warning: {e}")
    
    settings = get_settings()
    print(f"⚙️  LLM enabled: {settings.USE_LLM}")
    print(f"🌐 CORS origins: {settings.CORS_ORIGINS}")
    print(f"🎯 API running on http://{settings.API_HOST}:{settings.API_PORT}")
    
    yield
    
    # Shutdown
    print("👋 Shutting down Reddit Buyer Tool API...")


# Create FastAPI application
app = FastAPI(
    title="Reddit Buyer Tool API",
    description="API for finding and classifying buyer/prospect posts on Reddit",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
settings = get_settings()
origins = settings.CORS_ORIGINS.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Reddit Buyer Tool API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "fetch": "POST /api/fetch",
            "posts": "GET /api/posts",
            "classify": "POST /api/classify/{post_id}",
            "save_lead": "POST /api/save_lead/{post_id}",
            "export": "GET /api/export",
            "subreddits": "GET /api/subreddits",
            "health": "GET /api/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
