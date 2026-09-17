from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import json
from pathlib import Path

router = APIRouter()

class FineTuningRequest(BaseModel):
    base_model: str = "Qwen/Qwen2.5-3B-Instruct"
    output_dir: str = "./fine_tuned_scholarship_model"
    num_epochs: int = 3
    batch_size: int = 4
    learning_rate: float = 2e-4

class FineTuningResponse(BaseModel):
    status: str
    message: str
    output_dir: Optional[str] = None

@router.post("/start", response_model=FineTuningResponse)
async def start_fine_tuning(request: FineTuningRequest):
    """
    Start QLoRA fine-tuning process.
    Note: This requires GPU and can take significant time.
    """
    try:
        # Load training data
        training_data_path = Path(__file__).parent.parent.parent / "data" / "scholarships.json"
        
        if not training_data_path.exists():
            return FineTuningResponse(
                status="error",
                message="Training data not found. Please ensure scholarships.json exists in data/ directory."
            )
        
        with open(training_data_path, 'r') as f:
            training_data = json.load(f)
        
        # For now, return a message since actual training requires GPU
        # In production, this would trigger a background training job
        return FineTuningResponse(
            status="info",
            message=f"Fine-tuning configured for {len(training_data)} examples. To run actual training, execute: python -m app.services.fine_tuning (requires GPU)",
            output_dir=request.output_dir
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fine-tuning setup failed: {str(e)}")

@router.get("/status")
async def get_fine_tuning_status():
    """
    Check if a fine-tuned model exists and is available.
    """
    model_path = Path("./fine_tuned_scholarship_model")
    
    if model_path.exists():
        return {
            "status": "available",
            "model_path": str(model_path),
            "message": "Fine-tuned model is available for use"
        }
    else:
        return {
            "status": "not_available",
            "model_path": None,
            "message": "No fine-tuned model found. Use POST /start to begin fine-tuning."
        }