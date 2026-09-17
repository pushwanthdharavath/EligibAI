import json
from typing import List, Optional
from pathlib import Path
from app.models.scholarship import Scholarship

class ScholarshipDataset:
    """Manages the scholarship dataset loaded from JSON file."""
    
    def __init__(self, data_path: str = "data/scholarships.json"):
        self.data_path = Path(__file__).parent.parent.parent / data_path
        self.scholarships: List[Scholarship] = []
        self.load_dataset()
    
    def load_dataset(self):
        """Load scholarships from JSON file."""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.scholarships = [Scholarship(**item) for item in data]
            print(f"Loaded {len(self.scholarships)} scholarships from dataset")
        except FileNotFoundError:
            print(f"Warning: Scholarship dataset not found at {self.data_path}")
            self.scholarships = []
        except Exception as e:
            print(f"Error loading scholarship dataset: {e}")
            self.scholarships = []
    
    def get_all_scholarships(self) -> List[Scholarship]:
        """Return all scholarships."""
        return self.scholarships
    
    def get_scholarship_by_id(self, scholarship_id: str) -> Optional[Scholarship]:
        """Get a specific scholarship by ID."""
        for scholarship in self.scholarships:
            if scholarship.id == scholarship_id:
                return scholarship
        return None
    
    def filter_by_state(self, state: str) -> List[Scholarship]:
        """Filter scholarships by state (includes national schemes)."""
        filtered = []
        for scholarship in self.scholarships:
            if scholarship.state is None or scholarship.state == state:
                filtered.append(scholarship)
        return filtered
    
    def filter_by_education(self, education: str) -> List[Scholarship]:
        """Filter scholarships by education."""
        filtered = []
        for scholarship in self.scholarships:
            if scholarship.eligibility.education is None:
                continue
            for edu in scholarship.eligibility.education:
                if education.lower() in edu.lower() or edu.lower() in education.lower():
                    filtered.append(scholarship)
                    break
        return filtered
    
    def filter_by_category(self, category: str) -> List[Scholarship]:
        """Filter scholarships by category (includes schemes without category restriction)."""
        filtered = []
        for scholarship in self.scholarships:
            if scholarship.eligibility.category is None:
                filtered.append(scholarship)
            elif category in scholarship.eligibility.category:
                filtered.append(scholarship)
        return filtered
    
    def search_scholarships(self, filters: dict) -> List[Scholarship]:
        """
        Search scholarships based on multiple filters.
        Returns scholarships that match ALL provided filters.
        """
        results = self.scholarships.copy()
        
        if filters.get("state"):
            results = [s for s in results if s.state is None or s.state == filters["state"]]
        
        if filters.get("education"):
            results = [s for s in results if s.eligibility.education and 
                      any(filters["education"].lower() in edu.lower() or edu.lower() in filters["education"].lower() 
                          for edu in s.eligibility.education)]
        
        if filters.get("category"):
            results = [s for s in results if s.eligibility.category is None or 
                      filters["category"] in s.eligibility.category]
        
        return results