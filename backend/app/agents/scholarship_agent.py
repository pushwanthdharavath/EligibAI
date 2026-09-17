from typing import TypedDict, Annotated, Sequence, List, Dict, Any, Optional, Union
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import operator
# Old tool-based agent - deprecated in favor of LangGraph orchestrator
# from app.services.scholarship_dataset import ScholarshipDataset
from app.services.eligibility_engine import EligibilityEngine
from app.services.rag_pipeline import RAGPipeline
import asyncio

# Define the agent state
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_profile: Dict[str, Any]
    search_results: List[Dict[str, Any]]
    eligibility_results: List[Dict[str, Any]]

# Initialize services
# scholarship_dataset = ScholarshipDataset()  # Deprecated
eligibility_engine = EligibilityEngine()

# Define tools for the agent
# NOTE: These tools are deprecated in favor of the LangGraph orchestrator
# They are commented out to prevent errors from removed static dataset

# @tool
# def search_scholarships_by_state(state: str) -> str:
#     """Search for scholarships available in a specific state."""
#     scholarships = scholarship_dataset.filter_by_state(state)
#     return f"Found {len(scholarships)} scholarships available in {state}: " + \
#            ", ".join([s.scheme_name for s in scholarships])

# @tool
# def search_scholarships_by_education(education: str) -> str:
#     """Search for scholarships for a specific education level."""
#     scholarships = scholarship_dataset.filter_by_education(education)
#     return f"Found {len(scholarships)} scholarships for {education}: " + \
#            ", ".join([s.scheme_name for s in scholarships])

# @tool
# def search_scholarships_by_category(category: str) -> str:
#     """Search for scholarships for a specific category."""
#     scholarships = scholarship_dataset.filter_by_category(category)
#     return f"Found {len(scholarships)} scholarships for {category}: " + \
#            ", ".join([s.scheme_name for s in scholarships])

# @tool
# def get_scholarship_details(scholarship_id: str) -> str:
#     """Get detailed information about a specific scholarship."""
#     scholarship = scholarship_dataset.get_scholarship_by_id(scholarship_id)
#     if not scholarship:
#         return f"Scholarship with ID {scholarship_id} not found"
#     
#     return f"""
#     Scholarship: {scholarship.scheme_name}
#     Provider: {scholarship.provider}
#     State: {scholarship.state or 'All India'}
#     Benefit: {scholarship.benefit}
#     Deadline: {scholarship.deadline}
#     Education: {', '.join(scholarship.eligibility.education) if scholarship.eligibility.education else 'Not specified'}
#     Income Limit: {scholarship.eligibility.income_max if scholarship.eligibility.income_max else 'Not specified'}
#     Category: {', '.join(scholarship.eligibility.category) if scholarship.eligibility.category else 'Not specified'}
#     Source: {scholarship.source_url}
#     """

# @tool
# def check_eligibility_for_scholarship(scholarship_id: str, user_profile: Dict[str, Any]) -> str:
#     """Check if a user is eligible for a specific scholarship."""
#     scholarship = scholarship_dataset.get_scholarship_by_id(scholarship_id)
#     if not scholarship:
#         return f"Scholarship with ID {scholarship_id} not found"
#     
#     # Create a simple profile dict for the eligibility engine
#     # The eligibility engine expects certain fields, we'll map them
#     profile_dict = {
#         "fullName": user_profile.get("fullName", "Student"),
#         "age": str(user_profile.get("age", "20")),
#         "gender": user_profile.get("gender", "Male"),
#         "state": user_profile.get("state", ""),
#         "district": user_profile.get("district", ""),
#         "category": user_profile.get("category", "General"),
#         "course": user_profile.get("course", ""),
#         "yearOfStudy": user_profile.get("yearOfStudy", ""),
#         "annualFamilyIncome": str(user_profile.get("annualFamilyIncome", "0")),
#         "disabilityStatus": user_profile.get("disabilityStatus", "No"),
#         "searchQuery": "Find scholarships"
#     }
#     
#     # Check eligibility
#     evaluation = eligibility_engine.evaluate_eligibility(scholarship, profile_dict)
#     
#     return f"""
#     Eligibility Status for {scholarship.scheme_name}: {evaluation['overall_status']}
#     Reasons: {', '.join(evaluation['reasons'])}
#     """

# @tool
# def search_with_rag(query: str, state: str = None, education: str = None) -> str:
#     """Search for scholarships using semantic search with RAG."""
#     global rag_pipeline
#     if rag_pipeline is None:
#         from app.services.rag_pipeline import RAGPipeline
#         rag_pipeline = RAGPipeline()
#     
#     filters = {}
#     if state:
#         filters["state"] = state
#     if education:
#         filters["education"] = education
#     
#     results = rag_pipeline.search(query=query, top_k=5, filters=filters if filters else None)
#     
#     if not results:
#         return "No relevant scholarships found using semantic search."
#     
#     summary = f"Found {len(results)} relevant scholarships using semantic search:\n"
#     for i, result in enumerate(results, 1):
#         metadata = result["metadata"]
#         summary += f"{i}. {metadata.get('scheme_name', 'Unknown')} - Relevance: {result['combined_score']:.2f}\n"
#     
#     return summary

# List of tools - deprecated
tools = []  # Empty - use LangGraph orchestrator instead

# Create tool node
tool_node = ToolNode(tools)

def should_continue(state: AgentState) -> str:
    """Determine whether to continue using tools or end."""
    messages = state["messages"]
    last_message = messages[-1]
    
    # If the last message is a tool call, continue to tools
    if last_message.tool_calls:
        return "tools"
    
    # Otherwise, end
    return END

def call_model(state: AgentState, config: Dict[str, Any]):
    """Call the language model to decide which tools to use."""
    messages = state["messages"]
    
    # Import LLM (using a simple setup for now)
    from langchain_openai import ChatOpenAI
    from app.core.config import settings
    
    if not settings.OPENAI_API_KEY:
        # Return a simple response if no API key
        return {
            "messages": [
                AIMessage(
                    content="I don't have access to an LLM for autonomous tool calling. Please provide an OpenAI API key to enable the full agent capabilities."
                )
            ]
            + messages
        }
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=settings.OPENAI_API_KEY)
    llm_with_tools = llm.bind_tools(tools)
    
    response = llm_with_tools.invoke(messages)
    
    return {
        "messages": [response]
    }

def create_scholarship_agent():
    """Create the LangGraph scholarship agent."""
    
    # Define the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END
        }
    )
    
    # Add edge from tools back to agent
    workflow.add_edge("tools", "agent")
    
    # Compile the graph
    app = workflow.compile()
    
    return app

# Global agent instance
scholarship_agent = None
rag_pipeline = None

def get_scholarship_agent():
    """Get or create the scholarship agent."""
    global scholarship_agent
    if scholarship_agent is None:
        scholarship_agent = create_scholarship_agent()
    return scholarship_agent

def run_agent_query(query: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the scholarship agent with a query and user profile.
    
    NOTE: This function is deprecated. The old tool-based agent has been replaced
    by the LangGraph orchestrator. Use /api/live-search or /api/tavily/orchestrate
    instead for live web search and eligibility checking.
    """
    return {
        "query": query,
        "response": "This endpoint is deprecated. Please use /api/live-search for live web scholarship discovery with eligibility checking.",
        "tool_calls": [],
        "steps": 0,
        "deprecated": True
    }
