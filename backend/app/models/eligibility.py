from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class UserProfile(BaseModel):
    fullName: str = Field(..., description="Student's full name")
    age: str = Field(..., description="Student's age")
    gender: str = Field(..., description="Student's gender")
    state: str = Field(..., description="Student's state")
    district: Optional[str] = Field(None, description="Student's district (optional)")
    category: str = Field(..., description="Student's category (General/OBC/SC/ST/EWS)")
    course: str = Field(..., description="Course being pursued")
    yearOfStudy: str = Field(..., description="Current year of study")
    annualFamilyIncome: str = Field(..., description="Annual family income in INR")
    disabilityStatus: str = Field(..., description="Disability status (Yes/No)")
    searchQuery: str = Field(default="Find every scholarship I'm eligible for.", description="Natural language search query")

class ScholarshipResult(BaseModel):
    name: str
    status: str  # "Eligible", "Potentially Eligible", "Not Eligible"
    reasons: List[str]
    benefit: str
    deadline: str
    sourceUrl: Optional[str] = None
    provider: Optional[str] = None

class EligibilityResponse(BaseModel):
    scholarships: List[ScholarshipResult]
    profile: Dict[str, Any]
    totalFound: int
    processingTime: float