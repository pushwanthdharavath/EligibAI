from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class EvaluationResponse(BaseModel):
    status: str
    message: str
    eligibility_results: Optional[dict] = None
    report: Optional[str] = None

@router.post("/run", response_model=EvaluationResponse)
async def run_evaluation():
    """
    Run complete system evaluation including eligibility engine.
    """
    try:
        from app.services.evaluation import run_full_evaluation
        
        results = run_full_evaluation()
        
        return EvaluationResponse(
            status="success",
            message="Evaluation completed successfully",
            eligibility_results=results.get("eligibility_results"),
            report=results.get("report")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")

@router.get("/rag-status")
async def get_rag_evaluation_status():
    """
    Check if RAGAS evaluation is available.
    """
    try:
        from app.services.evaluation import RAGAS_AVAILABLE
        
        return {
            "ragas_available": RAGAS_AVAILABLE,
            "message": "RAGAS evaluation is available" if RAGAS_AVAILABLE else "RAGAS not available, will use fallback metrics"
        }
    except ImportError:
        return {
            "ragas_available": False,
            "message": "RAGAS evaluation not available"
        }