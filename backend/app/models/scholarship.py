from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from enum import Enum

class ComparisonOperator(str, Enum):
    LESS_THAN = "<"
    LESS_THAN_EQUAL = "<="
    GREATER_THAN = ">"
    GREATER_THAN_EQUAL = ">="
    EQUAL = "=="
    NOT_EQUAL = "!="
    IN = "in"
    NOT_IN = "not_in"

class EligibilityRule(BaseModel):
    parameter: str  # e.g., "family_income", "education", "state"
    operator: ComparisonOperator
    value: Union[str, int, float, List[str]]
    description: Optional[str] = None

class ScholarshipEligibility(BaseModel):
    education: Optional[List[str]] = None
    income_max: Optional[int] = None
    income_min: Optional[int] = None
    category: Optional[List[str]] = None
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    gender: Optional[str] = None
    state: Optional[List[str]] = None
    disability_required: Optional[bool] = None
    year_of_study: Optional[List[str]] = None
    college_type: Optional[List[str]] = None
    additional_rules: List[EligibilityRule] = []

class Scholarship(BaseModel):
    id: str
    scheme_name: str
    provider: str
    state: Optional[str] = None
    academic_year: str
    eligibility: ScholarshipEligibility
    benefit: str
    deadline: str
    source_url: str
    required_documents: Optional[List[str]] = None
    application_process: Optional[str] = None
    last_updated: Optional[str] = None
    metadata: Dict[str, Any] = {}