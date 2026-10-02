from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
import os
import logging
from pathlib import Path

# Force unbuffered output to see logs immediately
os.environ["PYTHONUNBUFFERED"] = "1"

# Configure logging to both console and file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('backend.log')
    ]
)

# Add the parent directory to the path to import from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api import routes
try:
    from app.api.routes_finetuning import router as finetuning_router
    finetuning_available = True
except ImportError:
    finetuning_available = False
    print("Fine-tuning routes not available (requires additional dependencies)")

try:
    from app.api.routes_evaluation import router as evaluation_router
    evaluation_available = True
except ImportError:
    evaluation_available = False
    print("Evaluation routes not available (requires additional dependencies)")

try:
    from app.api.routes_websearch import router as websearch_router
    websearch_available = True
except ImportError:
    websearch_available = False
    print("Web search routes not available (requires additional dependencies)")

try:
    from app.api.routes_tavily import router as tavily_router
    tavily_available = True
    print("Tavily routes loaded successfully")
except ImportError as e:
    tavily_available = False
    print(f"Tavily routes not available: {e}")

from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting EligibAI Backend...")
    yield
    # Shutdown
    print("Shutting down EligibAI Backend...")

app = FastAPI(
    title="EligibAI API",
    description="AI-Powered Scholarship Discovery & Eligibility System",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes.router, prefix="/api", tags=["eligibility"])

# Include fine-tuning routes if available
if finetuning_available:
    app.include_router(finetuning_router, prefix="/api/finetuning", tags=["finetuning"])

# Include evaluation routes if available
if evaluation_available:
    app.include_router(evaluation_router, prefix="/api/evaluation", tags=["evaluation"])

# Include web search routes if available
if websearch_available:
    app.include_router(websearch_router, prefix="/api/websearch", tags=["websearch"])

# Include Tavily routes if available
if tavily_available:
    app.include_router(tavily_router, prefix="/api/tavily")
    print("Tavily routes included successfully")

@app.get("/")
async def root():
    return {
        "message": "EligibAI API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    # Disable reload in production (check if running in production environment)
    is_production = os.environ.get("ENVIRONMENT") == "production"
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=not is_production,
        log_level="info"
    )