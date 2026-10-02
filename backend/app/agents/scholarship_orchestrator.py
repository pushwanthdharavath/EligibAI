from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from datetime import datetime

from app.services.tavily_search import TavilySearchService
from app.services.tavily_extract import TavilyExtractService
from app.services.llm_extraction import LLMExtractionService
from app.services.database import db_service
from app.services.eligibility_engine_v2 import eligibility_engine_v2


class OrchestratorState(TypedDict):
    """State for the scholarship discovery orchestration graph."""
    
    # Input
    query: str
    user_profile: Optional[Dict[str, Any]]
    max_results: int
    
    # Query Analysis
    analyzed_query: Optional[str]
    search_keywords: Optional[List[str]]
    
    # Tavily Search
    search_results: Optional[List[Dict[str, Any]]]
    search_error: Optional[str]
    
    # Tavily Extract
    extracted_content: Optional[List[Dict[str, Any]]]
    extraction_error: Optional[str]
    
    # LLM Extraction
    structured_scholarships: Optional[List[Dict[str, Any]]]
    extraction_metadata: Optional[List[Dict[str, Any]]]
    
    # Database Storage
    saved_scholarship_ids: Optional[List[int]]
    database_status: Optional[str]
    
    # Eligibility Checking
    eligibility_results: Optional[List[Dict[str, Any]]]
    
    # Evidence Generation
    final_results: Optional[List[Dict[str, Any]]]
    
    # Metadata
    start_time: str
    end_time: str
    error: Optional[str]


class ScholarshipOrchestrator:
    """
    LangGraph-based orchestration for the scholarship discovery pipeline.
    Replaces the old tool-based agent with a proper workflow graph.
    """
    
    def __init__(self):
        self.tavily_search = TavilySearchService()
        self.tavily_extract = TavilyExtractService()
        self.llm_extraction = LLMExtractionService(force_mock=False)  # Use real LLM (prefer OpenAI if Gemini unavailable)
        self.eligibility_engine = eligibility_engine_v2
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(OrchestratorState)
        
        # Add nodes
        workflow.add_node("query_analysis", self.query_analysis_node)
        workflow.add_node("tavily_search", self.tavily_search_node)
        workflow.add_node("tavily_extract", self.tavily_extract_node)
        workflow.add_node("llm_extraction", self.llm_extraction_node)
        workflow.add_node("database_storage", self.database_storage_node)
        workflow.add_node("eligibility_checking", self.eligibility_checking_node)
        workflow.add_node("evidence_generation", self.evidence_generation_node)
        
        # Define edges (linear flow)
        workflow.set_entry_point("query_analysis")
        workflow.add_edge("query_analysis", "tavily_search")
        workflow.add_edge("tavily_search", "tavily_extract")
        workflow.add_edge("tavily_extract", "llm_extraction")
        workflow.add_edge("llm_extraction", "database_storage")
        workflow.add_edge("database_storage", "eligibility_checking")
        workflow.add_edge("eligibility_checking", "evidence_generation")
        workflow.add_edge("evidence_generation", END)
        
        return workflow.compile()
    
    def query_analysis_node(self, state: OrchestratorState) -> OrchestratorState:
        """Analyze the user's query and extract search keywords."""
        try:
            query = state["query"]
            profile = state.get("user_profile", {})
            
            # Build search keywords from query and profile
            keywords = [query.lower()]
            
            if profile:
                if profile.get("state"):
                    keywords.append(profile["state"].lower())
                if profile.get("category"):
                    keywords.append(profile["category"].lower())
                if profile.get("course"):
                    keywords.append(profile["course"].lower())
            
            # Remove duplicates
            keywords = list(set(keywords))
            
            state["analyzed_query"] = query
            state["search_keywords"] = keywords
            
            print(f"Query Analysis: {query} -> Keywords: {keywords}")
            
        except Exception as e:
            state["error"] = f"Query analysis failed: {str(e)}"
            print(f"Query analysis error: {e}")
        
        return state
    
    def tavily_search_node(self, state: OrchestratorState) -> OrchestratorState:
        """Search for scholarships using Tavily."""
        try:
            query = state["analyzed_query"]
            profile = state.get("user_profile")
            max_results = state.get("max_results", 5)
            
            print(f"[ORCHESTRATOR] Tavily Search Node - Query: {query}, Max: {max_results}")
            
            search_results = self.tavily_search.search_scholarships(
                query=query,
                profile=profile,
                max_results=max_results
            )
            
            state["search_results"] = search_results
            state["search_error"] = None
            
            print(f"[ORCHESTRATOR] Tavily Search: Found {len(search_results)} results")
            
        except Exception as e:
            state["search_results"] = []
            state["search_error"] = str(e)
            print(f"[ORCHESTRATOR] Tavily search error: {e}")
        
        return state
    
    def tavily_extract_node(self, state: OrchestratorState) -> OrchestratorState:
        """Extract content from discovered URLs."""
        try:
            search_results = state.get("search_results", [])
            
            if not search_results:
                state["extracted_content"] = []
                state["extraction_error"] = "No search results to extract"
                return state
            
            urls = [result["url"] for result in search_results]
            
            extracted_content = self.tavily_extract.extract_scholarship_content(
                urls=urls,
                extract_depth="advanced"
            )
            
            state["extracted_content"] = extracted_content
            state["extraction_error"] = None
            
            print(f"Tavily Extract: Extracted {len(extracted_content)} URLs")
            
        except Exception as e:
            state["extracted_content"] = []
            state["extraction_error"] = str(e)
            print(f"Tavily extract error: {e}")
        
        return state
    
    def llm_extraction_node(self, state: OrchestratorState) -> OrchestratorState:
        """Convert extracted content to structured scholarship data."""
        try:
            extracted_content = state.get("extracted_content", [])
            search_results = state.get("search_results", [])
            
            print(f"[ORCHESTRATOR] LLM Extraction Node - Extracted content: {len(extracted_content)}, Search results: {len(search_results)}")
            
            if not extracted_content:
                state["structured_scholarships"] = []
                state["extraction_metadata"] = []
                print(f"[ORCHESTRATOR] No extracted content to process")
                return state
            
            structured_scholarships = []
            extraction_metadata = []
            skipped_count = 0
            
            for i, extraction in enumerate(extracted_content):
                if extraction.get("content"):
                    result = self.llm_extraction.extract_scholarship(
                        content=extraction["content"],
                        source_url=extraction["url"],
                        source_domain=extraction.get("source_type")
                    )
                    
                    if result.get("success"):
                        scholarship = result.get("scholarship")
                        # Skip scholarships with no name (likely webpage metadata)
                        if not scholarship.get("scholarship_name"):
                            print(f"[ORCHESTRATOR] Skipping extraction with no scholarship name from {extraction['url']}")
                            skipped_count += 1
                            continue
                        # Add extraction method indicator
                        extraction_meta = result.get("extraction_metadata", {})
                        model_used = extraction_meta.get("model_used", "unknown")
                        if model_used == "gemini-3.6-flash":
                            scholarship["extraction_method"] = "gemini"
                            scholarship["extraction_confidence"] = "high"
                        else:
                            scholarship["extraction_method"] = "mock"
                            scholarship["extraction_confidence"] = "low"
                        # Preserve is_official status from search results
                        if i < len(search_results):
                            scholarship["is_official"] = search_results[i].get("is_official", True)
                        structured_scholarships.append(scholarship)
                        extraction_metadata.append(extraction_meta)
                    else:
                        print(f"[ORCHESTRATOR] Extraction failed for {extraction['url']}: {result.get('error')}")
                        skipped_count += 1
            
            state["structured_scholarships"] = structured_scholarships
            state["extraction_metadata"] = extraction_metadata
            
            print(f"[ORCHESTRATOR] LLM Extraction: Structured {len(structured_scholarships)} scholarships, Skipped {skipped_count}")
            
        except Exception as e:
            state["structured_scholarships"] = []
            state["extraction_metadata"] = []
            print(f"[ORCHESTRATOR] LLM extraction error: {e}")
        
        return state
    
    def database_storage_node(self, state: OrchestratorState) -> OrchestratorState:
        """Save structured scholarships to PostgreSQL."""
        # Skip database storage entirely since PostgreSQL is not running
        state["saved_scholarship_ids"] = []
        state["database_status"] = "Database storage disabled"
        print("[ORCHESTRATOR] Database storage skipped (PostgreSQL not available)")
        return state
    
    def eligibility_checking_node(self, state: OrchestratorState) -> OrchestratorState:
        """Check eligibility for scholarships."""
        try:
            structured_scholarships = state.get("structured_scholarships", [])
            profile = state.get("user_profile")
            
            if not structured_scholarships or not profile:
                state["eligibility_results"] = []
                return state
            
            eligibility_results = self.eligibility_engine.evaluate_multiple_scholarships(
                scholarships=structured_scholarships,
                user_profile=profile
            )
            
            state["eligibility_results"] = eligibility_results
            
            print(f"Eligibility Checking: Evaluated {len(eligibility_results)} scholarships")
            
        except Exception as e:
            state["eligibility_results"] = []
            print(f"Eligibility checking error: {e}")
        
        return state
    
    def evidence_generation_node(self, state: OrchestratorState) -> OrchestratorState:
        """Generate final results with evidence."""
        try:
            eligibility_results = state.get("eligibility_results", [])
            structured_scholarships = state.get("structured_scholarships", [])
            extraction_metadata = state.get("extraction_metadata", [])
            
            print(f"[ORCHESTRATOR] Evidence Generation - Eligibility results: {len(eligibility_results)}, Structured scholarships: {len(structured_scholarships)}")
            
            # Combine eligibility results with scholarship data
            final_results = []
            
            for i, eligibility in enumerate(eligibility_results):
                if i < len(structured_scholarships):
                    scholarship_data = structured_scholarships[i]
                    final_result = {
                        **scholarship_data,
                        "eligibility": eligibility,
                        "pipeline_source": "langgraph_orchestrator",
                        "is_official": scholarship_data.get("is_official", True)  # Preserve official status
                    }
                    # Add extraction metadata if available
                    if i < len(extraction_metadata) and extraction_metadata[i]:
                        final_result["extraction_metadata"] = extraction_metadata[i]
                    final_results.append(final_result)
                    print(f"[ORCHESTRATOR] Final result {i}: {scholarship_data.get('scholarship_name')} - Status: {eligibility.get('overall_status')}")
            
            state["final_results"] = final_results
            state["end_time"] = datetime.now().isoformat()
            
            print(f"[ORCHESTRATOR] Evidence Generation: Generated {len(final_results)} final results")
            
        except Exception as e:
            state["final_results"] = []
            state["error"] = f"Evidence generation failed: {str(e)}"
            print(f"[ORCHESTRATOR] Evidence generation error: {e}")
        
        return state
    
    def run(self, query: str, user_profile: Optional[Dict[str, Any]] = None, 
            max_results: int = 5) -> Dict[str, Any]:
        """
        Run the complete orchestration pipeline.
        
        Args:
            query: User's natural language query
            user_profile: User's profile data
            max_results: Maximum number of search results
            
        Returns:
            Complete pipeline results
        """
        # Initialize state
        initial_state: OrchestratorState = {
            "query": query,
            "user_profile": user_profile,
            "max_results": max_results,
            "analyzed_query": None,
            "search_keywords": None,
            "search_results": None,
            "search_error": None,
            "extracted_content": None,
            "extraction_error": None,
            "structured_scholarships": None,
            "extraction_metadata": None,
            "saved_scholarship_ids": None,
            "database_status": None,
            "eligibility_results": None,
            "final_results": None,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "error": None
        }
        
        # Run the graph
        try:
            final_state = self.graph.invoke(initial_state)
            
            return {
                "success": True,
                "query": query,
                "results": final_state["final_results"],
                "search_results": final_state.get("search_results", []),  # Include raw search results
                "pipeline_summary": {
                    "search_results": len(final_state.get("search_results", [])),
                    "extracted_content": len(final_state.get("extracted_content", [])),
                    "structured_scholarships": len(final_state.get("structured_scholarships", [])),
                    "saved_to_database": len(final_state.get("saved_scholarship_ids", [])),
                    "eligibility_checked": len(final_state.get("eligibility_results", [])),
                    "final_results": len(final_state.get("final_results", []))
                },
                "timing": {
                    "start_time": final_state["start_time"],
                    "end_time": final_state["end_time"]
                },
                "errors": {
                    "search_error": final_state.get("search_error"),
                    "extraction_error": final_state.get("extraction_error"),
                    "database_status": final_state.get("database_status"),
                    "error": final_state.get("error")
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query
            }


# Global orchestrator instance
scholarship_orchestrator = ScholarshipOrchestrator()
