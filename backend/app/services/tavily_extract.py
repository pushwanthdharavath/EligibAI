from tavily import TavilyClient
from typing import List, Dict, Any, Optional
import os
from datetime import datetime
import base64

class TavilyExtractService:
    """Service for extracting complete content from scholarship URLs using Tavily."""
    
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY", "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")
        self.client = TavilyClient(api_key=self.api_key)
    
    def extract_scholarship_content(
        self, 
        urls: List[str],
        extract_depth: str = "advanced"
    ) -> List[Dict[str, Any]]:
        """
        Extract complete content from scholarship URLs.
        
        Args:
            urls: List of scholarship URLs to extract
            extract_depth: Extraction depth ("basic" or "advanced")
            
        Returns:
            List of extracted content with metadata
        """
        try:
            # Limit to 5 URLs per request to avoid rate limiting
            urls_to_extract = urls[:5]
            
            extract_result = self.client.extract(
                urls=urls_to_extract,
                extract_depth=extract_depth
            )
            
            results = []
            for result in extract_result.get("results", []):
                extracted_content = {
                    "url": result.get("url"),
                    "title": result.get("title"),
                    "content": result.get("raw_content") or result.get("content"),
                    "markdown_content": result.get("markdown_content"),
                    "extracted_at": datetime.now().isoformat(),
                    "word_count": len((result.get("raw_content") or result.get("content", "")).split()),
                    "source_type": self._identify_content_type(result.get("url"))
                }
                results.append(extracted_content)
            
            return results
            
        except Exception as e:
            print(f"Tavily extract error: {e}")
            return []
    
    def extract_single_scholarship(
        self, 
        url: str,
        extract_depth: str = "advanced"
    ) -> Optional[Dict[str, Any]]:
        """
        Extract content from a single scholarship URL.
        
        Args:
            url: Single scholarship URL
            extract_depth: Extraction depth
            
        Returns:
            Extracted content or None if failed
        """
        try:
            result = self.client.extract(
                urls=[url],
                extract_depth=extract_depth
            )
            
            if result.get("results"):
                extracted = result["results"][0]
                return {
                    "url": extracted.get("url"),
                    "title": extracted.get("title"),
                    "content": extracted.get("raw_content") or extracted.get("content"),
                    "markdown_content": extracted.get("markdown_content"),
                    "extracted_at": datetime.now().isoformat(),
                    "word_count": len((extracted.get("raw_content") or extracted.get("content", "")).split()),
                    "source_type": self._identify_content_type(url)
                }
            
            return None
            
        except Exception as e:
            print(f"Single extraction error: {e}")
            return None
    
    def _identify_content_type(self, url: str) -> str:
        """Identify if the URL is a webpage or PDF."""
        if url.lower().endswith('.pdf'):
            return "PDF"
        elif url.lower().endswith('.doc') or url.lower().endswith('.docx'):
            return "Document"
        else:
            return "Webpage"
    
    def clean_extracted_content(self, content: str) -> str:
        """
        Clean and normalize extracted content.
        
        Args:
            content: Raw extracted content
            
        Returns:
            Cleaned content
        """
        if not content:
            return ""
        
        # Remove excessive whitespace
        cleaned = " ".join(content.split())
        
        # Remove common artifacts
        artifacts = [
            "Click here to view details",
            "Download PDF",
            "Last updated",
            "Back to top"
        ]
        
        for artifact in artifacts:
            cleaned = cleaned.replace(artifact, "")
        
        return cleaned.strip()
    
    def extract_structured_sections(self, content: str) -> Dict[str, str]:
        """
        Attempt to extract structured sections from content.
        
        Args:
            content: Extracted content
            
        Returns:
            Dictionary with extracted sections
        """
        sections = {
            "eligibility": "",
            "benefits": "",
            "deadline": "",
            "application_process": "",
            "required_documents": ""
        }
        
        content_lower = content.lower()
        
        # Try to find eligibility section
        if "eligibility" in content_lower:
            sections["eligibility"] = self._extract_section(content, "eligibility")
        
        # Try to find benefits section
        if "benefit" in content_lower or "amount" in content_lower:
            sections["benefits"] = self._extract_section(content, "benefit")
        
        # Try to find deadline section
        if "deadline" in content_lower or "last date" in content_lower:
            sections["deadline"] = self._extract_section(content, "deadline")
        
        # Try to find application process
        if "application" in content_lower or "apply" in content_lower:
            sections["application_process"] = self._extract_section(content, "application")
        
        # Try to find required documents
        if "document" in content_lower or "certificate" in content_lower:
            sections["required_documents"] = self._extract_section(content, "document")
        
        return sections
    
    def _extract_section(self, content: str, keyword: str) -> str:
        """Extract text around a keyword."""
        content_lower = content.lower()
        keyword_index = content_lower.find(keyword.lower())
        
        if keyword_index == -1:
            return ""
        
        # Extract text around the keyword (500 characters)
        start = max(0, keyword_index - 50)
        end = min(len(content), keyword_index + 450)
        
        return content[start:end].strip()