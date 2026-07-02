from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, jobs, candidates, ranking
from app.database.migrations import run_migrations
from app.utils.logging import logger

app = FastAPI(
    title="TalentGraph AI API",
    description="Intelligent Candidate Discovery & Ranking System",
    version="1.0.0"
)

# Enable CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production environments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(candidates.router, prefix="/api")
app.include_router(ranking.router, prefix="/api")

@app.on_event("startup")
def on_startup():
    """Execute migrations on server startup to verify DB schemas."""
    logger.info("Initializing TalentGraph AI server...")
    try:
        success = run_migrations()
        if success:
            logger.info("Server startup initialization completed successfully!")
        else:
            logger.error("Server startup initialization failed due to migration failure.")
    except Exception as e:
        logger.error(f"Startup migrations crashed: {e}")

@app.get("/")
def read_root():
    return {
        "app": "TalentGraph AI MVP API",
        "status": "online",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
