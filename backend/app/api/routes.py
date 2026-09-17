from fastapi import APIRouter, HTTPException
from typing import List, Optional
import time
from datetime import datetime
from pydantic import BaseModel
from app.models.eligibility import UserProfile, EligibilityResponse, ScholarshipResult
from app.services.eligibility_engine import EligibilityEngine
from app.services.eligibility_engine_v2 import eligibility_engine_v2
# Static dataset removed - using live web search via LangGraph orchestrator
# from app.services.scholarship_dataset import ScholarshipDataset
from app.services.llm_service import LLMService
# Old agent deprecated - using LangGraph orchestrator instead
# from app.agents.scholarship_agent import run_agent_query
import json
from pathlib import Path

router = APIRouter()

# Initialize services
eligibility_engine = EligibilityEngine()
# Static dataset removed - using live web search via LangGraph orchestrator
# scholarship_dataset = ScholarshipDataset()
llm_service = LLMService()

class SearchRequest(BaseModel):
    query: str
    state: Optional[str] = None
    education: Optional[str] = None
    category: Optional[str] = None
    top_k: int = 10

class IndexResponse(BaseModel):
    status: str
    message: str
    chunks_indexed: Optional[int] = None

class SearchResponse(BaseModel):
    query: str
    results: List[dict]
    total_found: int

class FollowupRequest(BaseModel):
    question: str
    user_profile: UserProfile
    context: Optional[List[dict]] = None

class AgentRequest(BaseModel):
    query: str
    user_profile: UserProfile

class AgentResponse(BaseModel):
    query: str
    response: str
    tool_calls: List[str]
    steps: int

class SearchRequest(BaseModel):
    query: str
    user_profile: UserProfile

@router.post("/index", response_model=IndexResponse)
async def index_scholarships():
    """
    Index all scholarships into the Qdrant vector database for RAG search.
    
    NOTE: This endpoint has been deprecated. Static dataset has been removed.
    For RAG functionality with live web search, use the LangGraph orchestrator
    which handles vector indexing automatically when PostgreSQL and Qdrant are available.
    """
    return IndexResponse(
        status="deprecated",
        message="Static dataset indexing deprecated. Use /api/live-search for live web discovery with automatic RAG indexing.",
        chunks_indexed=0
    )

@router.post("/search", response_model=SearchResponse)
async def search_scholarships(request: SearchRequest):
    """
    Search for scholarships using RAG pipeline with semantic search and reranking.
    """
    global rag_pipeline
    try:
        # Initialize RAG pipeline if not already initialized
        if rag_pipeline is None:
            from app.services.rag_pipeline import RAGPipeline
            rag_pipeline = RAGPipeline()
        
        filters = {}
        if request.state:
            filters["state"] = request.state
        if request.education:
            filters["education"] = request.education
        if request.category:
            filters["category"] = request.category
        
        results = rag_pipeline.search(
            query=request.query,
            top_k=request.top_k,
            filters=filters if filters else None
        )
        
        return SearchResponse(
            query=request.query,
            results=results,
            total_found=len(results)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/eligibility", response_model=EligibilityResponse)
async def check_eligibility(profile: UserProfile, use_llm: bool = False):
    """
    Check scholarship eligibility based on user profile.
    
    NOTE: This endpoint has been updated to use live web search.
    Static dataset has been removed. For eligibility checking with real-time
    scholarship discovery, use /api/live-search instead.
    """
    start_time = time.time()
    
    try:
        # Redirect to live search which includes eligibility checking
        from app.agents.scholarship_orchestrator import scholarship_orchestrator
        
        # Convert UserProfile to dict format expected by orchestrator
        profile_dict = {
            "name": profile.fullName,
            "age": profile.age,
            "gender": profile.gender,
            "state": profile.state,
            "district": profile.district,
            "category": profile.category,
            "course": profile.course,
            "yearOfStudy": profile.yearOfStudy,
            "annualFamilyIncome": profile.annualFamilyIncome,
            "disabilityStatus": profile.disabilityStatus
        }
        
        # Run the LangGraph orchestrator with a default query
        result = scholarship_orchestrator.run(
            query=f"Scholarships for {profile.course} students in {profile.state}",
            user_profile=profile_dict,
            max_results=10
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Orchestration failed"))
        
        # Convert results to ScholarshipResult format
        scholarship_results = []
        for scholarship_result in result.get("results", []):
            eligibility = scholarship_result.get("eligibility", {})
            
            scholarship_result_formatted = ScholarshipResult(
                name=scholarship_result.get("scholarship_name", "Unknown"),
                status=eligibility.get("overall_status", "UNKNOWN"),
                reasons=[eligibility.get("explanation", "")],
                benefit=scholarship_result.get("benefits", ""),
                deadline=scholarship_result.get("deadline", ""),
                sourceUrl=scholarship_result.get("source_url", ""),
                provider=scholarship_result.get("provider", "")
            )
            scholarship_results.append(scholarship_result_formatted)
        
        processing_time = time.time() - start_time
        
        return EligibilityResponse(
            scholarships=scholarship_results,
            profile=profile.model_dump(),
            totalFound=len(scholarship_results),
            processingTime=processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/followup")
async def answer_followup(request: FollowupRequest):
    """
    Answer follow-up questions about scholarships using RAG context and LLM.
    """
    global rag_pipeline
    try:
        # Initialize RAG pipeline if not already initialized
        if rag_pipeline is None:
            from app.services.rag_pipeline import RAGPipeline
            rag_pipeline = RAGPipeline()
        
        # If context is not provided, search for relevant information
        if not request.context:
            # Build search query from user profile
            search_query = f"{request.question} {request.user_profile.course} {request.user_profile.state} {request.user_profile.category}"
            
            context = rag_pipeline.search(
                query=search_query,
                top_k=5,
                filters={
                    "state": request.user_profile.state,
                    "education": request.user_profile.course
                }
            )
        else:
            context = request.context
        
        # Generate answer using LLM
        answer = llm_service.answer_followup_question(
            question=request.question,
            context=context,
            user_profile=request.user_profile.model_dump()
        )
        
        return {
            "question": request.question,
            "answer": answer,
            "context_used": len(context) if context else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Follow-up failed: {str(e)}")

@router.post("/agent", response_model=AgentResponse)
async def run_agent(request: AgentRequest):
    """
    Run the LangGraph scholarship agent to autonomously search for scholarships.
    
    NOTE: This endpoint is deprecated. The old tool-based agent has been replaced
    by the LangGraph orchestrator. Use /api/live-search for live web discovery.
    """
    return AgentResponse(
        query=request.query,
        response="This endpoint is deprecated. Please use /api/live-search for live web scholarship discovery with eligibility checking.",
        tool_calls=[],
        steps=0
    )

@router.post("/live-search")
async def live_search(request: SearchRequest):
    """
    Search official sources in real-time using the new LangGraph orchestrator.
    This replaces the old web search with the Tavily+LLM pipeline.
    """
    try:
        from app.agents.scholarship_orchestrator import scholarship_orchestrator
        
        # Convert UserProfile to dict format expected by orchestrator
        profile_dict = {
            "name": request.user_profile.fullName,
            "age": request.user_profile.age,
            "gender": request.user_profile.gender,
            "state": request.user_profile.state,
            "district": request.user_profile.district,
            "category": request.user_profile.category,
            "course": request.user_profile.course,
            "yearOfStudy": request.user_profile.yearOfStudy,
            "annualFamilyIncome": request.user_profile.annualFamilyIncome,
            "disabilityStatus": request.user_profile.disabilityStatus
        }
        
        # Run the LangGraph orchestrator
        result = scholarship_orchestrator.run(
            query=request.query,
            user_profile=profile_dict,
            max_results=5
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Orchestration failed"))
        
        # Format results for frontend compatibility
        formatted_results = []
        for scholarship_result in result.get("results", []):
            eligibility = scholarship_result.get("eligibility", {})
            
            formatted_results.append({
                "title": scholarship_result.get("scholarship_name", "Unknown Scholarship"),
                "source": "Official Government Source",
                "source_url": scholarship_result.get("source_url", ""),
                "description": scholarship_result.get("benefits", ""),
                "deadline": scholarship_result.get("deadline", ""),
                "eligibility_status": eligibility.get("overall_status", "UNKNOWN"),
                "reasons": [eligibility.get("explanation", "")],
                "field_comparisons": eligibility.get("field_comparisons", []),
                "evidence": eligibility.get("evidence", {}),
                "scraped_at": scholarship_result.get("extraction_timestamp", datetime.now().isoformat()),
                "pipeline_source": scholarship_result.get("pipeline_source", "unknown")
            })
        
        return {
            "success": True,
            "query": request.query,
            "results": formatted_results,
            "count": len(formatted_results),
            "pipeline_summary": result.get("pipeline_summary", {}),
            "timing": result.get("timing", {})
        }
        
    except Exception as e:
        print(f"Live search error: {e}")
        raise HTTPException(status_code=500, detail=f"Live search failed: {str(e)}")