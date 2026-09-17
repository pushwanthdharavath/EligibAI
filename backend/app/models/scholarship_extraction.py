from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ScholarshipExtraction(BaseModel):
    """Structured schema for extracted scholarship information."""
    
    # Basic Information
    scholarship_name: str = Field(description="Name of the scholarship scheme")
    provider: Optional[str] = Field(default=None, description="Government department or organization providing the scholarship")
    
    # Eligibility - Demographics
    state: Optional[str] = Field(default=None, description="State or region where scholarship is applicable")
    district: Optional[List[str]] = Field(default=None, description="Specific districts if applicable")
    category: Optional[List[str]] = Field(default=None, description="Categories: SC, ST, OBC, EBC, General, Minority, Disabled, etc.")
    gender: Optional[str] = Field(default=None, description="Gender requirement: Male, Female, or All")
    age_limit: Optional[Dict[str, Any]] = Field(default=None, description="Age limits, e.g., {'min': 18, 'max': 30}")
    
    # Eligibility - Education
    course: Optional[List[str]] = Field(default=None, description="Eligible courses: B.Tech, B.E., M.Tech, etc.")
    education_level: Optional[List[str]] = Field(default=None, description="Education level: Undergraduate, Postgraduate, Diploma")
    year_of_study: Optional[List[str]] = Field(default=None, description="Year of study: 1st Year, 2nd Year, etc.")
    academic_requirements: Optional[str] = Field(default=None, description="Minimum marks, percentage, or academic criteria")
    
    # Eligibility - Financial
    income_limit: Optional[Dict[str, Any]] = Field(default=None, description="Income limits, e.g., {'max': 200000, 'unit': 'INR per annum'}")
    
    # Eligibility - Other
    disability_required: Optional[bool] = Field(default=None, description="Whether disability is required")
    institution_requirements: Optional[str] = Field(default=None, description="Specific institution or college requirements")
    single_child: Optional[bool] = Field(default=None, description="Whether single child status is required")
    
    # Benefits
    benefits: Optional[str] = Field(default=None, description="Financial benefits, coverage, and support provided")
    amount: Optional[str] = Field(default=None, description="Specific scholarship amount or range")
    
    # Application Information
    deadline: Optional[str] = Field(default=None, description="Application deadline date")
    application_url: Optional[str] = Field(default=None, description="Direct application URL if available")
    application_process: Optional[str] = Field(default=None, description="Step-by-step application process")
    required_documents: Optional[List[str]] = Field(default=None, description="List of required documents")
    
    # Source Information
    source_url: str = Field(description="Original source URL where this information was extracted")
    source_domain: Optional[str] = Field(default=None, description="Domain of the source")
    extraction_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    # Evidence and Confidence
    evidence_snippets: Optional[List[str]] = Field(default=None, description="Key text snippets from source that support the extraction")
    extraction_confidence: Optional[str] = Field(default="medium", description="Confidence level: high, medium, low")
    missing_fields: Optional[List[str]] = Field(default=None, description="Fields that could not be extracted")
    
    class Config:
        json_schema_extra = {
            "example": {
                "scholarship_name": "Telangana Post Matric Scholarship",
                "provider": "Telangana State Government",
                "state": "Telangana",
                "category": ["SC", "ST", "BC", "Disabled"],
                "course": ["B.Tech", "B.E.", "Diploma"],
                "income_limit": {"max": 200000, "unit": "INR per annum"},
                "benefits": "Tuition fee reimbursement, maintenance allowance",
                "deadline": "30th November",
                "source_url": "https://example.gov.in/scholarship"
            }
        }


class ExtractionRequest(BaseModel):
    """Request model for LLM extraction."""
    
    content: str = Field(description="Extracted content from Tavily")
    source_url: str = Field(description="Original source URL")
    source_domain: Optional[str] = Field(default=None, description="Source domain")
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "Full extracted text from scholarship page...",
                "source_url": "https://scholarships.gov.in/scheme-123"
            }
        }


class ExtractionResponse(BaseModel):
    """Response model for LLM extraction."""
    
    success: bool
    scholarship: Optional[ScholarshipExtraction] = None
    error: Optional[str] = None
    extraction_metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "scholarship": {},
                "extraction_metadata": {
                    "content_length": 2500,
                    "extraction_time": "2026-09-17T01:55:00",
                    "model_used": "gpt-4"
                }
            }
        }
