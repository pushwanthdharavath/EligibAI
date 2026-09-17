from typing import List, Dict, Any, Tuple, Optional, Union
from datetime import datetime
from enum import Enum


class ComparisonStatus(str, Enum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    NOT_SPECIFIED = "NOT_SPECIFIED"


class OverallEligibility(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    POTENTIALLY_ELIGIBLE = "POTENTIALLY_ELIGIBLE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    NEEDS_MORE_INFORMATION = "NEEDS_MORE_INFORMATION"


class FieldComparison:
    """Result of comparing a single field."""
    
    def __init__(self, field_name: str, status: ComparisonStatus, reason: str, 
                 user_value: Any = None, required_value: Any = None, evidence: Optional[str] = None):
        self.field_name = field_name
        self.status = status
        self.reason = reason
        self.user_value = user_value
        self.required_value = required_value
        self.evidence = evidence
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "field": self.field_name,
            "status": self.status.value,
            "reason": self.reason,
            "user_value": self.user_value,
            "required_value": self.required_value,
            "evidence": self.evidence
        }


class EligibilityEngineV2:
    """
    Deterministic rule engine for comparing user profiles against scholarship eligibility requirements.
    Uses MATCH/MISMATCH/NOT_SPECIFIED to prevent assuming requirements that aren't explicitly stated.
    Designed for the new Tavily+LLM extraction pipeline.
    """
    
    def __init__(self):
        self.education_mapping = {
            "B.Tech": ["B.Tech", "B.E.", "Technical Degree", "Engineering", "Bachelor of Technology"],
            "Diploma": ["Diploma", "Polytechnic"],
            "B.Sc": ["B.Sc", "Bachelor of Science"],
            "B.Com": ["B.Com", "Bachelor of Commerce"],
            "B.A": ["B.A", "Bachelor of Arts"],
            "M.Tech": ["M.Tech", "M.E.", "Master of Technology", "Master of Engineering"],
            "M.Sc": ["M.Sc", "Master of Science"],
            "M.Com": ["M.Com", "Master of Commerce"],
            "MBA": ["MBA", "Master of Business Administration"],
            "Undergraduate": ["B.Tech", "B.E.", "B.Sc", "B.Com", "B.A", "Diploma"],
            "Postgraduate": ["M.Tech", "M.E.", "M.Sc", "M.Com", "MBA", "Ph.D"]
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
    
    def compare_education(self, user_education: str, required_courses: Optional[List[str]], 
                         required_levels: Optional[List[str]], evidence: Optional[str] = None) -> FieldComparison:
        """Compare user education against required education."""
        if not required_courses and not required_levels:
            return FieldComparison(
                field_name="education",
                status=ComparisonStatus.NOT_SPECIFIED,
                reason="Education requirement not specified in scholarship",
                user_value=user_education,
                required_value=None,
                evidence=evidence
            )
        
        user_edu_normalized = self.normalize_education(user_education)
        
        # Check courses
        if required_courses:
            required_normalized = [e.lower() for e in required_courses]
            for user_edu in user_edu_normalized:
                for req_edu in required_normalized:
                    if user_edu in req_edu or req_edu in user_edu:
                        return FieldComparison(
                            field_name="education",
                            status=ComparisonStatus.MATCH,
                            reason=f"Education matches ({user_education})",
                            user_value=user_education,
                            required_value=required_courses,
                            evidence=evidence
                        )
        
        # Check education levels
        if required_levels:
            for level in required_levels:
                if level in self.education_mapping:
                    if user_education in self.education_mapping[level]:
                        return FieldComparison(
                            field_name="education",
                            status=ComparisonStatus.MATCH,
                            reason=f"Education level matches ({level})",
                            user_value=user_education,
                            required_value=required_levels,
                            evidence=evidence
                        )
        
        return FieldComparison(
            field_name="education",
            status=ComparisonStatus.MISMATCH,
            reason=f"Education mismatch. Required: {', '.join(required_courses or required_levels or [])}",
            user_value=user_education,
            required_value=required_courses or required_levels,
            evidence=evidence
        )
    
    def compare_income(self, user_income: int, income_limit: Optional[Dict[str, Any]], 
                      evidence: Optional[str] = None) -> FieldComparison:
        """Compare user income against income limits."""
        if not income_limit:
            return FieldComparison(
                field_name="income",
                status=ComparisonStatus.NOT_SPECIFIED,
                reason="Income requirement not specified",
                user_value=user_income,
                required_value=None,
                evidence=evidence
            )
        
        income_max = income_limit.get("max")
        income_min = income_limit.get("min")
        
        if income_max is not None and user_income > income_max:
            return FieldComparison(
                field_name="income",
                status=ComparisonStatus.MISMATCH,
                reason=f"Income exceeds limit. Required: ≤ ₹{income_max:,}, Your income: ₹{user_income:,}",
                user_value=user_income,
                required_value=income_limit,
                evidence=evidence
            )
        
        if income_min is not None and user_income < income_min:
            return FieldComparison(
                field_name="income",
                status=ComparisonStatus.MISMATCH,
                reason=f"Income below minimum. Required: ≥ ₹{income_min:,}, Your income: ₹{user_income:,}",
                user_value=user_income,
                required_value=income_limit,
                evidence=evidence
            )
        
        if income_max is not None:
            return FieldComparison(
                field_name="income",
                status=ComparisonStatus.MATCH,
                reason=f"Income requirement satisfied (₹{user_income:,} ≤ ₹{income_max:,})",
                user_value=user_income,
                required_value=income_limit,
                evidence=evidence
            )
        
        if income_min is not None:
            return FieldComparison(
                field_name="income",
                status=ComparisonStatus.MATCH,
                reason=f"Income requirement satisfied (₹{user_income:,} ≥ ₹{income_min:,})",
                user_value=user_income,
                required_value=income_limit,
                evidence=evidence
            )
        
        return FieldComparison(
            field_name="income",
            status=ComparisonStatus.NOT_SPECIFIED,
            reason="Income requirement not specified",
            user_value=user_income,
            required_value=None,
            evidence=evidence
        )
    
    def compare_category(self, user_category: str, required_categories: Optional[List[str]], 
                       evidence: Optional[str] = None) -> FieldComparison:
        """Compare user category against required categories."""
        if not required_categories:
            return FieldComparison(
                field_name="category",
                status=ComparisonStatus.NOT_SPECIFIED,
                reason="Category requirement not specified",
                user_value=user_category,
                required_value=None,
                evidence=evidence
            )
        
        # Normalize categories for comparison
        user_cat_normalized = user_category.upper()
        required_normalized = [c.upper() for c in required_categories]
        
        if user_cat_normalized in required_normalized:
            return FieldComparison(
                field_name="category",
                status=ComparisonStatus.MATCH,
                reason=f"Category matches ({user_category})",
                user_value=user_category,
                required_value=required_categories,
                evidence=evidence
            )
        
        return FieldComparison(
            field_name="category",
            status=ComparisonStatus.MISMATCH,
            reason=f"Category mismatch. Required: {', '.join(required_categories)}, Your category: {user_category}",
            user_value=user_category,
            required_value=required_categories,
            evidence=evidence
        )
    
    def compare_state(self, user_state: str, required_state: Optional[str], 
                     evidence: Optional[str] = None) -> FieldComparison:
        """Compare user state against required state."""
        if not required_state:
            return FieldComparison(
                field_name="state",
                status=ComparisonStatus.NOT_SPECIFIED,
                reason="State requirement not specified",
                user_value=user_state,
                required_value=None,
                evidence=evidence
            )
        
        if user_state.lower() == required_state.lower():
            return FieldComparison(
                field_name="state",
                status=ComparisonStatus.MATCH,
                reason=f"State matches ({user_state})",
                user_value=user_state,
                required_value=required_state,
                evidence=evidence
            )
        
        return FieldComparison(
            field_name="state",
            status=ComparisonStatus.MISMATCH,
            reason=f"State mismatch. Required: {required_state}, Your state: {user_state}",
            user_value=user_state,
            required_value=required_state,
            evidence=evidence
        )
    
    def compare_age(self, user_age: int, age_limit: Optional[Dict[str, Any]], 
                   evidence: Optional[str] = None) -> FieldComparison:
        """Compare user age against age limits."""
        if not age_limit:
            return FieldComparison(
                field_name="age",
                status=ComparisonStatus.NOT_SPECIFIED,
                reason="Age requirement not specified",
                user_value=user_age,
                required_value=None,
                evidence=evidence
            )
        
        age_min = age_limit.get("min")
        age_max = age_limit.get("max")
        
        if age_min is not None and user_age < age_min:
            return FieldComparison(
                field_name="age",
                status=ComparisonStatus.MISMATCH,
                reason=f"Age below minimum. Required: ≥ {age_min}, Your age: {user_age}",
                user_value=user_age,
                required_value=age_limit,
                evidence=evidence
            )
        
        if age_max is not None and user_age > age_max:
            return FieldComparison(
                field_name="age",
                status=ComparisonStatus.MISMATCH,
                reason=f"Age exceeds maximum. Required: ≤ {age_max}, Your age: {user_age}",
                user_value=user_age,
                required_value=age_limit,
                evidence=evidence
            )
        
        if age_min is not None:
            return FieldComparison(
                field_name="age",
                status=ComparisonStatus.MATCH,
                reason=f"Age requirement satisfied ({user_age} ≥ {age_min})",
                user_value=user_age,
                required_value=age_limit,
                evidence=evidence
            )
        
        if age_max is not None:
            return FieldComparison(
                field_name="age",
                status=ComparisonStatus.MATCH,
                reason=f"Age requirement satisfied ({user_age} ≤ {age_max})",
                user_value=user_age,
                required_value=age_limit,
                evidence=evidence
            )
        
        return FieldComparison(
            field_name="age",
            status=ComparisonStatus.NOT_SPECIFIED,
            reason="Age requirement not specified",
            user_value=user_age,
            required_value=None,
            evidence=evidence
        )
    
    def compare_gender(self, user_gender: str, required_gender: Optional[str], 
                      evidence: Optional[str] = None) -> FieldComparison:
        """Compare user gender against required gender."""
        if not required_gender:
            return FieldComparison(
                field_name="gender",
                status=ComparisonStatus.NOT_SPECIFIED,
                reason="Gender requirement not specified",
                user_value=user_gender,
                required_value=None,
                evidence=evidence
            )
        
        if user_gender.lower() == required_gender.lower() or required_gender.lower() == "any":
            return FieldComparison(
                field_name="gender",
                status=ComparisonStatus.MATCH,
                reason=f"Gender matches ({user_gender})",
                user_value=user_gender,
                required_value=required_gender,
                evidence=evidence
            )
        
        return FieldComparison(
            field_name="gender",
            status=ComparisonStatus.MISMATCH,
            reason=f"Gender mismatch. Required: {required_gender}, Your gender: {user_gender}",
            user_value=user_gender,
            required_value=required_gender,
            evidence=evidence
        )
    
    def compare_disability(self, user_disability: str, disability_required: Optional[bool], 
                         evidence: Optional[str] = None) -> FieldComparison:
        """Compare user disability status against requirement."""
        if disability_required is None:
            return FieldComparison(
                field_name="disability",
                status=ComparisonStatus.NOT_SPECIFIED,
                reason="Disability requirement not specified",
                user_value=user_disability,
                required_value=None,
                evidence=evidence
            )
        
        user_has_disability = user_disability.lower() in ["yes", "true", "1"]
        
        if disability_required and not user_has_disability:
            return FieldComparison(
                field_name="disability",
                status=ComparisonStatus.MISMATCH,
                reason="Disability certificate required",
                user_value=user_disability,
                required_value=disability_required,
                evidence=evidence
            )
        
        return FieldComparison(
            field_name="disability",
            status=ComparisonStatus.MATCH,
            reason="Disability requirement satisfied",
            user_value=user_disability,
            required_value=disability_required,
            evidence=evidence
        )
    
    def compare_year_of_study(self, user_year: str, required_years: Optional[List[str]], 
                             evidence: Optional[str] = None) -> FieldComparison:
        """Compare user year of study against required years."""
        if not required_years:
            return FieldComparison(
                field_name="year_of_study",
                status=ComparisonStatus.NOT_SPECIFIED,
                reason="Year of study requirement not specified",
                user_value=user_year,
                required_value=None,
                evidence=evidence
            )
        
        if user_year in required_years:
            return FieldComparison(
                field_name="year_of_study",
                status=ComparisonStatus.MATCH,
                reason=f"Year of study matches ({user_year})",
                user_value=user_year,
                required_value=required_years,
                evidence=evidence
            )
        
        return FieldComparison(
            field_name="year_of_study",
            status=ComparisonStatus.MISMATCH,
            reason=f"Year of study mismatch. Required: {', '.join(required_years)}, Your year: {user_year}",
            user_value=user_year,
            required_value=required_years,
            evidence=evidence
        )
    
    def evaluate_eligibility(
        self, 
        scholarship_data: Dict[str, Any], 
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate user eligibility for a scholarship using the new structured data format.
        Returns a detailed comparison with MATCH/MISMATCH/NOT_SPECIFIED status for each parameter.
        """
        # Extract user profile values
        user_education = user_profile.get("course", "")
        user_income_str = user_profile.get("annualFamilyIncome", "0")
        user_category = user_profile.get("category", "")
        user_state = user_profile.get("state", "")
        user_age_str = user_profile.get("age", "0")
        user_gender = user_profile.get("gender", "")
        user_disability = user_profile.get("disabilityStatus", "No")
        user_year = user_profile.get("yearOfStudy", "")
        
        # Parse numeric values
        try:
            user_income = int(user_income_str.replace(",", "").replace("₹", "").strip())
        except (ValueError, TypeError):
            user_income = 0
        
        try:
            user_age = int(user_age_str)
        except (ValueError, TypeError):
            user_age = 0
        
        # Extract scholarship requirements
        scholarship_name = scholarship_data.get("scholarship_name", "Unknown Scholarship")
        source_url = scholarship_data.get("source_url", "")
        evidence_snippets = scholarship_data.get("evidence_snippets", [])
        
        # Build evidence for each field
        def get_evidence_for_field(field_keywords: List[str]) -> Optional[str]:
            """Find evidence snippet containing field keywords."""
            for snippet in evidence_snippets:
                if any(keyword.lower() in snippet.lower() for keyword in field_keywords):
                    return snippet
            return None
        
        # Compare each field
        comparisons = [
            self.compare_education(
                user_education,
                scholarship_data.get("course"),
                scholarship_data.get("education_level"),
                get_evidence_for_field(["education", "course", "degree"])
            ),
            self.compare_income(
                user_income,
                scholarship_data.get("income_limit"),
                get_evidence_for_field(["income", "salary", "financial"])
            ),
            self.compare_category(
                user_category,
                scholarship_data.get("category"),
                get_evidence_for_field(["category", "caste", "reserved"])
            ),
            self.compare_state(
                user_state,
                scholarship_data.get("state"),
                get_evidence_for_field(["state", "residence", "domicile"])
            ),
            self.compare_age(
                user_age,
                scholarship_data.get("age_limit"),
                get_evidence_for_field(["age", "years", "born"])
            ),
            self.compare_gender(
                user_gender,
                scholarship_data.get("gender"),
                get_evidence_for_field(["gender", "male", "female"])
            ),
            self.compare_disability(
                user_disability,
                scholarship_data.get("disability_required"),
                get_evidence_for_field(["disability", "disabled", "specially abled"])
            ),
            self.compare_year_of_study(
                user_year,
                scholarship_data.get("year_of_study"),
                get_evidence_for_field(["year", "semester", "study"])
            )
        ]
        
        # Count statuses
        mismatches = [c for c in comparisons if c.status == ComparisonStatus.MISMATCH]
        matches = [c for c in comparisons if c.status == ComparisonStatus.MATCH]
        not_specified = [c for c in comparisons if c.status == ComparisonStatus.NOT_SPECIFIED]
        
        # Determine overall eligibility
        if mismatches:
            overall_status = OverallEligibility.NOT_ELIGIBLE
            explanation = f"Not eligible due to {len(mismatches)} mismatching requirement(s)"
        elif not_specified and not matches:
            overall_status = OverallEligibility.NEEDS_MORE_INFORMATION
            explanation = "Insufficient eligibility information specified"
        elif not_specified:
            overall_status = OverallEligibility.POTENTIALLY_ELIGIBLE
            explanation = f"Potentially eligible - {len(not_specified)} requirement(s) not specified"
        else:
            overall_status = OverallEligibility.ELIGIBLE
            explanation = "Eligible - all requirements satisfied"
        
        return {
            "scholarship_name": scholarship_name,
            "source_url": source_url,
            "overall_status": overall_status.value,
            "explanation": explanation,
            "field_comparisons": [c.to_dict() for c in comparisons],
            "summary": {
                "matches": len(matches),
                "mismatches": len(mismatches),
                "not_specified": len(not_specified)
            },
            "evidence": {
                "matching_conditions": [c.reason for c in matches],
                "mismatching_conditions": [c.reason for c in mismatches],
                "unknown_requirements": [c.field_name for c in not_specified],
                "source_evidence": evidence_snippets
            },
            "evaluated_at": datetime.now().isoformat()
        }
    
    def evaluate_multiple_scholarships(
        self, 
        scholarships: List[Dict[str, Any]], 
        user_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Evaluate eligibility for multiple scholarships.
        Returns results sorted by eligibility status (Eligible first).
        """
        results = []
        for scholarship in scholarships:
            result = self.evaluate_eligibility(scholarship, user_profile)
            results.append(result)
        
        # Sort: ELIGIBLE > POTENTIALLY_ELIGIBLE > NEEDS_MORE_INFORMATION > NOT_ELIGIBLE
        status_order = {
            OverallEligibility.ELIGIBLE.value: 0,
            OverallEligibility.POTENTIALLY_ELIGIBLE.value: 1,
            OverallEligibility.NEEDS_MORE_INFORMATION.value: 2,
            OverallEligibility.NOT_ELIGIBLE.value: 3
        }
        
        results.sort(key=lambda x: status_order.get(x["overall_status"], 4))
        return results


# Global eligibility engine instance
eligibility_engine_v2 = EligibilityEngineV2()
