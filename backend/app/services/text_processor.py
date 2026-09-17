from typing import List, Dict, Any
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter

class TextProcessor:
    """Service for processing and chunking text for RAG."""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\-\(\)]', '', text)
        return text.strip()
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks for embedding."""
        chunks = self.text_splitter.split_text(text)
        return [self.clean_text(chunk) for chunk in chunks if chunk.strip()]
    
    def prepare_scholarship_for_embedding(self, scholarship: Dict[str, Any]) -> List[str]:
        """Prepare scholarship data for embedding by creating searchable text chunks."""
        chunks = []
        
        # Create comprehensive text representation
        scholarship_text = f"""
        Scholarship Name: {scholarship['scheme_name']}
        Provider: {scholarship['provider']}
        State: {scholarship.get('state', 'All India')}
        Academic Year: {scholarship['academic_year']}
        
        Eligibility Requirements:
        Education: {', '.join(scholarship['eligibility'].get('education', ['Not specified']))}
        Income Limit: {scholarship['eligibility'].get('income_max', 'Not specified')}
        Category: {', '.join(scholarship['eligibility'].get('category', ['Not specified']))}
        Age Requirements: {scholarship['eligibility'].get('age_min', 'Not specified')} to {scholarship['eligibility'].get('age_max', 'Not specified')}
        Gender: {scholarship['eligibility'].get('gender', 'Not specified')}
        State: {', '.join(scholarship['eligibility'].get('state', ['Not specified']))}
        Year of Study: {', '.join(scholarship['eligibility'].get('year_of_study', ['Not specified']))}
        
        Benefits: {scholarship['benefit']}
        Deadline: {scholarship['deadline']}
        
        Required Documents: {', '.join(scholarship.get('required_documents', ['Not specified']))}
        Application Process: {scholarship.get('application_process', 'Not specified')}
        """
        
        # Chunk the comprehensive text
        chunks.extend(self.chunk_text(scholarship_text))
        
        # Also create specific focused chunks for better retrieval
        focused_chunks = [
            f"{scholarship['scheme_name']} - Eligibility: Education {', '.join(scholarship['eligibility'].get('education', []))}, Income {scholarship['eligibility'].get('income_max', 'N/A')}, Category {', '.join(scholarship['eligibility'].get('category', []))}",
            f"{scholarship['scheme_name']} - Benefits: {scholarship['benefit']}",
            f"{scholarship['scheme_name']} - Provider: {scholarship['provider']}, State: {scholarship.get('state', 'All India')}",
            f"{scholarship['scheme_name']} - Deadline: {scholarship['deadline']}, Documents: {', '.join(scholarship.get('required_documents', []))}"
        ]
        
        chunks.extend(focused_chunks)
        
        return chunks
    
    def create_metadata(self, scholarship: Dict[str, Any], chunk_index: int) -> Dict[str, Any]:
        """Create metadata for a chunk."""
        return {
            "scholarship_id": scholarship["id"],
            "scheme_name": scholarship["scheme_name"],
            "provider": scholarship["provider"],
            "state": scholarship.get("state"),
            "education": scholarship["eligibility"].get("education", []),
            "category": scholarship["eligibility"].get("category", []),
            "chunk_index": chunk_index,
            "academic_year": scholarship["academic_year"],
            "source_url": scholarship["source_url"],
            "deadline": scholarship["deadline"]
        }