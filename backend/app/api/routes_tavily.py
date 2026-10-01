from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from app.services.tavily_search import TavilySearchService
from app.services.tavily_extract import TavilyExtractService
from app.services.llm_extraction import LLMExtractionService
from app.services.database import db_service
from app.services.eligibility_engine_v2 import eligibility_engine_v2
from app.models.scholarship_extraction import ExtractionRequest, ExtractionResponse

router = APIRouter(tags=["tavily"])

# Lazy initialization of services
tavily_search = None
tavily_extract = None
llm_extraction = None

def get_tavily_search():
    global tavily_search
    if tavily_search is None:
        tavily_search = TavilySearchService()
    return tavily_search

def get_tavily_extract():
    global tavily_extract
    if tavily_extract is None:
        tavily_extract = TavilyExtractService()
    return tavily_extract

def get_llm_extraction():
    global llm_extraction
    if llm_extraction is None:
        llm_extraction = LLMExtractionService()
    return llm_extraction

class SearchRequest(BaseModel):
    query: str
    profile: Optional[Dict[str, Any]] = None
    max_results: int = 10

class ExtractRequest(BaseModel):
    urls: List[str]
    extract_depth: str = "advanced"

class SourceSearchRequest(BaseModel):
    source: str
    query: str
    max_results: int = 5

@router.post("/search")
async def search_scholarships(request: SearchRequest):
    """
    Search for scholarships using Tavily API.
    Prioritizes official government sources.
    """
    try:
        search_service = get_tavily_search()
        results = search_service.search_scholarships(
            query=request.query,
            profile=request.profile,
            max_results=request.max_results
        )
        
        return {
            "success": True,
            "query": request.query,
            "results_found": len(results),
            "official_sources_searched": len(search_service.official_domains),
            "scholarships": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tavily search failed: {str(e)}")

@router.post("/search/{source}")
async def search_by_source(source: str, request: SourceSearchRequest):
    """
    Search a specific official source for scholarships.
    """
    try:
        search_service = get_tavily_search()
        results = search_service.search_by_source(
            source=source,
            query=request.query,
            max_results=request.max_results
        )
        
        return {
            "success": True,
            "source": source,
            "query": request.query,
            "results_found": len(results),
            "scholarships": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Source search failed: {str(e)}")

@router.post("/extract")
async def extract_content(request: ExtractRequest):
    """
    Extract complete content from scholarship URLs.
    """
    try:
        extract_service = get_tavily_extract()
        results = extract_service.extract_scholarship_content(
            urls=request.urls,
            extract_depth=request.extract_depth
        )
        
        return {
            "success": True,
            "urls_processed": len(request.urls),
            "extractions_successful": len(results),
            "content": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content extraction failed: {str(e)}")

@router.post("/extract/single")
async def extract_single(url: str):
    """
    Extract content from a single scholarship URL.
    """
    try:
        extract_service = get_tavily_extract()
        result = extract_service.extract_single_scholarship(url)
        
        if not result:
            raise HTTPException(status_code=404, detail="Extraction failed")
        
        return {
            "success": True,
            "url": url,
            "content": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Single extraction failed: {str(e)}")

@router.get("/sources")
async def list_official_sources():
    """
    List the official government sources being prioritized.
    """
    try:
        search_service = get_tavily_search()
        return {
            "success": True,
            "official_sources": search_service.official_domains,
            "total_sources": len(search_service.official_domains)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sources: {str(e)}")

@router.post("/extract/structured")
async def extract_structured(request: ExtractionRequest):
    """
    Extract structured scholarship information using LLM.
    This endpoint takes extracted content and converts it to structured JSON.
    """
    try:
        extraction_service = get_llm_extraction()
        result = extraction_service.extract_scholarship(
            content=request.content,
            source_url=request.source_url,
            source_domain=request.source_domain
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Extraction failed"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Structured extraction failed: {str(e)}")

@router.post("/pipeline")
async def full_pipeline(request: SearchRequest):
    """
    Run the full Tavily pipeline: Search → Extract → LLM Extraction → Database Storage → RAG Indexing → Eligibility Check.
    This combines all steps into a single API call.
    Database and Qdrant are optional - pipeline works even if they're unavailable.
    """
    try:
        # Step 1: Search
        search_service = get_tavily_search()
        search_results = search_service.search_scholarships(
            query=request.query,
            profile=request.profile,
            max_results=min(request.max_results, 3)  # Limit to 3 for pipeline
        )
        
        if not search_results:
            return {
                "success": True,
                "query": request.query,
                "search_results": [],
                "extractions": [],
                "message": "No search results found"
            }
        
        # Step 2: Extract content
        urls = [result["url"] for result in search_results]
        extract_service = get_tavily_extract()
        extracted_content = extract_service.extract_scholarship_content(
            urls=urls,
            extract_depth="advanced"
        )
        
        # Step 3: LLM Structured Extraction
        extraction_service = get_llm_extraction()
        structured_extractions = []
        saved_to_db = 0
        
        for extraction in extracted_content:
            if extraction.get("content"):
                result = extraction_service.extract_scholarship(
                    content=extraction["content"],
                    source_url=extraction["url"],
                    source_domain=extraction.get("source_type")
                )
                if result.get("success"):
                    structured_extractions.append(result)
                    
                    # Step 4: Save to PostgreSQL (optional)
                    scholarship_data = result.get("scholarship")
                    if scholarship_data:
                        scholarship_id = db_service.save_scholarship(
                            scholarship_data=scholarship_data,
                            raw_content=extraction.get("content"),
                            content_type=extraction.get("source_type"),
                            extraction_metadata=result.get("extraction_metadata")
                        )
                        
                        if scholarship_id:
                            saved_to_db += 1
                            
                            # Log the extraction
                            db_service.log_extraction(
                                source_url=extraction["url"],
                                extraction_method=result.get("extraction_metadata", {}).get("model_used", "unknown"),
                                success=True,
                                extraction_metadata=result.get("extraction_metadata"),
                                content_length=len(extraction.get("content", "")),
                                tokens_used=result.get("extraction_metadata", {}).get("tokens_used")
                            )
        
        # Step 5: Eligibility Check (if profile provided)
        eligibility_results = []
        if request.profile and structured_extractions:
            scholarships_data = [e.get("scholarship") for e in structured_extractions if e.get("scholarship")]
            if scholarships_data:
                eligibility_results = eligibility_engine_v2.evaluate_multiple_scholarships(
                    scholarships=scholarships_data,
                    user_profile=request.profile
                )
        
        return {
            "success": True,
            "query": request.query,
            "search_results": search_results,
            "extractions_successful": len(extracted_content),
            "structured_extractions": structured_extractions,
            "eligibility_results": eligibility_results,
            "pipeline_summary": {
                "search_results_found": len(search_results),
                "content_extractions": len(extracted_content),
                "structured_extractions": len(structured_extractions),
                "saved_to_database": saved_to_db,
                "eligibility_checked": len(eligibility_results),
                "database_available": db_service._check_available() if hasattr(db_service, '_check_available') else False
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")

@router.post("/save")
async def save_to_database(request: ExtractionRequest):
    """
    Save extracted scholarship data to PostgreSQL.
    This endpoint takes structured extraction data and persists it.
    """
    try:
        extraction_service = get_llm_extraction()
        result = extraction_service.extract_scholarship(
            content=request.content,
            source_url=request.source_url,
            source_domain=request.source_domain
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Extraction failed"))
        
        scholarship_data = result.get("scholarship")
        if scholarship_data:
            scholarship_id = db_service.save_scholarship(
                scholarship_data=scholarship_data,
                raw_content=request.content,
                content_type="webpage",
                extraction_metadata=result.get("extraction_metadata")
            )
            
            # Log the extraction
            db_service.log_extraction(
                source_url=request.source_url,
                extraction_method=result.get("extraction_metadata", {}).get("model_used", "unknown"),
                success=True,
                extraction_metadata=result.get("extraction_metadata"),
                content_length=len(request.content),
                tokens_used=result.get("extraction_metadata", {}).get("tokens_used")
            )
            
            return {
                "success": True,
                "scholarship_id": scholarship_id,
                "scholarship": scholarship_data,
                "message": "Scholarship saved to database successfully"
            }
        
        raise HTTPException(status_code=500, detail="No scholarship data extracted")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database save failed: {str(e)}")

@router.get("/database/scholarships")
async def get_scholarships(limit: int = 50):
    """
    Get all scholarships from the database.
    """
    try:
        scholarships = db_service.get_all_scholarships(limit=limit)
        return {
            "success": True,
            "count": len(scholarships),
            "scholarships": scholarships
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve scholarships: {str(e)}")

@router.get("/database/scholarships/{scholarship_id}")
async def get_scholarship(scholarship_id: int):
    """
    Get a specific scholarship by ID.
    """
    try:
        scholarship = db_service.get_scholarship_by_id(scholarship_id)
        if not scholarship:
            raise HTTPException(status_code=404, detail="Scholarship not found")
        
        return {
            "success": True,
            "scholarship": scholarship
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve scholarship: {str(e)}")

@router.get("/database/search")
async def search_database(
    state: Optional[str] = None,
    category: Optional[str] = None,
    course: Optional[str] = None,
    limit: int = 50
):
    """
    Search scholarships in the database with filters.
    """
    try:
        category_list = category.split(",") if category else None
        course_list = course.split(",") if course else None
        
        scholarships = db_service.search_scholarships(
            state=state,
            category=category_list,
            course=course_list,
            limit=limit
        )
        
        return {
            "success": True,
            "count": len(scholarships),
            "filters": {
                "state": state,
                "category": category_list,
                "course": course_list
            },
            "scholarships": scholarships
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database search failed: {str(e)}")

@router.get("/database/status")
async def database_status():
    """
    Check database connection and status.
    """
    try:
        connection_ok = db_service.test_connection()
        
        if connection_ok:
            # Get count of scholarships
            scholarships = db_service.get_all_scholarships(limit=1000)
            
            return {
                "success": True,
                "database_status": "connected",
                "scholarship_count": len(scholarships),
                "message": "Database is connected and operational"
            }
        else:
            return {
                "success": False,
                "database_status": "disconnected",
                "message": "Could not connect to database"
            }
    except Exception as e:
        return {
            "success": False,
            "database_status": "error",
            "message": str(e)
        }

@router.post("/database/init")
async def initialize_database():
    """
    Initialize database tables.
    This should be called once to set up the database schema.
    """
    try:
        success = db_service.create_tables()
        if success:
            return {
                "success": True,
                "message": "Database tables created successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to create database tables")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database initialization failed: {str(e)}")

# Eligibility Engine endpoints

class EligibilityRequest(BaseModel):
    """Request model for eligibility checking."""
    scholarships: List[Dict[str, Any]]
    user_profile: Dict[str, Any]

@router.post("/eligibility/check")
async def check_eligibility(request: EligibilityRequest):
    """
    Check eligibility for scholarships using the deterministic eligibility engine.
    Returns MATCH/MISMATCH/NOT_SPECIFIED for each field.
    """
    try:
        results = eligibility_engine_v2.evaluate_multiple_scholarships(
            scholarships=request.scholarships,
            user_profile=request.user_profile
        )
        
        return {
            "success": True,
            "scholarships_evaluated": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eligibility check failed: {str(e)}")

@router.post("/eligibility/check-single")
async def check_single_eligibility(scholarship: Dict[str, Any], user_profile: Dict[str, Any]):
    """
    Check eligibility for a single scholarship.
    """
    try:
        result = eligibility_engine_v2.evaluate_eligibility(
            scholarship_data=scholarship,
            user_profile=user_profile
        )
        
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Eligibility check failed: {str(e)}")

# LangGraph Orchestration endpoints

@router.post("/orchestrate")
async def orchestrate_scholarship_search(request: SearchRequest):
    """
    Simplified endpoint that returns raw Tavily search results directly.
    Skip extraction and just return the search results with basic metadata.
    """
    try:
        print(f"[SIMPLIFIED ORCHESTRATION] Request received: query={request.query}, max_results={request.max_results}")
        
        # Direct Tavily search
        from app.services.tavily_search import TavilySearchService
        tavily_search = TavilySearchService()
        
        results = tavily_search.search_scholarships(
            query=request.query,
            profile=request.profile,
            max_results=request.max_results
        )
        
        print(f"[SIMPLIFIED ORCHESTRATION] Tavily returned {len(results)} results")
        
        # Return raw results without strict filtering
        final_results = []
        for result in results:
            snippet = result.get("snippet", "Visit source for details")
            title = result.get("title", "Scholarship")
            
            if snippet and len(snippet) > 300:
                snippet = snippet[:300] + "..."
            
            scholarship_data = {
                "scholarship_name": title,
                "provider": result.get("source", "Unknown"),
                "benefits": snippet,
                "deadline": "Visit source for deadline",
                "source_url": result.get("url"),
                "is_official": result.get("is_official", False),
                "eligibility": {
                    "overall_status": "NEEDS_MORE_INFORMATION",
                    "explanation": "Visit source for eligibility details"
                }
            }
            final_results.append(scholarship_data)
        
        print(f"[SIMPLIFIED ORCHESTRATION] Returning {len(final_results)} final results")
        
        return {
            "success": True,
            "query": request.query,
            "results": final_results,
            "search_results": results,
            "pipeline_summary": {
                "search_results": len(results),
                "extraction_skipped": True,
                "using_raw_search": True
            }
        }
        
    except Exception as e:
        print(f"[SIMPLIFIED ORCHESTRATION] Error: {e}")
        raise HTTPException(status_code=500, detail=f"Orchestration failed: {str(e)}")

class TestExtractionRequest(BaseModel):
    content: str
    source_url: str = "https://example.com"

@router.post("/test-extraction")
async def test_extraction(request: TestExtractionRequest):
    """
    Test the LLM extraction service directly to see which provider is being used.
    """
    try:
        extraction_service = get_llm_extraction()
        print(f"Testing extraction service directly...")
        result = extraction_service.extract_scholarship(
            content=request.content,
            source_url=request.source_url,
            source_domain="test"
        )
        print(f"Extraction test result: success={result.get('success')}")
        if result.get("extraction_metadata"):
            print(f"Extraction metadata: {result['extraction_metadata']}")
        return result
    except Exception as e:
        print(f"Test extraction error: {e}")
        raise HTTPException(status_code=500, detail=f"Test extraction failed: {str(e)}")