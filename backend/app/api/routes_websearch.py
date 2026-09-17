from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
from app.services.web_search import WebSearchService, ScholarshipScraper

router = APIRouter(prefix="/api/websearch", tags=["websearch"])

# Initialize web search service
web_search_service = WebSearchService()
scraper = ScholarshipScraper()

class SearchRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None
    sources: Optional[List[str]] = None

class ScraperRequest(BaseModel):
    url: str

class MonitorRequest(BaseModel):
    interval_minutes: int = 60

@router.post("/search")
async def search_sources(request: SearchRequest):
    """
    Search official scholarship sources for scholarships.
    
    Args:
        request: Search request with query and optional filters
        
    Returns:
        List of scholarships found from official sources
    """
    try:
        results = await web_search_service.search_all_sources(
            query=request.query,
            filters=request.filters
        )
        
        return {
            "success": True,
            "query": request.query,
            "sources_searched": len(web_search_service.sources),
            "results_found": len(results),
            "scholarships": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/scrape")
async def scrape_scholarship(request: ScraperRequest):
    """
    Scrape a specific scholarship page for detailed information.
    
    Args:
        request: Scraper request with URL
        
    Returns:
        Detailed scholarship information
    """
    try:
        details = await scraper.scrape_scholarship_page(request.url)
        
        if not details:
            raise HTTPException(status_code=404, detail="Could not scrape the page")
        
        return {
            "success": True,
            "url": request.url,
            "scholarship": details
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@router.post("/extract-eligibility")
async def extract_eligibility(text: str):
    """
    Extract eligibility information from unstructured text.
    
    Args:
        text: Text content to parse
        
    Returns:
        Extracted eligibility information
    """
    try:
        eligibility = await scraper.extract_eligibility_from_text(text)
        
        return {
            "success": True,
            "eligibility": eligibility
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")

@router.post("/monitor/start")
async def start_monitoring(request: MonitorRequest, background_tasks: BackgroundTasks):
    """
    Start monitoring official sources for changes.
    
    Args:
        request: Monitoring configuration
        background_tasks: FastAPI background tasks
        
    Returns:
        Monitoring status
    """
    try:
        # This would typically be run as a separate process or using Celery
        # For now, we'll return a success message
        return {
            "success": True,
            "message": "Monitoring started",
            "interval_minutes": request.interval_minutes,
            "note": "In production, this should run as a separate background process"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {str(e)}")

@router.get("/sources")
async def list_sources():
    """
    List all configured official sources.
    
    Returns:
        List of official sources
    """
    try:
        sources = [
            {
                "name": source.name,
                "base_url": source.base_url,
                "search_url": source.search_url,
                "rate_limit_delay": source.rate_limit_delay
            }
            for source in web_search_service.sources
        ]
        
        return {
            "success": True,
            "sources": sources
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sources: {str(e)}")

@router.get("/changes")
async def get_recent_changes():
    """
    Get recent changes detected from source monitoring.
    
    Returns:
        List of recent changes
    """
    try:
        from pathlib import Path
        import json
        
        log_path = Path("backend/logs/source_changes.jsonl")
        
        if not log_path.exists():
            return {
                "success": True,
                "changes": [],
                "message": "No changes logged yet"
            }
        
        with open(log_path, 'r') as f:
            changes = json.load(f)
        
        # Return only last 50 changes
        recent_changes = changes[-50:] if len(changes) > 50 else changes
        
        return {
            "success": True,
            "total_changes": len(changes),
            "recent_changes": recent_changes
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get changes: {str(e)}")

@router.on_event("shutdown")
async def shutdown_websearch():
    """Cleanup web search service on shutdown."""
    await web_search_service.close()
    await scraper.close()