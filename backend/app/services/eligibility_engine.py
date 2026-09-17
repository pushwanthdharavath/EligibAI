from typing import List, Dict, Any, Tuple, Optional, Union
from app.models.scholarship import Scholarship, ScholarshipEligibility, ComparisonOperator
from app.models.eligibility import UserProfile

class ComparisonResult:
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    NOT_SPECIFIED = "NOT_SPECIFIED"

class EligibilityEngine:
    """
    Deterministic rule engine for comparing user profiles against scholarship eligibility requirements.
    Uses MATCH/MISMATCH/NOT_SPECIFIED to prevent assuming requirements that aren't explicitly stated.
    """
    
    def __init__(self):
        self.education_mapping = {
            "B.Tech": ["B.Tech", "B.E.", "Technical Degree", "Engineering"],
            "Diploma": ["Diploma", "Polytechnic"],
            "B.Sc": ["B.Sc", "Bachelor of Science"],
            "B.Com": ["B.Com", "Bachelor of Commerce"],
            "B.A": ["B.A", "Bachelor of Arts"],
            "M.Tech": ["M.Tech", "M.E.", "Master of Technology", "Master of Engineering"],
            "M.Sc": ["M.Sc", "Master of Science"],
            "M.Com": ["M.Com", "Master of Commerce"],
            "MBA": ["MBA", "Master of Business Administration"],
        }
    
    def normalize_education(self, education: str) -> List[str]:
        """Normalize education to include possible aliases."""
        if not education:
            return []
        normalized = [education.lower()]
        for key, aliases in self.education_mapping.items():
            if education.lower() in [a.lower() for a in aliases]:
                normalized.extend([a.lower() for a in aliases])
        return list(set(normalized))
    
    def compare_education(self, user_education: str, required_education: Optional[List[str]]) -> Tuple[str, str]:
        """Compare user education against required education."""
        if not required_education:
            return ComparisonResult.NOT_SPECIFIED, "Education requirement not specified"
        
        user_edu_normalized = self.normalize_education(user_education)
        required_normalized = [e.lower() for e in required_education]
        
        for user_edu in user_edu_normalized:
            for req_edu in required_normalized:
                if user_edu in req_edu or req_edu in user_edu:
                    return ComparisonResult.MATCH, f"Education matches ({user_education})"
        
        return ComparisonResult.MISMATCH, f"Education mismatch. Required: {', '.join(required_education)}"
    
    def compare_income(self, user_income: int, income_max: Optional[int], income_min: Optional[int]) -> Tuple[str, str]:
        """Compare user income against income limits."""
        if income_max is None and income_min is None:
            return ComparisonResult.NOT_SPECIFIED, "Income requirement not specified"
        
        if income_max is not None and user_income > income_max:
            return ComparisonResult.MISMATCH, f"Income exceeds limit. Required: ≤ ₹{income_max:,}, Your income: ₹{user_income:,}"
        
        if income_min is not None and user_income < income_min:
            return ComparisonResult.MISMATCH, f"Income below minimum. Required: ≥ ₹{income_min:,}, Your income: ₹{user_income:,}"
        
        if income_max is not None:
            return ComparisonResult.MATCH, f"Income requirement satisfied (₹{user_income:,} ≤ ₹{income_max:,})"
        
        if income_min is not None:
            return ComparisonResult.MATCH, f"Income requirement satisfied (₹{user_income:,} ≥ ₹{income_min:,})"
        
        return ComparisonResult.NOT_SPECIFIED, "Income requirement not specified"
    
    def compare_category(self, user_category: str, required_categories: Optional[List[str]]) -> Tuple[str, str]:
        """Compare user category against required categories."""
        if not required_categories:
            return ComparisonResult.NOT_SPECIFIED, "Category requirement not specified"
        
        if user_category in required_categories:
            return ComparisonResult.MATCH, f"Category matches ({user_category})"
        
        return ComparisonResult.MISMATCH, f"Category mismatch. Required: {', '.join(required_categories)}, Your category: {user_category}"
    
    def compare_state(self, user_state: str, required_states: Optional[List[str]]) -> Tuple[str, str]:
        """Compare user state against required states."""
        if not required_states:
            return ComparisonResult.NOT_SPECIFIED, "State requirement not specified"
        
        if user_state in required_states:
            return ComparisonResult.MATCH, f"State matches ({user_state})"
        
        return ComparisonResult.MISMATCH, f"State mismatch. Required: {', '.join(required_states)}, Your state: {user_state}"
    
    def compare_age(self, user_age: int, age_min: Optional[int], age_max: Optional[int]) -> Tuple[str, str]:
        """Compare user age against age limits."""
        if age_min is None and age_max is None:
            return ComparisonResult.NOT_SPECIFIED, "Age requirement not specified"
        
        if age_min is not None and user_age < age_min:
            return ComparisonResult.MISMATCH, f"Age below minimum. Required: ≥ {age_min}, Your age: {user_age}"
        
        if age_max is not None and user_age > age_max:
            return ComparisonResult.MISMATCH, f"Age exceeds maximum. Required: ≤ {age_max}, Your age: {user_age}"
        
        if age_min is not None:
            return ComparisonResult.MATCH, f"Age requirement satisfied ({user_age} ≥ {age_min})"
        
        if age_max is not None:
            return ComparisonResult.MATCH, f"Age requirement satisfied ({user_age} ≤ {age_max})"
        
        return ComparisonResult.NOT_SPECIFIED, "Age requirement not specified"
    
    def compare_gender(self, user_gender: str, required_gender: Optional[str]) -> Tuple[str, str]:
        """Compare user gender against required gender."""
        if not required_gender:
            return ComparisonResult.NOT_SPECIFIED, "Gender requirement not specified"
        
        if user_gender == required_gender or required_gender.lower() == "any":
            return ComparisonResult.MATCH, f"Gender matches ({user_gender})"
        
        return ComparisonResult.MISMATCH, f"Gender mismatch. Required: {required_gender}, Your gender: {user_gender}"
    
    def compare_disability(self, user_disability: str, disability_required: Optional[bool]) -> Tuple[str, str]:
        """Compare user disability status against requirement."""
        if disability_required is None:
            return ComparisonResult.NOT_SPECIFIED, "Disability requirement not specified"
        
        user_has_disability = user_disability.lower() == "yes"
        
        if disability_required and not user_has_disability:
            return ComparisonResult.MISMATCH, "Disability certificate required"
        
        if not disability_required and user_has_disability:
            return ComparisonResult.MATCH, "Disability status acceptable"
        
        return ComparisonResult.MATCH, "Disability requirement satisfied"
    
    def compare_year_of_study(self, user_year: str, required_years: Optional[List[str]]) -> Tuple[str, str]:
        """Compare user year of study against required years."""
        if not required_years:
            return ComparisonResult.NOT_SPECIFIED, "Year of study requirement not specified"
        
        if user_year in required_years:
            return ComparisonResult.MATCH, f"Year of study matches ({user_year})"
        
        return ComparisonResult.MISMATCH, f"Year of study mismatch. Required: {', '.join(required_years)}, Your year: {user_year}"
    
    def evaluate_eligibility(self, scholarship: Scholarship, user_profile: Union[UserProfile, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate user eligibility for a scholarship.
        Returns a detailed comparison with MATCH/MISMATCH/NOT_SPECIFIED status for each parameter.
        """
        # Handle both UserProfile object and dict
        if isinstance(user_profile, dict):
            # Extract fields from dict
            annual_income = user_profile.get("annualFamilyIncome", "0")
            age = user_profile.get("age", "0")
            course = user_profile.get("course", "")
            state = user_profile.get("state", "")
            category = user_profile.get("category", "")
            year = user_profile.get("yearOfStudy", "")
            gender = user_profile.get("gender", "")
            disability = user_profile.get("disabilityStatus", "No")
        else:
            # Extract from UserProfile object
            annual_income = user_profile.annualFamilyIncome
            age = user_profile.age
            course = user_profile.course
            state = user_profile.state
            category = user_profile.category
            year = user_profile.yearOfStudy
            gender = user_profile.gender
            disability = user_profile.disabilityStatus
        
        eligibility = scholarship.eligibility
        results = {
            "scholarship_id": scholarship.id,
            "scholarship_name": scholarship.scheme_name,
            "comparisons": {},
            "overall_status": None,
            "reasons": []
        }
        
        # Parse user income
        try:
            user_income = int(annual_income)
        except (ValueError, TypeError):
            user_income = 0
        
        # Parse user age
        try:
            user_age = int(age)
        except (ValueError, TypeError):
            user_age = 0
        
        # Compare each parameter
        comparisons = {
            "education": self.compare_education(course, eligibility.education),
            "income": self.compare_income(user_income, eligibility.income_max, eligibility.income_min),
            "category": self.compare_category(category, eligibility.category),
            "state": self.compare_state(state, eligibility.state),
            "age": self.compare_age(user_age, eligibility.age_min, eligibility.age_max),
            "gender": self.compare_gender(gender, eligibility.gender),
            "disability": self.compare_disability(disability, eligibility.disability_required),
            "year_of_study": self.compare_year_of_study(year, eligibility.year_of_study),
        }
        
        results["comparisons"] = comparisons
        
        # Determine overall status
        mismatches = [k for k, (status, _) in comparisons.items() if status == ComparisonResult.MISMATCH]
        matches = [k for k, (status, _) in comparisons.items() if status == ComparisonResult.MATCH]
        not_specified = [k for k, (status, _) in comparisons.items() if status == ComparisonResult.NOT_SPECIFIED]
        
        if mismatches:
            results["overall_status"] = "Not Eligible"
            results["reasons"] = [comparisons[k][1] for k in mismatches]
        elif not_specified and not matches:
            results["overall_status"] = "Not Eligible"
            results["reasons"] = ["No eligibility criteria specified"]
        elif not_specified:
            results["overall_status"] = "Potentially Eligible"
            results["reasons"] = [comparisons[k][1] for k in matches]
            if not_specified:
                results["reasons"].append(f"Some eligibility information not specified: {', '.join(not_specified)}")
        else:
            results["overall_status"] = "Eligible"
            results["reasons"] = [comparisons[k][1] for k in matches]
        
        return results